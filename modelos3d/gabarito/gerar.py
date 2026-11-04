# Gera o STL do Gabarito de Largada, confere se imprime (imprimivel.py do Maker) e fatia
# para a A1 mini com PLA Lite (usa ../elevador/fatiar.py). Também gera o PNG de topo.
#
#   gabarito_impressao.3mf   o L + 3 calços, 1 prato
#
# Uso: python gerar.py [pasta_png]
# Rode antes o montagem.py (precisa terminar sem problemas).

import os
import sys

import parametros as p
import gabarito
from desenho import desenhar

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(AQUI, "..", "maker"))
sys.path.append(os.path.join(AQUI, "..", "elevador"))
from imprimivel import conferir  # noqa: E402
from fatiar import fatiar        # noqa: E402

PROCESSO = "0.24mm Draft @BBL A1M"      # rápido; as arestas são o que importa, não o acabamento


def exportar(peca, nome):
    from build123d import export_stl
    pasta = os.path.join(AQUI, "stl")
    os.makedirs(pasta, exist_ok=True)
    destino = os.path.join(pasta, nome + ".stl")
    export_stl(peca, destino, tolerance=0.005, angular_tolerance=0.1)
    return destino


def main(pasta_png=None):
    peca = gabarito.impressao()
    if not peca.is_valid:
        raise SystemExit("peça inválida")
    bb = peca.bounding_box()
    util = p.VOLUME_IMPRESSAO - 2 * p.MARGEM_PRATO
    if max(bb.size.X, bb.size.Y) > util or bb.size.Z > p.VOLUME_IMPRESSAO:
        raise SystemExit("não cabe no prato: %.1f × %.1f × %.1f" % (bb.size.X, bb.size.Y, bb.size.Z))
    stl = exportar(peca, "gabarito_impressao")
    exportar(gabarito.gabarito(), "gabarito_L")
    print("gabarito_impressao: %.1f cm³, %.1f × %.1f × %.1f mm" %
          (peca.volume / 1000, bb.size.X, bb.size.Y, bb.size.Z))
    resumo, problemas = conferir(stl)
    print("   " + resumo)
    if problemas:
        raise SystemExit("não imprime: " + "; ".join(problemas))
    r = fatiar([stl], "gabarito_impressao.3mf", pasta=AQUI, pasta_png=pasta_png, processo=PROCESSO)
    if r["minutos"] is None:
        raise SystemExit("falhou ao fatiar: %s" % r["erro"])
    print("gabarito_impressao.3mf: %.0f min, %.1f g, camada %.2f %s"
          % (r["minutos"], r["gramas"] or 0.0, r["camada"] or 0.0, r["erro"] or ""))
    for aviso in r["avisos"]:
        print("   aviso:", aviso)
    print(desenhar(os.path.join(AQUI, "gabarito_topo.png")))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
