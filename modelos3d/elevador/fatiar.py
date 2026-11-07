# Fatiamento pelo CLI do Bambu Studio: A1 mini 0.4, PLA Lite (0.20 mm Standard por padrão).
#
# Uso: fatiar(["a.stl", "b.stl"], "prato.3mf") -> minutos estimados.
#
# Os perfis de sistema do Bambu herdam de outros ("inherits"), e o CLI NÃO
# resolve essa herança: com o arquivo do sistema direto, ele cai no padrão
# interno (camada 0,20 genérica, qualquer que seja o perfil pedido). Por isso
# os perfis são achatados aqui (pai → filho) num diretório temporário antes de
# ir para o CLI.
#
# O CLI deixa um result.json na pasta de saída; ele é lido e apagado aqui.
# Com pasta_png, gera a imagem do prato e a move para lá (fora do projeto).

import glob
import json
import os
import shutil
import subprocess
import tempfile

BAMBU = "/Applications/BambuStudio.app/Contents/MacOS/BambuStudio"
PERFIS = "/Applications/BambuStudio.app/Contents/Resources/profiles/BBL"
MAQUINA = "Bambu Lab A1 mini 0.4 nozzle"
FILAMENTO = "Bambu PLA Lite @BBL A1M"
PROCESSO = "0.20mm Standard @BBL A1M"


def perfil_achatado(categoria, nome):
    # Junta a cadeia de herança do perfil, da raiz para o perfil pedido.
    cadeia = []
    atual = nome
    while atual:
        caminho = os.path.join(PERFIS, categoria, atual + ".json")
        if not os.path.exists(caminho):
            raise FileNotFoundError("perfil não encontrado: %s/%s" % (categoria, atual))
        with open(caminho) as f:
            dados = json.load(f)
        cadeia.append(dados)
        atual = dados.get("inherits")
    final = {}
    for dados in reversed(cadeia):
        final.update(dados)
    # Como um preset de usuário do Studio: todas as chaves explícitas e
    # "inherits" apontando para o preset de sistema (a checagem de
    # compatibilidade impressora × processo usa esse nome).
    final["inherits"] = nome
    final["name"] = nome + " (achatado)"
    final["from"] = "User"
    return final


def _gravar_perfis(pasta, processo):
    caminhos = []
    for categoria, nome in (("machine", MAQUINA), ("process", processo),
                            ("filament", FILAMENTO)):
        destino = os.path.join(pasta, categoria + ".json")
        with open(destino, "w") as f:
            json.dump(perfil_achatado(categoria, nome), f)
        caminhos.append(destino)
    return caminhos


def _contar_pratos(arquivo_3mf):
    # Número de pratos no 3MF (Metadata/model_settings.config).
    import zipfile
    if not os.path.exists(arquivo_3mf):
        return 0
    with zipfile.ZipFile(arquivo_3mf) as z:
        try:
            texto = z.read("Metadata/model_settings.config").decode("utf-8", "replace")
        except KeyError:
            return 1
    return max(1, texto.count("<plate>"))


def fatiar(stls, nome_3mf, pasta=None, pasta_png=None, processo=PROCESSO):
    # processo: nome de um perfil em profiles/BBL/process (sem .json).
    pasta = pasta or os.path.dirname(os.path.abspath(__file__))
    minutos = None
    erro = None
    camada = None
    gramas = None
    # Tudo acontece numa pasta temporária: além do 3MF, o CLI grava ali o
    # result.json e um plate_N.gcode solto. Só o 3MF vai para a pasta final.
    with tempfile.TemporaryDirectory() as tmp:
        maquina, proc, filamento = _gravar_perfis(tmp, processo)
        cmd = [
            BAMBU, "--slice", "1", "--arrange", "1", "--orient", "0",
            "--load-settings", maquina + ";" + proc,
            "--load-filaments", filamento,
            "--export-3mf", nome_3mf,          # nome relativo: o CLI junta com --outputdir
            "--outputdir", tmp,
        ]
        cmd += [os.path.abspath(s) for s in stls]
        saida = subprocess.run(cmd, capture_output=True, text=True, cwd=tmp)

        resultado = os.path.join(tmp, "result.json")
        if os.path.exists(resultado):
            with open(resultado) as f:
                dados = json.load(f)
            erro = dados.get("error_string")
            camada = dados.get("layer_height")
            pratos = dados.get("sliced_plates") or []
            if pratos:
                minutos = pratos[0].get("main_predication", 0) / 60.0
                filamentos = pratos[0].get("filaments") or []
                gramas = sum(f.get("total_used_g", 0) for f in filamentos) or None
        gerado = os.path.join(tmp, nome_3mf)
        n_pratos = _contar_pratos(gerado)
        if n_pratos > 1:
            # O --arrange abre outro prato quando as peças não cabem juntas, e o
            # CLI só fatia o primeiro: o tempo sairia errado e faltariam peças.
            erro = "as peças não cabem num prato só (%d pratos)" % n_pratos
            minutos = None
        if minutos is not None and os.path.exists(gerado):
            shutil.move(gerado, os.path.join(pasta, nome_3mf))
    if pasta_png and minutos is not None:
        # O CLI não aceita --export-png junto com o fatiamento: chamada separada,
        # direto na pasta das imagens (fora do projeto).
        os.makedirs(pasta_png, exist_ok=True)
        antes = set(glob.glob(os.path.join(pasta_png, "*.png")))
        # Roda dentro da pasta das imagens e apaga as sobras (gcode, result.json).
        subprocess.run([BAMBU, "--export-png", "0", "--outputdir", pasta_png,
                        os.path.join(pasta, nome_3mf)], capture_output=True, text=True,
                       cwd=pasta_png)
        base = os.path.splitext(nome_3mf)[0]
        for png in sorted(set(glob.glob(os.path.join(pasta_png, "*.png"))) - antes):
            shutil.move(png, os.path.join(pasta_png, base + "_" + os.path.basename(png)))
        for extra in glob.glob(os.path.join(pasta_png, "*.gcode")) + [
                os.path.join(pasta_png, "result.json")]:
            if os.path.exists(extra):
                os.remove(extra)
    avisos = [l for l in (saida.stdout + saida.stderr).splitlines()
              if "float" in l.lower() or "[error]" in l.lower()]
    return {"minutos": minutos, "erro": erro, "avisos": avisos, "camada": camada,
            "gramas": gramas, "arquivo": os.path.join(pasta, nome_3mf)}
