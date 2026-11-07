# Módulo LEGO do Dispositivo Maker v2: nada aqui é impresso.
#
# Peças do kit SPIKE Prime (45678) como sólidos simples (vigas como caixas de
# VIGA_SECAO, o lado seguro), no referencial da bandeja, com os furos de cada uma.
#
#   hub      deitado no fundo, tela para cima, na ponta oeste, encostado na parede
#            norte;
#   viga_sensor  7M EM PÉ, na ponta oeste do hub (furos 1 e 3 nos furos de 4 e 20 mm
#            da ponta, no furo do lado sul). O sensor encaixa pela ponta oeste nos
#            furos 5 e 7: fica deitado SOBRE o hub, olhando para o sul;
#   viga_encosto 9M deitada na ponta leste do hub (furos 1 e 5 nos furos de 4 mm da
#            ponta): desce até perto da parede sul e não deixa o hub andar em y;
#   motor    deitado sobre a prateleira da rampa (4 pinos), comprido para o oeste,
#            por cima do hub; o eixo vai ao longo da descida;
#   trava    viga 7M pinada no disco do motor (rampa.trava_local).
#
# Pinos: todos são pinos com atrito de 2 módulos (pretos).

import parametros as p
import rampa
from geometria import caixa

S = p.VIGA_SECAO / 2
PASSO = p.PASSO_LEGO

# --- Hub ------------------------------------------------------------------------------
HX0 = p.FOLGA_BANDEJA + p.VIGA_SECAO               # a viga do sensor fica a oeste
HX1 = HX0 + p.HUB_COMPRIMENTO
HY1 = p.BANDEJA_Y - p.FOLGA_BANDEJA
HY0 = HY1 - p.HUB_LARGURA
HZ0 = p.Z_FUNDO
HZ1 = HZ0 + p.HUB_ESPESSURA
HYC = (HY0 + HY1) / 2


def furos_ponta_hub():
    # Furos das 2 pontas do hub: (x da face, y, z), eixo em x.
    return [(x, HYC + dy, HZ0 + h) for x in (HX0, HX1)
            for dy in p.HUB_FUROS_PONTA for h in p.HUB_FUROS_ALTURA]


# --- Viga do sensor (7M em pé na ponta oeste) -----------------------------------------
VS_Y = HYC + p.HUB_FUROS_PONTA[0]                  # furo do lado sul da ponta
VS_Z = [HZ0 + p.HUB_FUROS_ALTURA[0] + i * PASSO for i in range(7)]
VS_X = (HX0 - p.VIGA_SECAO, HX0)
PINOS_HUB_SENSOR = [VS_Z[0], VS_Z[2]]              # furos 1 e 3 → furos de 4 e 20 mm
PINOS_SENSOR = [VS_Z[4], VS_Z[6]]                  # furos 5 e 7 → furos da ponta do sensor

# --- Sensor (deitado sobre o hub, olhando para o sul) ---------------------------------
SZC = (PINOS_SENSOR[0] + PINOS_SENSOR[1]) / 2      # meio da altura do sensor
SX0 = HX0
SX1 = SX0 + p.SENSOR_LARGURA
SY1 = VS_Y + p.SENSOR_FURO_PONTA_FUNDO             # traseira (norte)
SY0 = SY1 - p.SENSOR_PROFUNDIDADE                  # frente (olhos)
SZ0 = SZC - p.SENSOR_ALTURA / 2
SZ1 = SZC + p.SENSOR_ALTURA / 2
OLHOS = [((SX0 + SX1) / 2 + d, SY0, SZC) for d in (-p.SENSOR_OLHOS_ENTRE / 2,
                                                   p.SENSOR_OLHOS_ENTRE / 2)]

# --- Viga de encosto (9M deitada na ponta leste) --------------------------------------
VE_X = (HX1, HX1 + p.VIGA_SECAO)
VE_Z = HZ0 + p.HUB_FUROS_ALTURA[0]
VE_Y = [HYC + p.HUB_FUROS_PONTA[1] - i * PASSO for i in range(9)]   # do norte para o sul
PINOS_ENCOSTO = [VE_Y[0], VE_Y[4]]                 # furos 1 e 5 → furos da ponta


def _viga_z(x0, x1, y, zs):
    return caixa(x0, x1, y - S, y + S, zs[0] - S, zs[-1] + S)


def _viga_y(x0, x1, ys, z):
    return caixa(x0, x1, min(ys) - S, max(ys) + S, z - S, z + S)


def pecas(graus_trava=0.0):
    return {
        "hub": caixa(HX0, HX1, HY0, HY1, HZ0, HZ1),
        "sensor": caixa(SX0, SX1, SY0, SY1, SZ0, SZ1),
        "viga_sensor": _viga_z(VS_X[0], VS_X[1], VS_Y, VS_Z),
        "viga_encosto": _viga_y(VE_X[0], VE_X[1], VE_Y, VE_Z),
        "motor": rampa.local(rampa.motor_local()),
        "trava": rampa.local(rampa.trava_local(graus_trava)),
    }


def pinos():
    # (peça A, peça B, ponto do pino na bandeja, eixo) para a conferência da grade.
    r = []
    for z in PINOS_HUB_SENSOR:
        r.append(("viga_sensor", "hub", (HX0, VS_Y, z), "x"))
    for z in PINOS_SENSOR:
        r.append(("viga_sensor", "sensor", (HX0, VS_Y, z), "x"))
    for y in PINOS_ENCOSTO:
        r.append(("viga_encosto", "hub", (HX1, y, VE_Z), "x"))
    return r


LISTA = [
    ("viga 7M (reta, 7 furos)", 1, "em pé na ponta oeste do hub: segura o sensor"),
    ("viga 9M (reta, 9 furos)", 1, "deitada na ponta leste do hub: encosto contra a parede sul"),
    ("viga 7M (reta, 7 furos)", 1, "trava: pinada no disco do motor"),
    ("pino com atrito, 2 módulos (preto)", 12,
     "2 hub–viga do sensor, 2 viga–sensor, 2 hub–encosto, 4 motor–prateleira, 2 trava–disco"),
]


def texto_lista():
    return "\n".join("- %d× %s: %s" % (n, nome, uso) for nome, n, uso in LISTA)


if __name__ == "__main__":
    for nome, peca in pecas().items():
        bb = peca.bounding_box()
        print("%-13s x %6.1f–%6.1f  y %6.1f–%6.1f  z %6.1f–%6.1f"
              % (nome, bb.min.X, bb.max.X, bb.min.Y, bb.max.Y, bb.min.Z, bb.max.Z))
    print("olhos:", [tuple(round(c, 1) for c in o) for o in OLHOS])
    print(texto_lista())
