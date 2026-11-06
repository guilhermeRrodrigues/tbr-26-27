# CoopBot — programa do 2º hub: Dispositivo Maker (M8)
# =====================================================
# Roda NO HUB DO MAKER, não no robô. Grave com `tbr gravar --maker --nome "<hub>"`.
#
# 1. Espera o aviso do robô (avisar_maker() no tbr.py, por broadcast BLE):
#    luz LARANJA. A matriz mostra a distância lida em cm (99 = nada à vista),
#    para conferir a leitura com a área vazia.
# 2. Com o aviso, olha o ultrassônico: luz AZUL e as luzes do sensor acesas.
# 3. Viu algo a até MAKER_LIMIAR_MM em MAKER_LEITURAS leituras seguidas:
#    gira a trava MAKER_TRAVA_GRAUS e fica segurando. Luz VERDE.
#
# Feche a trava à mão ANTES de iniciar: o ângulo de partida vira o 0.
# Teste sem o robô: a seta ESQUERDA faz as vezes do aviso.
# Portas, canal e limiares ficam em config.py (seção Dispositivo Maker).

from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor, UltrasonicSensor
from pybricks.parameters import Button, Color, Stop
from pybricks.messaging import BLERadio
from pybricks.tools import wait

import config

# O hub antes do rádio (support#2734, corrigido no 4.0.1, mas não custa).
hub = PrimeHub()
radio = BLERadio(observe_channels=[config.MAKER_CANAL])
sensor = UltrasonicSensor(config.MAKER_PORTA_SENSOR)
trava = Motor(config.MAKER_PORTA_TRAVA)
trava.reset_angle(0)
trava.stop()                    # solta: o Bloco não força a trava


def _mostrar_distancia(mm):
    hub.display.number(min(99, mm // 10))


# --- 1. Espera o aviso do robô --------------------------------------------------
hub.light.on(Color.ORANGE)
sensor.lights.off()
print("MAKER esperando o aviso (canal %d)" % config.MAKER_CANAL)
while True:
    if radio.observe(config.MAKER_CANAL) == config.MAKER_SINAL:
        print("MAKER aviso recebido")
        break
    if Button.LEFT in hub.buttons.pressed():
        print("MAKER aviso simulado (seta esquerda)")
        break
    _mostrar_distancia(sensor.distance())
    wait(50)

wait(config.MAKER_ATRASO_MS)

# --- 2. Olha o ultrassônico -----------------------------------------------------
hub.light.on(Color.BLUE)
sensor.lights.on(100)
seguidas = 0
while seguidas < config.MAKER_LEITURAS:
    mm = sensor.distance()
    _mostrar_distancia(mm)
    if mm <= config.MAKER_LIMIAR_MM:
        seguidas += 1
    else:
        seguidas = 0
    wait(50)
print("MAKER viu algo a %d mm" % mm)

# --- 3. Abre a trava e segura ---------------------------------------------------
trava.run_target(config.MAKER_TRAVA_VEL, config.MAKER_TRAVA_GRAUS, then=Stop.HOLD)
hub.light.on(Color.GREEN)
sensor.lights.off()
hub.speaker.beep(800, 150)
print("MAKER trava aberta (%d graus)" % trava.angle())
# O programa continua vivo para o motor segurar a trava aberta.
while True:
    wait(100)
