# CoopBot — menu da partida
# =========================
# Um único programa no hub. Na matriz aparece o item escolhido:
#   1, 2, 3...   saídas (saidas.py)
#   P C G R B    rotinas de calibração (rotinas_cal.py)
#
#   ◀ ▶       escolhem o item
#   central    roda o item (e, durante uma saída, ABORTA e volta ao menu)
#   Bluetooth  encerra o programa
#
# Depois de uma saída completa o menu avança sozinho para a próxima. O
# cronômetro da partida (120 s) começa na primeira saída e não para.
#
# Roda NO HUB. Dialeto do hub: formatação com %, sem f-strings, sem anotações.

from pybricks.parameters import Button, Color
from pybricks.tools import wait, StopWatch

import tbr
import saidas
import rotinas_cal

# Assinatura impressa no boot: no `tbr rodar` ela confirma qual programa subiu.
print("COOPBOT TBR2026 menu")

# Diagnóstico de boot: o que este hub está usando DE VERDADE (no `tbr rodar`).
import config
print("DIAG sentidos roda dir=%s esq=%s" % (config.SENTIDO_RODA_DIR, config.SENTIDO_RODA_ESQ))
print("DIAG calibracao %s: roda=%.2f bitola=%.2f" % (
    "GRAVADA" if tbr.cal_gravada else "PADRAO (nada gravado)",
    tbr.cal["roda"], tbr.cal["bitola"]))
print("DIAG cor dir preto=%d branco=%d | esq preto=%d branco=%d" % (
    tbr.cal["preto_dir"], tbr.cal["branco_dir"], tbr.cal["preto_esq"], tbr.cal["branco_esq"]))
print("DIAG imu", tbr.hub.imu.settings())

# Cada item: (rótulo na matriz, nome, função, é_saida)
ITENS = []
for _i in range(len(saidas.SAIDAS)):
    _nome, _funcao = saidas.SAIDAS[_i]
    ITENS.append((str(_i + 1), _nome, _funcao, True))
for _letra, _nome, _funcao in rotinas_cal.ROTINAS:
    ITENS.append((_letra, _nome, _funcao, False))


def _soltar():
    while tbr.hub.buttons.pressed():
        wait(10)


def _mostrar_item(item):
    rotulo, nome, _, e_saida = item
    if e_saida:
        tbr.hub.display.number(int(rotulo))
    else:
        tbr.hub.display.char(rotulo)
    tbr.hub.light.on(Color.GREEN if e_saida else Color.MAGENTA)


def _executar(item):
    rotulo, nome, funcao, e_saida = item
    _soltar()                       # o central que disparou não pode abortar
    tbr.hub.light.on(Color.YELLOW)
    tbr.hub.speaker.beep(800, 80)
    if e_saida:
        if tbr.tempo_partida() == 0:
            tbr.iniciar_partida()
        tbr.zerar_rumo()
        tbr.zerar_anexos()
    print(">>> %s %s (partida em %.1f s)" % (rotulo, nome, tbr.tempo_partida()))
    cron = StopWatch()
    completa = False
    try:
        funcao()
        completa = True
    except tbr.SaidaAbortada:
        tbr.hub.light.on(Color.RED)
        tbr.hub.speaker.beep(200, 300)
        print("ABORTADA pelo botao central")
        _soltar()
    finally:
        tbr.parar_tudo()
    print("<<< %s levou %.1f s | partida %.1f s | restam %.1f s"
          % (rotulo, cron.time() / 1000.0, tbr.tempo_partida(), tbr.tempo_restante()))
    return completa


def menu():
    if not tbr.cal_gravada:
        print("AVISO: sem calibracao gravada, usando os padroes do config.py")
        tbr.hub.display.char("!")
        tbr.hub.speaker.beep(300, 300)
        wait(800)
    i = 0
    while True:
        _mostrar_item(ITENS[i])
        b = tbr.hub.buttons.pressed()
        if Button.RIGHT in b:
            i = (i + 1) % len(ITENS)
            _soltar()
        elif Button.LEFT in b:
            i = (i - 1) % len(ITENS)
            _soltar()
        elif Button.CENTER in b:
            completa = _executar(ITENS[i])
            # Saída completa avança para a próxima saída (nunca para as rotinas).
            if completa and ITENS[i][3] and i + 1 < len(saidas.SAIDAS):
                i += 1
        wait(20)


menu()
