"""Cenários de Monte Carlo do gêmeo digital.

Cada cenário sorteia um robô plausível (Parametros.sortear), roda o tbr.py real
e mede contra a VERDADE do mundo (não contra o que o giroscópio acha):

- giro:    sequência de virar_para para rumos sorteados; erro real de rumo
           depois de assentar e tempo de cada giro.
- reta:    andar_no_rumo / andar de 30 a 120 cm; desvio lateral e de rumo.
- largada: partida inteira (várias saídas) com o operador soltando o robô na
           base com erro; mede o erro de pose num ponto de missão a ~1 m.

Uso: python -m ferramentas.simgiro [cenario] [-n N] [-c CHAVE=VALOR ...]
"""

import math
import random
from multiprocessing import Pool

from .carregar import novo_robo
from .mundo import Parametros


def _norm(a):
    while a > 180.0:
        a -= 360.0
    while a <= -180.0:
        a += 360.0
    return a


def _robo(semente, config):
    rng = random.Random(semente)
    p = Parametros().sortear(rng)
    return novo_robo(p, semente=semente, config=config), rng


# ----------------------------------------------------------------------
def giro(semente, config=None, n=6):
    robo, rng = _robo(semente, config)
    t, m = robo.tbr, robo.mundo
    m.avancar(1500)                         # parado na base: bias se assenta
    t.zerar_rumo()
    th0 = m.theta
    erros, tempos, falhas = [], [], 0
    alvo = 0.0
    for _ in range(n):
        delta = rng.choice((1, -1)) * rng.choice((5, 10, 20, 30, 45, 60, 90, 90, 135, 180))
        alvo = _norm(alvo + delta)
        t0 = m.t
        ok = t.virar_para(alvo, rng.choice((t.LENTO, t.NORMAL, t.NORMAL, t.RAPIDO)))
        tempos.append(m.t - t0)
        falhas += 0 if ok else 1
        m.avancar(300)                      # assenta (coast) antes de medir
        erros.append(_norm(m.theta - th0 - alvo))
    return {"erro": erros, "tempo": tempos, "falhas": falhas}


def reta(semente, config=None, n=4):
    robo, rng = _robo(semente, config)
    t, m = robo.tbr, robo.mundo
    m.avancar(1500)
    t.zerar_rumo()
    lat, rum, dist, tempos = [], [], [], []
    extra = {"dist_andar": [], "dist_rumo": [], "lat_andar": [], "lat_rumo": []}
    for _ in range(n):
        # parte de um rumo levemente errado, como depois de um giro real
        t.zerar_rumo()
        x0, y0, th0 = m.x, m.y, m.theta
        m.theta += rng.gauss(0.0, 0.0)      # (perturbação opcional)
        cm = rng.choice((30, 50, 80, 120))
        usar_rumo = rng.random() < 0.5
        t1 = m.t
        if usar_rumo:
            t.andar_no_rumo(cm, 0, rng.choice((t.NORMAL, t.RAPIDO)))
        else:
            t.andar(cm, rng.choice((t.NORMAL, t.RAPIDO)))
        tempos.append(m.t - t1)
        m.avancar(300)
        h = th0 * math.pi / 180.0
        dx, dy = m.x - x0, m.y - y0
        ao_longo = dx * math.cos(h) - dy * math.sin(h)
        lateral = dx * math.sin(h) + dy * math.cos(h)
        lat.append(lateral)
        dist.append(ao_longo - cm * 10.0)
        rum.append(_norm(m.theta - th0))
        qual = "rumo" if usar_rumo else "andar"
        extra["dist_" + qual].append(ao_longo - cm * 10.0)
        extra["lat_" + qual].append(lateral)
    r = {"lateral": lat, "dist": dist, "rumo": rum, "tempo": tempos}
    r.update(extra)
    return r


# ----------------------------------------------------------------------
# Largada: uma partida com várias saídas
# ----------------------------------------------------------------------
SIGMA_OLHO = 1.5            # graus: operador soltando a olho
SIGMA_GABARITO = 0.2        # graus: com o gabarito
SIGMA_POS = 4.0             # mm


def _missao(t, rng):
    """Uma saída genérica: retas e giros por ~15-25 s, depois volta à base."""
    passos = rng.randint(3, 6)
    rumo = 0.0
    for _ in range(passos):
        rumo = _norm(rumo + rng.choice((-90, -45, 45, 90, 30, -30)))
        t.virar_para(rumo)
        t.andar_no_rumo(rng.choice((20, 30, 40)), rumo)
    t.voltar_base()


def largada(semente, config=None, saidas=4, gabarito=False, ancorar=False):
    """Erro real de pose depois de 100 cm em linha reta no começo de cada saída."""
    robo, rng = _robo(semente, config)
    t, m = robo.tbr, robo.mundo
    sigma = SIGMA_GABARITO if gabarito else SIGMA_OLHO
    # Referência da mesa: a direção "leste" verdadeira é 0. A 1ª largada é
    # feita com cuidado (gabarito/minuto de preparação).
    nominais = [0.0] + [rng.choice((0.0, 0.0, 90.0, -90.0)) for _ in range(saidas - 1)]
    m.theta = rng.gauss(0.0, SIGMA_GABARITO if gabarito else SIGMA_OLHO)
    m.avancar(2000)
    erros_rumo, erros_lat = [], []
    for k in range(saidas):
        if k > 0:
            # o operador pega o robô, leva à base e solta mais ou menos virado
            alvo_th = nominais[k] + rng.gauss(0.0, sigma)
            giro = alvo_th - m.theta
            giro = _norm(giro) + rng.choice((0, 360, -360)) * (rng.random() < 0.1)
            m.manusear(giro, rng.uniform(1000, 3000), x=rng.gauss(0, SIGMA_POS),
                       y=rng.gauss(0, SIGMA_POS), theta=alvo_th)
            m.avancar(rng.uniform(1500, 6000))   # parado na base até apertar
        # (o menu faz isso ao apertar)
        t.largar()
        x0, y0 = m.x, m.y
        if ancorar:
            m.faixas = [(x0 + 100.0, x0 + 115.0, 25.0)]
            t.alinhar_na_base()
            x0, y0 = m.x, m.y
            m.faixas = []
        t.andar_no_rumo(100, 0)
        m.avancar(200)
        h = nominais[k] * math.pi / 180.0
        dx, dy = m.x - x0, m.y - y0
        lateral = dx * math.sin(h) + dy * math.cos(h)
        erros_lat.append(lateral)
        erros_rumo.append(_norm(m.theta - nominais[k]))
        _missao(t, rng)
        t.parar_tudo()
    return {"rumo": erros_rumo, "lateral": erros_lat}


CENARIOS = {"giro": giro, "reta": reta, "largada": largada}


# ----------------------------------------------------------------------
def _rodar_um(args):
    nome, semente, config, kw = args
    try:
        return CENARIOS[nome](semente, config, **kw)
    except Exception as e:                       # um robô que quebra é um dado
        return {"excecao": "%s: %s" % (type(e).__name__, e)}


def rodar(nome, n=200, config=None, semente0=1000, processos=None, **kw):
    tarefas = [(nome, semente0 + i, config, kw) for i in range(n)]
    with Pool(processos) as pool:
        res = pool.map(_rodar_um, tarefas, chunksize=4)
    junto = {}
    excecoes = []
    for r in res:
        if "excecao" in r:
            excecoes.append(r["excecao"])
            continue
        for k, v in r.items():
            junto.setdefault(k, []).extend(v if isinstance(v, list) else [v])
    junto["_excecoes"] = excecoes
    return junto


def quantis(v):
    if not v:
        return None
    a = sorted(abs(x) for x in v)
    q = lambda f: a[min(len(a) - 1, int(f * len(a)))]
    media = sum(v) / len(v)
    return {"n": len(a), "media": media, "p50": q(0.50), "p95": q(0.95), "max": a[-1]}


def resumo(junto):
    linhas = []
    for k in sorted(junto):
        if k.startswith("_"):
            continue
        q = quantis(junto[k])
        if q is None:
            continue
        linhas.append("  %-8s n=%-5d média %+8.2f | |x| p50 %7.2f  p95 %7.2f  máx %7.2f"
                      % (k, q["n"], q["media"], q["p50"], q["p95"], q["max"]))
    if junto.get("_excecoes"):
        linhas.append("  EXCEÇÕES: %d (ex.: %s)" % (len(junto["_excecoes"]), junto["_excecoes"][0]))
    return "\n".join(linhas)
