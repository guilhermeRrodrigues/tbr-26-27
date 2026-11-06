"""Regressão do gêmeo digital (ferramentas/simgiro): o hub/tbr.py REAL rodando
contra robôs sorteados. Os limites são os números do Monte Carlo da madrugada
de 04/11 com folga (ver docs/giroscopio.md); se um deles quebrar, alguma
mudança no tbr.py piorou o giro, a reta ou a largada.

Roda em série (sem Pool) e com poucos robôs para caber no pytest.
"""

import sys

from ferramentas.simgiro import cenarios
from ferramentas.simgiro.carregar import novo_robo
from ferramentas.simgiro.mundo import Parametros


def _juntar(nome, n, config=None, semente0=5000, **kw):
    junto = {}
    for i in range(n):
        r = cenarios.CENARIOS[nome](semente0 + i, config, **kw)
        for k, v in r.items():
            junto.setdefault(k, []).extend(v if isinstance(v, list) else [v])
    return junto


def _p95(v):
    return cenarios.quantis(v)["p95"]


def _norm(a):
    return cenarios._norm(a)


# ----------------------------------------------------------------------
def teste_carregar_nao_suja_sys_modules():
    antes = {k: sys.modules.get(k) for k in ("pybricks", "pybricks.hubs", "tbr", "config", "calibracao")}
    robo = novo_robo(Parametros(), semente=1)
    robo.tbr.zerar_rumo()
    robo.tbr.girar(90)
    depois = {k: sys.modules.get(k) for k in antes}
    assert antes == depois


def teste_dois_robos_independentes():
    a = novo_robo(Parametros(), semente=1, config={"GIRO_TOL_FINAL": 0.5})
    b = novo_robo(Parametros(), semente=2, config={"GIRO_TOL_FINAL": 2.0})
    assert a.config.GIRO_TOL_FINAL == 0.5 and b.config.GIRO_TOL_FINAL == 2.0
    assert a.tbr is not b.tbr


def teste_giro_preciso():
    r = _juntar("giro", 60)
    assert r["falhas"] == [0] * 60
    assert _p95(r["erro"]) < 0.9, cenarios.quantis(r["erro"])
    assert max(abs(e) for e in r["erro"]) < 2.0, cenarios.quantis(r["erro"])


def teste_giro_de_180_gira_de_verdade():
    # O bug antigo: depois de andar no rumo 180, virar_para(0) via erro de
    # -179,99 (ou +180) e parava sem girar.
    for semente in range(20):
        robo = novo_robo(Parametros(), semente=semente)
        t, m = robo.tbr, robo.mundo
        m.avancar(1500)
        t.zerar_rumo()
        for alvo in (180, 0, -180, 0, 180, -90, 90):
            t.virar_para(alvo)
            m.avancar(300)
            assert abs(_norm(m.theta - alvo)) < 2.0, (semente, alvo, m.theta)
        t.andar_no_rumo(20, 180)
        t.virar_para(0)
        m.avancar(300)
        assert abs(_norm(m.theta)) < 2.0, (semente, m.theta)


def teste_reta_sem_vies():
    r = _juntar("reta", 40)
    media = sum(r["dist"]) / len(r["dist"])
    assert abs(media) < 3.0, cenarios.quantis(r["dist"])
    assert _p95(r["lateral"]) < 3.0, cenarios.quantis(r["lateral"])
    assert max(abs(x) for x in r["lateral"]) < 8.0, cenarios.quantis(r["lateral"])


def teste_alinhar_na_base():
    r = _juntar("largada", 25, ancorar=True, saidas=3)
    assert _p95(r["rumo"]) < 0.8, cenarios.quantis(r["rumo"])


def teste_largar_compensa_o_olho():
    # Com a mão a olho (sigma 1,5°), compensar pelo giroscópio tem de ser
    # melhor que confiar na mão.
    cfg = {"LARGADA_SIGMA_MAO": 1.5}
    com = _juntar("largada", 30, config=cfg)
    sem = _juntar("largada", 30, config=dict(cfg, LARGADA_COMPENSADA=False))
    assert _p95(com["rumo"][1:]) < _p95(sem["rumo"][1:]), (
        cenarios.quantis(com["rumo"]), cenarios.quantis(sem["rumo"]))


def teste_largar_sinal_e_limite():
    robo = novo_robo(Parametros(), semente=3, config={"LARGADA_SIGMA_MAO": 1.5})
    t, m = robo.tbr, robo.mundo
    m.avancar(2000)
    t.largar()                              # 1ª: fixa a mesa
    assert abs(t.rumo_mesa()) < 0.5
    m.manusear(3.0, 1500, theta=3.0)        # solto 3° anti-horário (+)
    m.avancar(2000)
    t.largar()
    r0 = t.rumo()
    # sabe que está torto, com o sinal certo; a 1ª referência também tem o
    # erro da mão, então a fusão fica no meio do caminho (~1,5°)
    assert 1.0 < r0 < 3.5, r0
    t.virar_para(0)
    m.avancar(300)
    assert abs(m.theta - (3.0 - r0)) < 0.7, (m.theta, r0)
    m.manusear(20.0, 1500, theta=20.0)      # torto demais: não compensa
    m.avancar(2000)
    t.largar()
    assert abs(t.rumo()) < 0.01


def teste_chaves_de_volta_rodam():
    # Desligar tudo volta ao comportamento antigo; tem de rodar sem exceção.
    velho = {"GIRO_FINO": False, "ANDAR_NO_RUMO": False, "RETA_PREVE_FREIO": False,
             "TOLERANCIAS_DB": False, "CORRECOES_RUMO": False,
             "EMENDA_SEM_AJUSTE": False,
             "LARGADA_COMPENSADA": False, "RUMO_VIRAR_ANTES": 20.0}
    for nome in ("giro", "reta", "largada"):
        r = cenarios.CENARIOS[nome](7, velho)
        assert r


def _x_apos_curva_emendada(emenda):
    # FINO_PARADO 0: o ajuste espera o teto de 250 ms, o pior caso da mesa.
    r = novo_robo(Parametros(), semente=3,
                  config={"EMENDA_SEM_AJUSTE": emenda, "FINO_PARADO": 0.0})
    r.mundo.avancar(1500)
    r.tbr.zerar_rumo()
    r.tbr.andar_no_rumo(20, 0, parar=False)
    r.tbr.curva(30, -25)
    return r.tbr.posicao()[0]


def teste_chave_da_emenda_devolve_o_trecho_reto_antes_da_curva():
    # Com a chave ligada a curva sai no ponto. Desligada, volta o método de
    # antes de 05/11: o ajuste de rumo espera andando e a curva sai depois.
    assert _x_apos_curva_emendada(False) - _x_apos_curva_emendada(True) > 3.0


def teste_sem_creep_giro_pequeno_ainda_gira():
    # Abaixo de GIRO_GROSSO_MIN só o creep girava: sem ele o robô ficava parado
    # e devolvia True como se tivesse virado.
    for fino in (True, False):
        r = novo_robo(Parametros(), semente=3, config={"CREEP": False, "GIRO_FINO": fino})
        r.mundo.avancar(1500)
        r.tbr.zerar_rumo()
        th0 = r.mundo.theta
        assert r.tbr.virar_para(6)
        r.mundo.avancar(300)
        assert r.mundo.theta - th0 > 3.0, r.mundo.theta - th0


def teste_usar_creep_vale_para_o_rumo_parado():
    # Desligado, a reta não gasta tempo alinhando: nem _creep nem _fino rodam.
    r = novo_robo(Parametros(), semente=3)
    assert r.config.CREEP is True
    r.tbr.usar_creep(False)
    assert r.config.CREEP is False
    chamou = []
    r.tbr._fino = lambda *a, **k: chamou.append(a) or True
    r.mundo.avancar(1500)
    r.tbr.zerar_rumo()
    r.tbr.virar_para(45)
    r.tbr.andar(20)
    assert not chamou


def teste_virar_ate_travar_fecha_no_alvo():
    # Sem nada para travar, tem de terminar no rumo pedido (antes deslizava
    # ~5 graus em coast além do alvo).
    for semente in range(5):
        robo = novo_robo(Parametros(), semente=semente)
        t, m = robo.tbr, robo.mundo
        m.avancar(1500)
        t.zerar_rumo()
        for alvo in (90, 0, -90, 180):
            assert t.virar_ate_travar(alvo) is False
            m.avancar(300)
            assert abs(_norm(m.theta - alvo)) < 1.0, (semente, alvo, m.theta)


# ----------------------------------------------------------------------
def _robo_com_central(*apertos):
    """Robô cujo botão central fica apertado nos intervalos (ini, fim), em ms."""
    r = novo_robo(Parametros(), semente=4)
    r.mundo.avancar(1500)
    t0 = r.mundo.t
    central = {r.tbr.Button.CENTER}
    original = r.mundo.esperar_usuario

    def esperar_usuario(ms):
        original(ms)
        t = r.mundo.t - t0
        r.mundo.botoes = central if any(a <= t < b for a, b in apertos) else set()

    r.mundo.esperar_usuario = esperar_usuario
    r.mundo.botoes = central if any(a <= 0 < b for a, b in apertos) else set()
    return r, lambda: r.mundo.t - t0


def teste_esperar_continua_com_toque_rapido():
    r, agora = _robo_com_central((300, 340))
    r.tbr.esperar()
    assert 340 <= agora() < 460


def teste_esperar_ignora_o_dedo_que_ja_estava_no_botao():
    r, agora = _robo_com_central((0, 200), (600, 640))
    r.tbr.esperar()
    assert agora() >= 640


def teste_esperar_nao_aborta_com_repique_nem_com_toque_longo():
    # Toque longo, repique ao soltar e a pausa logo depois: nada de abortar.
    # O repique dura mais que o laço de 10 ms, senão cairia entre duas leituras.
    r, agora = _robo_com_central((100, 900), (915, 935))
    r.tbr.esperar()
    assert agora() >= 935
    r.tbr.esperar(100)


def teste_central_volta_a_abortar_depois_do_gatilho():
    r, _ = _robo_com_central((100, 150), (400, 450))
    r.tbr.esperar()
    try:
        r.tbr.esperar(1000)
    except r.tbr.SaidaAbortada:
        return
    assert False, "o central devia abortar depois do gatilho"
