# CoopBot — programa do 2º hub: Dispositivo Maker (M8)
# =====================================================
# Roda NO HUB DO MAKER, não no robô. Grave com `tbr gravar --so-maker`.
#
# 1. Espera o aviso do robô (avisar_maker() no tbr.py, por broadcast BLE):
#    luz LARANJA.
# 2. Com o aviso, gira a trava MAKER_TRAVA_GRAUS e fica segurando: o Bloco
#    desce a rampa. Luz VERDE.
#
# Feche a trava à mão ANTES de iniciar: o ângulo de partida vira o 0.
# Teste sem o robô: a seta ESQUERDA faz as vezes do aviso.
# O robô transmite até o programa dele acabar. Reiniciar este hub com o aviso
# no ar solta a trava na hora: pare o programa do robô antes de repetir.
# Porta, canal e atraso ficam em config.py (seção Dispositivo Maker).

from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor
from pybricks.parameters import Button, Color, Stop
from pybricks.messaging import BLERadio
from pybricks.tools import wait

import config

# O hub antes do rádio (support#2734, corrigido no 4.0.1, mas não custa).
hub = PrimeHub()
radio = BLERadio(observe_channels=[config.MAKER_CANAL])
trava = Motor(config.MAKER_PORTA_TRAVA)
trava.reset_angle(0)
trava.stop()                    # solta: o Bloco não força a trava


# --- 1. Espera o aviso do robô --------------------------------------------------
hub.light.on(Color.ORANGE)
print("MAKER esperando o aviso (canal %d)" % config.MAKER_CANAL)
while True:
    if radio.observe(config.MAKER_CANAL) == config.MAKER_SINAL:
        print("MAKER aviso recebido")
        break
    if Button.LEFT in hub.buttons.pressed():
        print("MAKER aviso simulado (seta esquerda)")
        break
    wait(50)

wait(config.MAKER_ATRASO_MS)

# --- 2. Abre a trava e segura ---------------------------------------------------
trava.run_target(config.MAKER_TRAVA_VEL, config.MAKER_TRAVA_GRAUS, then=Stop.HOLD)
hub.light.on(Color.GREEN)
hub.speaker.beep(800, 150)
print("MAKER trava aberta (%d graus)" % trava.angle())
# O programa continua vivo para o motor segurar a trava aberta.
while True:
    wait(100)
