# Bloco de Educação Tecnológica (o "kit" que o Dispositivo Maker libera).
#
# Cubo de 45 mm: cabe na garra do elevador (abre 60, fecha até 30). As arestas
# são chanfradas para deslizar na rampa sem enganchar. Os desenhos são em
# BAIXO-relevo (todas as faces continuam planas):
#   - topo: engrenagem;
#   - 4 laterais: chip com terminais (o "kit de robótica").
# A face de baixo é lisa: é a que desliza nas nervuras da rampa.
#
# Referencial local: centrado em x e y, de z = 0 (face lisa) a z = BLOCO.
# Impressão: face lisa na mesa, sem suporte.

import math

from build123d import Box, Align, chamfer

import parametros as p
from geometria import caixa, cilindro, exportar, girar, mover, prisma

L = p.BLOCO
G = p.BLOCO_GRAVACAO


def _engrenagem(z0, z1, raio=13.0, dentes=10, altura_dente=3.0, furo=4.5):
    # Contorno de engrenagem (dentes trapezoidais) com furo central.
    pts = []
    for i in range(dentes):
        a0 = 2 * math.pi * i / dentes
        passo = 2 * math.pi / dentes
        for frac, r in ((0.0, raio - altura_dente), (0.2, raio), (0.5, raio),
                        (0.7, raio - altura_dente)):
            a = a0 + frac * passo
            pts.append((r * math.cos(a), r * math.sin(a)))
    contorno = prisma(pts, z0, z1)
    return contorno.cut(cilindro(furo, z0 - 1, z1 + 1))


def _chip(z0, z1, lado=18.0, terminais=4, term_largura=2.0, term_comp=4.0):
    # Chip quadrado (anel) com terminais nos 4 lados.
    m = lado / 2
    corpo = caixa(-m, m, -m, m, z0, z1).cut(caixa(-m + 2.5, m - 2.5, -m + 2.5, m - 2.5,
                                                 z0 - 1, z1 + 1))
    marca = cilindro(1.6, z0, z1, -m + 5.0, m - 5.0)   # pino 1 do chip
    corpo = corpo.fuse(marca)
    passo = lado / (terminais + 1)
    for i in range(terminais):
        t = -m + passo * (i + 1)
        w = term_largura / 2
        for x0, x1, y0, y1 in ((t - w, t + w, m + 1.0, m + 1.0 + term_comp),
                               (t - w, t + w, -m - 1.0 - term_comp, -m - 1.0),
                               (m + 1.0, m + 1.0 + term_comp, t - w, t + w),
                               (-m - 1.0 - term_comp, -m - 1.0, t - w, t + w)):
            corpo = corpo.fuse(caixa(x0, x1, y0, y1, z0, z1))
    return corpo


def peca():
    cubo = Box(L, L, L, align=(Align.CENTER, Align.CENTER, Align.MIN))
    cubo = chamfer(cubo.edges(), p.BLOCO_CHANFRO)
    # Topo: engrenagem gravada.
    cubo = cubo.cut(_engrenagem(L - G, L + 1))
    # Laterais: chip gravado em cada face (desenho feito no topo e girado).
    chip = _chip(L / 2 - G, L / 2 + 1)               # no plano z = L/2: vira a face +y
    for graus in (0, 90, 180, 270):
        face = mover(girar(chip, "x", -90), z=L / 2)  # topo local → face +y do cubo
        cubo = cubo.cut(girar(face, "z", graus))
    return cubo


def impressao():
    return peca()


if __name__ == "__main__":
    b = peca()
    bb = b.bounding_box()
    print("bloco: %.1f cm³, %.1f × %.1f × %.1f mm, válido=%s"
          % (b.volume / 1000, bb.size.X, bb.size.Y, bb.size.Z, b.is_valid()))
    print("gravado:", exportar(b, "bloco"))
