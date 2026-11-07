# Placa de teste da versão 2 (antes de imprimir o conjunto grande).
#
#   - mancais: furos Ø 8,6 / 8,8 / 9,0 (munhão do fuso, Ø 8) e Ø 6,6 / 6,8 / 7,0
#     (munhão da haste da garra, Ø 6). Na v1, Ø 8,4 ficou apertado demais.
#     Gravado em cada coluna: a folga diametral (.6 / .8 / 1.0);
#   - pino Technic HORIZONTAL: 2 furos deitados (5,2 e 5,4), como os da emenda
#     da torre. O furo vertical de 5,2 já foi validado; deitado, a impressão
#     muda o formato do furo;
#   - furo quadrado de 10,4 e um toco quadrado de 10 × 10 mm (peça solta): a
#     haste da garra passa de sextavada para quadrada, com a mesma folga de 0,4.
#
# Teste: girar os munhões já impressos (Ø 8 e Ø 6) nos furos; enfiar meio pino
# Technic nos furos deitados; deslizar o toco no furo quadrado.
#
# Uso: python teste_mancal.py   (grava stl/teste_mancal_*.stl e fatia o prato)

from build123d import BuildSketch, Location, Text, extrude

from fatiar import fatiar
from rosca import caixa, cilindro, exportar

ESPESSURA = 3.6
MANCAIS_X = [7.0, 18.0, 29.0]
FOLGAS = [0.6, 0.8, 1.0]
ROTULOS = [".6", ".8", "1.0"]
Y_MANCAL_8 = 7.0
Y_MANCAL_6 = 29.0
QUADRADO = 10.4
X_QUADRADO, Y_QUADRADO = 45.0, 18.0
# Bloco dos furos deitados (eixo dos furos em x).
BLOCO_X = (56.0, 66.0)
BLOCO_ALTURA = 9.6
PINOS_DEITADOS = [(5.2, 9.0), (5.4, 27.0)]  # (diâmetro, y)
Z_PINO = 5.0


def _texto(rotulo, x, y, z_topo, tamanho=4.0, fundo=0.6):
    with BuildSketch() as s:
        Text(rotulo, font_size=tamanho)
    return extrude(s.sketch, amount=fundo).moved(Location((x, y, z_topo - fundo)))


def placa():
    corpo = caixa(0, BLOCO_X[0], 0, 36, 0, ESPESSURA)
    corpo = corpo.fuse(caixa(BLOCO_X[0] - 0.01, BLOCO_X[1], 0, 36, 0, BLOCO_ALTURA))
    for x, folga, rotulo in zip(MANCAIS_X, FOLGAS, ROTULOS):
        corpo = corpo.cut(cilindro((8.0 + folga) / 2, -1, ESPESSURA + 1, x, Y_MANCAL_8))
        corpo = corpo.cut(cilindro((6.0 + folga) / 2, -1, ESPESSURA + 1, x, Y_MANCAL_6))
        corpo = corpo.cut(_texto(rotulo, x, 18.0, ESPESSURA))
    q = QUADRADO / 2
    corpo = corpo.cut(caixa(X_QUADRADO - q, X_QUADRADO + q, Y_QUADRADO - q, Y_QUADRADO + q,
                            -1, ESPESSURA + 1))
    from build123d import Axis
    for d, y in PINOS_DEITADOS:
        furo = cilindro(d / 2, BLOCO_X[0] - 1, BLOCO_X[1] + 1).rotate(Axis.Y, 90)
        furo = furo.moved(Location((0, y, Z_PINO)))
        corpo = corpo.cut(furo)
        corpo = corpo.cut(_texto("%.1f" % d, (BLOCO_X[0] + BLOCO_X[1]) / 2, y, BLOCO_ALTURA,
                                 tamanho=3.5))
    return corpo


def toco():
    return caixa(0, 10.0, 0, 10.0, 0, 20.0)


if __name__ == "__main__":
    import sys
    pl, tc = placa(), toco()
    for nome, peca in (("placa", pl), ("toco", tc)):
        if not peca.is_valid():
            raise SystemExit("inválida: " + nome)
        bb = peca.bounding_box()
        print("%-6s %5.1f × %5.1f × %5.1f mm" % (nome, bb.size.X, bb.size.Y, bb.size.Z))
    stls = [exportar(pl, "teste_mancal_placa"), exportar(tc, "teste_mancal_toco")]
    # Em 0,28, como a torre e os dedos (os furos deitados dependem da camada).
    r = fatiar(stls, "teste_mancal.3mf", pasta_png=sys.argv[1] if len(sys.argv) > 1 else None,
               processo="0.28mm Extra Draft @BBL A1M")
    print("teste_mancal.3mf: %.0f min, %.1f g, %s" % (r["minutos"] or 0, r["gramas"] or 0, r["erro"]))
