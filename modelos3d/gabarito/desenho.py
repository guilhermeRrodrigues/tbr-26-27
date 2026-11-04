# Vista de cima do gabarito sobre a base (PNG), com o robô nos giros pedidos.
# Uso: python desenho.py [saida.png]   (padrão: gabarito_topo.png)
# Só Pillow: desenha a partir de parametros.py e layout.py (não precisa do build123d).

import math
import sys

from PIL import Image, ImageDraw, ImageFont

import layout
import parametros as p

E = 2.4          # px por mm
MARG = 40


def px(x, y, alt):
    # base: +y para cima na imagem
    return (MARG + x * E, MARG + (alt - y) * E)


def retangulo(d, x0, y0, x1, y1, alt, **kw):
    a, b = px(x0, y1, alt), px(x1, y0, alt)
    d.rectangle([a, b], **kw)


def desenhar(destino):
    W, H = p.BASE_X, p.BASE_Y
    img = Image.new("RGB", (int(W * E + 2 * MARG), int(H * E + 2 * MARG + 150)), (236, 236, 232))
    d = ImageDraw.Draw(img)
    fonte = ImageFont.load_default()
    # tapete cinza, faixa verde, base branca
    f = p.FAIXA_LARG
    retangulo(d, -f, -f, W + f, H + f, H, fill=(24, 74, 44))
    retangulo(d, 0, 0, W, H, H, fill=(252, 252, 250))
    A, wt, wl = p.ARESTA_COMP, layout.larg_tras(), layout.larg_lado()
    cinza, cor = (120, 128, 140), (214, 90, 50)
    # L
    retangulo(d, 0, 0, A, wt, H, fill=cinza, outline=(40, 40, 50))
    retangulo(d, 0, 0, wl, A, H, fill=cinza, outline=(40, 40, 50))
    # nervuras das arestas externas
    retangulo(d, 0, 0, A, p.NERV_LARG, H, fill=(90, 98, 110))
    retangulo(d, 0, 0, p.NERV_LARG, A, H, fill=(90, 98, 110))
    # janelas
    for s in layout.janelas():
        retangulo(d, s - p.JANELA_COMP / 2, 0, s + p.JANELA_COMP / 2, p.JANELA_FUNDO, H,
                  fill=(252, 252, 250), outline=(40, 40, 50))
        retangulo(d, 0, s - p.JANELA_COMP / 2, p.JANELA_FUNDO, s + p.JANELA_COMP / 2, H,
                  fill=(252, 252, 250), outline=(40, 40, 50))
    # alça
    cx, cy = wl / 2, wt / 2
    a, b = px(cx - 11, cy - 11, H), px(cx + 11, cy + 11, H)
    d.line([a, b], fill=(255, 255, 255), width=int(p.ALCA_ESP * E))
    # robô por giro
    pal = {0: (40, 110, 200), 90: (200, 120, 30), 180: (130, 60, 170), 270: (30, 150, 120)}
    plano = layout.plano_de_batentes()
    for th in p.ORIENTACOES:
        x0, y0, x1, y1 = layout.retangulo(th)
        a, b = px(x0, y1, H), px(x1, y0, H)
        d.rectangle([a, b], outline=pal.get(th, (0, 0, 0)), width=3 if th == 0 else 2)
        # seta da frente
        fx, fy = -math.sin(math.radians(th)), math.cos(math.radians(th))
        cxr, cyr = layout.centro(th)
        d.line([px(cxr, cyr, H), px(cxr + fx * 45, cyr + fy * 45, H)], fill=pal.get(th), width=3)
        px0 = px(cxr + fx * 45, cyr + fy * 45, H)
        d.ellipse([px0[0] - 5, px0[1] - 5, px0[0] + 5, px0[1] + 5], fill=pal.get(th))
        k = p.ORIENTACOES.index(th)
        d.text(px(x0 + 4, y1 - 6 - 11 * k, H), "robo %d graus" % th, fill=pal.get(th), font=fonte)
    # batentes fixos
    l = p.CALCO_LARG / 2
    for x in plano["fixos_tras"]:
        retangulo(d, x - l, wt - p.CALCO_RECUO, x + l, p.DIST_TRAS, H, fill=(230, 40, 40), outline=(60, 0, 0))
    y = plano["fixo_lado"]
    retangulo(d, wl - p.CALCO_RECUO, y - l, p.DIST_LAT, y + l, H, fill=(230, 40, 40), outline=(60, 0, 0))
    # furos e calços (contorno) para os outros giros
    for x, ks in plano["furos_tras"].items():
        retangulo(d, x - l, wt - p.CALCO_RECUO, x + l, p.DIST_TRAS, H, outline=(230, 140, 0), width=2)
        c = px(x, wt - p.CALCO_PEG_V, H)
        d.ellipse([c[0] - 4, c[1] - 4, c[0] + 4, c[1] + 4], fill=(0, 0, 0))
    for y, ks in plano["furos_lado"].items():
        retangulo(d, wl - p.CALCO_RECUO, y - l, p.DIST_LAT, y + l, H, outline=(230, 140, 0), width=2)
        c = px(wl - p.CALCO_PEG_V, y, H)
        d.ellipse([c[0] - 4, c[1] - 4, c[0] + 4, c[1] + 4], fill=(0, 0, 0))
    # legenda
    y0 = int(H * E + 2 * MARG) - 10
    linhas = [
        "Gabarito de largada (vista de cima) - base %.0f x %.0f mm, faixa %.0f mm (PROVISORIO)"
        % (W, H, f),
        "Cinza: gabarito em L (arestas de %.0f mm). Vermelho: batentes fixos (giro 0 e 180). "
        % A + "Laranja/preto: furos dos calcos (giros 90 e 270).",
        "Retangulos coloridos: robo %.0f x %.0f mm nos giros %s; a bolinha marca a frente."
        % (p.ROBO_L, p.ROBO_W, ", ".join(str(t) for t in p.ORIENTACOES)),
        "Janelas de mira (entalhes) a %.0f e %.0f mm do canto, nas duas arestas. Alca em pe no canto."
        % layout.janelas(),
    ]
    for i, t in enumerate(linhas):
        d.text((MARG, y0 + i * 16), t, fill=(30, 30, 30), font=fonte)
    img.save(destino)
    return destino


if __name__ == "__main__":
    print(desenhar(sys.argv[1] if len(sys.argv) > 1 else "gabarito_topo.png"))
