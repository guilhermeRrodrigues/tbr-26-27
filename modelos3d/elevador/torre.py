# Torre (versão 2): 2 colunas + portal, emendados (a torre passa de 180 mm).
#
# coluna_esq / coluna_dir
#   - bloco maciço (14 × 28 × 10 mm) sobre a viga, com 3 furos de pino
#     Technic (5,2) por baixo, nas posições dos furos livres; o bloco da direita
#     (viga preta) tem rasgos em x de ±2 mm para tolerar a medida de 85 mm;
#   - transição a 45° e coluna de 14 × 14 até z = 175;
#   - espiga no topo (9 × 10 × 16) com furo de pino deitado (em x).
# portal
#   - as duas colunas de cima (z 175 até a travessa), com o encaixe da espiga e
#     o mesmo furo de pino deitado: um pino Technic atravessa coluna e espiga;
#   - travessa em "T" no topo (z 281–289): viga transversal ligando as colunas
#     e miolo central com mancal Ø 8 + folga para o munhão do fuso (B) e mancal
#     Ø 6 + folga em rasgo y ±1,5 para o munhão da haste da garra (F).
#
# Referencial: o do robô (já está na posição de montagem).
# Impressão: colunas em pé (bloco na mesa); portal de cabeça para baixo.

import parametros as p
from rosca import (
    caixa,
    cilindro,
    cilindro_x,
    de_cabeca_para_baixo,
    estadio,
    exportar,
    no_chao,
    prisma_yz,
)

Z_TOPO = p.Z_TRAVESSA + p.TRAVESSA_ESPESSURA          # 289
X_EXT = p.X_VIGA + p.COLUNA_LARGURA / 2               # 49,5
Z_BLOCO = p.Z_VIGAS + p.BLOCO_PINOS_ALTURA
CY0 = p.Y_COLUNA - p.COLUNA_SECAO / 2
CY1 = p.Y_COLUNA + p.COLUNA_SECAO / 2
ZE = p.Z_EMENDA_TORRE
Z_PINO_EMENDA = ZE + p.ESPIGA_ALTURA / 2


def coluna(lado):
    # lado = −1 (esquerda, viga cinza, furos redondos) ou +1 (direita, rasgos).
    xc = lado * p.X_VIGA
    x0, x1 = xc - p.COLUNA_LARGURA / 2, xc + p.COLUNA_LARGURA / 2
    by0, by1 = p.COLUNA_Y
    corpo = caixa(x0, x1, by0, by1, p.Z_VIGAS, Z_BLOCO)
    # Transição a 45°: do bloco (y by0..by1) até a coluna (y CY0..CY1).
    subida = max(CY0 - by0, by1 - CY1)
    z1 = Z_BLOCO + subida
    corpo = corpo.fuse(prisma_yz([(by0, Z_BLOCO - 0.01), (by1, Z_BLOCO - 0.01),
                                  (CY1, z1), (CY0, z1)], x0, x1))
    corpo = corpo.fuse(caixa(x0, x1, CY0, CY1, z1 - 0.01, ZE))
    # Espiga.
    ex, ey = p.ESPIGA_X / 2, p.ESPIGA_Y / 2
    corpo = corpo.fuse(caixa(xc - ex, xc + ex, p.Y_COLUNA - ey, p.Y_COLUNA + ey,
                             ZE - 0.01, ZE + p.ESPIGA_ALTURA))
    corpo = corpo.cut(cilindro_x(p.PINO_FURO_DEITADO / 2, x0 - 1.0, x1 + 1.0,
                                 p.Y_COLUNA, Z_PINO_EMENDA))
    # Furos de pino por baixo do bloco.
    z0, zf = p.Z_VIGAS - 1.0, p.Z_VIGAS + p.PINO_PROFUNDIDADE
    for y in p.FUROS_VIGA_Y:
        if lado < 0:
            corpo = corpo.cut(cilindro(p.PINO_FURO / 2, z0, zf, xc, y))
        else:
            corpo = corpo.cut(estadio(p.PINO_FURO / 2, p.RASGO_VIGA_X, z0, zf, xc, y, eixo="x"))
    return corpo


def portal():
    # Travessa em T: viga transversal + miolo dos mancais.
    corpo = caixa(-X_EXT, X_EXT, CY0, CY1, p.Z_TRAVESSA, Z_TOPO)
    ty0, ty1 = p.TRAVESSA_Y
    corpo = corpo.fuse(caixa(-p.TRAVESSA_MIOLO_X, p.TRAVESSA_MIOLO_X, ty0, ty1,
                             p.Z_TRAVESSA, Z_TOPO))
    ex = p.ESPIGA_X / 2 + p.FOLGA_ESPIGA / 2
    ey = p.ESPIGA_Y / 2 + p.FOLGA_ESPIGA / 2
    for lado in (-1, 1):
        xc = lado * p.X_VIGA
        x0, x1 = xc - p.COLUNA_LARGURA / 2, xc + p.COLUNA_LARGURA / 2
        corpo = corpo.fuse(caixa(x0, x1, CY0, CY1, ZE, p.Z_TRAVESSA + 0.01))
        corpo = corpo.cut(caixa(xc - ex, xc + ex, p.Y_COLUNA - ey, p.Y_COLUNA + ey,
                                ZE - 1.0, ZE + p.ESPIGA_ALTURA + 0.5))
        corpo = corpo.cut(cilindro_x(p.PINO_FURO_DEITADO / 2, x0 - 1.0, x1 + 1.0,
                                     p.Y_COLUNA, Z_PINO_EMENDA))
    # Mancais.
    zt0, zt1 = p.Z_TRAVESSA - 1.0, Z_TOPO + 1.0
    corpo = corpo.cut(cilindro((p.DIAM_MUNHAO_FUSO + p.FOLGA_MANCAL) / 2, zt0, zt1,
                               0.0, p.Y_EIXO_B))
    corpo = corpo.cut(estadio((p.DIAM_MUNHAO_GARRA + p.FOLGA_MANCAL) / 2, p.TOLERANCIA_F_B,
                              zt0, zt1, 0.0, p.Y_EIXO_F))
    return corpo


def pecas():
    return {"coluna_esq": coluna(-1), "coluna_dir": coluna(1), "portal": portal()}


def impressao():
    s = pecas()
    return {"coluna_esq": no_chao(s["coluna_esq"]), "coluna_dir": no_chao(s["coluna_dir"]),
            "portal": de_cabeca_para_baixo(s["portal"])}


if __name__ == "__main__":
    for nome, s in impressao().items():
        print("gravado:", exportar(s, nome))
