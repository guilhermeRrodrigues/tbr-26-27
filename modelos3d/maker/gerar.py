# Gera os STL do Dispositivo Maker v2 (na orientação de impressão), confere se cada
# peça imprime (imprimivel.py: base, altura e balanço) e fatia para a A1 mini com PLA
# Lite, camada 0,24:
#
#   maker_impressao.3mf   rampa fina (deitada sobre a lateral leste) + Bloco Overclock
#                         (topo na mesa)
#   maker_rampa.3mf       só a rampa (para quem já imprimiu o Bloco)
#
# Uso: python gerar.py [pasta_png]
# Rode antes o montagem.py (interferência, bandeja, feixe, trava e descida) e, se o
# logo mudar, o logo.py. O fatiamento usa ../elevador/fatiar.py (que não importa
# parametros). A v1 (4 pratos, 185 g, 4,8 h) está em ../maker_v1/.

import os
import sys

import parametros as p
import bloco
import rampa
from geometria import exportar
from imprimivel import conferir

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(AQUI, "..", "elevador"))
from fatiar import fatiar  # noqa: E402

PROCESSO = "0.24mm Draft @BBL A1M"        # mais rápido que 0,20 (furos de pino: testar)
PRATOS = {"maker_impressao.3mf": ["rampa", "bloco"], "maker_rampa.3mf": ["rampa"]}
V1 = (185.0, 290.0)                       # v1: gramas e minutos (4 pratos)


def pecas_de_impressao():
    return {"rampa": rampa.impressao(), "bloco": bloco.impressao()}


def main(pasta_png=None):
    stl = {}
    for nome, peca in pecas_de_impressao().items():
        if not peca.is_valid():
            raise SystemExit("peça inválida: " + nome)
        bb = peca.bounding_box()
        maior = max(bb.size.X, bb.size.Y, bb.size.Z)
        if maior > p.VOLUME_IMPRESSAO:
            raise SystemExit("%s não cabe na impressora: %.1f mm" % (nome, maior))
        stl[nome] = exportar(peca, nome)
        resumo, problemas = conferir(stl[nome])
        print("%-6s %5.1f cm³  %5.1f × %5.1f × %5.1f mm; %s"
              % (nome, peca.volume / 1000, bb.size.X, bb.size.Y, bb.size.Z, resumo))
        if problemas:
            raise SystemExit("%s não imprime: %s" % (nome, "; ".join(problemas)))
    for prato, nomes in PRATOS.items():
        r = fatiar([stl[n] for n in nomes], prato, pasta=AQUI, pasta_png=pasta_png,
                   processo=PROCESSO)
        if r["minutos"] is None:
            raise SystemExit("falhou ao fatiar %s: %s" % (prato, r["erro"]))
        g = r["gramas"] or 0.0
        print("%s: %.0f min, %.1f g, camada %.2f %s"
              % (prato, r["minutos"], g, r["camada"] or 0.0, r["erro"] or ""))
        for aviso in r["avisos"]:
            if "ZFiller" not in aviso:
                print("   aviso:", aviso)
        if len(nomes) == 2:
            print("v1 → v2: %.0f g → %.0f g (%.0f%% a menos), %.1f h → %.1f h"
                  % (V1[0], g, 100 * (1 - g / V1[0]), V1[1] / 60, r["minutos"] / 60))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
