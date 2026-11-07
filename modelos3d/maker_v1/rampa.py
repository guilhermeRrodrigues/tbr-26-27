# Rampa do Bloco, com o suporte do motor da comporta.
#
# Peça única, na ponta leste da bandeja (encosta na parede leste):
#   - 2 laterais que apoiam no fundo da bandeja, com um ASSENTO sobre a parede sul
#     e uma ABA que desce por fora dela: a parede fica presa entre as laterais e
#     a aba, e a rampa não anda em y (sem cola nem fita);
#   - placa inclinada (ANGULO_RAMPA) com nervuras ao longo da descida; ela passa
#     sobre a parede sul e termina num LÁBIO fora da bandeja, a LABIO_ALTURA do
#     tapete (não toca o tapete);
#   - parede de trás logo atrás do Bloco carregado, e fenda do dente na placa;
#   - SUPORTE do motor, do lado de fora da lateral oeste: o motor médio fica em pé
#     (eixo em x, disco virado para a lateral, cabo saindo por cima), apoiado num
#     pé e preso por 6 pinos Technic numa placa ao norte dele. Um eixo LEGO passa
#     do disco, pelo mancal da lateral, até o dente (comporta.py), dentro do túnel.
#
# Referencial: o da bandeja (parametros.py). "s" é a distância ao longo da
# superfície, medida a partir da ponta do lábio, subindo; "n" é a altura na normal.
# Impressão: deitada sobre a lateral LESTE (placa, parede de trás, pé e placa de
# pinos ficam em pé; os furos de pino ficam deitados). Sem suporte.

import math

import parametros as p
from geometria import caixa, cilindro_x, cilindro_y, exportar, girar, no_chao, prisma_yz, tan

A = p.ANGULO_RAMPA
TAN, COS, SIN = tan(A), math.cos(math.radians(A)), math.sin(math.radians(A))
T = p.PAREDE_ESPESSURA
E = p.RAMPA_ESPESSURA
EV = E / COS                                      # espessura da placa na vertical
Z_U_EXT = p.Z_PAREDE + p.FOLGA_SOBRE_PAREDE       # face de baixo da placa em y = −T
Y_PONTA = -T - (Z_U_EXT - p.LABIO_ALTURA) / TAN   # ponta do lábio

# Canal do Bloco (x), encostado na parede leste.
XR1 = p.X_RAMPA_LESTE
XC1 = XR1 - p.RAMPA_PAREDE
XC0 = XC1 - (p.BLOCO + 2 * p.FOLGA_BLOCO)
XR0 = XC0 - p.RAMPA_PAREDE


def z_baixo(y):
    # Face de baixo da placa.
    return Z_U_EXT + (y + T) * TAN


def z_sup(y):
    # Superfície da placa (sem as nervuras).
    return z_baixo(y) + EV


def ponto(s, n=0.0):
    # Ponto (y, z) a s da ponta, ao longo da superfície, e n acima dela (na normal).
    y = Y_PONTA + s * COS - n * SIN
    z = z_sup(Y_PONTA) + s * SIN + n * COS
    return y, z


def s_de_y(y):
    return (y - Y_PONTA) / COS


# --- Eixo do motor e dente ----------------------------------------------------------------
# O eixo fica DIST_EIXO_PLACA abaixo da superfície (na normal), no ponto S_EIXO. O
# dente tem R_DENTE do eixo à ponta. Aberto (90°), fica paralelo à placa e aponta
# para BAIXO da rampa: a ponta não pode chegar ao fundo nem à parede sul. O pé do
# motor também precisa de espaço. S_EIXO é o MENOR que cumpre tudo: o Bloco fica o
# mais baixo possível, cai de menos altura, e a rampa fica curta.
D = p.DIST_EIXO_PLACA
R_DENTE = D + p.DENTE_ACIMA
W_DENTE = p.DENTE_ESPESSURA / 2                   # meia espessura, ao longo da rampa
PE_MIN = 2.0                                      # espessura mínima do pé do motor


def _cabe(s):
    y, z = ponto(s, -D)
    # Aberto, o dente aponta para baixo da rampa; a face de baixo dele fica W_DENTE
    # mais funda que a linha do dente.
    ponta_y = y - R_DENTE * COS + W_DENTE * SIN
    ponta_z = z - R_DENTE * SIN - W_DENTE * COS
    pe = z - p.MOTOR_FRENTE - 0.3 - p.Z_FUNDO
    return (ponta_y >= p.FOLGA_DENTE_TUNEL
            and ponta_z >= p.Z_FUNDO + p.FOLGA_DENTE_TUNEL
            and pe >= PE_MIN
            and y - p.MOTOR_LARGURA / 2 >= p.FOLGA_BANDEJA)


S_EIXO = next(i * 0.25 for i in range(2000) if _cabe(i * 0.25))
Y_EIXO, Z_EIXO = ponto(S_EIXO, -D)

# Bloco carregado: apoiado nas nervuras, encostado no dente.
S_BLOCO_FRENTE = S_EIXO + W_DENTE + 0.5
S_BLOCO_TRAS = S_BLOCO_FRENTE + p.BLOCO
Y_TRAS = ponto(S_BLOCO_TRAS, p.NERVURA_ALTURA)[0] + p.FOLGA_BLOCO_TRAS  # canto de baixo, atrás

# Motor em pé, fora da lateral oeste, com o disco a 0,5 da lateral.
XM_TOPO = XR0 - 0.5 - p.MOTOR_DISCO_SALIENCIA     # plano de cima do motor (lado do disco)
XM0 = XM_TOPO - p.MOTOR_ALTURA                     # fundo do motor (lado oeste)
YM0, YM1 = Y_EIXO - p.MOTOR_LARGURA / 2, Y_EIXO + p.MOTOR_LARGURA / 2
ZM0, ZM1 = Z_EIXO - p.MOTOR_FRENTE, Z_EIXO + p.MOTOR_TRAS
# Placa de pinos ao norte do motor.
YP0 = YM1 + 0.3
YP1 = YP0 + p.SUPORTE_MOTOR_ESPESSURA
FUROS_MOTOR = [(XM0 + h, Z_EIXO + c) for h in p.MOTOR_FUROS_ALTURA
               for c in p.MOTOR_FUROS_COMPRIMENTO]

Y_NORTE = max(Y_TRAS + p.RAMPA_PAREDE, YP1)
if Y_NORTE > p.BANDEJA_Y - p.FOLGA_BANDEJA:
    raise SystemExit("rampa não cabe na bandeja: termina em y = %.1f" % Y_NORTE)

# Cubo do dente, logo dentro da lateral oeste; o dente no meio do cubo.
X_CUBO = (XC0 + 0.5, XC0 + 0.5 + p.CUBO_DENTE_COMPRIMENTO)
X_DENTE = (X_CUBO[0] + X_CUBO[1]) / 2


def _laterais():
    zf, zp = p.Z_FUNDO, p.Z_PAREDE
    yi = 0.5                                   # folga da face interna da parede sul
    ye = -T - 0.5                              # face interna da aba
    perfil = [
        (Y_NORTE, zf),
        (yi, zf),
        (yi, zp + p.ASSENTO_FOLGA),
        (ye, zp + p.ASSENTO_FOLGA),
        (ye, zp - p.GANCHO_DESCIDA),
        (ye - p.GANCHO_ESPESSURA, zp - p.GANCHO_DESCIDA),
        (Y_PONTA, z_baixo(Y_PONTA)),
        (Y_PONTA, z_sup(Y_PONTA) + p.TRILHO_ALTURA),
        (Y_NORTE, z_sup(Y_NORTE) + p.TRILHO_ALTURA),
    ]
    oeste = prisma_yz(perfil, XR0, XC0)
    leste = prisma_yz(perfil, XC1, XR1)
    # Mancal do eixo LEGO na lateral oeste.
    oeste = oeste.cut(cilindro_x(p.FURO_EIXO_LIVRE / 2, XR0 - 1, XC0 + 1, Y_EIXO, Z_EIXO))
    return oeste.fuse(leste)


def _placa():
    perfil = [(Y_PONTA, z_baixo(Y_PONTA)), (Y_NORTE, z_baixo(Y_NORTE)),
              (Y_NORTE, z_sup(Y_NORTE)), (Y_PONTA, z_sup(Y_PONTA))]
    placa = prisma_yz(perfil, XC0 - 0.01, XC1 + 0.01)
    # Nervuras ao longo da descida.
    n = int((XC1 - XC0) // p.NERVURA_PASSO)
    x0 = (XC0 + XC1) / 2 - (n - 1) * p.NERVURA_PASSO / 2
    h = p.NERVURA_ALTURA / COS
    for i in range(n):
        x = x0 + i * p.NERVURA_PASSO
        nerv = prisma_yz([(Y_PONTA, z_sup(Y_PONTA) - 0.01), (Y_TRAS, z_sup(Y_TRAS) - 0.01),
                          (Y_TRAS, z_sup(Y_TRAS) + h), (Y_PONTA, z_sup(Y_PONTA) + h)],
                         x - p.NERVURA_LARGURA / 2, x + p.NERVURA_LARGURA / 2)
        placa = placa.fuse(nerv)
    return placa


def _tras():
    return caixa(XR0, XR1, Y_TRAS, Y_NORTE, p.Z_FUNDO, z_sup(Y_NORTE) + p.TRILHO_ALTURA)


def limites_fenda():
    # Fenda do dente: (s0, s1) ao longo da descida e (x0, x1). Para baixo, vai até
    # onde o dente, girando, ainda atravessa a placa.
    f = p.FOLGA_FENDA
    alcance = math.sqrt(R_DENTE ** 2 - (D - E - 0.5) ** 2) + W_DENTE + f
    w = p.DENTE_LARGURA / 2 + f
    return S_EIXO - alcance, S_EIXO + W_DENTE + f, X_DENTE - w, X_DENTE + w


def _fenda():
    s0, s1, xa, xb = limites_fenda()
    cantos = [ponto(s0, -E - 2), ponto(s1, -E - 2), ponto(s1, p.NERVURA_ALTURA + 2),
              ponto(s0, p.NERVURA_ALTURA + 2)]
    return prisma_yz(cantos, xa, xb)


def _suporte_motor():
    e = 2.0
    x0, x1 = XM0 - e, XR0 + 1.0                    # entra 1 mm na lateral
    pe = caixa(x0, x1, YM0, YP0 + 0.01, p.Z_FUNDO, ZM0 - 0.3)
    z_topo = max(z for _, z in FUROS_MOTOR) + 6.0
    placa = caixa(x0, x1, YP0, YP1, p.Z_FUNDO, z_topo)
    for x, z in FUROS_MOTOR:
        placa = placa.cut(cilindro_y(p.PINO_FURO / 2, YP0 - 1, YP1 + 1, x, z))
    return pe.fuse(placa)


def peca():
    r = _laterais().fuse(_placa()).fuse(_tras()).fuse(_suporte_motor())
    return r.cut(_fenda())


def impressao():
    # Deitada sobre a lateral leste (x = XR1 vai para z = 0).
    return no_chao(girar(peca(), "y", -90))


if __name__ == "__main__":
    r = peca()
    bb = r.bounding_box()
    print("rampa: %.1f cm³, x %.1f–%.1f, y %.1f–%.1f, z %.1f–%.1f, válida=%s"
          % (r.volume / 1000, bb.min.X, bb.max.X, bb.min.Y, bb.max.Y, bb.min.Z, bb.max.Z,
             r.is_valid()))
    print("lábio: y %.1f (%.1f além da face externa), ponta a %.1f do tapete"
          % (Y_PONTA, -T - Y_PONTA, z_baixo(Y_PONTA)))
    print("eixo: s = %.1f, y = %.1f, z = %.1f; dente de %.1f; Bloco de s %.1f a %.1f"
          % (S_EIXO, Y_EIXO, Z_EIXO, R_DENTE, S_BLOCO_FRENTE, S_BLOCO_TRAS))
    print("motor: x %.1f–%.1f, y %.1f–%.1f, z %.1f–%.1f"
          % (XM0, XM_TOPO + p.MOTOR_DISCO_SALIENCIA, YM0, YM1, ZM0, ZM1))
    print("gravado:", exportar(r, "rampa"))
