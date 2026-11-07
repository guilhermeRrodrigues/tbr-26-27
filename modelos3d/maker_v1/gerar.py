# Gera os STL do Dispositivo Maker (na orientação de impressão) e fatia os pratos
# para a A1 mini com PLA Lite.
#
#   P0  maker_p0_teste.3mf     placa de teste + 3 cunhas + gabaritos do motor e do sensor
#   P1  maker_p1_base.3mf      base (luva do hub + placa perfurada do sensor)
#   P2  maker_p2_rampa.3mf     rampa (com o suporte do motor) + comporta
#   P3  maker_p3_bloco.3mf     Bloco de Educação Tecnológica
#   maker_todos.3mf            os 4 pratos num projeto só (juntar_pratos.py)
#
# Uso: python gerar.py [pasta_png] [filtro_de_prato]
# Rode antes o montagem.py: ele confere interferência, bandeja, feixe e descida.
# O fatiamento usa ../elevador/fatiar.py (que não importa parametros).

import os
import sys

import parametros as p
import base
import bloco
import comporta
import rampa
import teste_encaixe
from geometria import exportar

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(AQUI, "..", "elevador"))
from fatiar import fatiar  # noqa: E402
from juntar_pratos import juntar  # noqa: E402

PADRAO = "0.20mm Standard @BBL A1M"
RAPIDO = "0.28mm Extra Draft @BBL A1M"
PRATOS = [
    ("maker_p0_teste.3mf", ["placa_teste", "cunha_25", "cunha_30", "cunha_35",
                            "gabarito_motor", "gabarito_sensor"], RAPIDO),
    ("maker_p1_base.3mf", ["base"], RAPIDO),
    # Furo em cruz do dente, mancal e furos de pino do suporte: 0,20.
    ("maker_p2_rampa.3mf", ["rampa", "comporta"], PADRAO),
    ("maker_p3_bloco.3mf", ["bloco"], PADRAO),
]
# Ordem de impressão (e dos pratos no maker_todos.3mf).
ORDEM = ["maker_p0_teste.3mf", "maker_p3_bloco.3mf", "maker_p1_base.3mf", "maker_p2_rampa.3mf"]


def pecas_de_impressao():
    s = dict(teste_encaixe.pecas())
    s["base"] = base.impressao()
    s["rampa"] = rampa.impressao()
    s["comporta"] = comporta.impressao()
    s["bloco"] = bloco.impressao()
    return s


def main(pasta_png=None, so=None):
    stl = {}
    for nome, peca in pecas_de_impressao().items():
        if not peca.is_valid():
            raise SystemExit("peça inválida: " + nome)
        bb = peca.bounding_box()
        maior = max(bb.size.X, bb.size.Y, bb.size.Z)
        if maior > p.VOLUME_IMPRESSAO:
            raise SystemExit("%s não cabe na impressora: %.1f mm" % (nome, maior))
        stl[nome] = exportar(peca, nome)
        print("%-15s %6.1f cm³  %5.1f × %5.1f × %5.1f mm"
              % (nome, peca.volume / 1000, bb.size.X, bb.size.Y, bb.size.Z))
    total = 0.0
    gramas = 0.0
    for arquivo, nomes, processo in PRATOS:
        if so and so not in arquivo:
            continue
        # pasta=AQUI: sem ela, o fatiar() gravaria o 3MF na pasta do elevador.
        r = fatiar([stl[n] for n in nomes], arquivo, pasta=AQUI, pasta_png=pasta_png,
                   processo=processo)
        if r["minutos"] is None:
            raise SystemExit("falhou ao fatiar %s: %s" % (arquivo, r["erro"]))
        total += r["minutos"]
        gramas += r["gramas"] or 0.0
        print("%-22s %5.0f min  %5.1f g  camada %.2f  %s"
              % (arquivo, r["minutos"], r["gramas"] or 0.0, r["camada"] or 0.0, r["erro"]))
        for aviso in r["avisos"]:
            if "ZFiller" not in aviso:
                print("   aviso:", aviso)
    print("total: %.0f min (%.1f h), %.0f g de PLA Lite" % (total, total / 60, gramas))
    if not so:
        # Os 4 pratos num projeto só, na ordem de impressão (camada 0,28 por objeto).
        def caminho(a):
            return os.path.join(AQUI, a)
        r = juntar([caminho(a) for a in ORDEM], caminho("maker_todos.3mf"),
                   base=caminho("maker_p2_rampa.3mf"),
                   camadas={caminho(a): 0.28 for a, _, proc in PRATOS if proc == RAPIDO})
        print("maker_todos.3mf: " + ", ".join("%.0f min" % m for _, m, _ in r))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None, sys.argv[2] if len(sys.argv) > 2 else None)
