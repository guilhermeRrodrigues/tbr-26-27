# Bloco de Educação Tecnológica (v2): caixa oca da Overclock.
#
# Cubo de 45 mm (cabe na garra do elevador: abre 70, fecha até 30), ABERTO EMBAIXO:
# paredes de BLOCO_PAREDE e topo de BLOCO_TOPO. Arestas de fora chanfradas, e as de
# baixo também: a borda de baixo fica recolhida e desliza nas nervuras da rampa
# sem enganchar.
# Logo da Overclock (logo_overclock.json, de logo.py) em BAIXO-relevo (faces planas
# para a garra) no topo e nas 4 laterais, sempre de pé para quem olha de fora:
#   topo:     linhas LOGO_LINHAS_TOPO, corpo da chave LOGO_CORPO_TOPO;
#   laterais: linhas LOGO_LINHAS_LADO, corpo LOGO_CORPO_LADO.
#
# Referencial local: centrado em x e y, de z = 0 (borda aberta) a z = BLOCO.
# Impressão: de cabeça para baixo (topo na mesa: o logo sai nas primeiras camadas),
# sem suporte.

from build123d import Align, Axis, Box, chamfer, offset

import parametros as p
import logo
from geometria import caixa, exportar, girar, mover, no_chao, prisma

L = p.BLOCO


def _caixa_oca():
    cubo = Box(L, L, L, align=(Align.CENTER, Align.CENTER, Align.MIN))
    cubo = chamfer(cubo.edges(), p.BLOCO_CHANFRO)
    baixo = cubo.faces().sort_by(Axis.Z)[0]
    oca = offset(cubo, amount=-p.BLOCO_PAREDE, openings=[baixo])
    # Topo mais grosso (o logo do topo é mais fundo).
    extra = p.BLOCO_TOPO - p.BLOCO_PAREDE
    if extra > 0:
        m = L / 2 - p.BLOCO_PAREDE - p.BLOCO_CHANFRO
        topo = caixa(-m, m, -m, m, L - p.BLOCO_PAREDE - extra, L - p.BLOCO_PAREDE + 0.01)
        oca = oca.fuse(topo)
    return oca


def _relevo(poligonos, profundidade):
    # Prismas do logo no plano z = L/2 (face de cima, com o cubo centrado na origem),
    # entrando `profundidade` na face.
    r = None
    for pol in poligonos:
        s = prisma([tuple(q) for q in pol[0]], L / 2 - profundidade, L / 2 + 1)
        for furo in pol[1:]:
            s = s.cut(prisma([tuple(q) for q in furo], L / 2 - profundidade - 1, L / 2 + 2))
        r = s if r is None else r.fuse(s)
    return r


def _faces(dados, camadas):
    # Recorte do logo no topo e nas 4 laterais (cubo centrado na origem).
    cortes = []
    topo = [_relevo(dados[k], prof) for k, prof in camadas["topo"] if prof > 0]
    lado = [_relevo(dados[k], prof) for k, prof in camadas["lado"] if prof > 0]
    cortes += topo
    for r in lado:
        sul = girar(r, "x", 90)                 # topo → face −y, de pé para quem olha
        for graus in (0, 90, 180, 270):
            cortes.append(girar(sul, "z", graus))
    return cortes


def peca(com_logo=True):
    b = _caixa_oca()
    if not com_logo:
        return b
    dados = logo.carregar()
    camadas = {"topo": [("linhas", p.LOGO_LINHAS_TOPO), ("corpo", p.LOGO_CORPO_TOPO)],
               "lado": [("linhas", p.LOGO_LINHAS_LADO), ("corpo", p.LOGO_CORPO_LADO)]}
    for corte in _faces(dados, camadas):
        b = b.cut(mover(corte, z=L / 2))
    return b


def impressao():
    return no_chao(girar(peca(), "x", 180))


def envelope():
    # Cubo cheio com o mesmo chanfro: para as conferências de colisão (a caixa oca
    # deixaria passar o que entrasse por baixo).
    cubo = Box(L, L, L, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return chamfer(cubo.edges(), p.BLOCO_CHANFRO)


if __name__ == "__main__":
    b = peca()
    bb = b.bounding_box()
    print("bloco: %.1f cm³, %.1f × %.1f × %.1f mm, válido=%s"
          % (b.volume / 1000, bb.size.X, bb.size.Y, bb.size.Z, b.is_valid()))
    print("gravado:", exportar(b, "bloco"))

