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


# --- Movimento -----------------------------------------------------------------
def andar(cm, vel=NORMAL, parar=True):
    _avancar(cm)
    _passo("andar(%g)" % cm, _t_reta(cm, vel) - (0 if parar else _ASSENTA_S))
    return True


def andar_no_rumo(cm, rumo, vel=NORMAL, parar=True):
    # Muito torto: vira no lugar antes. Pouco torto: corrige andando (aqui
    # aproximado como se já saísse no rumo certo).
    global _rumo
    delta = _normalizar(rumo - _rumo)
    t_giro = _t_giro(delta) if abs(delta) > _C["RUMO_VIRAR_ANTES"] else 0.0
    _rumo += delta
    _avancar(cm)
    _passo("andar_no_rumo(%g, %g)" % (cm, rumo),
           t_giro + _t_reta(cm, vel) - (0 if parar else _ASSENTA_S))
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


def curva(raio_cm, graus, vel=NORMAL):
    global _x, _y, _rumo
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
    _passo("curva(%g, %g)" % (raio_cm, graus), _t_reta(comprimento, vel))
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


# --- Hub ---------------------------------------------------------------------------
def bipe(freq=600, ms=100):
    pass


def mostrar(valor):
    pass


def luz(c):
    pass


def esperar(ms):
    _passo("esperar(%d)" % ms, ms / 1000.0)


def esperar_botao():
    _passo("esperar_botao()", 1.0)


def iniciar_partida():
    pass


def tempo_partida():
    return _t


def tempo_restante():
    return _C["PARTIDA_S"] - _t
