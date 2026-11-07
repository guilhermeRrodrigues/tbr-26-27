# Base do Dispositivo Maker: luva do hub + placa perfurada do ultrassônico.
#
# Peça única, na ponta oeste da bandeja (encosta na parede oeste; a largura é a
# da bandeja menos a folga, então ela também não anda em y):
#   - placa de fundo, vazada onde não há carga;
#   - LUVA do hub SPIKE em pé, sobre a ponta dos botões: paredes de LUVA_ALTURA
#     ao norte, ao sul e a leste; a oeste só 2 cantoneiras, para o dedo chegar aos
#     botões (que ficam a BOTOES_ALTURA da ponta de baixo, na face da tela). As
#     portas ficam nas faces norte e sul: use as do SUL (plugues para fora). O USB
#     fica em cima, então o hub carrega sem sair da luva;
#   - PLACA PERFURADA (grade de furos Technic no passo de 8 mm) na ponta oeste,
#     com mãos-francesas atrás. O ultrassônico prende nela por 2 pinos nos furos
#     de trás e olha para o SUL, por cima da parede da bandeja. A grade deixa
#     escolher a altura e corrigir a posição dos furos se a medida real diferir.
#
# Referencial: o da bandeja (parametros.py).
# Impressão: em pé sobre a placa de fundo; os furos da placa perfurada ficam
# deitados (5,2, validado deitado no elevador).

import parametros as p
import rampa
from geometria import caixa, cilindro_y, exportar, no_chao, prisma_yz

X0 = p.FOLGA_BANDEJA
X1 = rampa.XM0 - 2.0 - 1.0                     # 1 mm antes do suporte do motor
Y0 = p.FOLGA_BANDEJA
Y1 = p.BANDEJA_Y - p.FOLGA_BANDEJA
ZB0 = p.Z_FUNDO
ZB1 = p.Z_FUNDO + p.BASE_ESPESSURA
M = p.PASSO_LEGO

# --- Ultrassônico deitado (caixa envolvente, no referencial da bandeja) -------------
SX, SY, SZ = p.SENSOR_LARGURA, p.SENSOR_PROFUNDIDADE, p.SENSOR_ALTURA
SENSOR_Y_FRENTE = Y0 + 1.0
Y_PLACA = SENSOR_Y_FRENTE + SY                 # face sul da placa perfurada
XS = X0 + 1.0 + SX / 2                         # centro do sensor em x
ZS = p.SENSOR_Z_CENTRO                         # centro dos olhos (meia altura)
SENSOR = (XS - SX / 2, XS + SX / 2, SENSOR_Y_FRENTE, Y_PLACA, ZS - SZ / 2, ZS + SZ / 2)
_d = p.SENSOR_OLHOS_ENTRE / 2
SENSOR_OLHOS = [(XS - _d, ZS), (XS + _d, ZS)]
# Furos de trás do sensor (onde vão os 2 pinos).
Z_FUROS_SENSOR = ZS - SZ / 2 + p.SENSOR_FUROS_TRAS_Z
FUROS_SENSOR = [(XS - p.SENSOR_FUROS_TRAS_X, Z_FUROS_SENSOR),
                (XS + p.SENSOR_FUROS_TRAS_X, Z_FUROS_SENSOR)]

# --- Placa perfurada: grade centrada nos furos do sensor -----------------------------
COLS, LINHAS = p.GRADE_SENSOR
FUROS_PLACA = [(XS + (i - (COLS - 1) / 2) * M, Z_FUROS_SENSOR + (j - (LINHAS - 1) / 2) * M)
               for i in range(COLS) for j in range(LINHAS)]
PX0 = min(x for x, _ in FUROS_PLACA) - M / 2
PX1 = max(x for x, _ in FUROS_PLACA) + M / 2
PZ1 = max(z for _, z in FUROS_PLACA) + M / 2
Y_PLACA_N = Y_PLACA + p.PLACA_SENSOR_ESPESSURA
MAO_FRANCESA = 22.0
NERVURA = 3.0

# --- Hub em pé ---------------------------------------------------------------------------
PAREDE_LUVA = 2.5
F = p.FOLGA_HUB
HUB_X0 = max(PX1, XS + SX / 2) + p.VAO_BOTOES
HUB_Y1 = Y1 - PAREDE_LUVA - F
HUB_Y0 = HUB_Y1 - p.HUB_LARGURA
HUB = (HUB_X0, HUB_X0 + p.HUB_ESPESSURA, HUB_Y0, HUB_Y1, ZB1, ZB1 + p.HUB_COMPRIMENTO)
CANTONEIRA = 8.0               # pernas das cantoneiras do lado oeste (botões)


def _luva():
    hx0, hx1, hy0, hy1, _, _ = HUB
    e, zt, z0 = PAREDE_LUVA, ZB1 + p.LUVA_ALTURA, ZB1 - 0.01
    norte = caixa(hx0 - F - e, hx1 + F + e, hy1 + F, hy1 + F + e, z0, zt)
    sul = caixa(hx0 - F - e, hx1 + F + e, hy0 - F - e, hy0 - F, z0, zt)
    leste = caixa(hx1 + F, hx1 + F + e, hy0 - F - e, hy1 + F + e, z0, zt)
    corpo = norte.fuse(sul).fuse(leste)
    c = CANTONEIRA
    for ya, yb in ((hy0 - F, hy0 - F + c), (hy1 + F - c, hy1 + F)):
        corpo = corpo.fuse(caixa(hx0 - F - e, hx0 - F, ya, yb, z0, zt))
    return corpo


def _placa_fundo():
    corpo = caixa(X0, X1, Y0, Y1, ZB0, ZB1)
    # Janelas onde não há carga: debaixo do sensor (ele fica pendurado nos pinos) e
    # atrás da placa perfurada, entre as mãos-francesas.
    b = 6.0
    corpo = corpo.cut(caixa(SENSOR[0] + b, SENSOR[1] - b, Y0 + b, Y_PLACA - 2, ZB0 - 1, ZB1 + 1))
    corpo = corpo.cut(caixa(PX0 + NERVURA + b, PX1 - NERVURA - b, Y_PLACA_N + 2, Y1 - b,
                            ZB0 - 1, ZB1 + 1))
    return corpo


def _placa_sensor():
    corpo = caixa(PX0, PX1, Y_PLACA, Y_PLACA_N, ZB1 - 0.01, PZ1)
    for x in (PX0, PX1 - NERVURA):
        perfil = [(Y_PLACA_N - 0.01, ZB1 - 0.01), (Y_PLACA_N + MAO_FRANCESA, ZB1 - 0.01),
                  (Y_PLACA_N - 0.01, PZ1 - 4.0)]
        corpo = corpo.fuse(prisma_yz(perfil, x, x + NERVURA))
    for x, z in FUROS_PLACA:
        corpo = corpo.cut(cilindro_y(p.PINO_FURO / 2, Y_PLACA - 1, Y_PLACA_N + 1, x, z))
    return corpo


def peca():
    return _placa_fundo().fuse(_luva()).fuse(_placa_sensor())


def impressao():
    return no_chao(peca())


if __name__ == "__main__":
    b = peca()
    bb = b.bounding_box()
    print("base: %.1f cm³, x %.1f–%.1f (%.1f mm), y %.1f–%.1f, z até %.1f, válida=%s"
          % (b.volume / 1000, bb.min.X, bb.max.X, bb.size.X, bb.min.Y, bb.max.Y, bb.max.Z,
             b.is_valid()))
    print("hub: x %.1f–%.1f, y %.1f–%.1f, topo a %.1f (plugues: %.1f mm ao sul)"
          % (HUB[0], HUB[1], HUB[2], HUB[3], HUB[5], HUB[2] - F - PAREDE_LUVA - Y0))
    print("sensor: x %.1f–%.1f, frente em y %.1f, olhos %s, pinos em %s"
          % (SENSOR[0], SENSOR[1], SENSOR_Y_FRENTE, SENSOR_OLHOS, FUROS_SENSOR))
    print("gravado:", exportar(b, "base"))
