"""Dublê do hub/tbr.py para rodar missões no PC.

Mesma API pública do tbr.py (o teste testes/teste_api.py garante), sem
hardware: cada comando só registra o passo, avança a posição estimada e soma
um tempo estimado. Serve para achar erro de digitação e nome errado antes de
ir ao robô, e para ter uma ideia do tempo de cada saída contra os 120 s.

Os tempos são ESTIMATIVAS grosseiras (velocidade + rampa de aceleração). O que
depende da mesa (achar uma linha, chegar num cruzamento) usa o máximo pedido.
"""

import math

from ferramentas.hubconfig import constantes

_C = constantes()

LENTO = _C["VEL_LENTO"]
NORMAL = _C["VEL_NORMAL"]
RAPIDO = _C["VEL_RAPIDO"]
PRETO = "preto"
BRANCO = "branco"
VERDE = "verde"
BORDA = "borda"
DIR = "dir"
ESQ = "esq"
QUALQUER = "qualquer"
HORARIO = 1
ANTI_HORARIO = -1

# Tempo fixo de assentamento de cada manobra (creep, freio), em s.
_ASSENTA_S = 0.15


class SaidaAbortada(Exception):
    pass


class _Qualquer:
    """Aceita qualquer atributo/chamada: substitui hub, db e Color."""

    def __init__(self, nome):
        self._nome = nome

    def __getattr__(self, attr):
        return _Qualquer("%s.%s" % (self._nome, attr))

    def __call__(self, *args, **kwargs):
        return _Qualquer(self._nome + "()")

    def __repr__(self):
        return self._nome


Color = _Qualquer("Color")
hub = _Qualquer("hub")
db = _Qualquer("db")
cal = {"roda": _C["RODA_MM"], "bitola": _C["BITOLA_MM"]}
cal_gravada = False

# --- Estado da simulação ---------------------------------------------------------
_t = 0.0
_x = 0.0
_y = 0.0
_rumo = 0.0
_odo = 0.0
_anexos = [0.0, 0.0]
_partida = None
passos = []          # [(t, x, y, rumo, descricao)]


def reiniciar():
    """Zera tudo (o simulador chama antes de cada saída)."""
    global _t, _x, _y, _rumo, _odo, _anexos, passos
    _t = 0.0
    _x = _y = _rumo = _odo = 0.0
    _anexos = [0.0, 0.0]
    passos = []


def tempo():
    return _t


def _passo(descricao, segundos):
    global _t
    _t += segundos
    passos.append((_t, _x, _y, _rumo, descricao))


def _t_reta(cm, vel):
    vel = abs(vel)
    return abs(cm) * 10.0 / vel + vel / _C["ACEL_RETA"] + _ASSENTA_S


def _taxa_giro(vel):
    return {LENTO: _C["GIRO_LENTO"], NORMAL: _C["VEL_GIRO"],
            RAPIDO: _C["GIRO_RAPIDO"]}.get(vel, abs(vel))


def _t_giro(graus, vel=NORMAL):
    taxa = _taxa_giro(vel)
    return abs(graus) / taxa + taxa / _C["ACEL_GIRO"] + 2 * _ASSENTA_S


def _avancar(cm):
    global _x, _y, _odo
    _odo += cm
    h = math.radians(_rumo)
    _x += cm * math.cos(h)
    _y -= cm * math.sin(h)


def _normalizar(graus):
    while graus > 180.0:
        graus -= 360.0
    while graus <= -180.0:
        graus += 360.0
    return graus


def _conferir_vel(nome, vel, parar):
    # Compila e roda no hub, mas o robô não faz o que a equipe escreveu. Só o
    # `tbr verificar` confere: o hub/tbr.py continua aceitando.
    # Casos reais: andar_no_rumo(24, 358,5, LENTO) virou vel=5 e parar=150;
    # andar_no_rumo(32, RAPIDO, -21) virou rumo=450 e vel=-21.
    dica = " (vírgula em vez de ponto, ou argumentos trocados?)"
    if not isinstance(parar, bool):
        raise ValueError("%s: parar=%r não é True/False%s" % (nome, parar, dica))
    if vel < 0:
        raise ValueError("%s: vel=%r negativa; a ré vem do sinal de cm%s" % (nome, vel, dica))
    if vel < _C["RUMO_VEL_FINAL"]:
        raise ValueError("%s: vel=%r mm/s é baixa demais (mínimo %d)%s"
                         % (nome, vel, _C["RUMO_VEL_FINAL"], dica))


# --- Movimento -----------------------------------------------------------------
def andar(cm, vel=NORMAL, parar=True):
    _conferir_vel("andar", vel, parar)
    _avancar(cm)
    _passo("andar(%g)" % cm, _t_reta(cm, vel) - (0 if parar else _ASSENTA_S))
    return True


def andar_no_rumo(cm, rumo, vel=NORMAL, parar=True):
    # Muito torto: vira no lugar antes. Pouco torto: corrige andando (aqui
    # aproximado como se já saísse no rumo certo).
    global _rumo
    _conferir_vel("andar_no_rumo", vel, parar)
    delta = _normalizar(rumo - _rumo)
    t_giro = _t_giro(delta) if abs(delta) > _C["RUMO_VIRAR_ANTES"] else 0.0
    _rumo += delta
    _avancar(cm)
    _passo("andar_no_rumo(%g, %g)" % (cm, rumo),
           t_giro + _t_reta(cm, vel) - (0 if parar else _ASSENTA_S))
    return True


def andar_com_forca(cm, rumo=None, forca=100, ms=_C["FORCA_TRAVOU_MS"]):
    # Nada resiste aqui: tempo de um andar_no_rumo em RAPIDO, sem a rampa da saída
    # que o hub não faz (na mesa a velocidade depende da bateria e da carga).
    global _rumo
    if not 10 <= forca <= 100:
        raise ValueError("andar_com_forca: forca=%r fora de 10 a 100 "
                         "(vírgula em vez de ponto, ou argumentos trocados?)" % (forca,))
    delta = 0.0 if rumo is None else _normalizar(rumo - _rumo)
    t_giro = _t_giro(delta) if abs(delta) > _C["RUMO_VIRAR_ANTES"] else 0.0
    _rumo += delta
    _avancar(cm)
    _passo("andar_com_forca(%g)" % cm, t_giro + _t_reta(cm, RAPIDO))
    return True


def girar(graus, vel=NORMAL):
    global _rumo
    _rumo += graus
    _passo("girar(%g)" % graus, _t_giro(graus, vel))
    return True


def virar_para(rumo, vel=NORMAL):
    global _rumo
    delta = _normalizar(rumo - _rumo)
    _rumo += delta
    _passo("virar_para(%g)" % rumo, _t_giro(delta, vel) if abs(delta) > 0.5 else 0.0)
    return True


def andar_ate_travar(max_cm, vel=LENTO, ms=250):
    # No simulador nada trava: anda o limite inteiro, como andar().
    _avancar(max_cm)
    _passo("andar_ate_travar(%g)" % max_cm, _t_reta(max_cm, vel))
    return False


def virar_ate_travar(rumo, vel=LENTO, ms=250):
    # No simulador nada trava: gira até o rumo, como virar_para.
    global _rumo
    delta = _normalizar(rumo - _rumo)
    _rumo += delta
    _passo("virar_ate_travar(%g)" % rumo, _t_giro(delta, vel) if abs(delta) > 0.5 else 0.0)
    return False


def sacudir(ms, cm=_C["SACUDIR_CM"], graus=_C["SACUDIR_GRAUS"]):
    # Termina onde começou: só gasta o tempo (+ a volta ao centro).
    _passo("sacudir(%d)" % ms, ms / 1000.0 + 2 * _ASSENTA_S)
    return True


def curva(raio_cm, graus, vel=NORMAL, parar=True):
    global _x, _y, _rumo
    _conferir_vel("curva", vel, parar)
    # Arco: o centro fica a `raio` para o lado da curva.
    h0 = math.radians(_rumo)
    sinal = 1.0 if graus >= 0 else -1.0
    # vetor "direita" do robô em (x leste, y norte): rumo 0 => direita = sul
    dx_dir, dy_dir = -math.sin(h0), -math.cos(h0)
    cx = _x + sinal * raio_cm * dx_dir
    cy = _y + sinal * raio_cm * dy_dir
    ang = math.atan2(_y - cy, _x - cx) - math.radians(graus)
    _x = cx + abs(raio_cm) * math.cos(ang)
    _y = cy + abs(raio_cm) * math.sin(ang)
    _rumo += graus
    comprimento = abs(raio_cm * math.radians(graus))
    _passo("curva(%g, %g)" % (raio_cm, graus),
           _t_reta(comprimento, vel) - (0 if parar else _ASSENTA_S))
    return True


def ir_para(x, y, vel=NORMAL, de_re=False):
    dx, dy = x - _x, y - _y
    dist = math.hypot(dx, dy)
    if dist < 0.5:
        return True
    rumo = -math.degrees(math.atan2(dy, dx))
    if de_re:
        rumo += 180.0
        dist = -dist
    virar_para(rumo, vel)
    andar(dist, vel)
    passos[-1] = passos[-1][:4] + ("ir_para(%g, %g)" % (x, y),)
    return True


def voltar_base(vel=RAPIDO, de_re=False):
    ir_para(0, 0, vel, de_re)
    passos[-1] = passos[-1][:4] + ("voltar_base()",)
    return True


def parar_tudo():
    pass


def giro_fino(ligado=True):
    # O simulador não modela o giro fino: só registra o passo.
    _passo("giro_fino(%s)" % ligado, 0.0)


def usar_creep(ligado=True):
    # O simulador não modela o creep: só registra o passo.
    _passo("usar_creep(%s)" % ligado, 0.0)


def usar_giroscopio(ligado=True):
    # O simulador não modela o giroscópio: só registra o passo.
    _passo("usar_giroscopio(%s)" % ligado, 0.0)


# --- Linhas ----------------------------------------------------------------------
def reflexao(sensor):
    return 50.0


def reflexao_crua(sensor):
    return 50


def cor(sensor):
    return Color.NONE


def ate_linha(cor_alvo=PRETO, sensor=QUALQUER, vel=LENTO, max_cm=50):
    # Sem mapa da mesa: supõe que a linha aparece na metade do máximo.
    cm = max_cm / 2.0 * (1 if vel > 0 else -1)
    _avancar(cm)
    _passo("ate_linha(max %g) ~%g cm" % (max_cm, abs(cm)), _t_reta(cm, vel))
    return True


def alinhar_na_linha(vel=LENTO, max_cm=30, rumo=None, fino=True):
    global _rumo
    _avancar(max_cm / 2.0)
    if rumo is not None:
        _rumo = float(rumo)
    _passo("alinhar_na_linha()", _t_reta(max_cm / 2.0, vel) + (1.0 if fino else 0.0))
    return True


def alinhar_na_base(rumo=0, vel=LENTO, max_cm=30, fino=True):
    global _rumo
    _avancar(max_cm / 2.0)
    if rumo is not None:
        _rumo = float(rumo)
    _passo("alinhar_na_base()", _t_reta(max_cm / 2.0, vel) + (1.0 if fino else 0.0))
    return True


def seguir_linha(cm, sensor=DIR, borda=ESQ, vel=_C["SEGUIR_VEL"], kp=None, kd=None):
    _avancar(cm)
    _passo("seguir_linha(%g)" % cm, _t_reta(cm, vel))
    return True


def seguir_linha_ate_cruzamento(sensor=DIR, borda=ESQ, vel=_C["SEGUIR_VEL"],
                                max_cm=150, kp=None, kd=None):
    # Sem mapa da mesa: supõe que o cruzamento está no máximo pedido.
    _avancar(max_cm)
    _passo("seguir_linha_ate_cruzamento(max %g)" % max_cm, _t_reta(max_cm, vel))
    return True


# --- Posição e rumo ---------------------------------------------------------------
def zerar_rumo():
    global _x, _y, _rumo
    _x = _y = _rumo = 0.0


def largar(nominal=None):
    # No dublê o robô é sempre solto perfeito: a largada não tem erro.
    zerar_rumo()


def rumo_mesa():
    return _rumo


def desvio_largada(nominal=None):
    return None


def definir_mesa(nominal=0):
    pass


def zerar_posicao():
    definir_posicao(0, 0)


def definir_posicao(x, y):
    global _x, _y
    _x, _y = float(x), float(y)


def posicao():
    return _x, _y, _rumo


def rumo():
    return _rumo


def odometro():
    return _odo


# --- Anexos ----------------------------------------------------------------------
def _anexo(i, graus, vel, esperar):
    _anexos[i] += graus
    _passo("anexo%d(%g)" % (i + 1, graus), abs(graus) / abs(vel) + 0.05 if esperar else 0.0)
    return True


def anexo1(graus, vel=_C["VEL_ANEXO"], esperar=True):
    return _anexo(0, graus, vel, esperar)


def anexo2(graus, vel=_C["VEL_ANEXO"], esperar=True):
    return _anexo(1, graus, vel, esperar)


def anexo1_ir_para(angulo, vel=_C["VEL_ANEXO"], esperar=True):
    return _anexo(0, angulo - _anexos[0], vel, esperar)


def anexo2_ir_para(angulo, vel=_C["VEL_ANEXO"], esperar=True):
    return _anexo(1, angulo - _anexos[1], vel, esperar)


def anexo1_aumentar(graus, vel=_C["VEL_ANEXO"], esperar=True):
    # No simulador o anexo está sempre onde foi mandado: igual ao anexo1().
    return _anexo(0, graus, vel, esperar)


def anexo2_aumentar(graus, vel=_C["VEL_ANEXO"], esperar=True):
    return _anexo(1, graus, vel, esperar)


def anexo1_ate_travar(sentido=HORARIO, forca=50, teto_ms=3000, esperar=True):
    _passo("anexo1_ate_travar(%d)" % sentido, 0.6 if esperar else 0.0)
    return True


def anexo2_ate_travar(sentido=HORARIO, forca=50, teto_ms=3000, esperar=True):
    _passo("anexo2_ate_travar(%d)" % sentido, 0.6 if esperar else 0.0)
    return True


def anexo1_recolher(sentido=HORARIO, forca=30, teto_ms=1500, esperar=True):
    _anexos[0] = 0.0
    _passo("anexo1_recolher()", 0.4 if esperar else 0.0)
    return True


def anexo2_recolher(sentido=HORARIO, forca=30, teto_ms=1500, esperar=True):
    _anexos[1] = 0.0
    _passo("anexo2_recolher()", 0.4 if esperar else 0.0)
    return True


def zerar_anexos():
    _anexos[0] = _anexos[1] = 0.0


def esperar_anexos(teto_ms=5000):
    return True


def angulo_anexo1():
    return _anexos[0]


def angulo_anexo2():
    return _anexos[1]


# --- Elevador (anexo2) e garra (anexo1) --------------------------------------------
def _traduzir_vel(vel, prefixo):
    return {LENTO: _C[prefixo + "_LENTO"], NORMAL: _C[prefixo + "_NORMAL"],
            RAPIDO: _C[prefixo + "_RAPIDO"]}.get(vel, abs(vel))


def _mover(i, graus_alvo, vel, prefixo, esperar, descricao):
    taxa = _traduzir_vel(vel, prefixo)
    delta = graus_alvo - _anexos[i]
    _anexos[i] = graus_alvo
    _passo(descricao, abs(delta) / taxa + 0.05 if esperar else 0.0)
    return True


def _elevador(alvo_cm, vel, esperar, descricao):
    alvo = min(max(alvo_cm, 0.0), _C["ELEVADOR_CURSO_CM"])
    if abs(alvo - alvo_cm) > 0.05:
        print("AVISO: %s: %.1f cm fora do curso, vai a %.1f" % (descricao, alvo_cm, alvo))
    graus = _C["ELEVADOR_SOBE"] * alvo * _C["ELEVADOR_GRAUS_CM"]
    return _mover(1, graus, vel, "ELEVADOR", esperar, descricao)


def altura_elevador():
    return _C["ELEVADOR_SOBE"] * _anexos[1] / _C["ELEVADOR_GRAUS_CM"]


def subir(cm=None, vel=NORMAL, forca=_C["ELEVADOR_FORCA"], esperar=True):
    alvo = _C["ELEVADOR_CURSO_CM"] if cm is None else altura_elevador() + cm
    return _elevador(alvo, vel, esperar, "subir(%s)" % ("" if cm is None else "%g" % cm))


def descer(cm=None, vel=NORMAL, forca=_C["ELEVADOR_FORCA"], esperar=True):
    alvo = 0.0 if cm is None else altura_elevador() - cm
    return _elevador(alvo, vel, esperar, "descer(%s)" % ("" if cm is None else "%g" % cm))


def elevador_ir_para(cm, vel=NORMAL, forca=_C["ELEVADOR_FORCA"], esperar=True):
    return _elevador(cm, vel, esperar, "elevador_ir_para(%g)" % cm)


def _garra(abertura_cm, vel, esperar, descricao):
    minimo = _C["GARRA_ABERTA_CM"] - _C["GARRA_CURSO_CM"]
    alvo = min(max(abertura_cm, minimo), _C["GARRA_ABERTA_CM"])
    if abs(alvo - abertura_cm) > 0.05:
        print("AVISO: %s: abertura de %.1f cm fora do curso, vai a %.1f" % (descricao, abertura_cm, alvo))
    graus = _C["GARRA_FECHA"] * (_C["GARRA_ABERTA_CM"] - alvo) * _C["GARRA_GRAUS_CM"]
    return _mover(0, graus, vel, "GARRA", esperar, descricao)


def abertura_garra():
    return _C["GARRA_ABERTA_CM"] - _C["GARRA_FECHA"] * _anexos[0] / _C["GARRA_GRAUS_CM"]


def abrir(cm=None, vel=NORMAL, forca=_C["GARRA_FORCA_ABRIR"], esperar=True):
    if cm is None:
        _anexos[0] = 0.0                # batente = 0
        _passo("abrir()", 0.5 if esperar else 0.0)
        return True
    return _garra(abertura_garra() + cm, vel, esperar, "abrir(%g)" % cm)


def fechar(cm=None, vel=NORMAL, forca=_C["GARRA_FORCA"], esperar=True):
    if cm is None:
        # Sem peça, fecha até o fim do curso; com peça pararia antes.
        _anexos[0] = _C["GARRA_FECHA"] * _C["GARRA_CURSO_CM"] * _C["GARRA_GRAUS_CM"]
        _passo("fechar()", 0.5 if esperar else 0.0)
        return True
    return _garra(abertura_garra() - cm, vel, esperar, "fechar(%g)" % cm)


def apertar(forca=_C["GARRA_FORCA_APERTAR"], vel=LENTO, esperar=True):
    # Sem peça, fecha até o fim do curso; no hub continua empurrando depois.
    _anexos[0] = _C["GARRA_FECHA"] * _C["GARRA_CURSO_CM"] * _C["GARRA_GRAUS_CM"]
    _passo("apertar()", 0.5 if esperar else 0.0)
    return True


def garra_ir_para(cm, vel=NORMAL, forca=_C["GARRA_FORCA"], esperar=True):
    return _garra(cm, vel, esperar, "garra_ir_para(%g)" % cm)


# --- Hub ---------------------------------------------------------------------------
def bipe(freq=600, ms=100):
    pass


def mostrar(valor):
    pass


def luz(c):
    pass


def avisar_maker():
    _passo("avisar_maker()", 0.0)


def esperar(ms=None):
    if ms is None:
        _passo("esperar()", 1.0)
    else:
        _passo("esperar(%d)" % ms, ms / 1000.0)


def esperar_botao():
    _passo("esperar_botao()", 1.0)


def iniciar_partida():
    pass


def tempo_partida():
    return _t


def tempo_restante():
    return _C["PARTIDA_S"] - _t
