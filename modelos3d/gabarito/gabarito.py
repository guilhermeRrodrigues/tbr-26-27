# Geometria do Gabarito de Largada (build123d). Referencial da base (ver parametros.py):
# origem no canto interno de trás-esquerda; a placa fica no tapete, z = 0 embaixo.
#
#   gabarito()  -> o L com nervuras, bisel, janelas, alça, batentes fixos e furos
#   calco()     -> um batente móvel (na posição de uso, em coordenadas locais)
#   impressao() -> tudo no prato: L de cara para cima e os calços virados ao lado

import math

from build123d import Align, Box, Cylinder, Face, Location, Vector, Wire, extrude, Axis

import parametros as p
import layout


def caixa(x0, x1, y0, y1, z0, z1):
    return Box(x1 - x0, y1 - y0, z1 - z0,
               align=(Align.MIN, Align.MIN, Align.MIN)).moved(Location((x0, y0, z0)))


def cilindro(raio, z0, z1, x, y):
    return Cylinder(raio, z1 - z0,
                    align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(Location((x, y, z0)))


def prisma_yz(perfil, x0, x1):
    face = Face(Wire.make_polygon([Vector(x0, y, z) for y, z in perfil], close=True))
    return extrude(face, amount=x1 - x0, dir=(1, 0, 0))


def prisma_xz(perfil, y0, y1):
    face = Face(Wire.make_polygon([Vector(x, y0, z) for x, z in perfil], close=True))
    return extrude(face, amount=y1 - y0, dir=(0, 1, 0))


def prisma_xy(pontos, z0, z1):
    face = Face(Wire.make_polygon([Vector(x, y, z0) for x, y in pontos], close=True))
    return extrude(face, amount=z1 - z0, dir=(0, 0, 1))


def _perfil_nervura():
    # corte da nervura de referência: d = distância da aresta externa, z para cima.
    # Face externa vertical até PLACA+1 e bisel de 45° até o topo: a aresta fica "fina".
    t, a, b = p.PLACA, p.NERV_ALT, p.BISEL
    return [(0, 0), (0, t + a - b), (b, t + a), (p.NERV_LARG, t + a), (p.NERV_LARG, 0)]


def _placa():
    A = p.ARESTA_COMP
    wt, wl = layout.larg_tras(), layout.larg_lado()
    placa = caixa(0, A, 0, wt, 0, p.PLACA).fuse(caixa(0, wl, 0, A, 0, p.PLACA))
    perfil = _perfil_nervura()
    nerv_t = prisma_yz(perfil, 0, A)                              # ao longo de x, y = d
    nerv_l = prisma_xz(perfil, 0, A)                              # ao longo de y, x = d
    return placa.fuse(nerv_t).fuse(nerv_l)


def _janelas(corpo):
    A = p.ARESTA_COMP
    h = p.PLACA + p.NERV_ALT + 2
    for s in layout.janelas():
        # entalhe aberto para fora, na aresta de trás (corre em x) e na esquerda (corre em y)
        corpo = corpo.cut(caixa(s - p.JANELA_COMP / 2, s + p.JANELA_COMP / 2,
                                -1, p.JANELA_FUNDO, -1, h))
        corpo = corpo.cut(caixa(-1, p.JANELA_FUNDO,
                                s - p.JANELA_COMP / 2, s + p.JANELA_COMP / 2, -1, h))
        # índice: sulco fino saindo do fundo da janela, no eixo dela
        l, f = p.INDICE_LARG / 2, p.PLACA - p.INDICE_FUNDO
        corpo = corpo.cut(caixa(s - l, s + l, p.JANELA_FUNDO - 0.01,
                                p.JANELA_FUNDO + p.INDICE_COMP, f, p.PLACA + 1))
        corpo = corpo.cut(caixa(p.JANELA_FUNDO - 0.01, p.JANELA_FUNDO + p.INDICE_COMP,
                                s - l, s + l, f, p.PLACA + 1))
    return corpo


def _alca():
    # Aba em pé na diagonal do canto; furo em losango (45°, imprime sem suporte).
    wt, wl = layout.larg_tras(), layout.larg_lado()
    cx, cy = wl / 2, wt / 2
    c, s = math.cos(math.radians(45)), math.sin(math.radians(45))
    h, e = p.ALCA_COMP / 2, p.ALCA_ESP / 2
    # perfil em (u, z): u ao longo da diagonal
    perfil = [(-h, 0), (h, 0), (h, p.ALCA_ALT - 8), (h - 6, p.ALCA_ALT),
              (-h + 6, p.ALCA_ALT), (-h, p.ALCA_ALT - 8)]
    aba = prisma_xz(perfil, -e, e)                        # u em x, espessura em y
    r = p.ALCA_FURO
    zc = p.ALCA_ALT * 0.5 + 1
    losango = prisma_xz([(0, zc - r), (r, zc), (0, zc + r), (-r, zc)], -e - 1, e + 1)
    aba = aba.cut(losango)
    # aba.rotate gira sobre o eixo Z pela origem; depois leva ao centro do canto
    aba = aba.rotate(Axis.Z, 45).moved(Location((cx, cy, p.PLACA - 0.01)))
    return aba


def _bloco_batente_fixo_tras(x, ):
    # prisma de z = 0 até o topo: avança até y = DIST_TRAS (face de contato)
    l = p.CALCO_LARG / 2
    return caixa(x - l, x + l, layout.larg_tras() - p.CALCO_RECUO, p.DIST_TRAS,
                 0, p.PLACA + _h_batente())


def _bloco_batente_fixo_lado(y):
    l = p.CALCO_LARG / 2
    return caixa(layout.larg_lado() - p.CALCO_RECUO, p.DIST_LAT, y - l, y + l,
                 0, p.PLACA + _h_batente())


def _h_batente():
    return p.H_BATENTE


def _marcas(corpo, plano):
    # Pontos gravados ao lado de cada furo: uma coluna por giro que o usa, com k pontos
    # para o k-ésimo giro da lista (1 ponto = 90°, 3 pontos = 270°). Ficam sob o calço
    # quando ele está montado; servem para escolher o furo na hora de montar.
    wt, wl = layout.larg_tras(), layout.larg_lado()
    r, f = p.MARCA_DIAM / 2, p.PLACA - p.MARCA_FUNDO
    for x, ks in plano["furos_tras"].items():
        for fila, k in enumerate(ks):
            cx = x + (-5.5 if fila == 0 else 5.5)
            for i in range(k):
                corpo = corpo.cut(cilindro(r, f, p.PLACA + 1, cx, wt - p.CALCO_PEG_V + (i - (k - 1) / 2) * 3.6))
    for y, ks in plano["furos_lado"].items():
        for fila, k in enumerate(ks):
            cy = y + (-5.5 if fila == 0 else 5.5)
            for i in range(k):
                corpo = corpo.cut(cilindro(r, f, p.PLACA + 1, wl - p.CALCO_PEG_V + (i - (k - 1) / 2) * 3.6, cy))
    return corpo


def gabarito():
    plano = layout.plano_de_batentes()
    wt, wl = layout.larg_tras(), layout.larg_lado()
    corpo = _placa()
    for x in plano["fixos_tras"]:
        corpo = corpo.fuse(_bloco_batente_fixo_tras(x))
    corpo = corpo.fuse(_bloco_batente_fixo_lado(plano["fixo_lado"]))
    corpo = corpo.fuse(_alca())
    corpo = _janelas(corpo)
    for x in plano["furos_tras"]:
        corpo = corpo.cut(cilindro(p.FURO_PEG / 2, -1, p.PLACA + 1, x, wt - p.CALCO_PEG_V))
    for y in plano["furos_lado"]:
        corpo = corpo.cut(cilindro(p.FURO_PEG / 2, -1, p.PLACA + 1, wl - p.CALCO_PEG_V, y))
    return _marcas(corpo, plano)


def calco():
    # Batente móvel em coordenadas locais de USO: u ao longo da aresta (centrado em 0),
    # v para longe da aresta interna da placa (v = 0 é a aresta). Apoia na placa (z = PLACA),
    # avança FOLGA_PLACA além da aresta (face de contato em v = FOLGA_PLACA); o lábio
    # desce rente à aresta (v ≥ 0) e o pino entra no furo.
    l = p.CALCO_LARG / 2
    h = _h_batente()
    corpo = caixa(-l, l, -p.CALCO_RECUO, p.FOLGA_PLACA, p.PLACA, p.PLACA + h)
    corpo = corpo.fuse(caixa(-l, l, 0, p.CALCO_LABIO, 0.0, p.PLACA + 0.01))
    corpo = corpo.fuse(cilindro(p.CALCO_PEG / 2, 0.4, p.PLACA + 0.01, 0, -p.CALCO_PEG_V))
    return corpo


def calco_na_tras(x):
    return calco().moved(Location((x, layout.larg_tras(), 0)))


def calco_no_lado(y):
    return calco().rotate(Axis.Z, -90).moved(Location((layout.larg_lado(), y, 0)))


def calco_impressao():
    # virado (corpo na mesa): lábio e pino sobem
    c = calco().rotate(Axis.X, 180)
    return c.moved(Location((0, 0, -c.bounding_box().min.Z)))


N_CALCOS = 3


def impressao():
    # O L e os calços numa malha só (um objeto), os calços no vão interno do L.
    peca = gabarito()
    A = p.ARESTA_COMP
    x0 = layout.larg_lado() + 16.0
    for i in range(N_CALCOS):
        c = calco_impressao()
        peca = peca.fuse(c.moved(Location((x0 + 12.0 + i * 20.0, layout.larg_tras() + 20.0, 0))))
    return peca
