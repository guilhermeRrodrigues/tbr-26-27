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
VERDE = "verde"
BORDA = "borda"         # saiu do branco (moldura da base): alinhar_na_base

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

if config.TOLERANCIAS_DB:
    # O "concluído" padrão do pbio aceita ~18 graus e ~13 mm (docs/giroscopio.md).
    try:
        db.heading_control.target_tolerances(speed=config.TOL_DB_RUMO_VEL,
                                             position=config.TOL_DB_RUMO)
        db.distance_control.target_tolerances(speed=config.TOL_DB_DIST_VEL,
                                              position=config.TOL_DB_DIST)
    except Exception as e:
        print("AVISO: target_tolerances recusado (%s); done() com o padrao" % e)

# --- Estado ------------------------------------------------------------------------
_rumo_alvo = 0.0
_x = 0.0
_y = 0.0
_dist_ant = 0.0
_cron_partida = None
_vel_aplicada = None
_tarefa = [None, None]      # tarefa de cada anexo (ver _vigiar_anexos)
_resultado = [True, True]   # como terminou o último movimento de cada anexo
_freio_ms = float(config.FINO_FREIO_MS)     # aprendido no ajuste fino do giro
_freio_reta_ms = float(config.RETA_FREIO_MS)    # aprendido no fim das retas
# Rumo da MESA = db.angle() + _nominal: _nominal é a direção da mesa para onde
# apontava o rumo 0 desta saída. _mesa_cron mede a idade da referência.
_nominal = 0.0
_mesa_cron = None
_mesa_var = 0.0             # variância (graus^2) do rumo da mesa na referência


# --- Utilidades internas ---------------------------------------------------------
def _clamp(v, a, b):
    return max(a, min(b, v))


def _traduzir_vel(vel, lento, normal, rapido):
    # LENTO/NORMAL/RAPIDO -> o valor do config; qualquer outro número já vale direto.
    if vel == LENTO:
        return lento
    if vel == NORMAL:
        return normal
    if vel == RAPIDO:
        return rapido
    return abs(vel)


def _taxa_giro(vel):
    return _traduzir_vel(vel, config.GIRO_LENTO, config.GIRO_NORMAL, config.GIRO_RAPIDO)


def _aplicar_vel(vel, taxa_giro=config.VEL_GIRO):
    global _vel_aplicada
    chave = (abs(vel), taxa_giro)
    if chave != _vel_aplicada:
        db.settings(abs(vel), config.ACEL_RETA, taxa_giro, config.ACEL_GIRO)
        _vel_aplicada = chave


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


def _manter():
    # Pose em dia e anexos vigiados: o que não pode parar nem numa pausa.
    _atualizar_pose()
    _vigiar_anexos()


def _checar():
    # Chamado em TODO laço de controle: abortar, manter a pose em dia e vigiar
    # os anexos que se mexem em paralelo.
    _manter()
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


def _giro_invertido(erro_inicial, normalizar):
    # Se o erro de rumo CRESCE muito além do inicial, o robô está girando ao
    # contrário do giroscópio (portas/sentidos das rodas trocados). Sem esta
    # vigia ele gira sem parar até travar.
    if abs(_erro_rumo(normalizar)) > abs(erro_inicial) + 30:
        db.stop()
        hub.light.on(Color.RED)
        print("ERRO: o robo girou AO CONTRARIO do giroscopio. Rode a rotina P e")
        print("confira PORTA_RODA_DIR/ESQ e SENTIDO_RODA_* em config.py.")
        return True
    return False


def _sem_progresso(vigia, t):
    # vigia = [t_ref, d_ref]. True se o robô não andou PROGRESSO_MIN_MM em
    # STALL_ABORTA_MS: encostado em algo que cede (blocos, peça), as rodas
    # ainda giram um pouco e o db.stalled() não dispara.
    d = db.distance()
    if abs(d - vigia[1]) >= config.PROGRESSO_MIN_MM:
        vigia[0] = t
        vigia[1] = d
        return False
    return t - vigia[0] > config.STALL_ABORTA_MS


def _esperar_db(teto_ms, vigiar_giro=None, progresso=False):
    # Espera o DriveBase concluir a manobra. Sai por: concluída (True), travada
    # por STALL_ABORTA_MS, sem progresso, teto de tempo ou giro invertido (False).
    # vigiar_giro = (erro_inicial, normalizar) liga a vigia de giro invertido.
    # progresso=True (retas e curvas) liga a vigia de "anda sem sair do lugar".
    cron = StopWatch()
    stall_desde = None
    vigia = [0, db.distance()]
    # Com TOLERANCIAS_DB apertadas, o atrito pode deixar o robô parado a um
    # fio da tolerância: depois do tempo teórico, parado de vez = concluído.
    teorico = (teto_ms - config.TETO_MIN_MS) / config.TETO_FATOR
    parado_desde = None
    while not db.done():
        _checar()
        if vigiar_giro is not None and _giro_invertido(vigiar_giro[0], vigiar_giro[1]):
            return False
        t = cron.time()
        if config.TOLERANCIAS_DB and t > teorico + 300:
            st = db.state()
            if abs(st[1]) < 5 and abs(st[3]) < 2 and not db.stalled():
                if parado_desde is None:
                    parado_desde = t
                elif t - parado_desde > 150:
                    break
            else:
                parado_desde = None
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
        if progresso and _sem_progresso(vigia, t):
            db.stop()
            print("AVISO: robo sem progresso (encostado?), movimento abortado")
            return False
        wait(config.PERIODO_MS)
    _atualizar_pose()
    return True


def _creep(normalizar=True, tol_entra=None, tol_sai=None):
    # Fase FINA do giro (método do Baymax): fecha o rumo por VELOCIDADE
    # (db.drive), não por posição (db.turn), porque db.turn de 1-2 graus cai na
    # zona morta do controlador. Para quando chega ou quando PASSA do alvo
    # (nunca fica oscilando de um lado para o outro).
    if not config.CREEP:
        return True
    if config.GIRO_FINO:
        return _fino(normalizar, tol_entra)
    if tol_entra is None:
        tol_entra = config.GIRO_TOL_ENTRA
    if tol_sai is None:
        tol_sai = config.GIRO_TOL_SAI
    erro = _erro_rumo(normalizar)
    if abs(erro) <= tol_entra:
        return True
    sentido = 1.0 if erro > 0 else -1.0
    erro_inicial = erro
    cron = StopWatch()
    teto = _teto(abs(erro) / config.CREEP_TAXA_MIN * 1000)
    stall_desde = None
    ok = True
    while True:
        _checar()
        if _giro_invertido(erro_inicial, normalizar):
            ok = False
            break
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


def _taxa_medida():
    # Guinada medida pelo giroscópio (graus/s).
    return db.state()[3]


def _esperar_parar(teto_ms=250):
    # Espera a guinada cair abaixo de FINO_PARADO: só então o erro é de verdade.
    cron = StopWatch()
    while cron.time() < teto_ms:
        _checar()
        if abs(_taxa_medida()) < config.FINO_PARADO:
            return
        wait(config.PERIODO_MS)


def _fino(normalizar=True, tol_entra=None):
    # Ajuste FINO do rumo (GIRO_FINO): mede PARADO, gira com um pulso por
    # velocidade e FREIA antes do alvo, prevendo quanto o robô ainda gira
    # depois do freio (_freio_ms, aprendido a cada pulso). Repete nos dois
    # sentidos até GIRO_TOL_FINAL, com FINO_TENTATIVAS e FINO_TETO_MS.
    # O freio também desliga o controle: o próximo db.drive parte do estado
    # MEDIDO, sem o atraso acumulado da referência anterior.
    global _freio_ms
    if tol_entra is None:
        tol_entra = config.GIRO_TOL_ENTRA
    # Ainda girando (veio de um coast/freio), o erro de agora mente: o robô
    # ainda desliza. Só decide "já está no rumo" depois de parar.
    _esperar_parar()
    if abs(_erro_rumo(normalizar)) <= tol_entra:
        return True
    erro_inicial = _erro_rumo(normalizar)
    cron = StopWatch()
    ok = True
    pulsos = 0
    travou = False
    while not travou:
        _esperar_parar()
        erro = _erro_rumo(normalizar)
        if abs(erro) <= config.GIRO_TOL_FINAL:
            break
        if pulsos >= config.FINO_TENTATIVAS or cron.time() > config.FINO_TETO_MS:
            print("AVISO: ajuste fino parou com erro=%.1f" % erro)
            break
        pulsos += 1
        sentido = 1.0 if erro > 0 else -1.0
        stall_desde = None
        t_pulso = cron.time()
        while True:
            _checar()
            if _giro_invertido(erro_inicial, normalizar):
                return False
            restante = _erro_rumo(normalizar) * sentido
            if restante <= abs(_taxa_medida()) * _freio_ms / 1000.0:
                break
            t = cron.time()
            if t > config.FINO_TETO_MS:
                break
            if db.stalled():
                if stall_desde is None:
                    stall_desde = t
                elif t - stall_desde > config.STALL_ABORTA_MS:
                    print("AVISO: travado no ajuste de rumo; erro=%.1f" % _erro_rumo(normalizar))
                    ok = False
                    travou = True
                    break
            else:
                stall_desde = None
            taxa = _clamp(config.CREEP_GANHO * restante,
                          config.CREEP_TAXA_MIN, config.CREEP_TAXA_MAX)
            db.drive(0, sentido * taxa)
            wait(config.PERIODO_MS)
        w0 = abs(_taxa_medida())
        a0 = db.angle()
        db.brake()
        _esperar_parar()
        if w0 > 5 and not travou:
            # quanto girou depois do freio, em "ms de guinada": aprende devagar
            est = abs(db.angle() - a0) / w0 * 1000.0
            _freio_ms = _clamp(0.7 * _freio_ms + 0.3 * est, 5.0, 150.0)
        if config.DIAG_GIRO:
            # Separa atrito (pulso longo, chega perto) de encostado em algo
            # (pulso longo, erro não muda) e de passada (erro troca de sinal).
            print("DIAG fino pulso %d: erro %.2f -> %.2f em %d ms, guinada no freio %d"
                  % (pulsos, erro, _erro_rumo(normalizar), cron.time() - t_pulso, w0))
    db.stop()
    _atualizar_pose()
    return ok


def _giro_por_velocidade(normalizar, taxa):
    # Giro GROSSO fechado no giroscópio por velocidade (db.drive), como o
    # andar_no_rumo faz na reta. O db.turn dava a manobra por concluída com
    # ~15 graus ainda faltando, depois de ~1,4 s num giro de 40.
    # Rampa de frenagem w = sqrt(a.erro), com metade da ACEL_GIRO de folga
    # para o atraso do giroscópio. Sai girando devagar a GIRO_GROSSO_SAI do
    # alvo, e o creep fecha o resto.
    erro0 = _erro_rumo(normalizar)
    sentido = 1.0 if erro0 > 0 else -1.0
    cron = StopWatch()
    teto = _teto(abs(erro0) / taxa * 1000)
    h_ref = db.angle()
    t_ref = 0
    while True:
        _checar()
        if _giro_invertido(erro0, normalizar):
            return False
        restante = _erro_rumo(normalizar) * sentido
        sai = config.GIRO_GROSSO_SAI
        if config.GIRO_FINO:
            # freia antes: o robô ainda gira ~guinada x tempo de freio
            sai = config.FINO_GROSSO_SAI + abs(_taxa_medida()) * _freio_ms / 1000.0
        if restante <= sai:
            break
        t = cron.time()
        if t > teto:
            db.stop()
            print("AVISO: giro estourou o teto de %d ms" % teto)
            return False
        h = db.angle()
        if abs(h - h_ref) >= 1:
            h_ref = h
            t_ref = t
        elif t - t_ref > config.STALL_ABORTA_MS:
            db.stop()
            print("AVISO: robo TRAVADO no giro, abortado")
            return False
        w = min(taxa, max(config.CREEP_TAXA_MIN, sqrt(config.ACEL_GIRO * restante)))
        db.drive(0, sentido * w)
        wait(config.PERIODO_MS)
    if config.GIRO_FINO:
        db.brake()          # desliga o controle: o fino parte do estado medido
    else:
        db.drive(0, 0)
    _atualizar_pose()
    return True


def _desembrulhar_alvo():
    # Escolhe o caminho UMA vez: o rumo desejado vira o equivalente contínuo
    # mais perto do rumo atual. Sem isto, num alvo a ~180 graus o ruído levava
    # o erro normalizado de +180 a -179,99 no meio do giro, e ele parava
    # achando que já tinha passado (virar_para(180) a partir de 0 não girava).
    global _rumo_alvo
    _rumo_alvo = db.angle() + _erro_rumo(True)


def _ir_ate_rumo(normalizar=True, vel=NORMAL):
    if config.CORRECOES_RUMO and normalizar:
        _desembrulhar_alvo()
        normalizar = False
    if config.GIRO_FINO and config.CREEP:
        return _ir_ate_rumo_fino(normalizar, vel)
    erro = _erro_rumo(normalizar)
    ok = True
    cron = StopWatch()
    t_grosso = 0
    sobra = erro
    # Sem creep, o grosso faz o giro inteiro: abaixo de GIRO_GROSSO_MIN era o
    # creep que girava, e o robô simplesmente não viraria.
    if abs(erro) > config.GIRO_GROSSO_MIN or not config.CREEP:
        taxa = _taxa_giro(vel)
        _aplicar_vel(NORMAL, taxa)
        if config.GIRO_POR_VELOCIDADE:
            ok = _giro_por_velocidade(normalizar, taxa)
        else:
            db.turn(erro, wait=False)      # erro > 0: horário
            ok = _esperar_db(_teto(abs(erro) / taxa * 1000), (erro, normalizar))
        t_grosso = cron.time()
        sobra = _erro_rumo(normalizar)
        if not ok:
            return False               # não insiste com o creep num giro que falhou
        # O grosso entrega a GIRO_GROSSO_SAI (2°) do alvo, que não passa do
        # GIRO_TOL_ENTRA (2°): o creep normal achava "já está bom" e todo giro
        # terminava ~1,8° curto. Depois do grosso o creep sempre fecha.
        ok = _creep(normalizar, tol_entra=config.GIRO_TOL_SAI) and ok
    else:
        ok = _creep(normalizar) and ok
    if config.DIAG_GIRO:
        # Para achar onde o giro gasta tempo: no giro grosso (db.turn até o
        # db.done) ou no creep que fecha o resto.
        print("DIAG giro %.1f: grosso %d ms (sobrou %.1f) + creep %d ms (final %.1f)"
              % (erro, t_grosso, sobra, cron.time() - t_grosso, _erro_rumo(normalizar)))
    return ok


def _ir_ate_rumo_fino(normalizar, vel):
    # GIRO_FINO: grosso por velocidade (ou db.turn) terminando com freio, e o
    # ajuste fino parado até GIRO_TOL_FINAL, inclusive em giros pequenos.
    erro = _erro_rumo(normalizar)
    ok = True
    cron = StopWatch()
    t_grosso = 0
    sobra = erro
    if abs(erro) > config.GIRO_GROSSO_MIN:
        taxa = _taxa_giro(vel)
        _aplicar_vel(NORMAL, taxa)
        if config.GIRO_POR_VELOCIDADE:
            ok = _giro_por_velocidade(normalizar, taxa)
        else:
            db.turn(erro, wait=False)
            ok = _esperar_db(_teto(abs(erro) / taxa * 1000), (erro, normalizar))
            db.brake()
        t_grosso = cron.time()
        sobra = _erro_rumo(normalizar)
        if not ok:
            return False
    ok = _fino(normalizar, tol_entra=config.GIRO_TOL_FINAL) and ok
    if config.DIAG_GIRO:
        print("DIAG giro %.1f: grosso %d ms (sobrou %.1f) + fino %d ms (final %.2f, freio %d ms)"
              % (erro, t_grosso, sobra, cron.time() - t_grosso, _erro_rumo(normalizar),
                 _freio_ms))
    return ok


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
    if cor_alvo == VERDE:
        # Cor pela leitura HSV do sensor, não pela reflexão calibrada.
        return _sensor(qual).color() == Color.GREEN
    r = reflexao(qual)
    if cor_alvo == BORDA:
        return r <= config.LIMIAR_BORDA
    if cor_alvo == PRETO:
        return r <= config.LIMIAR_PRETO
    if cor_alvo == BRANCO:
        return r >= config.LIMIAR_BRANCO
    raise ValueError("cor deve ser PRETO, BRANCO ou VERDE, veio %s" % cor_alvo)


def _graus_motor(vel_mm):
    # mm/s de roda -> graus/s de motor (transmissão direta).
    return vel_mm * 360.0 / (pi * cal["roda"])


# --- Cronômetro por comando (config.CRONOMETRO) ----------------------------------
# Cada comando da linguagem imprime quanto levou DE VERDADE no robô, para achar
# onde o tempo de uma saída vai. Só o comando de fora imprime: ir_para() que
# chama virar_para() e andar() aparece como uma linha só.
_cron_nivel = 0


def _andando():
    # O robô ainda anda: veio emendado de um movimento com parar=False.
    return abs(db.state()[1]) >= 5


def _emendado():
    # Emenda sem frear: o movimento novo segue direto, sem ajustar o rumo.
    return config.EMENDA_SEM_AJUSTE and _andando()


def _fmt(v):
    if isinstance(v, float):
        return "%g" % v
    return str(v)


def _cronometrado(nome):
    def envolver(f):
        if not config.CRONOMETRO:
            return f

        def w(*args, **kw):
            global _cron_nivel
            _cron_nivel += 1
            cron = StopWatch()
            try:
                return f(*args, **kw)
            finally:
                _cron_nivel -= 1
                if _cron_nivel == 0:
                    partes = [_fmt(a) for a in args]
                    for k in kw:
                        partes.append("%s=%s" % (k, _fmt(kw[k])))
                    linha = "T %6d ms  %s(%s)" % (cron.time(), nome, ", ".join(partes))
                    if config.DIAG_POSE:
                        linha += "  x=%.1f y=%.1f rumo=%.1f erro=%.1f" % (posicao() + (_erro_rumo(),))
                    print(linha)
        return w
    return envolver


# ===================================================================================
# MOVIMENTO
# ===================================================================================
@_cronometrado("andar")
def andar(cm, vel=NORMAL, parar=True):
    """Anda `cm` centímetros mantendo o rumo atual (negativo = de ré).

    parar=False emenda no próximo movimento sem frear (mais rápido, menos preciso).
    O próximo comando TEM de ser um movimento (andar, curva...): sem ele o robô
    continua andando.
    """
    if config.ANDAR_NO_RUMO:
        return andar_no_rumo(cm, _rumo_alvo, vel, parar)
    _creep()                                     # sai alinhado ao rumo
    _aplicar_vel(vel)
    db.straight(cm * 10, then=Stop.HOLD if parar else Stop.NONE, wait=False)
    ok = _esperar_db(_teto(abs(cm) * 10.0 / abs(vel) * 1000), progresso=True)
    if parar:
        ok = _creep() and ok
        db.stop()
    return ok


@_cronometrado("andar_no_rumo")
def andar_no_rumo(cm, rumo, vel=NORMAL, parar=True):
    """Anda `cm` centímetros no rumo ABSOLUTO `rumo`, corrigindo a direção o
    tempo todo (negativo = de ré, com a frente apontando para `rumo`).

    Diferença para andar(): andar() segura o rumo em que o robô já está; aqui o
    alvo é o rumo pedido, e se o robô sair dele no caminho (escorregou, bateu,
    foi empurrado pelo anexo), ele guina de volta enquanto anda.
    Começando mais torto que config.RUMO_VIRAR_ANTES, vira no lugar antes.
    parar=False emenda no próximo movimento sem frear; o próximo comando TEM de
    ser um movimento, ou o robô continua andando.
    """
    global _rumo_alvo
    _rumo_alvo = float(rumo)
    # Emendada num movimento (parar=False), não gira no lugar: corrige andando.
    if abs(_erro_rumo()) > config.RUMO_VIRAR_ANTES and not _emendado():
        if not _ir_ate_rumo(normalizar=True):
            db.stop()
            return False
    alvo_mm = abs(cm) * 10.0
    sentido = 1.0 if cm >= 0 else -1.0
    v_max = abs(vel)
    _aplicar_vel(vel)                            # aceleração do db.drive
    d0 = db.distance()
    cron = StopWatch()
    teto = _teto(alvo_mm / v_max * 1000)
    stall_desde = None
    vigia = [0, d0]
    ok = True
    prever = parar and config.RETA_PREVE_FREIO
    while True:
        _checar()
        restante = alvo_mm - abs(db.distance() - d0)
        # Com RETA_PREVE_FREIO, freia quando o que falta é o que o robô ainda
        # anda depois do freio (velocidade x _freio_reta_ms, aprendido).
        if restante <= (abs(db.state()[1]) * _freio_reta_ms / 1000.0 if prever else 0):
            break
        t = cron.time()
        if t > teto:
            print("AVISO: andar_no_rumo estourou o teto de %d ms" % teto)
            ok = False
            break
        if db.stalled():
            if stall_desde is None:
                stall_desde = t
            elif t - stall_desde > config.STALL_ABORTA_MS:
                print("AVISO: robo TRAVADO, andar_no_rumo abortado")
                ok = False
                break
        else:
            stall_desde = None
        if _sem_progresso(vigia, t):
            print("AVISO: robo sem progresso (encostado?), andar_no_rumo abortado")
            ok = False
            break
        v = v_max
        if parar:
            # Rampa de frenagem (v^2 = 2.a.d) para não passar do ponto.
            v = min(v_max, max(config.RUMO_VEL_FINAL,
                               sqrt(2.0 * config.ACEL_RETA * restante)))
        # A guinada corrige o RUMO, então o sinal não muda andando de ré.
        guinada = _taxa_correcao(_erro_rumo())
        if config.RETA_LIMITE_RODA:
            # Folga para corrigir: com a roda de fora no limite do motor, a
            # correção do giroscópio some e a reta entorta (pbio #1032).
            v = min(v, config.RETA_LIMITE_RODA - abs(guinada) * pi / 180.0 * cal["bitola"] / 2.0)
        db.drive(sentido * v, guinada)
        wait(config.PERIODO_MS)
    if parar or not ok:
        v0 = abs(db.state()[1])
        d_freio = db.distance()
        db.brake()
        if prever and ok:
            _aprender_freio_reta(v0, d_freio)
        _atualizar_pose()
    if parar:
        erro_fim = _erro_rumo()
        cron_fim = StopWatch()
        ok = _creep() and ok
        db.stop()
        if config.DIAG_POSE and cron_fim.time() > 50:
            print("DIAG fim da reta: erro %.1f, ajuste %d ms" % (erro_fim, cron_fim.time()))
    return ok


def _aprender_freio_reta(v0, d_freio):
    # Espera as rodas pararem e aprende quanto o robô andou depois do freio,
    # em "ms de velocidade" (média móvel lenta, com limites).
    global _freio_reta_ms
    cron = StopWatch()
    while cron.time() < 250 and abs(db.state()[1]) > 5:
        _checar()
        wait(config.PERIODO_MS)
    if v0 > 20:
        est = abs(db.distance() - d_freio) / v0 * 1000.0
        _freio_reta_ms = _clamp(0.7 * _freio_reta_ms + 0.3 * est, 0.0, 150.0)


@_cronometrado("andar_ate_travar")
def andar_ate_travar(max_cm, vel=LENTO, ms=250):
    """Anda no rumo desejado até ENCOSTAR em algo, no máximo `max_cm` (negativo =
    de ré). Encostar = as rodas não avançam 3 mm em `ms` milissegundos (parede,
    peça, borda da mesa). Corrige a direção andando, como o andar_no_rumo.
    Devolve True se travou e False se chegou ao limite sem encostar.
    Ao travar, solta as rodas sem tentar corrigir o rumo (encostado, o giro
    fino brigaria com a parede). Roda que patina continua contando como
    avanço: encoste devagar (LENTO).
    Pode vir emendado num andar(..., RAPIDO, parar=False): chega rápido e só
    o fim é devagar (o robô freia de uma velocidade para a outra andando)."""
    if not _andando():
        _creep()                                 # parado: sai alinhado ao rumo
        _aplicar_vel(vel)                        # aceleração do db.drive
    # Emendado (já andando): sem creep, que giraria no lugar, e sem
    # db.settings com o robô em movimento. A aceleração já é a ACEL_RETA da
    # reta anterior, e o rumo se corrige andando no laço abaixo.
    alvo_mm = abs(max_cm) * 10.0
    sentido = 1.0 if max_cm >= 0 else -1.0
    v_max = abs(vel)
    d0 = db.distance()
    cron = StopWatch()
    teto = _teto(alvo_mm / v_max * 1000)
    d_ref = d0
    t_ref = 0
    travou = False
    while True:
        _checar()
        d = db.distance()
        restante = alvo_mm - abs(d - d0)
        if restante <= 0:
            break
        t = cron.time()
        if t > teto:
            print("AVISO: andar_ate_travar estourou o teto de %d ms" % teto)
            break
        if abs(d - d_ref) >= 3:
            d_ref = d
            t_ref = t
        elif t - t_ref > ms:
            travou = True
            break
        # Rampa de frenagem só para não passar do limite.
        v = min(v_max, max(config.RUMO_VEL_FINAL, sqrt(2.0 * config.ACEL_RETA * restante)))
        db.drive(sentido * v, _taxa_correcao(_erro_rumo()))
        wait(config.PERIODO_MS)
    db.brake()
    andou_cm = abs(db.distance() - d0) / 10.0
    if travou:
        print("andar_ate_travar: encostou em %.1f cm" % andou_cm)
    else:
        print("AVISO: andar_ate_travar chegou a %.1f cm sem encostar" % andou_cm)
    _atualizar_pose()
    if not travou:
        _creep()
    db.stop()
    return travou


@_cronometrado("girar")
def girar(graus, vel=NORMAL):
    """Gira no lugar `graus` (positivo = horário/direita) a partir do rumo desejado.

    vel: LENTO, NORMAL, RAPIDO ou um número em graus/s.
    """
    global _rumo_alvo
    _rumo_alvo = _rumo_alvo + graus
    ok = _ir_ate_rumo(normalizar=False, vel=vel)
    db.stop()
    if not ok and config.CORRECOES_RUMO:
        _rumo_alvo = db.angle()         # não deixa o resto do giro pendente
    return ok


@_cronometrado("virar_para")
def virar_para(rumo, vel=NORMAL):
    """Gira até o rumo ABSOLUTO `rumo` pelo caminho mais curto.

    vel: LENTO, NORMAL, RAPIDO ou um número em graus/s.
    """
    global _rumo_alvo
    _rumo_alvo = float(rumo)
    ok = _ir_ate_rumo(normalizar=True, vel=vel)
    db.stop()
    return ok


@_cronometrado("virar_ate_travar")
def virar_ate_travar(rumo, vel=LENTO, ms=250):
    """Gira rumo ao rumo ABSOLUTO `rumo`, mas para antes se o robô TRAVAR.

    Travar = o giroscópio não muda 1 grau em `ms` milissegundos (o anexo ou o
    robô encostou em algo). O rumo onde parou vira o rumo desejado, então os
    próximos andar() não tentam completar o giro. Devolve True se travou.
    """
    global _rumo_alvo
    db.stop()
    _rumo_alvo = float(rumo)
    # Com CORRECOES_RUMO o caminho é escolhido uma vez (alvo desembrulhado) e
    # o erro deixa de ser normalizado no meio do giro.
    norm = not config.CORRECOES_RUMO
    if not norm:
        _desembrulhar_alvo()
    erro = _erro_rumo(norm)
    if abs(erro) <= config.GIRO_TOL_ENTRA:
        return False
    sentido = 1.0 if erro > 0 else -1.0
    taxa = _taxa_giro(vel) * sentido
    teto = _teto(abs(erro) / abs(taxa) * 1000)
    cron = StopWatch()
    ang_ref = db.angle()
    t_ref = 0
    travou = False
    while True:
        _checar()
        if _giro_invertido(erro, norm):
            break
        if _erro_rumo(norm) * sentido <= config.GIRO_TOL_SAI:    # chegou ou passou
            break
        t = cron.time()
        if t > teto:
            print("AVISO: virar_ate_travar no teto; erro=%.1f" % _erro_rumo(norm))
            break
        if abs(db.angle() - ang_ref) >= 1.0:
            ang_ref = db.angle()
            t_ref = t
        elif t - t_ref > ms:
            travou = True
            break
        db.drive(0, taxa)
        wait(config.PERIODO_MS)
    if config.CORRECOES_RUMO and not travou:
        db.brake()                  # em coast deslizava ~5 graus além do alvo
    else:
        db.stop()
    if travou:
        _rumo_alvo = db.angle()
    elif config.CORRECOES_RUMO:
        _creep(norm, tol_entra=config.GIRO_TOL_SAI)     # chegou: fecha o giro
        db.stop()
    _atualizar_pose()
    return travou


def _esperar_passo_sacudida(cron, ms):
    # Um passo da sacudida acaba quando chega, quando trava (pula para o
    # próximo, sem abortar: sacudir encostado em algo é o uso normal) ou
    # quando o tempo total acaba.
    # Sempre ao menos uma volta (_checar + wait): um passo que já nasce pronto
    # ou travado não pode deixar o laço de sacudir() girar sem parar.
    passo = StopWatch()
    while True:
        _checar()
        wait(config.PERIODO_MS)
        if db.done():
            return
        if config.TOLERANCIAS_DB and passo.time() > 150:
            st = db.state()
            if abs(st[1]) < 5 and abs(st[3]) < 2:
                return              # parado a um fio da tolerância: próximo passo
        if cron.time() >= ms or db.stalled():
            db.stop()
            return


@_cronometrado("sacudir")
def sacudir(ms, cm=config.SACUDIR_CM, graus=config.SACUDIR_GRAUS):
    """Sacode o robô por `ms` milissegundos: vai e volta `cm` para a frente e
    para trás e vira `graus` para cada lado, sempre em torno do ponto e do rumo
    onde começou. No fim, volta para eles.

    Para assentar uma peça, soltar um anexo enroscado ou encaixar algo.
    cm=0 só vira para os lados; graus=0 só vai para a frente e para trás.
    Anexos lançados com esperar=False continuam se mexendo durante a sacudida.
    """
    global _vel_aplicada
    db.stop()
    d0 = db.distance()
    # Alvos ABSOLUTOS em torno do centro: o erro de um passo não acumula.
    passos = []
    if cm:
        mm = abs(cm) * 10.0
        passos += [(True, mm), (True, -mm), (True, 0.0)]
    if graus:
        g = abs(graus)
        passos += [(False, g), (False, -g), (False, 0.0)]
    if not passos:
        return True
    db.settings(config.VEL_NORMAL, config.SACUDIR_ACEL_RETA,
                config.VEL_GIRO, config.SACUDIR_ACEL_GIRO)
    _vel_aplicada = None                 # o próximo movimento reaplica as suas
    cron = StopWatch()
    k = 0
    while cron.time() < ms:
        reta, alvo = passos[k % len(passos)]
        k += 1
        if reta:
            db.straight(d0 + alvo - db.distance(), wait=False)
        else:
            db.turn(_rumo_alvo + alvo - db.angle(), wait=False)
        _esperar_passo_sacudida(cron, ms)
    db.stop()
    _atualizar_pose()
    # Volta ao centro: primeiro o rumo, depois a distância.
    ok = _ir_ate_rumo()
    volta = d0 - db.distance()
    if abs(volta) > 1:
        _aplicar_vel(NORMAL)
        db.straight(volta, wait=False)
        ok = _esperar_db(_teto(abs(volta) / NORMAL * 1000)) and ok
    db.stop()
    return ok


@_cronometrado("curva")
def curva(raio_cm, graus, vel=NORMAL, parar=True):
    """Anda em arco de raio `raio_cm`, mudando o rumo em `graus` (+ = direita).

    parar=False emenda no próximo movimento sem frear, como em andar(): uma
    sequência andar/curva/andar com parar=False vira um caminho contínuo.
    """
    global _rumo_alvo
    if not _emendado():
        # Parado: sai alinhado ao rumo. Emendada num andar(parar=False), NÃO:
        # o ajuste de rumo esperava o robô parar de guinar (até 250 ms, com o
        # robô andando reto no comando antigo) e, com mais de GIRO_TOL_ENTRA
        # de erro, girava no lugar freando. A curva saía depois do ponto, umas
        # vezes sim e outras não. O erro que sobrar a próxima reta corrige.
        _creep()
    _aplicar_vel(vel)
    db.curve(raio_cm * 10, graus, then=Stop.HOLD if parar else Stop.NONE, wait=False)
    comprimento = abs(raio_cm * 10 * graus * pi / 180.0)
    ok = _esperar_db(_teto(comprimento / abs(vel) * 1000 + abs(graus) / config.VEL_GIRO * 1000),
                     progresso=True)
    _rumo_alvo = _rumo_alvo + graus
    if not ok and config.CORRECOES_RUMO:
        _rumo_alvo = db.angle()         # curva abortada: não tenta completar
    if parar:
        ok = _creep() and ok
        db.stop()
    return ok


@_cronometrado("ir_para")
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
    ok = virar_para(rumo, vel)
    return andar(dist, vel) and ok


@_cronometrado("voltar_base")
def voltar_base(vel=RAPIDO, de_re=False):
    """Volta ao ponto de partida da saída (x=0, y=0)."""
    return ir_para(0, 0, vel, de_re)


def parar_tudo():
    """Para tração e anexos (não levanta exceção)."""
    db.stop()
    _anexo1.stop()
    _anexo2.stop()
    _tarefa[0] = None
    _tarefa[1] = None


def usar_creep(ligado=True):
    """Liga ou desliga o ajuste de rumo com o robô parado daqui em diante.

    Desligado, os giros são só a fase grossa e nada alinha o rumo antes ou
    depois das retas: o erro que sobrar a reta seguinte corrige andando.
    Vale só para a saída em curso: no fim de cada saída (completa ou
    abortada) o menu volta ao valor do config.py.
    """
    config.CREEP = ligado


def giro_fino(ligado=True):
    """Liga ou desliga o ajuste fino do giro (config.GIRO_FINO) daqui em diante.

    Vale só para a saída em curso: no fim de cada saída (completa ou
    abortada) o menu volta ao valor do config.py.
    """
    config.GIRO_FINO = ligado


_giro_desligado = None      # (rumo, heading do IMU) no instante em que desligou


def usar_giroscopio(ligado=True):
    """Liga ou desliga o giroscópio no rumo do robô daqui em diante.

    Desligado, o rumo (retas, giros, posição) vem só das rodas. Vale só para
    a saída em curso: no fim de cada saída (completa ou abortada) o menu
    religa. Dá para religar no meio da saída com usar_giroscopio(True): o
    rumo volta a ser o do giroscópio, que continuou medindo o tempo todo.
    """
    global _giro_desligado
    if (not ligado) == (_giro_desligado is not None):
        return                                   # já está assim
    d = db.distance()
    if ligado:
        # Rumo de quando desligou + o que o giroscópio viu girar desde então:
        # a referência da mesa (rumo_mesa) continua valendo nas próximas saídas.
        a0, h0 = _giro_desligado
        a = a0 + hub.imu.heading() - h0
        _giro_desligado = None
        db.use_gyro(True)
    else:
        a = db.angle()
        _giro_desligado = (a, hub.imu.heading())
        db.use_gyro(False)
    db.reset(distance=d, angle=a)                # o rumo segue de onde estava
    _atualizar_pose()


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


@_cronometrado("ate_linha")
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
    cron = StopWatch()
    # Teto: uma roda presa (ou um sensor que nunca vê a cor) com a outra já
    # parada não anda a distância máxima e prenderia o laço para sempre.
    teto = _teto(max_cm * 10.0 / abs(vel_mm) * 1000)
    while not (feito_dir and feito_esq):
        _checar()
        if abs(db.distance() - d0) >= max_cm * 10 or cron.time() > teto:
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


@_cronometrado("alinhar_na_linha")
def alinhar_na_linha(vel=LENTO, max_cm=30, rumo=None, fino=True):
    """Para com os DOIS sensores sobre a borda de uma linha preta à frente.

    Deixa o robô perpendicular à linha: é o jeito de corrigir o rumo numa mesa
    sem bordas. Se você sabe o rumo da linha no tapete, passe `rumo=...`: o
    giroscópio é reescrito com esse valor e o erro acumulado some.
    fino=True faz uma segunda passada lenta (recua 1,5 cm e volta ao preto).
    """
    return _alinhar(vel, max_cm, rumo, fino, PRETO, "alinhar_na_linha")


@_cronometrado("alinhar_na_base")
def alinhar_na_base(rumo=0, vel=LENTO, max_cm=30, fino=True):
    """Sai da base de FRENTE e esquadreja na MOLDURA verde da base.

    Cada roda anda até o SEU sensor sair do branco da base (refletância abaixo
    de config.LIMIAR_BORDA) e segura; com fino=True recua 1,5 cm e repete bem
    devagar. Parado e perpendicular à moldura, o rumo vira `rumo` (padrão 0 =
    a direção desta saída): o erro de quem soltou o robô na base some, e a
    referência do rumo da mesa é renovada.
    Custa ~1,5 a 3 s. O caminho dos sensores até a moldura tem de ser BRANCO
    liso: o logo ou qualquer desenho escuro no meio engana o sensor.
    """
    return _alinhar(vel, max_cm, rumo, fino, BORDA, "alinhar_na_base")


def _alinhar(vel, max_cm, rumo, fino, cor_alvo, nome):
    global _rumo_alvo, _mesa_cron, _mesa_var
    db.stop()
    a0 = db.angle()
    ok = _quadrar(vel, cor_alvo, max_cm)
    if ok and fino:
        # Recuo FIXO, não "até o branco": atrás da faixa preta pode haver fundo
        # cinza/bege que nunca passa do LIMIAR_BRANCO.
        _aplicar_vel(LENTO)
        db.straight(-15, wait=False)
        _esperar_db(_teto(15.0 / LENTO * 1000))
        # A passada fina define o rumo: a cada laço de 10 ms a roda anda
        # vel x 10 ms; a 25 mm/s são 0,25 mm (~0,2 grau entre os sensores).
        lenta = config.ALINHAR_VEL_FINA if config.CORRECOES_RUMO else abs(vel) / 3.0
        ok = _quadrar(lenta, cor_alvo, 4)
    _roda_dir.hold()
    _roda_esq.hold()
    _atualizar_pose()
    if not ok:
        print("AVISO: %s nao achou a linha em %d cm" % (nome, max_cm))
        return False
    girou = db.angle() - a0
    if config.CORRECOES_RUMO and abs(girou) > config.ALINHAR_MAX_GIRO:
        # Um sensor já começou sobre a cor (sombra, logo) ou uma roda patinou:
        # o esquadro é falso. Não apaga o giroscópio com ele.
        print("AVISO: %s girou %.1f graus: rumo NAO reescrito" % (nome, girou))
        _rumo_alvo = db.angle()
        db.stop()
        return False
    if rumo is not None:
        # db.reset e não hub.imu.reset_heading: com use_gyro, o reset do heading
        # levanta OSError desde o Pybricks 3.6 (lição do Baymax).
        db.reset(distance=db.distance(), angle=rumo)
        _rumo_alvo = float(rumo)
        if _mesa_cron is not None:
            # o rumo da mesa acabou de ser reancorado numa linha do tapete
            _mesa_cron = StopWatch()
            _mesa_var = 0.25 ** 2
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
    rumos = []                  # últimas leituras de rumo (média no fim)
    while True:
        _checar()
        if config.CORRECOES_RUMO:
            rumos.append(db.angle())
            if len(rumos) > 20:
                rumos.pop(0)
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
    # Depois de seguir a linha, o rumo desejado passa a ser o da linha: a MÉDIA
    # dos últimos ~200 ms, não uma leitura no meio da oscilação do PD.
    if rumos:
        _rumo_alvo = sum(rumos) / len(rumos)
    else:
        _rumo_alvo = db.angle()
    return chegou


@_cronometrado("seguir_linha")
def seguir_linha(cm, sensor=DIR, borda=ESQ, vel=config.SEGUIR_VEL, kp=None, kd=None):
    """Segue a BORDA de uma linha por `cm` centímetros.

    sensor: qual sensor segue (DIR ou ESQ). borda: ESQ = borda esquerda da
    linha preta (preto à direita do sensor), DIR = borda direita. As linhas do
    tapete TBR são faixas preta+branca: siga a borda entre as duas.
    """
    return _seguir(sensor, borda, vel, kp, kd, cm, None)


@_cronometrado("seguir_linha_ate_cruzamento")
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
def _norm180(a):
    while a > 180.0:
        a -= 360.0
    while a <= -180.0:
        a += 360.0
    return a


def _mesa_valida():
    return (_mesa_cron is not None
            and _mesa_cron.time() < config.LARGADA_REF_MAX_S * 1000)


def rumo_mesa():
    """Rumo do robô na MESA (graus): 0 = a direção fixada na 1ª saída ou na
    rotina Z. None se ainda não há referência."""
    if _mesa_cron is None:
        return None
    return db.angle() + _nominal


def _peso_giro():
    # Peso do giroscópio na fusão com a mão: sigma do rumo da mesa agora.
    minutos = _mesa_cron.time() / 60000.0
    var_giro = _mesa_var + (config.LARGADA_DERIVA * minutos) ** 2
    var_mao = config.LARGADA_SIGMA_MAO ** 2
    w = var_mao / (var_mao + var_giro) if var_mao + var_giro > 0 else 1.0
    return w, var_mao * var_giro / (var_mao + var_giro) if var_mao + var_giro > 0 else 0.0


def desvio_largada(nominal=None):
    """(desvio, nominal) do robô parado na base: quanto ele está torto em
    relação à direção nominal da saída (graus), já fundindo o giroscópio com a
    mão (ver config.LARGADA_COMPENSADA). `nominal` None = o múltiplo de
    config.LARGADA_PASSO mais perto. None se não há referência da mesa válida."""
    if not _mesa_valida():
        return None
    h = db.angle() + _nominal
    if nominal is None:
        n = round(h / config.LARGADA_PASSO) * config.LARGADA_PASSO
    else:
        n = float(nominal)
    d = _norm180(h - n)
    if abs(d) > config.LARGADA_MAX_DESVIO:
        return d, n                 # torto demais: largar() não compensa
    return _peso_giro()[0] * d, n


def definir_mesa(nominal=0):
    """O robô parado aponta EXATAMENTE para a direção `nominal` da mesa (ex.: no
    gabarito). A partir daqui as largadas são medidas contra isso."""
    global _nominal, _mesa_cron, _mesa_var
    _nominal = float(nominal) - db.angle()
    _mesa_cron = StopWatch()
    _mesa_var = config.LARGADA_SIGMA_MAO ** 2


def zerar_rumo():
    """O rumo atual vira 0 e a posição volta a (0, 0).

    O rumo da mesa continua valendo. Mas, no começo de uma saída, isto DESCARTA
    a compensação do largar(): o robô passa a achar que o torto é reto. O menu
    já chama largar(); a saída não precisa chamar zerar_rumo()."""
    global _rumo_alvo, _x, _y, _dist_ant, _nominal
    db.stop()
    _nominal = _nominal + db.angle()        # o rumo da MESA continua o mesmo
    db.reset(distance=0, angle=0)
    _rumo_alvo = 0.0
    _x = 0.0
    _y = 0.0
    _dist_ant = 0.0


def largar(nominal=None):
    """Começo de uma saída (o menu chama): rumo 0 = direção da saída e
    posição (0, 0).

    Com config.LARGADA_COMPENSADA e a referência da mesa válida, o rumo inicial
    NÃO é zero: é o quanto o robô foi solto torto em relação à direção nominal
    (`nominal`, ou o múltiplo de LARGADA_PASSO mais perto). O 1º movimento
    corrige. Sem referência (1ª saída), esta largada vira a referência.
    """
    global _nominal, _mesa_cron, _mesa_var
    h = db.angle() + _nominal               # rumo na mesa, antes de zerar
    r = desvio_largada(nominal) if config.LARGADA_COMPENSADA else None
    if r is not None:
        w, var_fundida = _peso_giro()
    zerar_rumo()
    if not config.LARGADA_COMPENSADA:
        return
    if r is None:
        # 1ª saída (ou referência velha): esta largada define a mesa.
        if _mesa_cron is None or nominal is not None:
            _nominal = 0.0 if nominal is None else float(nominal)
        else:
            # referência velha: ainda serve para saber a direção nominal
            _nominal = round(h / config.LARGADA_PASSO) * config.LARGADA_PASSO
        _mesa_cron = StopWatch()
        _mesa_var = config.LARGADA_SIGMA_MAO ** 2
        print("Largada: referencia da mesa fixada (direcao %d)" % _nominal)
    elif abs(r[0]) > config.LARGADA_MAX_DESVIO:
        # Torto demais para ser erro de mão: saída diagonal não declarada.
        # Rumo 0 = para onde aponta, e a mesa continua valendo.
        _nominal = h
        print("AVISO: largada %.1f graus fora de %d: sem compensar" % (r[0], r[1]))
    else:
        # r[0] já é o desvio fundido (w x o que o giroscópio vê). Ele vira o
        # rumo inicial e a nova referência da mesa, com a variância fundida.
        db.reset(distance=0, angle=r[0])
        _nominal = r[1]
        _mesa_cron = StopWatch()
        _mesa_var = var_fundida
        print("Largada: %+.1f graus da direcao %d (compensado, giroscopio viu %+.1f, peso %.2f)"
              % (r[0], r[1], r[0] / w if w > 0 else 0.0, w))


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


def odometro():
    """Centímetros percorridos pelas rodas (ré desconta). Use a diferença entre
    duas leituras para saber quanto um movimento andou, ex.: um ate_linha."""
    return db.distance() / 10.0


# ===================================================================================
# ANEXOS (motor 1 = porta F, motor 2 = porta B)
# ===================================================================================
# Todo movimento de anexo vira uma TAREFA vigiada por _vigiar_anexos(), que roda
# dentro de _checar(), ou seja, em todo laço de controle da linguagem. Por isso
# um anexo lançado com esperar=False continua se mexendo (e para sozinho se
# travar ou estourar o tempo) enquanto o robô anda, gira, segue linha, sacode
# ou espera. esperar=True é só "lançar e aguardar a tarefa acabar".
# Índices e não o motor como chave de dict: hash de objeto Pybricks não é garantido.
_ALVO = 0           # run_angle / run_target: acaba quando o motor chega
_TRAVAR = 1         # dc até parar: acaba quando o motor trava
_MOTORES = (_anexo1, _anexo2)
_RECOLHER_AVISO_GRAUS = 30   # recolher achou o batente mais longe que isto do 0: avisa
# Força dos comandos por posição = limite de torque do controle do motor, em %
# do torque de fábrica. Vale também para o hold que segura o anexo depois.
_TORQUE_MAX = [m.control.limits()[2] for m in _MOTORES]
_forca = [100, 100]          # % aplicado agora em cada motor


def _aplicar_forca(i, forca):
    f = _clamp(forca, 10, 100)
    if f == _forca[i]:
        return
    m = _MOTORES[i]
    torque = int(_TORQUE_MAX[i] * f / 100)
    try:
        m.control.limits(torque=torque)
    except Exception:
        # Firmware que não deixa mudar o limite com o controle ativo: solta o
        # motor por um instante e tenta de novo.
        m.stop()
        m.control.limits(torque=torque)
    _forca[i] = f


def _lancar(i, modo, teto_ms, zerar=False, sentido=1, limite=None, continuar=False):
    # [modo, cron, teto, desde, zerar, sentido, limite, continuar]
    # zerar = ao travar, ali vira o ângulo 0; limite = ângulo que o modo _TRAVAR
    # não passa (None = sem limite), no `sentido` em que o motor empurra;
    # continuar = ao travar (ou no teto), a tarefa acaba mas o motor CONTINUA
    # empurrando, sem hold (o apertar()).
    _tarefa[i] = [modo, StopWatch(), teto_ms, None, zerar, sentido, limite, continuar]
    _resultado[i] = True


def _encerrar(i, ok):
    _tarefa[i] = None
    _resultado[i] = ok


def _vigiar_anexos():
    for i in (0, 1):
        tarefa = _tarefa[i]
        if tarefa is None:
            continue
        m = _MOTORES[i]
        t = tarefa[1].time()
        if tarefa[0] == _ALVO:
            if m.done():
                _encerrar(i, True)
            elif t > tarefa[2]:
                m.stop()
                print("AVISO: anexo%d estourou o teto de %d ms (em %d graus)" % (i + 1, tarefa[2], m.angle()))
                _encerrar(i, False)
            elif m.stalled():
                if tarefa[3] is None:
                    tarefa[3] = t
                elif t - tarefa[3] > config.STALL_ABORTA_MS:
                    m.hold()
                    print("AVISO: anexo%d travado em %d graus, movimento encerrado" % (i + 1, m.angle()))
                    _encerrar(i, False)
            else:
                tarefa[3] = None
        else:
            # Empurra com duty fixo até o motor parar (fim de curso / objeto
            # preso) e então segura. run_until_stalled não serve: não tem teto
            # e prende o programa se nunca travar.
            if t > tarefa[2]:
                if not tarefa[7]:
                    m.hold()
                print("AVISO: anexo%d nao travou em %d ms (em %d graus)" % (i + 1, tarefa[2], m.angle()))
                _encerrar(i, False)
            elif tarefa[6] is not None and tarefa[5] * (m.angle() - tarefa[6]) >= 0:
                m.hold()
                print("AVISO: anexo%d passou do limite (%d graus) sem travar" % (i + 1, tarefa[6]))
                _encerrar(i, False)
            elif t < 150:
                pass                            # deixa o motor arrancar
            elif abs(m.speed()) < 30:
                if tarefa[3] is None:
                    tarefa[3] = t
                elif t - tarefa[3] > 100:
                    if tarefa[4]:
                        a = m.angle()
                        if abs(a) > _RECOLHER_AVISO_GRAUS:
                            print("AVISO: anexo%d recolhido com o batente em %d graus "
                                  "(dente pulou?), zero refeito" % (i + 1, a))
                        m.reset_angle(0)
                    if not tarefa[7]:
                        m.hold()
                    _encerrar(i, True)
            else:
                tarefa[3] = None


def _aguardar(i):
    while _tarefa[i] is not None:
        _checar()
        wait(config.PERIODO_MS)
    return _resultado[i]


def _girar_anexo(i, graus, vel, esperar):
    _aplicar_forca(i, 100)
    _MOTORES[i].run_angle(vel, graus, then=Stop.HOLD, wait=False)
    _lancar(i, _ALVO, _teto(abs(graus) / abs(vel) * 1000))
    return _aguardar(i) if esperar else True


def _anexo_para(i, angulo, vel, esperar, forca=100):
    _aplicar_forca(i, forca)
    m = _MOTORES[i]
    teto = _teto(abs(angulo - m.angle()) / abs(vel) * 1000)
    m.run_target(vel, angulo, then=Stop.HOLD, wait=False)
    _lancar(i, _ALVO, teto)
    return _aguardar(i) if esperar else True


def _anexo_travar(i, sentido, forca, teto_ms, esperar, zerar=False, limite=None):
    _aplicar_forca(i, 100)      # o hold depois de travar segura com tudo
    _MOTORES[i].dc(sentido * _clamp(forca, 10, 100))
    _lancar(i, _TRAVAR, teto_ms, zerar, sentido, limite)
    return _aguardar(i) if esperar else True


def _anexo_empurrar(i, sentido, vel, forca, teto_ms, esperar, zerar=False, limite=None,
                    continuar=False):
    # Como _anexo_travar, mas com velocidade controlada e torque limitado em
    # vez de duty fixo: o hold que segura depois também fica com essa força.
    # Abaixo de 60 graus/s o vigia confundiria andar devagar com travar.
    _aplicar_forca(i, forca)
    _MOTORES[i].run(sentido * max(60, abs(vel)))
    _lancar(i, _TRAVAR, teto_ms, zerar, sentido, limite, continuar)
    return _aguardar(i) if esperar else True


@_cronometrado("anexo1")
def anexo1(graus, vel=config.VEL_ANEXO, esperar=True):
    """Gira o motor do anexo 1 (porta F) `graus` relativos.
    esperar=False: devolve na hora e o anexo se mexe enquanto o robô anda,
    gira ou faz outro movimento (vigiado: para sozinho se travar)."""
    return _girar_anexo(0, graus, vel, esperar)


@_cronometrado("anexo2")
def anexo2(graus, vel=config.VEL_ANEXO, esperar=True):
    """Gira o motor do anexo 2 (porta B) `graus` relativos."""
    return _girar_anexo(1, graus, vel, esperar)


@_cronometrado("anexo1_ir_para")
def anexo1_ir_para(angulo, vel=config.VEL_ANEXO, esperar=True):
    """Leva o anexo 1 ao ângulo ABSOLUTO `angulo` (0 = onde foi zerado)."""
    return _anexo_para(0, angulo, vel, esperar)


@_cronometrado("anexo2_ir_para")
def anexo2_ir_para(angulo, vel=config.VEL_ANEXO, esperar=True):
    """Leva o anexo 2 ao ângulo ABSOLUTO `angulo`."""
    return _anexo_para(1, angulo, vel, esperar)


@_cronometrado("anexo1_aumentar")
def anexo1_aumentar(graus, vel=config.VEL_ANEXO, esperar=True):
    """Soma `graus` ao ângulo MEDIDO AGORA do anexo 1 (negativo diminui).

    Diferença para anexo1(): este parte do alvo anterior do motor, então se o
    anexo foi empurrado ou cedeu com peso, o erro acumula. Aqui a conta começa
    de onde o encoder diz que ele está.
    """
    return _anexo_para(0, _anexo1.angle() + graus, vel, esperar)


@_cronometrado("anexo2_aumentar")
def anexo2_aumentar(graus, vel=config.VEL_ANEXO, esperar=True):
    """Soma `graus` ao ângulo MEDIDO AGORA do anexo 2 (negativo diminui)."""
    return _anexo_para(1, _anexo2.angle() + graus, vel, esperar)


@_cronometrado("anexo1_ate_travar")
def anexo1_ate_travar(sentido=HORARIO, forca=50, teto_ms=3000, esperar=True):
    """Gira o anexo 1 até travar (garra fechando, braço no fim de curso).
    esperar=False: fecha enquanto o robô se mexe."""
    return _anexo_travar(0, sentido, forca, teto_ms, esperar)


@_cronometrado("anexo2_ate_travar")
def anexo2_ate_travar(sentido=HORARIO, forca=50, teto_ms=3000, esperar=True):
    """Gira o anexo 2 até travar."""
    return _anexo_travar(1, sentido, forca, teto_ms, esperar)


@_cronometrado("anexo1_recolher")
def anexo1_recolher(sentido=HORARIO, forca=30, teto_ms=1500, esperar=True):
    """Leva o anexo 1 até o batente (`sentido` = para onde fica o batente) e
    faz dali o ângulo 0. Corrige o 0 depois de forçar o braço: engrenagem que
    pula dente faz o motor girar sem o braço e o 0 antigo fica errado."""
    return _anexo_travar(0, sentido, forca, teto_ms, esperar, True)


@_cronometrado("anexo2_recolher")
def anexo2_recolher(sentido=HORARIO, forca=30, teto_ms=1500, esperar=True):
    """Leva o anexo 2 até o batente e faz dali o ângulo 0."""
    return _anexo_travar(1, sentido, forca, teto_ms, esperar, True)


def zerar_anexos():
    """A posição atual dos dois anexos vira o ângulo 0."""
    _anexo1.reset_angle(0)
    _anexo2.reset_angle(0)


@_cronometrado("esperar_anexos")
def esperar_anexos(teto_ms=5000):
    """Espera os anexos lançados com esperar=False terminarem. Devolve False se
    algum travou, estourou o próprio teto ou passou de `teto_ms` aqui."""
    lancados = [i for i in (0, 1) if _tarefa[i] is not None]
    cron = StopWatch()
    while _tarefa[0] is not None or _tarefa[1] is not None:
        _checar()
        if cron.time() > teto_ms:
            for i in (0, 1):
                if _tarefa[i] is not None:
                    _MOTORES[i].hold()
                    print("AVISO: esperar_anexos: anexo%d nao terminou em %d ms" % (i + 1, teto_ms))
                    _encerrar(i, False)
            break
        wait(config.PERIODO_MS)
    ok = True
    for i in lancados:
        ok = ok and _resultado[i]
    return ok


def angulo_anexo1():
    return _anexo1.angle()


def angulo_anexo2():
    return _anexo2.angle()


# ===================================================================================
# ELEVADOR (anexo2, porta B) E GARRA (anexo1, porta F)
# ===================================================================================
# Comandos em centímetros sobre os anexos de modelos3d/elevador. Por baixo são
# os mesmos motores e tarefas vigiadas dos anexos: esperar=False funciona igual,
# esperar_anexos() espera por eles e os anexo1_/anexo2_ continuam valendo.
# Os limites de curso são em software, contados do 0 que o menu faz no início
# de cada saída: comece com o carro EMBAIXO e a garra ABERTA (ou chame abrir()).
_FOLGA_LIMITE_GRAUS = 20    # abrir()/fechar() por força: margem além do curso


def _elevador(alvo_cm, vel, forca, esperar, nome):
    alvo = _clamp(alvo_cm, 0.0, config.ELEVADOR_CURSO_CM)
    if abs(alvo - alvo_cm) > 0.05:
        print("AVISO: %s: %.1f cm fora do curso (0 a %.1f), vai a %.1f"
              % (nome, alvo_cm, config.ELEVADOR_CURSO_CM, alvo))
    graus = config.ELEVADOR_SOBE * alvo * config.ELEVADOR_GRAUS_CM
    taxa = _traduzir_vel(vel, config.ELEVADOR_LENTO, config.ELEVADOR_NORMAL, config.ELEVADOR_RAPIDO)
    return _anexo_para(1, graus, taxa, esperar, forca)


def altura_elevador():
    """Altura do carro em cm acima do ponto de partida (0 = embaixo)."""
    return config.ELEVADOR_SOBE * _anexo2.angle() / config.ELEVADOR_GRAUS_CM


@_cronometrado("subir")
def subir(cm=None, vel=NORMAL, forca=config.ELEVADOR_FORCA, esperar=True):
    """Sobe o carro do elevador `cm` a partir da altura medida agora. Sem `cm`,
    vai até o topo do curso. vel = LENTO/NORMAL/RAPIDO ou graus/s de motor.
    forca = % do torque do motor, que vale também para SEGURAR o carro depois
    (o fuso não se auto-trava: força baixa com peso pode deixar descer).
    esperar=False: sobe enquanto o robô anda. Não passa do curso (avisa)."""
    alvo = config.ELEVADOR_CURSO_CM if cm is None else altura_elevador() + cm
    return _elevador(alvo, vel, forca, esperar, "subir")


@_cronometrado("descer")
def descer(cm=None, vel=NORMAL, forca=config.ELEVADOR_FORCA, esperar=True):
    """Desce o carro `cm` a partir da altura medida agora. Sem `cm`, vai até
    embaixo (altura 0). Força baixa = desce sem esmagar o que estiver embaixo:
    se encostar, avisa "travado" e para ali. Não passa do curso (avisa)."""
    alvo = 0.0 if cm is None else altura_elevador() - cm
    return _elevador(alvo, vel, forca, esperar, "descer")


@_cronometrado("elevador_ir_para")
def elevador_ir_para(cm, vel=NORMAL, forca=config.ELEVADOR_FORCA, esperar=True):
    """Leva o carro à altura ABSOLUTA `cm` (0 = embaixo, máx. ELEVADOR_CURSO_CM)."""
    return _elevador(cm, vel, forca, esperar, "elevador_ir_para")


def _garra(abertura_cm, vel, forca, esperar, nome):
    minimo = config.GARRA_ABERTA_CM - config.GARRA_CURSO_CM
    alvo = _clamp(abertura_cm, minimo, config.GARRA_ABERTA_CM)
    if abs(alvo - abertura_cm) > 0.05:
        print("AVISO: %s: abertura de %.1f cm fora do curso (%.1f a %.1f), vai a %.1f"
              % (nome, abertura_cm, minimo, config.GARRA_ABERTA_CM, alvo))
    graus = config.GARRA_FECHA * (config.GARRA_ABERTA_CM - alvo) * config.GARRA_GRAUS_CM
    return _anexo_para(0, graus, _taxa_garra(vel), esperar, forca)


def _taxa_garra(vel):
    return _traduzir_vel(vel, config.GARRA_LENTO, config.GARRA_NORMAL, config.GARRA_RAPIDO)


def _limite_garra(sentido):
    # Ângulo que a garra não passa empurrando por força: o curso inteiro a
    # partir de AGORA, mais a folga. Vale mesmo se o 0 estiver errado.
    curso = config.GARRA_CURSO_CM * config.GARRA_GRAUS_CM + _FOLGA_LIMITE_GRAUS
    return _anexo1.angle() + sentido * curso


def abertura_garra():
    """Distância entre os dedos em cm (GARRA_ABERTA_CM = aberta no batente)."""
    return config.GARRA_ABERTA_CM - config.GARRA_FECHA * _anexo1.angle() / config.GARRA_GRAUS_CM


@_cronometrado("abrir")
def abrir(cm=None, vel=NORMAL, forca=config.GARRA_FORCA_ABRIR, esperar=True):
    """Abre a garra `cm` a partir da abertura medida agora. Sem `cm`, abre até o
    batente e faz dali o 0: use no início da saída se a garra não começou
    aberta. vel = LENTO/NORMAL/RAPIDO ou graus/s de motor; forca = % do torque."""
    if cm is None:
        sentido = -config.GARRA_FECHA
        return _anexo_empurrar(0, sentido, _taxa_garra(vel), forca, 1500, esperar,
                               True, _limite_garra(sentido))
    return _garra(abertura_garra() + cm, vel, forca, esperar, "abrir")


@_cronometrado("fechar")
def fechar(cm=None, vel=NORMAL, forca=config.GARRA_FORCA, esperar=True):
    """Fecha a garra `cm` a partir da abertura medida agora (se encostar numa
    peça antes, avisa "travado" e segura ali). Sem `cm`, fecha até travar na
    peça ou no fim do curso e segura: é o jeito de PEGAR algo. forca = % do
    torque, com que ela aperta e continua segurando."""
    if cm is None:
        sentido = config.GARRA_FECHA
        return _anexo_empurrar(0, sentido, _taxa_garra(vel), forca, 1500, esperar,
                               False, _limite_garra(sentido))
    return _garra(abertura_garra() - cm, vel, forca, esperar, "fechar")


@_cronometrado("apertar")
def apertar(forca=config.GARRA_FORCA_APERTAR, vel=LENTO, esperar=True):
    """Fecha a garra e fica SEMPRE empurrando com `forca`% do torque: se a peça
    escorregar ou ceder, a garra fecha mais sozinha. Não termina por conta
    própria: continua até outro comando de garra (abrir, fechar,
    garra_ir_para, anexo1_...) ou o fim da saída. esperar=True devolve quando
    a garra encosta (o aperto continua); esperar=False devolve na hora.
    Força baixa: o motor fica parado empurrando, e é isso que ele aguenta."""
    sentido = config.GARRA_FECHA
    return _anexo_empurrar(0, sentido, _taxa_garra(vel), forca, 1500, esperar,
                           False, _limite_garra(sentido), True)


@_cronometrado("garra_ir_para")
def garra_ir_para(cm, vel=NORMAL, forca=config.GARRA_FORCA, esperar=True):
    """Deixa `cm` entre os dedos (de GARRA_ABERTA_CM - GARRA_CURSO_CM até
    GARRA_ABERTA_CM), por posição."""
    return _garra(cm, vel, forca, esperar, "garra_ir_para")


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


_radio = None


def avisar_maker():
    """Avisa o 2º hub (Dispositivo Maker) que os trabalhadores foram entregues.

    Liga o broadcast BLE no canal MAKER_CANAL e segue na hora: o rádio continua
    anunciando sozinho até o programa acabar. Só depois deste aviso o hub do
    Maker (hub/maker.py) começa a olhar o ultrassônico. Uma falha do rádio só
    é impressa: não aborta a saída.
    """
    global _radio
    try:
        if _radio is None:
            from pybricks.messaging import BLERadio
            _radio = BLERadio(broadcast_channel=config.MAKER_CANAL)
        _radio.broadcast(config.MAKER_SINAL)
        print("MAKER aviso enviado (canal %d)" % config.MAKER_CANAL)
    except Exception as e:
        print("MAKER aviso FALHOU: %s" % e)


def _central_ficar(apertado, ms=0):
    # Espera o central ficar nesse estado por ms seguidos, sem abortar.
    cron = StopWatch()
    while True:
        if (Button.CENTER in hub.buttons.pressed()) != apertado:
            cron.reset()
        elif cron.time() >= ms:
            return
        _manter()
        wait(config.PERIODO_MS)


@_cronometrado("esperar")
def esperar(ms=None):
    """esperar(ms): pausa que continua respondendo ao botão de abortar.

    esperar(): gatilho. Segura a saída até um novo toque no botão central, que
    aqui continua em vez de abortar (quem encerra é o botão Bluetooth). Basta
    um toque rápido; o robô segue quando o dedo sai do botão.
    """
    if ms is None:
        _central_ficar(False)       # o dedo que já estava lá não conta
        _central_ficar(True)
        # Voltar com o central apertado (ou repicando) abortaria a saída no
        # próximo _checar().
        _central_ficar(False, config.BOTAO_REPIQUE_MS)
        return
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
