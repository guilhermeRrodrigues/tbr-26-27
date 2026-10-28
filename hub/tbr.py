# CoopBot — a linguagem das missões
# ==================================
# Funções em português por cima do Pybricks. Uma missão é só uma sequência
# delas:
#
#     from tbr import *
#
#     def m7():
#         seguir_linha_ate_cruzamento(DIR)
#         andar(8)
#         anexo1(-90)
#         voltar_base()
#
# Convenções:
#   - Distância em CENTÍMETROS, ângulo em GRAUS, tempo em MILISSEGUNDOS.
#   - Rumo 0 = para onde o robô apontava ao iniciar a saída (leste, saindo da
#     base). Positivo = horário (direita). O rumo é ABSOLUTO: girar(90) duas
#     vezes dá rumo 180 exato, sem o erro de um giro passar para o próximo.
#   - Posição (x, y) em cm a partir do ponto de partida da saída. x cresce para
#     a frente (leste), y cresce para a esquerda (norte).
#   - Movimento devolve True se terminou, False se abortou (travou ou estourou
#     o tempo). A missão pode reagir: `if not andar(20): voltar_base()`.
#   - Botão CENTRAL durante uma saída = abortar tudo e voltar ao menu.
#
# Roda NO HUB. Dialeto do hub: formatação com %, sem f-strings, sem anotações.
# Nomes que começam com _ são internos e não são exportados pelo import *.

from pybricks.hubs import PrimeHub
from pybricks.pupdevices import Motor, ColorSensor
from pybricks.parameters import Button, Color, Stop
from pybricks.robotics import DriveBase
from pybricks.tools import wait, StopWatch
from umath import sin, cos, atan2, sqrt, pi

import config
import calibracao

# --- Constantes da linguagem -------------------------------------------------
LENTO = config.VEL_LENTO
NORMAL = config.VEL_NORMAL
RAPIDO = config.VEL_RAPIDO

PRETO = "preto"
BRANCO = "branco"

DIR = "dir"
ESQ = "esq"
QUALQUER = "qualquer"

HORARIO = 1
ANTI_HORARIO = -1


class SaidaAbortada(Exception):
    """Levantada quando o botão central é apertado durante uma saída."""
    pass


# --- Hardware ------------------------------------------------------------------
hub = PrimeHub()
# O botão central fica livre para o menu e para abortar. Quem ENCERRA o
# programa é o botão Bluetooth.
hub.system.set_stop_button(Button.BLUETOOTH)

# O giroscópio calibra sozinho no boot, mas SÓ se o robô estiver imóvel. Até
# ficar pronto, nada anda (luz amarela).
hub.light.on(Color.YELLOW)
while not hub.imu.ready():
    wait(50)


def _letra(porta):
    return str(porta)[-1]


def _abrir(classe, porta, *args):
    # Falha de porta vira um aviso legível no hub (letra da porta piscando em
    # vermelho), em vez de um OSError que só aparece no PC.
    try:
        return classe(porta, *args)
    except OSError:
        hub.light.on(Color.RED)
        print("ERRO: nada conectado (ou dispositivo errado) na porta %s" % _letra(porta))
        while True:
            hub.display.char(_letra(porta))
            hub.speaker.beep(200, 150)
            wait(600)
            hub.display.off()
            wait(300)


_roda_dir = _abrir(Motor, config.PORTA_RODA_DIR, config.SENTIDO_RODA_DIR)
_roda_esq = _abrir(Motor, config.PORTA_RODA_ESQ, config.SENTIDO_RODA_ESQ)
_anexo1 = _abrir(Motor, config.PORTA_ANEXO1, config.SENTIDO_ANEXO1)
_anexo2 = _abrir(Motor, config.PORTA_ANEXO2, config.SENTIDO_ANEXO2)
_cor_dir = _abrir(ColorSensor, config.PORTA_COR_DIR)
_cor_esq = _abrir(ColorSensor, config.PORTA_COR_ESQ)

# Zera os encoders ANTES de criar o DriveBase (lição medida no Baymax: o
# DriveBase captura o ângulo inicial dos motores ao nascer).
_roda_dir.reset_angle(0)
_roda_esq.reset_angle(0)

cal, cal_gravada = calibracao.carregar(hub)

db = DriveBase(_roda_esq, _roda_dir, cal["roda"], cal["bitola"])
db.use_gyro(True)

# --- Estado ------------------------------------------------------------------------
_rumo_alvo = 0.0
_x = 0.0
_y = 0.0
_dist_ant = 0.0
_cron_partida = None
_vel_aplicada = None


# --- Utilidades internas ---------------------------------------------------------
def _clamp(v, a, b):
    return max(a, min(b, v))


def _aplicar_vel(vel):
    global _vel_aplicada
    vel = abs(vel)
    if vel != _vel_aplicada:
        db.settings(vel, config.ACEL_RETA, config.VEL_GIRO, config.ACEL_GIRO)
        _vel_aplicada = vel


def _teto(ms_teorico):
    return int(config.TETO_FATOR * ms_teorico) + config.TETO_MIN_MS


def _atualizar_pose():
    # Odometria: integra cada pedacinho de distância na direção do giroscópio.
    global _x, _y, _dist_ant
    d = db.distance()
    dd = d - _dist_ant
    _dist_ant = d
    if dd:
        h = db.angle() * pi / 180.0
        _x += dd * cos(h) / 10.0
        _y -= dd * sin(h) / 10.0      # rumo horário-positivo => y para a esquerda


def _checar():
    # Chamado em TODO laço de controle: abortar e manter a pose em dia.
    _atualizar_pose()
    if Button.CENTER in hub.buttons.pressed():
        parar_tudo()
        raise SaidaAbortada()


def _erro_rumo(normalizar=True):
    # Erro até o rumo_alvo. Normalizado = caminho curto, em (-180, 180]. Sem
    # normalizar, um giro relativo de qualquer tamanho (ex.: 360) é representável.
    erro = _rumo_alvo - db.angle()
    if not normalizar:
        return erro
    while erro > 180.0:
        erro -= 360.0
    while erro <= -180.0:
        erro += 360.0
    return erro


def _taxa_correcao(erro):
    # Guinada proporcional ao erro de rumo, saturada.
    taxa = config.CREEP_GANHO * erro
    return _clamp(taxa, -config.CREEP_TAXA_MAX, config.CREEP_TAXA_MAX)


def _esperar_db(teto_ms):
    # Espera o DriveBase concluir a manobra. Sai por: concluída (True), travada
    # por STALL_ABORTA_MS ou teto de tempo (False).
    cron = StopWatch()
    stall_desde = None
    while not db.done():
        _checar()
        t = cron.time()
        if t > teto_ms:
            db.stop()
            print("AVISO: movimento estourou o teto de %d ms" % teto_ms)
            return False
        if db.stalled():
            if stall_desde is None:
                stall_desde = t
            elif t - stall_desde > config.STALL_ABORTA_MS:
                db.stop()
                print("AVISO: robo TRAVADO, movimento abortado")
                return False
        else:
            stall_desde = None
        wait(config.PERIODO_MS)
    _atualizar_pose()
    return True


def _creep(normalizar=True, tol_entra=None, tol_sai=None):
    # Fase FINA do giro (método do Baymax): fecha o rumo por VELOCIDADE
    # (db.drive), não por posição (db.turn), porque db.turn de 1-2 graus cai na
    # zona morta do controlador. Para quando chega ou quando PASSA do alvo
    # (nunca fica oscilando de um lado para o outro).
    if tol_entra is None:
        tol_entra = config.GIRO_TOL_ENTRA
    if tol_sai is None:
        tol_sai = config.GIRO_TOL_SAI
    erro = _erro_rumo(normalizar)
    if abs(erro) <= tol_entra:
        return True
    sentido = 1.0 if erro > 0 else -1.0
    cron = StopWatch()
    teto = _teto(abs(erro) / config.CREEP_TAXA_MIN * 1000)
    stall_desde = None
    ok = True
    while True:
        _checar()
        erro = _erro_rumo(normalizar)
        restante = erro * sentido
        if restante <= tol_sai:          # chegou ou passou
            break
        t = cron.time()
        if t > teto:
            print("AVISO: ajuste de rumo no teto; erro=%.1f" % erro)
            ok = False
            break
        if db.stalled():
            if stall_desde is None:
                stall_desde = t
            elif t - stall_desde > config.STALL_ABORTA_MS:
                print("AVISO: travado no ajuste de rumo; erro=%.1f" % erro)
                ok = False
                break
        else:
            stall_desde = None
        taxa = config.CREEP_GANHO * erro
        if abs(taxa) < config.CREEP_TAXA_MIN:
            taxa = config.CREEP_TAXA_MIN * sentido
        taxa = _clamp(taxa, -config.CREEP_TAXA_MAX, config.CREEP_TAXA_MAX)
        db.drive(0, taxa)
        wait(config.PERIODO_MS)
    db.stop()
    return ok


def _ir_ate_rumo(normalizar=True):
    erro = _erro_rumo(normalizar)
    ok = True
    if abs(erro) > config.GIRO_GROSSO_MIN:
        _aplicar_vel(NORMAL)
        db.turn(erro, wait=False)      # erro > 0: horário
        ok = _esperar_db(_teto(abs(erro) / config.VEL_GIRO * 1000))
    return _creep(normalizar) and ok


def _sensor(qual):
    if qual == DIR:
        return _cor_dir
    if qual == ESQ:
        return _cor_esq
    raise ValueError("sensor deve ser DIR ou ESQ, veio %s" % qual)


def _normalizar_reflexao(qual, bruto):
    preto = cal["preto_" + qual]
    branco = cal["branco_" + qual]
    return _clamp((bruto - preto) * 100.0 / (branco - preto), 0.0, 100.0)


def _vendo(qual, cor_alvo):
    r = reflexao(qual)
    if cor_alvo == PRETO:
        return r <= config.LIMIAR_PRETO
    if cor_alvo == BRANCO:
        return r >= config.LIMIAR_BRANCO
    raise ValueError("cor deve ser PRETO ou BRANCO, veio %s" % cor_alvo)


def _graus_motor(vel_mm):
    # mm/s de roda -> graus/s de motor (transmissão direta).
    return vel_mm * 360.0 / (pi * cal["roda"])


# ===================================================================================
# MOVIMENTO
# ===================================================================================
def andar(cm, vel=NORMAL, parar=True):
    """Anda `cm` centímetros mantendo o rumo atual (negativo = de ré).

    parar=False emenda no próximo movimento sem frear (mais rápido, menos preciso).
    """
    _creep()                                     # sai alinhado ao rumo
    _aplicar_vel(vel)
    db.straight(cm * 10, then=Stop.HOLD if parar else Stop.NONE, wait=False)
    ok = _esperar_db(_teto(abs(cm) * 10.0 / abs(vel) * 1000))
    if parar:
        ok = _creep() and ok
        db.stop()
    return ok


def girar(graus):
    """Gira no lugar `graus` (positivo = horário/direita) a partir do rumo desejado."""
    global _rumo_alvo
    _rumo_alvo = _rumo_alvo + graus
    ok = _ir_ate_rumo(normalizar=False)
    db.stop()
    return ok


def virar_para(rumo):
    """Gira até o rumo ABSOLUTO `rumo` pelo caminho mais curto."""
    global _rumo_alvo
    _rumo_alvo = float(rumo)
    ok = _ir_ate_rumo(normalizar=True)
    db.stop()
    return ok


def curva(raio_cm, graus, vel=NORMAL):
    """Anda em arco de raio `raio_cm`, mudando o rumo em `graus` (+ = direita)."""
    global _rumo_alvo
    _creep()
    _aplicar_vel(vel)
    db.curve(raio_cm * 10, graus, wait=False)
    comprimento = abs(raio_cm * 10 * graus * pi / 180.0)
    ok = _esperar_db(_teto(comprimento / abs(vel) * 1000 + abs(graus) / config.VEL_GIRO * 1000))
    _rumo_alvo = _rumo_alvo + graus
    ok = _creep() and ok
    db.stop()
    return ok


def ir_para(x, y, vel=NORMAL, de_re=False):
    """Vira para o ponto (x, y) em cm e anda até ele (pela odometria)."""
    dx = x - _x
    dy = y - _y
    dist = sqrt(dx * dx + dy * dy)
    if dist < 0.5:
        return True
    rumo = -atan2(dy, dx) * 180.0 / pi
    if de_re:
        rumo += 180.0
        dist = -dist
    ok = virar_para(rumo)
    return andar(dist, vel) and ok


def voltar_base(vel=RAPIDO, de_re=False):
    """Volta ao ponto de partida da saída (x=0, y=0)."""
    return ir_para(0, 0, vel, de_re)


def parar_tudo():
    """Para tração e anexos (não levanta exceção)."""
    db.stop()
    _anexo1.stop()
    _anexo2.stop()


# ===================================================================================
# LINHAS
# ===================================================================================
def reflexao(sensor):
    """Refletância NORMALIZADA pela calibração: 0 = preto, 100 = branco."""
    s = _sensor(sensor)
    return _normalizar_reflexao(sensor, s.reflection())


def reflexao_crua(sensor):
    """Refletância bruta do sensor (0-100), sem calibração."""
    return _sensor(sensor).reflection()


def cor(sensor):
    """Cor detectada (Color.BLACK, Color.WHITE, Color.GREEN, ... ou Color.NONE)."""
    return _sensor(sensor).color()


def ate_linha(cor_alvo=PRETO, sensor=QUALQUER, vel=LENTO, max_cm=50):
    """Anda reto (vel negativa = de ré) até um sensor ver `cor_alvo`.

    sensor: DIR, ESQ ou QUALQUER. Devolve True se achou, False se andou
    `max_cm` sem achar.
    """
    _creep()
    d0 = db.distance()
    achou = False
    cron = StopWatch()
    teto = _teto(max_cm * 10.0 / abs(vel) * 1000)
    while True:
        _checar()
        if sensor == QUALQUER:
            achou = _vendo(DIR, cor_alvo) or _vendo(ESQ, cor_alvo)
        else:
            achou = _vendo(sensor, cor_alvo)
        if achou:
            break
        if abs(db.distance() - d0) >= max_cm * 10 or cron.time() > teto:
            break
        db.drive(vel, _taxa_correcao(_erro_rumo()))
        wait(config.PERIODO_MS)
    db.brake()
    _atualizar_pose()
    if not achou:
        print("AVISO: ate_linha nao achou %s em %d cm" % (cor_alvo, max_cm))
    return achou


def _quadrar(vel_mm, cor_alvo, max_cm):
    # Cada roda anda até o SEU sensor ver a cor alvo e então segura. Termina
    # quando as duas seguraram.
    v = _graus_motor(vel_mm)
    d0 = db.distance()
    feito_dir = False
    feito_esq = False
    while not (feito_dir and feito_esq):
        _checar()
        if abs(db.distance() - d0) >= max_cm * 10:
            _roda_dir.hold()
            _roda_esq.hold()
            return False
        if not feito_dir:
            if _vendo(DIR, cor_alvo):
                _roda_dir.hold()
                feito_dir = True
            else:
                _roda_dir.run(v)
        if not feito_esq:
            if _vendo(ESQ, cor_alvo):
                _roda_esq.hold()
                feito_esq = True
            else:
                _roda_esq.run(v)
        wait(config.PERIODO_MS)
    return True


def alinhar_na_linha(vel=LENTO, max_cm=30, rumo=None, fino=True):
    """Para com os DOIS sensores sobre a borda de uma linha preta à frente.

    Deixa o robô perpendicular à linha: é o jeito de corrigir o rumo numa mesa
    sem bordas. Se você sabe o rumo da linha no tapete, passe `rumo=...`: o
    giroscópio é reescrito com esse valor e o erro acumulado some.
    fino=True faz uma segunda passada lenta (recua 1,5 cm e volta ao preto).
    """
    global _rumo_alvo
    db.stop()
    ok = _quadrar(vel, PRETO, max_cm)
    if ok and fino:
        # Recuo FIXO, não "até o branco": atrás da faixa preta pode haver fundo
        # cinza/bege que nunca passa do LIMIAR_BRANCO.
        _aplicar_vel(LENTO)
        db.straight(-15, wait=False)
        _esperar_db(_teto(15.0 / LENTO * 1000))
        ok = _quadrar(abs(vel) / 3.0, PRETO, 4)
    _roda_dir.hold()
    _roda_esq.hold()
    _atualizar_pose()
    if not ok:
        print("AVISO: alinhar_na_linha nao achou a linha em %d cm" % max_cm)
        return False
    if rumo is not None:
        # db.reset e não hub.imu.reset_heading: com use_gyro, o reset do heading
        # levanta OSError desde o Pybricks 3.6 (lição do Baymax).
        db.reset(distance=db.distance(), angle=rumo)
        _rumo_alvo = float(rumo)
    else:
        _rumo_alvo = db.angle()
    db.stop()
    return True


def _seguir(sensor, borda, vel, kp, kd, max_cm, parar_quando):
    global _rumo_alvo
    if kp is None:
        kp = config.SEGUIR_KP
    if kd is None:
        kd = config.SEGUIR_KD
    sinal = 1.0 if borda == ESQ else -1.0
    d0 = db.distance()
    erro_ant = reflexao(sensor) - 50.0
    cron = StopWatch()
    teto = _teto(max_cm * 10.0 / abs(vel) * 1000)
    chegou = False
    while True:
        _checar()
        if parar_quando is not None and parar_quando():
            chegou = True
            break
        if abs(db.distance() - d0) >= max_cm * 10:
            chegou = parar_quando is None
            break
        if cron.time() > teto:
            print("AVISO: seguir_linha estourou o tempo")
            break
        erro = reflexao(sensor) - 50.0
        guinada = sinal * (kp * erro + kd * (erro - erro_ant))
        erro_ant = erro
        db.drive(vel, guinada)
        wait(config.PERIODO_MS)
    db.brake()
    _atualizar_pose()
    # Depois de seguir a linha, o rumo desejado passa a ser o da linha.
    _rumo_alvo = db.angle()
    return chegou


def seguir_linha(cm, sensor=DIR, borda=ESQ, vel=config.SEGUIR_VEL, kp=None, kd=None):
    """Segue a BORDA de uma linha por `cm` centímetros.

    sensor: qual sensor segue (DIR ou ESQ). borda: ESQ = borda esquerda da
    linha preta (preto à direita do sensor), DIR = borda direita. As linhas do
    tapete TBR são faixas preta+branca: siga a borda entre as duas.
    """
    return _seguir(sensor, borda, vel, kp, kd, cm, None)


def seguir_linha_ate_cruzamento(sensor=DIR, borda=ESQ, vel=config.SEGUIR_VEL,
                                max_cm=150, kp=None, kd=None):
    """Segue a linha com `sensor` até o OUTRO sensor ver preto (cruzamento ou
    barra preta no fim da linha). Devolve False se andou `max_cm` sem achar."""
    outro = ESQ if sensor == DIR else DIR
    return _seguir(sensor, borda, vel, kp, kd, max_cm,
                   lambda: _vendo(outro, PRETO))


# ===================================================================================
# POSIÇÃO E RUMO
# ===================================================================================
def zerar_rumo():
    """O rumo atual vira 0 e a posição volta a (0, 0). O menu chama no início
    de cada saída."""
    global _rumo_alvo, _x, _y, _dist_ant
    db.stop()
    db.reset(distance=0, angle=0)
    _rumo_alvo = 0.0
    _x = 0.0
    _y = 0.0
    _dist_ant = 0.0


def zerar_posicao():
    """Só a posição volta a (0, 0); o rumo continua."""
    definir_posicao(0, 0)


def definir_posicao(x, y):
    """Corrige a posição estimada (ex.: depois de alinhar numa linha conhecida)."""
    global _x, _y, _dist_ant
    _atualizar_pose()
    _x = float(x)
    _y = float(y)
    _dist_ant = db.distance()


def posicao():
    """(x, y, rumo) estimados: cm, cm, graus."""
    _atualizar_pose()
    return _x, _y, db.angle()


def rumo():
    """Rumo atual medido pelo giroscópio (graus)."""
    return db.angle()


# ===================================================================================
# ANEXOS (motor 1 = porta F, motor 2 = porta B)
# ===================================================================================
def _esperar_motor(m, teto_ms):
    cron = StopWatch()
    stall_desde = None
    while not m.done():
        _checar()
        t = cron.time()
        if t > teto_ms:
            m.stop()
            print("AVISO: anexo estourou o teto de %d ms" % teto_ms)
            return False
        if m.stalled():
            if stall_desde is None:
                stall_desde = t
            elif t - stall_desde > config.STALL_ABORTA_MS:
                m.hold()
                print("AVISO: anexo travado, movimento encerrado")
                return False
        else:
            stall_desde = None
        wait(config.PERIODO_MS)
    return True


def _girar_anexo(m, graus, vel, esperar):
    m.run_angle(vel, graus, then=Stop.HOLD, wait=False)
    if esperar:
        return _esperar_motor(m, _teto(abs(graus) / abs(vel) * 1000))
    return True


def _anexo_para(m, angulo, vel, esperar):
    m.run_target(vel, angulo, then=Stop.HOLD, wait=False)
    if esperar:
        return _esperar_motor(m, _teto(abs(angulo - m.angle()) / abs(vel) * 1000))
    return True


def _anexo_travar(m, sentido, forca, teto_ms):
    # Empurra com `forca` % de duty até o motor parar (fim de curso / objeto
    # preso) e então segura. Mesma ideia das mãos do Baymax, mas com laço próprio:
    # run_until_stalled não tem teto e prende o programa se nunca travar.
    m.dc(sentido * _clamp(forca, 10, 100))
    cron = StopWatch()
    parado_desde = None
    wait(150)                                   # deixa o motor arrancar
    while cron.time() < teto_ms:
        _checar()
        if abs(m.speed()) < 30:
            if parado_desde is None:
                parado_desde = cron.time()
            elif cron.time() - parado_desde > 100:
                m.hold()
                return True
        else:
            parado_desde = None
        wait(config.PERIODO_MS)
    m.hold()
    print("AVISO: anexo nao travou em %d ms" % teto_ms)
    return False


def anexo1(graus, vel=config.VEL_ANEXO, esperar=True):
    """Gira o motor do anexo 1 (porta F) `graus` relativos.
    esperar=False: devolve na hora e o motor gira enquanto o robô anda."""
    return _girar_anexo(_anexo1, graus, vel, esperar)


def anexo2(graus, vel=config.VEL_ANEXO, esperar=True):
    """Gira o motor do anexo 2 (porta B) `graus` relativos."""
    return _girar_anexo(_anexo2, graus, vel, esperar)


def anexo1_ir_para(angulo, vel=config.VEL_ANEXO, esperar=True):
    """Leva o anexo 1 ao ângulo ABSOLUTO `angulo` (0 = onde foi zerado)."""
    return _anexo_para(_anexo1, angulo, vel, esperar)


def anexo2_ir_para(angulo, vel=config.VEL_ANEXO, esperar=True):
    """Leva o anexo 2 ao ângulo ABSOLUTO `angulo`."""
    return _anexo_para(_anexo2, angulo, vel, esperar)


def anexo1_ate_travar(sentido=HORARIO, forca=50, teto_ms=3000):
    """Gira o anexo 1 até travar (garra fechando, braço no fim de curso)."""
    return _anexo_travar(_anexo1, sentido, forca, teto_ms)


def anexo2_ate_travar(sentido=HORARIO, forca=50, teto_ms=3000):
    """Gira o anexo 2 até travar."""
    return _anexo_travar(_anexo2, sentido, forca, teto_ms)


def zerar_anexos():
    """A posição atual dos dois anexos vira o ângulo 0."""
    _anexo1.reset_angle(0)
    _anexo2.reset_angle(0)


def esperar_anexos(teto_ms=5000):
    """Espera os anexos lançados com esperar=False terminarem."""
    ok1 = _esperar_motor(_anexo1, teto_ms)
    ok2 = _esperar_motor(_anexo2, teto_ms)
    return ok1 and ok2


def angulo_anexo1():
    return _anexo1.angle()


def angulo_anexo2():
    return _anexo2.angle()


# ===================================================================================
# HUB
# ===================================================================================
def bipe(freq=600, ms=100):
    hub.speaker.beep(freq, ms)


def mostrar(valor):
    """Número de -99 a 99 ou um caractere na matriz; texto maior rola."""
    if isinstance(valor, int) and -99 <= valor <= 99:
        hub.display.number(valor)
    elif isinstance(valor, str) and len(valor) == 1:
        hub.display.char(valor)
    else:
        hub.display.text(str(valor), 300, 50)


def luz(c):
    """Cor do botão central: luz(Color.GREEN), luz(Color.RED)..."""
    hub.light.on(c)


def esperar(ms):
    """Pausa que continua respondendo ao botão de abortar."""
    cron = StopWatch()
    while cron.time() < ms:
        _checar()
        wait(config.PERIODO_MS)


def esperar_botao():
    """Espera apertar e soltar a seta ESQUERDA ou DIREITA (o central aborta)."""
    while not (Button.LEFT in hub.buttons.pressed() or
               Button.RIGHT in hub.buttons.pressed()):
        _checar()
        wait(config.PERIODO_MS)
    while hub.buttons.pressed():
        wait(config.PERIODO_MS)


def iniciar_partida():
    """Começa o cronômetro de 120 s (o menu chama na primeira saída)."""
    global _cron_partida
    _cron_partida = StopWatch()


def tempo_partida():
    """Segundos desde o início da partida (0 se ainda não começou)."""
    if _cron_partida is None:
        return 0.0
    return _cron_partida.time() / 1000.0


def tempo_restante():
    """Segundos que faltam para os 120 s."""
    return config.PARTIDA_S - tempo_partida()
