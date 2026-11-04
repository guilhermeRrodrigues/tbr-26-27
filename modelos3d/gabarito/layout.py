# Posições dos contatos do robô com o gabarito, para cada giro de largada.
# Python puro (sem build123d), usado por gabarito.py, montagem.py e desenho.py.
#
# O robô fica no canto do L: a face que olha para -y encosta na aresta de TRÁS
# (dois contatos) e a face que olha para -x encosta na aresta ESQUERDA (um contato).

import math

import parametros as p

FACES = ("frente", "tras", "esq", "dir")


def tamanho(theta):
    # (sx, sy): tamanho do retângulo do robô na base, para o giro theta.
    return (p.ROBO_W, p.ROBO_L) if theta % 180 == 0 else (p.ROBO_L, p.ROBO_W)


def centro(theta):
    sx, sy = tamanho(theta)
    return (p.DIST_LAT + sx / 2, p.DIST_TRAS + sy / 2)


def retangulo(theta):
    sx, sy = tamanho(theta)
    return (p.DIST_LAT, p.DIST_TRAS, p.DIST_LAT + sx, p.DIST_TRAS + sy)


def _versores(theta):
    t = math.radians(theta)
    f = (-math.sin(t), math.cos(t))          # frente do robô
    l = (-math.cos(t), -math.sin(t))         # esquerda do robô
    return f, l


def _normal_da_face(face, theta):
    f, l = _versores(theta)
    return {"frente": f, "tras": (-f[0], -f[1]), "esq": l, "dir": (-l[0], -l[1])}[face]


def _meia_face(face):
    # meia extensão do robô na direção da normal da face
    return p.ROBO_L / 2 if face in ("frente", "tras") else p.ROBO_W / 2


def _tangente(face, theta):
    # sentido de u > 0 ao longo da face
    f, l = _versores(theta)
    return l if face in ("frente", "tras") else f


def _arred(v):
    return round(v, 6)


def face_voltada(theta, direcao):
    # face do robô cuja normal aponta para `direcao` ((0,-1) trás da base; (-1,0) esquerda)
    for face in FACES:
        n = _normal_da_face(face, theta)
        if abs(n[0] - direcao[0]) < 1e-6 and abs(n[1] - direcao[1]) < 1e-6:
            return face
    raise ValueError("giro %s não é múltiplo de 90°" % theta)


def _u_dois(face):
    return {"tras": p.TRAS_U, "frente": p.FRENTE_U, "esq": p.LADO_U, "dir": p.LADO_U}[face]


def contatos(theta):
    # Devolve {"tras_face", "lado_face", "tras": [x1, x2], "lado": y}: posições (mm, na base)
    # dos contatos com a aresta de trás (x) e com a aresta esquerda (y). O contato fica
    # sobre a face do robô, em y = DIST_TRAS (trás) ou x = DIST_LAT (esquerda).
    cx, cy = centro(theta)
    ft = face_voltada(theta, (0, -1))
    fl = face_voltada(theta, (-1, 0))
    t = _tangente(ft, theta)
    u2 = _u_dois(ft)
    xs = sorted(_arred(cx + u * t[0]) for u in (-u2, u2))
    tl = _tangente(fl, theta)
    y = _arred(cy + p.LATERAL_UNICO_U[fl] * tl[1])
    return {"tras_face": ft, "lado_face": fl, "tras": xs, "lado": y}


def aresta_faixa():
    # (x0, x1) da aresta de trás e (y0, y1) da esquerda, só para conferência
    return (0.0, p.ARESTA_COMP)


def larg_tras():
    return p.DIST_TRAS - p.FOLGA_PLACA


def larg_lado():
    return p.DIST_LAT - p.FOLGA_PLACA


def janelas():
    # centros das janelas de mira, medidos ao longo de cada aresta a partir do canto
    return (p.JANELA_S_PERTO, p.ARESTA_COMP - p.JANELA_S_PONTA)


def plano_de_batentes():
    # Decide quais batentes são FIXOS (giro 0) e quais furos recebem calços (outros giros).
    # Devolve dict com:
    #   fixos_tras: [x...], fixo_lado: y
    #   furos_tras: {x: [indices de giro]}, furos_lado: {y: [indices de giro]}
    # Contatos de outros giros a menos de 1 mm de um batente já existente o reutilizam.
    c0 = contatos(0)
    fixos_tras = list(c0["tras"])
    fixo_lado = c0["lado"]
    furos_tras, furos_lado = {}, {}
    for k, th in enumerate(p.ORIENTACOES):
        if th == 0:
            continue
        c = contatos(th)
        for x in c["tras"]:
            if any(abs(x - f) < 1.0 for f in fixos_tras):
                continue
            chave = next((a for a in furos_tras if abs(a - x) < 1.0), x)
            furos_tras.setdefault(chave, []).append(k)
        y = c["lado"]
        if abs(y - fixo_lado) >= 1.0:
            chave = next((a for a in furos_lado if abs(a - y) < 1.0), y)
            furos_lado.setdefault(chave, []).append(k)
    return {"fixos_tras": fixos_tras, "fixo_lado": fixo_lado,
            "furos_tras": furos_tras, "furos_lado": furos_lado}
