# Figuras do manual de montagem do Dispositivo Maker v2 (manual/*.png).
#
# Renderiza o próprio modelo (rampa.py, bloco.py, lego.py) passo a passo: as peças
# novas de cada passo em cor, as já montadas apagadas, os pinos em preto e uma seta
# no sentido do encaixe. As peças LEGO ganham detalhes só para a figura (furos nas
# vigas, tela do hub, olhos do sensor, disco do motor).
#
# Renderizador próprio (numpy + PIL): projeção ortográfica, z-buffer, sombreado
# simples e contornos por descontinuidade de peça, profundidade e normal.
#
# Uso: python manual.py   (grava manual/*.png; a página é manual/manual.html)

import math
import os

import numpy as np
from PIL import Image, ImageDraw

import parametros as p
import bloco
import lego
import rampa
from geometria import caixa, cilindro, cilindro_x, cilindro_y, girar, mover

AQUI = os.path.dirname(os.path.abspath(__file__))
PASTA = os.path.join(AQUI, "manual")

FUNDO = (241, 242, 238)
LINHA = (38, 42, 48)
SETA = (214, 74, 40)
COR = {
    "impressa": (226, 112, 62),
    "bloco": (232, 140, 70),
    "viga": (62, 134, 201),
    "eletronica": (222, 224, 228),
    "detalhe": (70, 76, 86),
    "pino": (34, 35, 38),
    "bandeja": (233, 200, 74),
}
APAGADA = 0.62          # quanto a peça já montada se mistura com o fundo

R_PINO = p.PINO_DIAM / 2
MEIA = p.VIGA_SECAO / 2


# --- Peças para a figura --------------------------------------------------------------------

def _cil(eixo, raio, centro, comp):
    x, y, z = centro
    if eixo == "x":
        return cilindro_x(raio, x - comp / 2, x + comp / 2, y, z)
    if eixo == "y":
        return cilindro_y(raio, y - comp / 2, y + comp / 2, x, z)
    return cilindro(raio, z - comp / 2, z + comp / 2, x, y)


def viga(centros, eixo):
    # Viga LEGO com pontas redondas e furos, pelos centros dos furos e o eixo deles.
    c = np.array(centros, float)
    r = None
    for q in c:
        s = _cil(eixo, MEIA, q, p.VIGA_SECAO)
        r = s if r is None else r.fuse(s)
    i = "xyz".index(eixo)
    for a, b in zip(c, c[1:]):
        lo, hi = np.minimum(a, b), np.maximum(a, b)
        lim = []
        for k in range(3):
            if k == i or hi[k] - lo[k] < 1e-6:
                lim += [lo[k] - MEIA, hi[k] + MEIA]
            else:
                lim += [lo[k], hi[k]]
        r = r.fuse(caixa(*lim))
    for q in c:
        r = r.cut(_cil(eixo, 2.45, q, p.VIGA_SECAO + 1))
    return r


def pino(centro, eixo):
    return _cil(eixo, R_PINO, centro, 2 * p.PINO_LADO)


def hub():
    x0, x1, y0, y1, z0, z1 = lego.HX0, lego.HX1, lego.HY0, lego.HY1, lego.HZ0, lego.HZ1
    corpo = caixa(x0, x1, y0, y1, z0, z1)
    xm = (x0 + x1) / 2 - 10
    tela = caixa(xm - 15, xm + 15, lego.HYC - 15, lego.HYC + 15, z1 - 0.01, z1 + 0.6)
    botao = cilindro(5, z1 - 0.01, z1 + 0.8, xm + 27, lego.HYC)
    return corpo, tela.fuse(botao)


def sensor():
    corpo = caixa(lego.SX0, lego.SX1, lego.SY0, lego.SY1, lego.SZ0, lego.SZ1)
    olhos = None
    for x, y, z in lego.OLHOS:
        o = cilindro_y(9.0, y - 1.5, y + 0.1, x, z)
        olhos = o if olhos is None else olhos.fuse(o)
    return corpo, olhos


def motor():
    corpo = caixa(rampa.X_EIXO - p.MOTOR_TRAS, rampa.X_EIXO + p.MOTOR_FRENTE, rampa.S_DISCO,
                  rampa.S_DISCO + p.MOTOR_ALTURA, rampa.H_EIXO - p.MOTOR_LARGURA / 2,
                  rampa.H_EIXO + p.MOTOR_LARGURA / 2)
    disco = cilindro_y(p.MOTOR_DISCO_DIAM / 2, rampa.S_DISCO - p.MOTOR_DISCO_SALIENCIA,
                       rampa.S_DISCO, rampa.X_EIXO, rampa.H_EIXO)
    return rampa.local(corpo), rampa.local(disco)


def _trava_local(graus):
    c = [(rampa.X_EIXO + p.PASSO_LEGO * (i - 1), sum(rampa.S_TRAVA) / 2, rampa.H_EIXO)
         for i in range(p.TRAVA_FUROS)]
    v = mover(viga(c, "y"), x=-rampa.X_EIXO, z=-rampa.H_EIXO)
    return mover(girar(v, "y", -graus), x=rampa.X_EIXO, z=rampa.H_EIXO)


def trava(graus=0.0):
    return rampa.local(_trava_local(graus))


def viga_sensor():
    return viga([(lego.VS_X[0] + MEIA, lego.VS_Y, z) for z in lego.VS_Z], "x")


def viga_encosto():
    return viga([(lego.VE_X[0] + MEIA, y, lego.VE_Z) for y in lego.VE_Y], "x")


def pinos_hub_sensor():
    return [pino((lego.HX0, lego.VS_Y, z), "x") for z in lego.PINOS_HUB_SENSOR]


def pinos_sensor():
    return [pino((lego.HX0, lego.VS_Y, z), "x") for z in lego.PINOS_SENSOR]


def pinos_encosto():
    return [pino((lego.HX1, y, lego.VE_Z), "x") for y in lego.PINOS_ENCOSTO]


def pinos_motor():
    n = rampa.N_PRATELEIRA[1] + 0.15
    return [rampa.local(pino((x, s, n), "z")) for x, s in rampa.FUROS_MOTOR]


def pinos_trava():
    s = rampa.S_DISCO - p.MOTOR_DISCO_SALIENCIA
    return [rampa.local(pino((rampa.X_EIXO + d, s, rampa.H_EIXO), "y")) for d in (-8, 8)]


def local_vetor(x=0.0, s=0.0, n=0.0):
    # Deslocamento no referencial da rampa → bandeja.
    a = math.radians(p.ANGULO_RAMPA)
    return (x, s * math.cos(a) - n * math.sin(a), s * math.sin(a) + n * math.cos(a))


def desloca(peca, v):
    return mover(peca, *v)


# --- Renderizador ---------------------------------------------------------------------------

def _malha(shape, tol):
    v, t = shape.tessellate(tol, 0.3)
    if not t:
        return np.zeros((0, 3, 3))
    V = np.array([(q.X, q.Y, q.Z) for q in v])
    return V[np.array(t)]


def _apaga(cor):
    return tuple(int(c + (f - c) * APAGADA) for c, f in zip(cor, FUNDO))


def render(itens, cam, nome, setas=(), tam=(1400, 860), ss=2, margem=0.07, tol=0.08):
    # itens: (peça, cor, apagada?). cam: direção de onde se olha (do alvo para o olho).
    cam = np.array(cam, float)
    cam /= np.linalg.norm(cam)
    f = -cam
    r = np.cross(f, (0, 0, 1.0))
    r /= np.linalg.norm(r)
    u = np.cross(r, f)
    luz = cam * 0.7 + r * -0.35 + u * 0.6
    luz /= np.linalg.norm(luz)
    tris, cores, ids = [], [], []
    for i, (peca, cor, apagada) in enumerate(itens):
        t = _malha(peca, tol)
        tris.append(t)
        cores.append(np.tile(np.array(_apaga(cor) if apagada else cor, float), (len(t), 1)))
        ids.append(np.full(len(t), i + 1))
    T = np.concatenate(tris)
    C = np.concatenate(cores)
    I = np.concatenate(ids)
    n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    ln = np.linalg.norm(n, axis=1)
    ok = ln > 1e-12
    T, C, I, n = T[ok], C[ok], I[ok], n[ok] / ln[ok][:, None]
    sx, sy, sd = (np.einsum("ijk,k->ij", T, w) for w in (r, u, cam))
    W, H = tam[0] * ss, tam[1] * ss
    lx, ly = sx.max() - sx.min(), sy.max() - sy.min()
    esc = min(W * (1 - 2 * margem) / lx, H * (1 - 2 * margem) / ly)
    ox = (W - lx * esc) / 2 - sx.min() * esc
    oy = (H - ly * esc) / 2 - sy.min() * esc
    px, py = sx * esc + ox, H - (sy * esc + oy)
    zb = np.full((H, W), -1e18)
    ib = np.full((H, W), -1, dtype=np.int64)
    for k in range(len(T)):
        x, y, d = px[k], py[k], sd[k]
        xa, xb = max(int(x.min()), 0), min(int(x.max()) + 1, W - 1)
        ya, yb = max(int(y.min()), 0), min(int(y.max()) + 1, H - 1)
        if xb < xa or yb < ya:
            continue
        den = (y[1] - y[2]) * (x[0] - x[2]) + (x[2] - x[1]) * (y[0] - y[2])
        if abs(den) < 1e-9:
            continue
        X, Y = np.meshgrid(np.arange(xa, xb + 1) + 0.5, np.arange(ya, yb + 1) + 0.5)
        l1 = ((y[1] - y[2]) * (X - x[2]) + (x[2] - x[1]) * (Y - y[2])) / den
        l2 = ((y[2] - y[0]) * (X - x[2]) + (x[0] - x[2]) * (Y - y[2])) / den
        l3 = 1 - l1 - l2
        m = (l1 >= -1e-4) & (l2 >= -1e-4) & (l3 >= -1e-4)
        if not m.any():
            continue
        D = (l1 * d[0] + l2 * d[1] + l3 * d[2])[m]
        Xi, Yi = X[m].astype(int), Y[m].astype(int)
        sel = D > zb[Yi, Xi]
        zb[Yi[sel], Xi[sel]] = D[sel]
        ib[Yi[sel], Xi[sel]] = k
    vis = ib >= 0
    img = np.tile(np.array(FUNDO, float), (H, W, 1))
    nn = n.copy()
    nn[(nn * cam).sum(1) < 0] *= -1                         # normal virada para o olho
    sombra = 0.50 + 0.50 * np.clip((nn * luz).sum(1), 0, 1)
    img[vis] = C[ib[vis]] * sombra[ib[vis]][:, None]
    # Contornos: troca de peça, salto de profundidade ou quina.
    idb = np.where(vis, I[np.maximum(ib, 0)], 0)
    nb = np.zeros((H, W, 3))
    nb[vis] = nn[ib[vis]]
    salto = 0.9                                      # mm
    borda = np.zeros((H, W), bool)
    for dy, dx in ((0, 1), (1, 0), (1, 1), (1, -1)):
        a = (slice(0, H - dy), slice(max(0, -dx), W - max(0, dx)))
        b = (slice(dy, H), slice(max(0, dx), W - max(0, -dx)))
        e = idb[a] != idb[b]
        both = vis[a] & vis[b]
        e |= both & (np.abs(zb[a] - zb[b]) > salto)
        e |= both & ((nb[a] * nb[b]).sum(-1) < math.cos(math.radians(30)))
        borda[a] |= e
    img[borda] = img[borda] * 0.15 + np.array(LINHA) * 0.85
    im = Image.fromarray(np.clip(img, 0, 255).astype("uint8")).resize(tam, Image.LANCZOS)
    # Setas (pontos 3D → tela).
    dr = ImageDraw.Draw(im)
    for a, b in setas:
        pa = np.array(a, float)
        pb = np.array(b, float)
        qa = ((pa * r).sum() * esc + ox) / ss, (H - ((pa * u).sum() * esc + oy)) / ss
        qb = ((pb * r).sum() * esc + ox) / ss, (H - ((pb * u).sum() * esc + oy)) / ss
        dr.line([qa, qb], fill=SETA, width=6)
        ang = math.atan2(qb[1] - qa[1], qb[0] - qa[0])
        L = 22
        pts = [qb, (qb[0] - L * math.cos(ang - 0.45), qb[1] - L * math.sin(ang - 0.45)),
               (qb[0] - L * math.cos(ang + 0.45), qb[1] - L * math.sin(ang + 0.45))]
        dr.polygon(pts, fill=SETA)
    os.makedirs(PASTA, exist_ok=True)
    destino = os.path.join(PASTA, nome + ".png")
    im.save(destino, optimize=True)
    print("gravado:", destino, "(%d triângulos)" % len(T))
    return destino


# --- Passos ---------------------------------------------------------------------------------

def _lista(pecas, cor, apagada):
    return [(q, cor, apagada) for q in pecas]


def modulo_hub(etapa, apagar_ate):
    # Itens do módulo do hub até a etapa (1 viga do sensor, 2 sensor, 3 encosto).
    # As etapas <= apagar_ate saem apagadas.
    corpo, tela = hub()
    a0 = apagar_ate >= 0
    itens = [(corpo, COR["eletronica"], a0), (tela, COR["detalhe"], a0)]
    if etapa >= 1:
        a = apagar_ate >= 1
        itens += [(viga_sensor(), COR["viga"], a)] + _lista(pinos_hub_sensor(), COR["pino"], a)
    if etapa >= 2:
        a = apagar_ate >= 2
        sc, so = sensor()
        itens += [(sc, COR["eletronica"], a), (so, COR["detalhe"], a)]
        itens += _lista(pinos_sensor(), COR["pino"], a)
    if etapa >= 3:
        a = apagar_ate >= 3
        itens += [(viga_encosto(), COR["viga"], a)] + _lista(pinos_encosto(), COR["pino"], a)
    return itens


def modulo_rampa(etapa, apagar_ate, graus=0.0):
    a0 = apagar_ate >= 0
    itens = [(rampa.peca(), COR["impressa"], a0)]
    if etapa >= 4:
        a = apagar_ate >= 4
        mc, md = motor()
        itens += [(mc, COR["eletronica"], a), (md, COR["detalhe"], a)]
        itens += _lista(pinos_motor(), COR["pino"], a)
    if etapa >= 5:
        a = apagar_ate >= 5
        itens += [(trava(graus), COR["viga"], a)] + _lista(pinos_trava(), COR["pino"], a)
    return itens


def explodir(itens, de, v):
    # Desloca os itens a partir do índice `de` (as peças novas) pelo vetor v.
    return itens[:de] + [(desloca(q, v), c, a) for q, c, a in itens[de:]]


def _centro(peca):
    c = peca.bounding_box().center()
    return (c.X, c.Y, c.Z)


def figuras():
    sudoeste = (-1.0, -1.3, 1.0)
    sudeste = (1.0, -1.25, 0.95)
    # Passo 1: viga do sensor na ponta oeste do hub (vem do oeste).
    it = modulo_hub(1, 0)
    corpo, _ = hub()
    v = (-30.0, 0.0, 0.0)
    viga_pos = _centro(viga_sensor())
    it = [it[0], it[1], (desloca(it[2][0], v), it[2][1], False)] + it[3:]
    render(it, sudoeste, "passo1",
           setas=[((viga_pos[0] - 30 - 2, viga_pos[1] - 14, viga_pos[2] - 14),
                   (viga_pos[0] - 9, viga_pos[1] - 14, viga_pos[2] - 14))])
    # Passo 2: sensor na viga, por cima do hub (vem do leste).
    it = modulo_hub(2, 1)
    v = (30.0, 0.0, 0.0)
    sc = _centro(sensor()[0])
    it = it[:5] + explodir(it[5:7], 0, v) + it[7:]
    render(it, sudoeste, "passo2",
           setas=[((sc[0] + 6, sc[1] - 26, sc[2] + 16), (sc[0] - 20, sc[1] - 26, sc[2] + 16))])
    # Passo 3: encosto na ponta leste (vem do leste).
    it = modulo_hub(3, 2)
    v = (30.0, 0.0, 0.0)
    it = it[:-3] + [(desloca(it[-3][0], v), it[-3][1], False)] + it[-2:]
    ec = _centro(viga_encosto())
    render(it, sudeste, "passo3",
           setas=[((ec[0] + 40, ec[1], ec[2] + 16), (ec[0] + 14, ec[1], ec[2] + 16))])
    # Passo 4: motor na prateleira da rampa (desce na normal da placa).
    it = modulo_rampa(4, 0)
    v = local_vetor(n=40)
    it = it[:1] + explodir(it[1:3], 0, v) + it[3:]
    mc = _centro(motor()[0])
    render(it, (-0.9, 0.75, 1.35), "passo4",
           setas=[(tuple(np.add(mc, local_vetor(x=24, n=27))),
                   tuple(np.add(mc, local_vetor(x=24, n=-2))))])
    # Passo 5: trava no disco (vem de baixo da rampa).
    it = modulo_rampa(5, 4)
    v = local_vetor(s=-26)
    it = it[:-3] + [(desloca(it[-3][0], v), it[-3][1], False)] + it[-2:]
    tc = _centro(trava())
    render(it, sudeste, "passo5",
           setas=[(tuple(np.add(tc, local_vetor(x=18, s=-40, n=12))),
                   tuple(np.add(tc, local_vetor(x=18, s=-12, n=12))))])
    # Passo 6: os dois módulos na bandeja (descem).
    tray = montagem_bandeja()
    sobe = (0.0, 0.0, 45.0)
    it = [(tray, COR["bandeja"], False)]
    it += [(desloca(q, sobe), c, True) for q, c, _ in modulo_hub(3, 3)]
    it += [(desloca(q, sobe), c, True) for q, c, _ in modulo_rampa(5, 5)]
    hb = (lego.HX0 + lego.HX1) / 2, lego.HYC, lego.HZ1
    rb = (rampa.XR0 + rampa.XR1) / 2, -6.0, p.Z_PAREDE
    render(it, (-0.55, -1.3, 1.05), "passo6",
           setas=[((hb[0], hb[1], hb[2] + 42), (hb[0], hb[1], hb[2] + 6)),
                  ((rb[0] + 30, rb[1] - 6, rb[2] + 40), (rb[0] + 30, rb[1] - 6, rb[2] + 6))])
    # Passo 7: carregado (trava fechada, Bloco na rampa) e depois de soltar.
    final = [(tray, COR["bandeja"], True)]
    final += [(q, c, True) for q, c, _ in modulo_hub(3, 3)]
    carregado = final + [(q, c, True) for q, c, _ in modulo_rampa(5, 5)]
    b = _bloco_em(rampa.S_FRENTE)
    render(carregado + [(b, COR["bloco"], False)], sudeste, "passo7")
    aberto = final + [(q, c, True) for q, c, _ in modulo_rampa(5, 5, p.GIRO_ABERTURA)][:-3]
    aberto += _lista(pinos_trava(), COR["pino"], True)
    aberto += [(trava(p.GIRO_ABERTURA), COR["viga"], False)]
    caido = mover(bloco.peca(), (rampa.XC0 + rampa.XC1) / 2, rampa.Y_PONTA - p.BLOCO / 2 - 1, 0)
    render(aberto + [(caido, COR["bloco"], False)], sudeste, "funcionando")
    # Capa: tudo montado e carregado, em cor.
    capa = [(tray, COR["bandeja"], False)]
    capa += [(q, c, False) for q, c, _ in modulo_hub(3, -1)]
    capa += [(q, c, False) for q, c, _ in modulo_rampa(5, -1)]
    render(capa + [(b, COR["bloco"], False)], (-0.35, -1.25, 0.85), "capa", tam=(1600, 900))
    pecas()


def _bloco_em(s):
    b = girar(mover(bloco.peca(), y=p.BLOCO / 2), "x", p.ANGULO_RAMPA)
    y, z = rampa.ponto(s, p.NERVURA_ALTURA)
    return mover(b, (rampa.XC0 + rampa.XC1) / 2, y, z)


def montagem_bandeja():
    import montagem
    return montagem.bandeja()


def pecas():
    # Todas as peças lado a lado, em cor.
    it = []
    x = 0.0

    def poe(peca, cor, gap=14.0, y=0.0):
        nonlocal x
        bb = peca.bounding_box()
        q = mover(peca, x - bb.min.X, y - bb.min.Y, -bb.min.Z)
        it.append((q, cor, False))
        x += bb.size.X + gap

    r = girar(rampa.peca(), "z", 90)
    poe(r, COR["impressa"])
    poe(bloco.peca(), COR["bloco"], 24)
    corpo, tela = hub()
    bb = corpo.bounding_box()
    dx = x - bb.min.X
    it.append((mover(corpo, dx, -bb.min.Y, -bb.min.Z), COR["eletronica"], False))
    it.append((mover(tela, dx, -bb.min.Y, -bb.min.Z), COR["detalhe"], False))
    x += bb.size.X + 14
    sc, so = sensor()
    bb = sc.bounding_box()
    dx = x - bb.min.X
    it.append((mover(sc, dx, -bb.min.Y + 8, -bb.min.Z), COR["eletronica"], False))
    it.append((mover(so, dx, -bb.min.Y + 8, -bb.min.Z), COR["detalhe"], False))
    x += bb.size.X + 14
    mc = caixa(0, 72, 0, 24, 0, 23.6)
    md = cilindro(p.MOTOR_DISCO_DIAM / 2, 23.6, 32.0, p.MOTOR_FRENTE, 12)
    it.append((mover(mc, x, 8, 0), COR["eletronica"], False))
    it.append((mover(md, x, 8, 0), COR["detalhe"], False))
    x0 = x
    x += 0
    # Vigas e pinos numa fileira na frente.
    y = -40.0
    xv = 0.0
    for n_furos in (7, 7, 9):
        v = viga([(MEIA + 8 * i, 0, MEIA) for i in range(n_furos)], "z")
        it.append((mover(v, xv, y, 0), COR["viga"], False))
        xv += (n_furos - 1) * 8 + p.VIGA_SECAO + 12
    for i in range(12):
        q = pino((0, 0, 0), "x")
        it.append((mover(q, xv + 8 + (i % 6) * 22, y - 2 + (i // 6) * 10, R_PINO),
                   COR["pino"], False))
    del x0
    render(it, (0.0, -1.1, 1.25), "pecas", tam=(1600, 760), margem=0.04)


if __name__ == "__main__":
    figuras()
