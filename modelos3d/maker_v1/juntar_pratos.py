# Junta os 3MF de um prato só (saídos do fatiar()) num projeto do Bambu Studio
# com vários pratos, para abrir tudo numa janela só.
#
#   juntar(["a.3mf", "b.3mf"], "todos.3mf", base="b.3mf", camadas={"a.3mf": 0.28})
#
# O projeto fica com os ajustes de processo do 3MF `base`. Os pratos que pediam
# outra altura de camada ganham um ajuste POR OBJETO (layer_height), que o Bambu
# mostra na lista de objetos. Depois de juntar, o CLI fatia todos os pratos de
# novo (--slice 0), e o resultado traz o tempo e as gramas de cada prato.
#
# Os pratos do Bambu ficam numa grade: com n pratos, ceil(sqrt(n)) colunas, e cada
# prato fica a 1,2 × o tamanho da mesa do anterior (x para a direita, y para
# baixo). As peças de cada arquivo são deslocadas para o prato dele.

import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
import zipfile

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(AQUI, "..", "elevador"))
from fatiar import BAMBU  # noqa: E402

MESA = 180.0                       # A1 mini
PASSO_PRATO = MESA * 1.2           # LOGICAL_PART_PLATE_GAP do Bambu = 1/5
DESLOCA_ID = 1000                  # ids do arquivo k ganham k × 1000

_FIXOS = ("[Content_Types].xml", "_rels/.rels")


def _origem(k, n):
    colunas = int(round(math.sqrt(n)))
    if math.sqrt(n) > colunas:
        colunas += 1
    return (k % colunas) * PASSO_PRATO, -(k // colunas) * PASSO_PRATO


def _novo_uuid(m):
    return '%s="%s"' % (m.group(1), uuid.uuid4())


def _renumerar(texto, desloca, atributos):
    for nome in atributos:
        texto = re.sub(r'(\b%s=")(\d+)"' % nome,
                       lambda m: '%s%d"' % (m.group(1), int(m.group(2)) + desloca), texto)
    return re.sub(r'(p:UUID)="[^"]*"', _novo_uuid, texto)


def _mover_item(item, dx, dy):
    def troca(m):
        v = [float(x) for x in m.group(1).split()]
        v[9] += dx
        v[10] += dy
        return 'transform="%s"' % " ".join("%.6g" % x for x in v)
    return re.sub(r'transform="([^"]*)"', troca, item)


def juntar(arquivos, destino, base=None, camadas=None):
    camadas = camadas or {}
    base = base or arquivos[0]
    n = len(arquivos)
    objetos, itens, cfg_objetos, cfg_pratos, arquivos_obj = [], [], [], [], {}
    figuras = {}
    total_malhas = 0
    with zipfile.ZipFile(base) as z:
        projeto = z.read("Metadata/project_settings.config")
        fixos = {f: z.read(f) for f in _FIXOS}
        cabecalho = z.read("3D/3dmodel.model").decode().split("<resources>")[0]
    for k, arq in enumerate(arquivos):
        d = k * DESLOCA_ID
        dx, dy = _origem(k, n)
        with zipfile.ZipFile(arq) as z:
            modelo = z.read("3D/3dmodel.model").decode()
            cfg = z.read("Metadata/model_settings.config").decode()
            for nome in z.namelist():
                m = re.match(r"3D/Objects/object_(\d+)\.model$", nome)
                if m:
                    novo = "3D/Objects/object_%d.model" % (int(m.group(1)) + d)
                    arquivos_obj[novo] = _renumerar(z.read(nome).decode(), d, ["id"])
                    total_malhas += 1
                for fig in ("plate_1.png", "plate_1_small.png", "plate_no_light_1.png",
                            "top_1.png", "pick_1.png"):
                    if nome == "Metadata/" + fig:
                        figuras["Metadata/" + fig.replace("_1", "_%d" % (k + 1))] = z.read(nome)
        # 3dmodel.model: objetos (com componentes) e itens da montagem.
        recursos = modelo.split("<resources>")[1].split("</resources>")[0]
        for obj in re.findall(r"<object .*?</object>", recursos, re.S):
            obj = re.sub(r'(p:path="/3D/Objects/object_)(\d+)(\.model")',
                         lambda m: "%s%d%s" % (m.group(1), int(m.group(2)) + d, m.group(3)), obj)
            objetos.append(_renumerar(obj, d, ["id", "objectid"]))
        for item in re.findall(r"<item [^>]*/>", modelo):
            itens.append(_mover_item(_renumerar(item, d, ["objectid"]), dx, dy))
        # model_settings.config: objetos (+ camada própria) e o prato.
        for obj in re.findall(r"  <object id=.*?\n  </object>", cfg, re.S):
            obj = re.sub(r'(<object id="|<part id=")(\d+)"',
                         lambda m: '%s%d"' % (m.group(1), int(m.group(2)) + d), obj)
            camada = camadas.get(arq)
            if camada:
                obj = obj.replace('<metadata key="extruder" value="1"/>',
                                  '<metadata key="extruder" value="1"/>\n'
                                  '    <metadata key="layer_height" value="%g"/>' % camada, 1)
            cfg_objetos.append(obj)
        prato = re.search(r"  <plate>.*?</plate>", cfg, re.S).group(0)
        prato = re.sub(r'(key="(?:object_id|identify_id)" value=")(\d+)"',
                       lambda m: '%s%d"' % (m.group(1), int(m.group(2)) + d), prato)
        prato = prato.replace('key="plater_id" value="1"', 'key="plater_id" value="%d"' % (k + 1))
        nome_prato = os.path.splitext(os.path.basename(arq))[0]
        prato = prato.replace('key="plater_name" value=""',
                              'key="plater_name" value="%s"' % nome_prato)
        prato = re.sub(r'(value="Metadata/[a-z_]+)_1(\.(?:png|gcode))"',
                       lambda m: '%s_%d%s"' % (m.group(1), k + 1, m.group(2)), prato)
        prato = prato.replace('value="Metadata/plate_%d.gcode"' % (k + 1), 'value=""')
        cfg_pratos.append(prato)

    modelo = (cabecalho + "<resources>\n  " + "\n  ".join(objetos) + "\n </resources>\n"
              ' <build p:UUID="%s">\n  ' % uuid.uuid4() + "\n  ".join(itens)
              + "\n </build>\n</model>\n")
    cfg = ('<?xml version="1.0" encoding="UTF-8"?>\n<config>\n' + "\n".join(cfg_objetos)
           + "\n" + "\n".join(cfg_pratos) + "\n  <assemble>\n  </assemble>\n</config>\n")
    rels = ('<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas'
            '.openxmlformats.org/package/2006/relationships">\n'
            + "".join(' <Relationship Target="/%s" Id="rel-%d" Type="http://schemas.microsoft'
                      '.com/3dmanufacturing/2013/01/3dmodel"/>\n' % (f, i + 1)
                      for i, f in enumerate(sorted(arquivos_obj)))
            + "</Relationships>")
    corte = ('<?xml version="1.0" encoding="utf-8"?>\n<objects>\n'
             + "".join(' <object id="%d">\n  <cut_id id="0" check_sum="1" connectors_cnt="0"/>\n'
                       ' </object>\n' % (i + 1) for i in range(total_malhas))
             + "</objects>\n")
    sequencia = {"plate_%d" % (k + 1): {"nozzle_sequence": [0], "optimal_assignment": [0],
                                         "sequence": [1]} for k in range(n)}
    with tempfile.TemporaryDirectory() as tmp:
        cru = os.path.join(tmp, "cru.3mf")
        with zipfile.ZipFile(cru, "w", zipfile.ZIP_DEFLATED) as z:
            for nome, dados in fixos.items():
                z.writestr(nome, dados)
            z.writestr("3D/3dmodel.model", modelo)
            z.writestr("3D/_rels/3dmodel.model.rels", rels)
            for nome, dados in sorted(arquivos_obj.items()):
                z.writestr(nome, dados)
            for nome, dados in figuras.items():
                z.writestr(nome, dados)
            z.writestr("Metadata/project_settings.config", projeto)
            z.writestr("Metadata/model_settings.config", cfg)
            z.writestr("Metadata/cut_information.xml", corte)
            z.writestr("Metadata/filament_sequence.json", json.dumps(sequencia))
        saida = os.path.join(tmp, "saida")
        os.makedirs(saida)
        nome = os.path.basename(destino)
        r = subprocess.run([BAMBU, "--slice", "0", "--export-3mf", nome, "--outputdir", saida,
                            cru], capture_output=True, text=True, cwd=saida)
        resultado = os.path.join(saida, "result.json")
        dados = json.load(open(resultado)) if os.path.exists(resultado) else {}
        pratos = dados.get("sliced_plates") or []
        if len(pratos) != n or not os.path.exists(os.path.join(saida, nome)):
            raise RuntimeError("o Bambu não fatiou os %d pratos (%s): %s"
                               % (n, dados.get("error_string"), r.stderr[-500:]))
        shutil.move(os.path.join(saida, nome), destino)
    return [(p.get("id"), p.get("main_predication", 0) / 60.0,
             sum(f.get("total_used_g", 0) for f in p.get("filaments") or []))
            for p in pratos]


if __name__ == "__main__":
    pratos = ["maker_p0_teste.3mf", "maker_p3_bloco.3mf", "maker_p1_base.3mf",
              "maker_p2_rampa.3mf"]
    r = juntar([os.path.join(AQUI, a) for a in pratos], os.path.join(AQUI, "maker_todos.3mf"),
               base=os.path.join(AQUI, "maker_p2_rampa.3mf"),
               camadas={os.path.join(AQUI, "maker_p0_teste.3mf"): 0.28,
                        os.path.join(AQUI, "maker_p1_base.3mf"): 0.28})
    for (i, minutos, gramas), a in zip(r, pratos):
        print("prato %s  %-20s %4.0f min  %5.1f g" % (i, a, minutos, gramas))
