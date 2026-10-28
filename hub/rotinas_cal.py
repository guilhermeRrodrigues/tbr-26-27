# CoopBot — rotinas de calibração do menu
# =======================================
# Cada rotina aparece no menu com uma letra:
#   P  Portas   gira cada motor e mostra os sensores (confere o mapa de portas)
#   C  Cor      mede preto/branco dos dois sensores passando sobre uma linha
#   G  Giro     escala do giroscópio (heading_correction), girando o robô à mão
#   R  Reta     anda 50 cm; você mede e corrige o diâmetro da roda
#   B  Bitola   gira 3 voltas pelos encoders e compara com o giroscópio
#
# Os valores são gravados no hub (calibracao.py) e valem a partir do PRÓXIMO
# início do programa. Durante a rotina: setas ◀ ▶ respondem, o central confirma.

from pybricks.parameters import Axis, Button, Color
from pybricks.tools import wait

import calibracao
import config
import tbr

VOLTAS_GIRO = 5
HC_MIN, HC_MAX = 300.0, 800.0      # graus brutos por volta aceitos (Baymax)
RETA_CM = 50
BITOLA_GRAUS = 1080                 # 3 voltas


def _soltar_botoes():
    while tbr.hub.buttons.pressed():
        wait(10)


def _esperar_central():
    _soltar_botoes()
    while Button.CENTER not in tbr.hub.buttons.pressed():
        wait(10)
    _soltar_botoes()


def _ok(gravou):
    if gravou:
        tbr.hub.light.on(Color.GREEN)
        tbr.hub.speaker.beep(900, 200)
        print("Gravado. Reinicie o programa para usar os novos valores.")
    else:
        tbr.hub.light.on(Color.RED)
        tbr.hub.speaker.beep(200, 400)
        print("NAO gravado (valor fora da faixa ou falha no storage).")
    wait(1000)


def _ajustar(valor, minimo, maximo):
    # ◀ ▶ mudam o número mostrado na matriz; o central confirma.
    _soltar_botoes()
    while True:
        tbr.hub.display.number(valor)
        b = tbr.hub.buttons.pressed()
        if Button.LEFT in b and valor > minimo:
            valor -= 1
        elif Button.RIGHT in b and valor < maximo:
            valor += 1
        elif Button.CENTER in b:
            _soltar_botoes()
            return valor
        wait(180)


def portas():
    """Gira cada motor, um por vez, e depois mostra a refletância dos sensores."""
    print("=== Portas ===")
    print("Cada roda deve girar PARA A FRENTE; o robo deve andar 10 cm RETO.")
    passos = (
        (config.PORTA_RODA_DIR, tbr._roda_dir, 360),
        (config.PORTA_RODA_ESQ, tbr._roda_esq, 360),
        (config.PORTA_ANEXO1, tbr._anexo1, 180),
        (config.PORTA_ANEXO2, tbr._anexo2, 180),
    )
    tbr.db.stop()
    for porta, motor, graus in passos:
        tbr.hub.display.char(tbr._letra(porta))
        print("Porta %s girando %d graus" % (tbr._letra(porta), graus))
        motor.run_angle(300, graus)
        wait(400)
    tbr.hub.display.char("^")
    tbr.andar(10, tbr.LENTO)
    print("Sensores: ◀ = esquerdo (%s), ▶ = direito (%s), central = sair"
          % (tbr._letra(config.PORTA_COR_ESQ), tbr._letra(config.PORTA_COR_DIR)))
    _soltar_botoes()
    lado = tbr.DIR
    while True:
        b = tbr.hub.buttons.pressed()
        if Button.LEFT in b:
            lado = tbr.ESQ
        elif Button.RIGHT in b:
            lado = tbr.DIR
        elif Button.CENTER in b:
            break
        tbr.hub.light.on(Color.BLUE if lado == tbr.ESQ else Color.ORANGE)
        bruto = tbr.reflexao_crua(lado)
        tbr.hub.display.number(min(bruto, 99))
        wait(100)
    _soltar_botoes()


def cor():
    """Passa os dois sensores sobre uma linha e grava o mínimo (preto) e o
    máximo (branco) de cada um."""
    print("=== Cor ===")
    print("Coloque o robo ~5 cm ANTES de uma linha preta/branca, de frente para")
    print("ela. Central para comecar.")
    tbr.hub.display.char("C")
    _esperar_central()
    minimos = {tbr.DIR: 100, tbr.ESQ: 100}
    maximos = {tbr.DIR: 0, tbr.ESQ: 0}
    tbr._aplicar_vel(80)
    tbr.db.straight(150, wait=False)
    while not tbr.db.done():
        for lado in (tbr.DIR, tbr.ESQ):
            r = tbr.reflexao_crua(lado)
            minimos[lado] = min(minimos[lado], r)
            maximos[lado] = max(maximos[lado], r)
        wait(5)
    tbr.db.stop()
    print("DIR preto=%d branco=%d | ESQ preto=%d branco=%d"
          % (minimos[tbr.DIR], maximos[tbr.DIR], minimos[tbr.ESQ], maximos[tbr.ESQ]))
    _ok(calibracao.salvar(tbr.hub,
                          preto_dir=minimos[tbr.DIR], branco_dir=maximos[tbr.DIR],
                          preto_esq=minimos[tbr.ESQ], branco_esq=maximos[tbr.ESQ]))


def giro():
    """Escala do giroscópio: gire o robô À MÃO VOLTAS_GIRO voltas completas."""
    print("=== Giro ===")
    print("Marque o chao e o robo alinhados. Central para INICIAR.")
    tbr.hub.display.char("G")
    _esperar_central()
    bruto_inicial = tbr.hub.imu.rotation(-Axis.Z, calibrated=False)
    tbr.hub.light.on(Color.BLUE)
    print("Gire %d voltas completas no sentido HORARIO, pare na marca e" % VOLTAS_GIRO)
    print("aperte o central.")
    _esperar_central()
    bruto_final = tbr.hub.imu.rotation(-Axis.Z, calibrated=False)
    por_volta = abs(bruto_final - bruto_inicial) / VOLTAS_GIRO
    print("Medido: %.1f graus brutos por volta" % por_volta)
    if HC_MIN <= por_volta <= HC_MAX:
        # Persiste sozinho no hub (não usa o storage). Imprime a tupla inteira:
        # o layout de settings() muda entre versões do firmware (Baymax).
        tbr.hub.imu.settings(heading_correction=por_volta)
        print("IMU settings:", tbr.hub.imu.settings())
        _ok(True)
    else:
        _ok(False)


def reta():
    """Anda RETA_CM; você mede quanto andou de verdade e corrige a roda."""
    print("=== Reta ===")
    print("Marque a posicao do eixo das rodas. Central para andar %d cm." % RETA_CM)
    tbr.hub.display.char("R")
    _esperar_central()
    tbr.zerar_rumo()
    tbr.andar(RETA_CM, tbr.LENTO)
    print("Meca quanto ele andou. Na matriz: diferenca em MILIMETROS")
    print("(real - %d0). ◀ ▶ ajustam, central grava." % RETA_CM)
    erro_mm = _ajustar(0, -99, 99)
    real = RETA_CM * 10 + erro_mm
    nova = tbr.cal["roda"] * real / (RETA_CM * 10.0)
    print("roda: %.2f -> %.2f mm" % (tbr.cal["roda"], nova))
    _ok(calibracao.salvar(tbr.hub, roda=nova))


def bitola():
    """Gira BITOLA_GRAUS só pelos encoders e compara com o giroscópio."""
    print("=== Bitola ===")
    print("Robo no tapete, com espaco para girar. Central para comecar.")
    tbr.hub.display.char("B")
    _esperar_central()
    tbr.db.use_gyro(False)
    try:
        inicio = tbr.hub.imu.heading()
        tbr._aplicar_vel(tbr.LENTO)
        tbr.db.turn(BITOLA_GRAUS)
        wait(500)
        medido = abs(tbr.hub.imu.heading() - inicio)
    finally:
        tbr.db.use_gyro(True)
    print("Comandado %d graus, giroscopio mediu %.1f" % (BITOLA_GRAUS, medido))
    if medido < 90:
        _ok(False)
        return
    nova = tbr.cal["bitola"] * BITOLA_GRAUS / medido
    print("bitola: %.1f -> %.1f mm" % (tbr.cal["bitola"], nova))
    _ok(calibracao.salvar(tbr.hub, bitola=nova))


# Entradas do menu: (letra, nome, função)
ROTINAS = (
    ("P", "Portas", portas),
    ("C", "Cor", cor),
    ("G", "Giro", giro),
    ("R", "Reta", reta),
    ("B", "Bitola", bitola),
)
