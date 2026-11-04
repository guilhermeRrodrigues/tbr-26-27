# CoopBot — rotinas de calibração do menu
# =======================================
# Cada rotina aparece no menu com uma letra:
#   P  Portas   gira cada motor e mostra os sensores (confere o mapa de portas)
#   C  Cor      mede preto/branco dos dois sensores passando sobre uma linha
#   G  Giro     escala do giroscópio (heading_correction), girando o robô à mão
#   R  Reta     anda 50 cm; você mede e corrige o diâmetro da roda
#   B  Bitola   gira 3 voltas pelos encoders e compara com o giroscópio
#   A  Anexo    mede, girando o braço à mão, quantos graus ele abre a partir do
#               batente de trás (o ABRE_ANEXO das missões). Não grava nada.
#   D  Deriva   robô PARADO 60 s: quanto o rumo anda sozinho (graus/min)
#   T  Teste    bateria de giros: erro final medido e tempo de cada um
#   Z  Zero     fixa o rumo da MESA com o robô no gabarito (largada compensada)
#
# Os valores são gravados no hub (calibracao.py) e valem a partir do PRÓXIMO
# início do programa. Durante a rotina: setas ◀ ▶ respondem, o central confirma.

from pybricks.parameters import Axis, Button, Color
from pybricks.tools import wait, StopWatch

import calibracao
import config
import tbr

VOLTAS_GIRO = 5
# heading_correction aceito: o firmware só aceita 360±15. A faixa antiga
# (300-800) deixava passar uma volta a mais ou a menos na contagem.
HC_MIN, HC_MAX = 345.0, 375.0
HC_ASSIMETRIA_MAX = 0.5             # % entre horário e anti-horário
DERIVA_S = 60
TESTE_GIROS = (90, -90, 180, -180, 45, -45, 30, -30, 135, -135, 10, -10)
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

    # Giro de 90 graus SÓ pelos encoders: o giroscópio tem de ver +90 (horário).
    # Se vir -90, a direita e a esquerda das rodas estão trocadas no config.
    tbr.db.use_gyro(False)
    try:
        inicio = tbr.hub.imu.heading()
        tbr._aplicar_vel(tbr.LENTO)
        tbr.db.turn(90)
        wait(300)
        visto = tbr.hub.imu.heading() - inicio
    finally:
        tbr.db.stop()
        tbr.db.use_gyro(True)
    if visto > 45:
        print("Giro OK: comandado +90, giroscopio viu %+.0f" % visto)
        tbr.hub.display.char("V")
        tbr.hub.speaker.beep(900, 150)
    else:
        print("GIRO INVERTIDO: comandado +90, giroscopio viu %+.0f." % visto)
        print("Troque PORTA_RODA_DIR <-> PORTA_RODA_ESQ e SENTIDO_RODA_DIR <->")
        print("SENTIDO_RODA_ESQ em config.py.")
        tbr.hub.display.char("X")
        tbr.hub.light.on(Color.RED)
        tbr.hub.speaker.beep(200, 600)
    wait(1500)

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
    """Escala do giroscópio: gire o robô À MÃO VOLTAS_GIRO voltas para cada lado."""
    print("=== Giro ===")
    print("Robo APOIADO no tapete, alinhado a uma marca (ex.: no gabarito).")
    print("Central para INICIAR.")
    tbr.hub.display.char("G")
    _esperar_central()
    b0 = tbr.hub.imu.rotation(-Axis.Z, calibrated=False)
    tbr.hub.light.on(Color.BLUE)
    print("1) Gire %d voltas no sentido HORARIO, sempre apoiado e sem pressa," % VOLTAS_GIRO)
    print("   pare na marca e aperte o central.")
    _esperar_central()
    b1 = tbr.hub.imu.rotation(-Axis.Z, calibrated=False)
    tbr.hub.light.on(Color.CYAN)
    print("2) Agora %d voltas ANTI-HORARIO, de volta a marca, e central." % VOLTAS_GIRO)
    _esperar_central()
    b2 = tbr.hub.imu.rotation(-Axis.Z, calibrated=False)
    # A média dos dois sentidos cancela o bias que entra durante as voltas.
    hor = abs(b1 - b0) / VOLTAS_GIRO
    anti = abs(b1 - b2) / VOLTAS_GIRO
    por_volta = (hor + anti) / 2.0
    assim = abs(hor - anti) * 100.0 / por_volta if por_volta else 100.0
    print("Horario %.2f | anti-horario %.2f | media %.2f graus brutos por volta"
          % (hor, anti, por_volta))
    print("Diferenca entre os sentidos: %.2f%%" % assim)
    if assim > HC_ASSIMETRIA_MAX:
        print("Diferenca grande: o robo escorregou, saiu da marca ou a contagem de")
        print("voltas errou. Repita.")
        _ok(False)
        return
    if HC_MIN <= por_volta <= HC_MAX:
        # Persiste sozinho no hub (não usa o storage). Imprime a tupla inteira:
        # o layout de settings() muda entre versões do firmware (Baymax).
        tbr.hub.imu.settings(heading_correction=por_volta)
        print("IMU settings:", tbr.hub.imu.settings())
        _ok(True)
    else:
        print("Fora de %d-%d: contagem de voltas errada?" % (HC_MIN, HC_MAX))
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


def anexo():
    """Mede quantos graus o anexo1 gira do batente de trás até onde deve abrir."""
    print("=== Anexo ===")
    print("1) Encoste o braco no batente de TRAS e aperte o central.")
    tbr._anexo1.stop()                  # solto: mexe à mão
    tbr.hub.display.char("A")
    _esperar_central()
    tbr._anexo1.reset_angle(0)
    print("2) Leve o braco A MAO ate onde ele deve ficar aberto e aperte o central.")
    print("   (a matriz mostra dezenas de graus com sinal: -22 = -220 graus)")
    ultimo = None
    while Button.CENTER not in tbr.hub.buttons.pressed():
        a = tbr._anexo1.angle()
        tbr.hub.display.number(max(-99, min(99, int(a / 10))))
        if ultimo is None or abs(a - ultimo) >= 10:
            print("   anexo1: %d graus" % a)
            ultimo = a
        wait(50)
    _soltar_botoes()
    a = tbr._anexo1.angle()
    print("ABRE_ANEXO = %d   (copie para a missao COM O SINAL: negativo = para a frente)" % a)
    tbr.hub.light.on(Color.GREEN)
    tbr.hub.speaker.beep(900, 200)
    wait(1500)


def deriva():
    """Robô PARADO DERIVA_S segundos: quanto o rumo anda sozinho."""
    print("=== Deriva ===")
    print("Robo parado no tapete, nada encostado. Central e NAO toque por %d s." % DERIVA_S)
    tbr.hub.display.char("D")
    _esperar_central()
    tbr.parar_tudo()                 # tudo em coast: o firmware pode reestimar o bias
    wait(1500)
    h0 = tbr.rumo()
    cron = StopWatch()
    marca = 0
    parado_ms = 0
    while cron.time() < DERIVA_S * 1000:
        restam = DERIVA_S - cron.time() // 1000
        tbr.hub.display.number(min(99, restam))
        if tbr.hub.imu.stationary():
            parado_ms += 100
        if cron.time() >= marca:
            print("  %3d s: rumo %+.2f" % (marca // 1000, tbr.rumo() - h0))
            marca += 10000
        wait(100)
    total = tbr.rumo() - h0
    por_min = total * 60000.0 / cron.time()
    print("Deriva: %+.2f graus em %d s = %+.2f graus/min (parado %d%% do tempo)"
          % (total, DERIVA_S, por_min, parado_ms * 100 // (DERIVA_S * 1000)))
    print("Em 2 min de partida: ~%.1f graus. Bom: < 0,3 graus/min." % abs(por_min * 2))
    tbr.hub.display.number(max(-99, min(99, int(round(por_min * 10)))))
    tbr.hub.light.on(Color.GREEN if abs(por_min) < 0.3 else Color.YELLOW
                     if abs(por_min) < 1.0 else Color.RED)
    print("(a matriz mostra decimos de grau por minuto)")
    _esperar_central()


def teste_giro():
    """Bateria de giros: o erro final que o giroscópio vê e o tempo de cada um."""
    print("=== Teste de giro ===")
    print("Robo no tapete com espaco para girar, alinhado a uma marca.")
    print("Central para comecar; no fim ele volta a direcao inicial.")
    tbr.hub.display.char("T")
    _esperar_central()
    tbr.parar_tudo()
    wait(1000)
    base = tbr.rumo()
    erros = []
    tempos = []
    for alvo in TESTE_GIROS:
        cron = StopWatch()
        ok = tbr.virar_para(base + alvo)
        ms = cron.time()
        wait(300)                    # assenta: o erro medido é o que ficou
        erro = tbr.rumo() - (base + alvo)
        erros.append(abs(erro))
        tempos.append(ms)
        print("  virar_para(%+4d): %4d ms, erro %+.2f%s" % (alvo, ms, erro, "" if ok else " FALHOU"))
    tbr.virar_para(base)
    wait(300)
    erros.sort()
    print("Erro medio %.2f | maximo %.2f graus | tempo medio %d ms"
          % (sum(erros) / len(erros), erros[-1], sum(tempos) // len(tempos)))
    print("Confira a marca no chao: o robo deve estar de novo na direcao inicial.")
    print("(o giroscopio nao ve o proprio erro de escala: a marca e a prova real)")
    tbr.hub.display.number(min(99, int(round(erros[-1] * 10))))
    _esperar_central()


def referencia():
    """Fixa o rumo da MESA: robô no gabarito, apontando para a direção 0."""
    print("=== Referencia da mesa ===")
    print("Robo no GABARITO, na direcao da 1a saida. Central e solte o robo.")
    tbr.hub.display.char("Z")
    _esperar_central()
    tbr.parar_tudo()
    wait(1200)
    tbr.definir_mesa(0)
    print("Referencia fixada: as proximas largadas sao medidas contra ela.")
    tbr.hub.light.on(Color.GREEN)
    tbr.hub.speaker.beep(900, 200)
    wait(800)


# Entradas do menu: (letra, nome, função)
ROTINAS = (
    ("P", "Portas", portas),
    ("C", "Cor", cor),
    ("G", "Giro", giro),
    ("R", "Reta", reta),
    ("B", "Bitola", bitola),
    ("A", "Anexo", anexo),
    ("D", "Deriva", deriva),
    ("T", "Teste de giro", teste_giro),
    ("Z", "Referencia da mesa", referencia),
)
