# Vetoriza o logo da Overclock (chave inglesa com raios) para o baixo-relevo do Bloco.
#
#   python logo.py [png] [pasta_previa]
#
# Lê o PNG (RGBA, fundo transparente) uma vez e grava logo_overclock.json, que o
# bloco.py usa: assim o gerar.py não depende do arquivo original. O FDM de uma cor
# só lê o desenho por sombra, então o logo vira 2 camadas:
#   "linhas": o contorno escuro da chave, o furo do sextavado, as sombras ciano
#             dos raios e uma borda fina em volta dos raios brancos;
#   "corpo":  o corpo da chave (cinza e ciano dentro do contorno).
# Os raios brancos e o fundo ficam no nível da face.
#
# Coordenadas no JSON: mm, centradas, y para cima, cabendo em LOGO_LADO.
# Cada camada é uma lista de polígonos [contorno, furo, furo, ...].

import json
import os
import sys
from collections import deque

import numpy as np
from PIL import Image

import parametros as p

AQUI = os.path.dirname(os.path.abspath(__file__))
ORIGEM = os.path.expanduser("~/Downloads/overclock logo1.png")
DESTINO = os.path.join(AQUI, "logo_overclock.json")
MM_PX = 0.05                       # resolução da vetorização
BORDA_RAIO = 0.45                  # borda rebaixada em volta dos raios brancos (mm)
MENOR_ILHA = 0.8                   # descarta manchas menores que isto (mm, lado do quadrado)
TOLERANCIA = 0.06                  # simplificação dos contornos (mm)


def _classes(caminho):
    im = Image.open(caminho).convert("RGBA")
    a = np.array(im).astype(int)
    opaco = a[..., 3] > 128
    ys, xs = np.where(opaco)
    a = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    opaco = opaco[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    sat = np.maximum(np.maximum(r, g), b) - np.minimum(np.minimum(r, g), b)
    lum = (r + g + b) / 3
    escuro = opaco & (lum < 75)
    branco = opaco & (lum > 215) & (sat < 45) & ~escuro
    ciano = opaco & (sat > 60) & ~escuro & ~branco
    cinza = opaco & ~escuro & ~branco & ~ciano
    return {"escuro": escuro, "branco": branco, "ciano": ciano, "cinza": cinza}


def _reduzir(mascara, px):
    # Reamostra para px de largura (média por área) e binariza em 0,5.
    h, w = mascara.shape
    alvo = (px, max(1, int(round(h * px / w))))
    im = Image.fromarray((mascara * 255).astype("uint8")).resize(alvo, Image.BOX)
    return np.array(im) > 127


def _dilatar(m, r):
    out = m.copy()
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy <= r * r:
                out |= np.roll(np.roll(m, dy, 0), dx, 1)
    return out


def _componentes(m):
    # Rótulos de 4-vizinhança (BFS), sem scipy.
    rot = np.zeros(m.shape, int)
    n = 0
    h, w = m.shape
    for y0, x0 in zip(*np.where(m)):
        if rot[y0, x0]:
            continue
        n += 1
        fila = deque([(y0, x0)])
        rot[y0, x0] = n
        while fila:
            y, x = fila.popleft()
            for yy, xx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                if 0 <= yy < h and 0 <= xx < w and m[yy, xx] and not rot[yy, xx]:
                    rot[yy, xx] = n
                    fila.append((yy, xx))
    return rot, n


def _limpar(m, menor_px):
    # Tira manchas pequenas e furos pequenos.
    for alvo in (True, False):
        rot, n = _componentes(m if alvo else ~m)
        if n:
            area = np.bincount(rot.ravel())
            for i in range(1, n + 1):
                if area[i] < menor_px:
                    m = m & ~(rot == i) if alvo else m | (rot == i)
    return m


def _simplificar(pts, tol):
    # Douglas–Peucker num contorno fechado.
    def dp(seg):
        if len(seg) < 3:
            return seg
        a, b = seg[0], seg[-1]
        ab = b - a
        n = np.hypot(*ab)
        if n < 1e-9:
            d = np.hypot(*(seg - a).T)
        else:
            d = np.abs(ab[0] * (seg[:, 1] - a[1]) - ab[1] * (seg[:, 0] - a[0])) / n
        i = int(np.argmax(d))
        if d[i] <= tol:
            return np.array([a, b])
        return np.vstack([dp(seg[:i + 1])[:-1], dp(seg[i:])])
    meio = len(pts) // 2
    return np.vstack([dp(pts[:meio + 1])[:-1], dp(pts[meio:])[:-1]])


def _area(pts):
    x, y = pts[:, 0], pts[:, 1]
    return 0.5 * float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))


def _poligonos(m, escala, centro):
    # Contornos da máscara (matplotlib) agrupados em [contorno, furos...].
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.path import Path
    pad = np.pad(m.astype(float), 1)
    cs = plt.contour(pad, levels=[0.5])
    aneis = []
    for seg in cs.allsegs[0]:
        if len(seg) < 4:
            continue
        pts = (seg - 1.0) * escala          # px → mm
        pts[:, 1] = -pts[:, 1]               # imagem tem y para baixo
        pts = pts - centro
        pts = _simplificar(pts, TOLERANCIA)
        if len(pts) >= 3 and abs(_area(pts)) > (MENOR_ILHA / 2) ** 2:
            aneis.append(pts)
    plt.close("all")
    # Profundidade de aninhamento: par = contorno, ímpar = furo.
    caminhos = [Path(a) for a in aneis]
    prof = []
    for i, a in enumerate(aneis):
        pt = a[0]
        prof.append(sum(1 for j, c in enumerate(caminhos) if j != i and c.contains_point(pt)))
    polis = []
    for i, a in enumerate(aneis):
        if prof[i] % 2:
            continue
        furos = [aneis[j] for j in range(len(aneis)) if prof[j] == prof[i] + 1
                 and caminhos[i].contains_point(aneis[j][0])]
        polis.append([a.round(3).tolist()] + [f.round(3).tolist() for f in furos])
    return polis


def vetorizar(origem=ORIGEM, lado=None):
    lado = lado or p.LOGO_LADO
    c = _classes(origem)
    h, w = c["escuro"].shape
    escala_img = lado / max(h, w)                    # mm por pixel do original
    px = int(round(w * escala_img / MM_PX))
    m = {k: _reduzir(v, px) for k, v in c.items()}
    menor = int((MENOR_ILHA / MM_PX) ** 2)
    # Corpo da chave: o maior componente de cinza+ciano (as sombras dos raios são finas
    # e ficam separadas do corpo pelo contorno escuro).
    cc = m["cinza"] | m["ciano"]
    rot, n = _componentes(cc)
    area = np.bincount(rot.ravel())
    area[0] = 0
    corpo = rot == int(np.argmax(area))
    corpo = _limpar(corpo, menor)
    sombras = cc & ~corpo
    borda = _dilatar(m["branco"], int(round(BORDA_RAIO / MM_PX))) & ~m["branco"] & ~corpo
    linhas = _limpar((m["escuro"] | sombras | borda) & ~m["branco"], menor)
    corpo = corpo & ~linhas
    hh, ww = linhas.shape
    centro = np.array([ww * MM_PX / 2, -hh * MM_PX / 2])
    dados = {"lado": lado, "largura": ww * MM_PX, "altura": hh * MM_PX,
             "linhas": _poligonos(linhas, MM_PX, centro),
             "corpo": _poligonos(corpo, MM_PX, centro)}
    return dados, {"linhas": linhas, "corpo": corpo, "branco": m["branco"]}


def previa(mascaras, destino):
    # Face do Bloco vista de frente: claro = face, médio = corpo, escuro = linhas.
    img = np.full(mascaras["linhas"].shape, 230, "uint8")
    img[mascaras["corpo"]] = 150
    img[mascaras["linhas"]] = 40
    Image.fromarray(img).save(destino)
    return destino


def carregar():
    with open(DESTINO) as f:
        return json.load(f)


if __name__ == "__main__":
    origem = sys.argv[1] if len(sys.argv) > 1 else ORIGEM
    dados, masc = vetorizar(origem)
    with open(DESTINO, "w") as f:
        json.dump(dados, f, separators=(",", ":"))
    n = {k: (len(dados[k]), sum(len(a) for pol in dados[k] for a in pol))
         for k in ("linhas", "corpo")}
    print("logo %.1f × %.1f mm; linhas: %d polígonos (%d pontos); corpo: %d (%d)"
          % (dados["largura"], dados["altura"], n["linhas"][0], n["linhas"][1],
             n["corpo"][0], n["corpo"][1]))
    print("gravado:", DESTINO)
    if len(sys.argv) > 2:
        print("prévia:", previa(masc, os.path.join(sys.argv[2], "logo_previa.png")))
