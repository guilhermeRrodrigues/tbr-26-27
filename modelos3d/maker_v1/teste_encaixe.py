# Prato de teste P0 do Dispositivo Maker: imprima ANTES do resto.
#
#   placa_teste   trecho de 70 mm da rampa (mesmas nervuras, trilhos e canal)
#   cunha_25/30/35  apoios: a placa deita sobre a cunha e fica no ângulo dela
#   gabarito_motor  os 6 furos do suporte do motor (mesma posição da rampa)
#   gabarito_sensor os 2 furos de trás do ultrassônico
#
# Como testar:
#   1. Deslize: com o Bloco (P3) na placa, apoie a placa em cada cunha. Escolha o
#      MENOR ângulo em que o Bloco desce sozinho, partindo parado, 5 vezes em 5.
#      Ponha esse valor em ANGULO_RAMPA (parametros.py).
#   2. Motor: com 6 pinos Technic, prenda o gabarito na lateral do motor médio
#      (furos que atravessam os 24 mm). Os 6 pinos têm que entrar juntos. Se não
#      entrarem, corrija MOTOR_FUROS_COMPRIMENTO / MOTOR_FUROS_ALTURA.
#   3. Sensor: com 2 pinos, prenda o gabarito na traseira do ultrassônico. Se não
#      entrarem, corrija SENSOR_FUROS_TRAS_X (a placa perfurada da base tem grade,
#      então só o par de furos precisa bater).
#
# Impressão: tudo deitado, sem suporte (camada 0,28).

import math

import parametros as p
from geometria import caixa, cilindro, exportar, girar, no_chao, prisma_xz

COMPRIMENTO = 70.0
CANAL = p.BLOCO + 2 * p.FOLGA_BLOCO
CUNHA_BASE = 70.0
CUNHA_LARGURA = 12.0


def placa_teste():
    w, e, t = CANAL / 2, p.RAMPA_ESPESSURA, p.RAMPA_PAREDE
    corpo = caixa(-w - t, w + t, 0, COMPRIMENTO, 0, e)
    for x0 in (-w - t, w):
        corpo = corpo.fuse(caixa(x0, x0 + t, 0, COMPRIMENTO, e - 0.01, e + p.TRILHO_ALTURA))
    n = int(CANAL // p.NERVURA_PASSO)
    x_ini = -(n - 1) * p.NERVURA_PASSO / 2
    for i in range(n):
        x = x_ini + i * p.NERVURA_PASSO
        corpo = corpo.fuse(caixa(x - p.NERVURA_LARGURA / 2, x + p.NERVURA_LARGURA / 2,
                                 0, COMPRIMENTO, e - 0.01, e + p.NERVURA_ALTURA))
    return corpo


def cunha(graus):
    # Triângulo retângulo deitado: a hipotenusa tem o ângulo pedido. Batente na
    # ponta alta para a placa não escorregar da cunha.
    h = CUNHA_BASE * math.tan(math.radians(graus))
    perfil = [(0, 0), (CUNHA_BASE, 0), (CUNHA_BASE, h)]
    corpo = prisma_xz(perfil, 0, CUNHA_LARGURA)
    # Vazada: só o contorno de d mm (economiza PLA).
    d = 4.0
    a = math.radians(graus)
    x1 = (d + d / math.cos(a)) / math.tan(a)
    z2 = (CUNHA_BASE - d) * math.tan(a) - d / math.cos(a)
    corpo = corpo.cut(prisma_xz([(x1, d), (CUNHA_BASE - d, d), (CUNHA_BASE - d, z2)],
                                -1, CUNHA_LARGURA + 1))
    # Marca do ângulo: 1 furo a cada 5°, na base.
    for i in range(int(graus // 5)):
        corpo = corpo.cut(caixa(x1 + 2 + 4 * i, x1 + 4 + 4 * i, 2, CUNHA_LARGURA - 2,
                                -1, d + 1))
    return corpo


def _gabarito(furos, ponte=4.0):
    # Placa de pinos (PLACA_SENSOR_ESPESSURA) só com ressaltos nos furos, ligados
    # por barras: furos (x, z) no plano; a placa fica deitada (furos na vertical).
    e = p.PLACA_SENSOR_ESPESSURA
    r = p.PINO_FURO / 2 + 2.5
    xs = sorted({x for x, _ in furos})
    zs = sorted({z for _, z in furos})
    corpo = None
    for x, z in furos:
        c = caixa(x - r, x + r, z - r, z + r, 0, e)
        corpo = c if corpo is None else corpo.fuse(c)
    for x in xs if len(zs) > 1 else []:
        corpo = corpo.fuse(caixa(x - ponte / 2, x + ponte / 2, zs[0], zs[-1], 0, e))
    for z in zs if len(xs) > 1 else []:
        corpo = corpo.fuse(caixa(xs[0], xs[-1], z - ponte / 2, z + ponte / 2, 0, e))
    for x, z in furos:
        corpo = corpo.cut(cilindro(p.PINO_FURO / 2, -1, e + 1, x, z))
    return corpo


def gabarito_motor():
    return _gabarito([(h, c) for h in p.MOTOR_FUROS_ALTURA for c in p.MOTOR_FUROS_COMPRIMENTO])


def gabarito_sensor():
    x = p.SENSOR_FUROS_TRAS_X
    return _gabarito([(-x, 0.0), (x, 0.0)])


def pecas():
    return {
        "placa_teste": no_chao(placa_teste()),
        "cunha_25": no_chao(girar(cunha(25), "x", 90)),
        "cunha_30": no_chao(girar(cunha(30), "x", 90)),
        "cunha_35": no_chao(girar(cunha(35), "x", 90)),
        "gabarito_motor": no_chao(gabarito_motor()),
        "gabarito_sensor": no_chao(gabarito_sensor()),
    }


if __name__ == "__main__":
    for nome, peca in pecas().items():
        bb = peca.bounding_box()
        print("%-15s %5.1f cm³  %5.1f × %5.1f × %5.1f  válida=%s"
              % (nome, peca.volume / 1000, bb.size.X, bb.size.Y, bb.size.Z, peca.is_valid()))
        exportar(peca, nome)
