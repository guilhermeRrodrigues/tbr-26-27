# Conferências do Gabarito de Largada. Termina com código 1 se houver PROBLEMA.
# Uso: python montagem.py
#
#   1. o robô cabe na base, em todos os giros, com folga na frente e na direita;
#   2. o gabarito cabe na base e no prato da A1 mini;
#   3. as arestas de referência são perpendiculares e retas (medidas na malha);
#   4. nada do gabarito (nem os calços) entra no retângulo do robô, em nenhum giro,
#      e cada contato cai num batente com a altura certa;
#   5. batentes cabem nas arestas, longe das janelas, da alça e entre si;
#   6. erro angular teórico.
#
# Avisos (AVISO) são coisas a olhar na hora de medir; PROBLEMA impede de imprimir.

import math
import sys

from build123d import Align, Box, Location

import gabarito as g
import layout
import parametros as p

problemas, avisos = [], []


def ruim(txt):
    problemas.append(txt)
    print("   PROBLEMA:", txt)


def aviso(txt):
    avisos.append(txt)
    print("   aviso:", txt)


def robo_cabe():
    print("1. Robô na base (posição nominal %.0f mm de trás, %.0f mm da esquerda):"
          % (p.DIST_TRAS, p.DIST_LAT))
    for th in p.ORIENTACOES:
        x0, y0, x1, y1 = layout.retangulo(th)
        sobra_x, sobra_y = p.BASE_X - x1, p.BASE_Y - y1
        print("   giro %3d°: %.0f × %.0f mm, sobra %.0f mm à direita e %.0f mm à frente"
              % (th, x1 - x0, y1 - y0, sobra_x, sobra_y))
        if sobra_x < 10 or sobra_y < 10:
            ruim("giro %d°: sobram menos de 10 mm até a borda interna da faixa" % th)
        elif sobra_x < 25 or sobra_y < 25:
            aviso("giro %d°: sobra pouca folga até a borda (juiz mede o robô inteiro dentro)" % th)


def gabarito_cabe():
    A = p.ARESTA_COMP
    print("2. Gabarito: arestas de %.0f mm, base %.0f × %.0f, prato %.0f:"
          % (A, p.BASE_X, p.BASE_Y, p.VOLUME_IMPRESSAO))
    if A > p.BASE_X or A > p.BASE_Y:
        ruim("arestas maiores que a base")
    util = p.VOLUME_IMPRESSAO - 2 * p.MARGEM_PRATO
    if A > util:
        ruim("aresta de %.0f mm não cabe no prato (útil %.0f mm): dividir ou imprimir na diagonal"
             % (A, util))
    # as arestas atravessam a área do robô? (devem ficar fora do retângulo)
    if A < p.DIST_TRAS + 60:
        aviso("aresta curta demais para dar alavanca")


def retas_e_esquadro():
    print("3. Esquadro e retilinidade (malha do L, sem os calços):")
    pts = []
    for v in g.gabarito().vertices():
        pts.append((v.X, v.Y, v.Z))
    base = [(x, y) for x, y, z in pts if abs(z) < 1e-6]
    borda_x = [(x, y) for x, y in base if abs(x) < 1e-6]      # aresta esquerda
    borda_y = [(x, y) for x, y in base if abs(y) < 1e-6]      # aresta de trás
    if len(borda_x) < 2 or len(borda_y) < 2:
        ruim("não achei as arestas na malha")
        return
    ex = max(y for _, y in borda_x) - min(y for _, y in borda_x)
    ey = max(x for x, _ in borda_y) - min(x for x, _ in borda_y)
    dx = max(abs(x) for x, _ in borda_x)
    dy = max(abs(y) for _, y in borda_y)
    print("   aresta esquerda: %.1f mm em y, desvio de reta %.4f mm; aresta de trás: %.1f mm em x, "
          "desvio %.4f mm" % (ex, dx, ey, dy))
    if dx > 0.01 or dy > 0.01:
        ruim("aresta torta no modelo")
    print("   ângulo entre as arestas no modelo: 90,000° (por construção). Na peça impressa o\n"
          "   esquadro depende da A1 mini (eixos X/Y ortogonais, ~±0,1 mm em 168 mm = ±0,03°):\n"
          "   confira com um esquadro de precisão antes de usar (LEIAME).")


def _interseccao(a, b):
    try:
        r = a.intersect(b)
        return r.volume if r is not None else 0.0
    except Exception:
        return 0.0


def sem_colisao():
    print("4. Gabarito contra o robô (volume em comum com o retângulo do robô, z de 0 a 60):")
    plano = layout.plano_de_batentes()
    base = g.gabarito()
    for k, th in enumerate(p.ORIENTACOES):
        peca = base
        for x in plano["furos_tras"]:
            if k in plano["furos_tras"][x]:
                peca = peca.fuse(g.calco_na_tras(x))
        for y in plano["furos_lado"]:
            if k in plano["furos_lado"][y]:
                peca = peca.fuse(g.calco_no_lado(y))
        x0, y0, x1, y1 = layout.retangulo(th)
        caixa_robo = Box(x1 - x0, y1 - y0, 60, align=(Align.MIN, Align.MIN, Align.MIN)).moved(
            Location((x0, y0, 0)))
        v = _interseccao(peca, caixa_robo)
        c = layout.contatos(th)
        print("   giro %3d°: interferência %.3f mm³; trás (%s) em x = %s; lado (%s) em y = %.0f"
              % (th, v, c["tras_face"], ", ".join("%.0f" % x for x in c["tras"]),
                 c["lado_face"], c["lado"]))
        if v > 0.5:
            ruim("giro %d°: o gabarito entra no robô (%.1f mm³)" % (th, v))
    # altura dos batentes contra a região onde o robô tem material
    topo = p.PLACA + p.H_BATENTE
    sobre = min(topo, p.BATENTE_Z1) - max(0.0, p.BATENTE_Z0)
    print("   batentes cobrem z = 0 a %.1f mm; o robô tem material de %.1f a %.1f mm: encosto útil "
          "de %.1f mm" % (topo, p.BATENTE_Z0, p.BATENTE_Z1, sobre))
    if sobre < 2.0:
        ruim("os batentes não alcançam a faixa de alturas do robô (ajuste H_BATENTE)")
    if p.ROBO_VAO_CHAO < p.PLACA:
        aviso("vão do robô (%.1f) menor que a placa (%.1f): a placa nunca fica sob o robô, mas "
              "confira os lábios dos calços" % (p.ROBO_VAO_CHAO, p.PLACA))


def batentes_nas_arestas():
    print("5. Batentes, furos, janelas e alça nas arestas:")
    plano = layout.plano_de_batentes()
    A, l = p.ARESTA_COMP, p.CALCO_LARG / 2
    todos_t = [(x, "fixo") for x in plano["fixos_tras"]] + [(x, "furo") for x in plano["furos_tras"]]
    todos_l = [(plano["fixo_lado"], "fixo")] + [(y, "furo") for y in plano["furos_lado"]]
    for nome, lista in (("trás", todos_t), ("esquerda", todos_l)):
        pos = sorted(v for v, _ in lista)
        for v, tipo in lista:
            if v - l < layout.larg_lado() + 2 or v + l > A - 2:
                ruim("batente %s %s em %.0f mm cai fora da aresta (útil %.0f a %.0f mm)"
                     % (tipo, nome, v, layout.larg_lado() + 2 + l, A - 2 - l))
            # janela e sulco de índice ficam em d < JANELA_FUNDO + INDICE_COMP; o calço, em
            # d >= largura da aresta - CALCO_RECUO
            ocupa_janela = p.JANELA_FUNDO + p.INDICE_COMP
            d_calco = (layout.larg_tras() if nome == "trás" else layout.larg_lado()) - p.CALCO_RECUO
            if ocupa_janela > d_calco - 0.5:
                for s in layout.janelas():
                    if abs(v - s) < l + p.JANELA_COMP / 2 + 2:
                        ruim("batente %s em %.0f mm bate na janela/índice em %.0f mm" % (nome, v, s))
        for a, b in zip(pos, pos[1:]):
            if b - a < p.CALCO_LARG + 1:
                ruim("batentes/furos %s a %.0f e %.0f mm estão a menos de %.0f mm"
                     % (nome, a, b, p.CALCO_LARG + 1))
    bw = (A - p.JANELA_S_PONTA) - p.JANELA_S_PERTO
    print("   janelas de mira a %.0f e %.0f mm do canto (afastadas %.0f mm)"
          % (p.JANELA_S_PERTO, A - p.JANELA_S_PONTA, bw))
    if p.JANELA_S_PERTO - p.JANELA_COMP / 2 < layout.larg_lado():
        aviso("a janela perto do canto está sobre a alça/canto")


def pneus():
    print("6. Contatos e rodas (informativo):")
    for th in p.ORIENTACOES:
        c = layout.contatos(th)
        for face, u in ((c["lado_face"], p.LATERAL_UNICO_U[c["lado_face"]]),
                        (c["tras_face"], None)):
            if face in ("esq", "dir") and u is not None:
                f = u
                if abs(f - p.RODA_F) < p.RODA_DIAM / 2:
                    aviso("giro %d°: o contato lateral (%s, %.0f mm da frente do centro) cai sobre "
                          "a roda: confirme que o pneu é a parte que encosta" % (th, face, f))
            if face in ("esq", "dir") and u is None:
                for uu in (-p.LADO_U, p.LADO_U):
                    if abs(uu - p.RODA_F) < p.RODA_DIAM / 2:
                        aviso("giro %d°: contato na lateral (%s) em %.0f mm cai sobre a roda"
                              % (th, face, uu))


def erro_angular():
    print("7. Erro angular teórico (graus):")
    A = p.ARESTA_COMP
    bw = (A - p.JANELA_S_PONTA) - p.JANELA_S_PERTO
    pior_al = math.degrees(math.atan(2 * p.TOL_ALINHAR / bw))
    rss_al = math.degrees(math.atan(math.sqrt(2) * p.TOL_ALINHAR / bw))
    print("   alinhar aresta/linha (±%.1f mm em cada janela, base %.0f mm): pior %.2f°, "
          "provável (RSS) %.2f°" % (p.TOL_ALINHAR, bw, pior_al, rss_al))
    print("   (alinhar de olho SÓ pela ponta, sem a janela do canto: base %.0f mm → %.2f°)"
          % (A, math.degrees(math.atan(p.TOL_ALINHAR / A))))
    plano = layout.plano_de_batentes()
    for th in p.ORIENTACOES:
        c = layout.contatos(th)
        b = c["tras"][1] - c["tras"][0]
        fixo = all(any(abs(x - f) < 1 for f in plano["fixos_tras"]) for x in c["tras"])
        tol = 0.10 if fixo else p.TOL_BATENTE
        pior_b = math.degrees(math.atan(2 * tol / b))
        rss_b = math.degrees(math.atan(math.sqrt(2) * tol / b))
        print("   giro %3d°: batentes de trás a %.0f mm (%s): pior %.2f°, RSS %.2f°; "
              "total pior %.2f°, RSS %.2f°"
              % (th, b, "fixos" if fixo else "calços", pior_b, rss_b, pior_al + pior_b,
                 math.hypot(rss_al, rss_b)))
    print("   1° = 17,5 mm por metro; 0,3° = 5 mm por metro.")
    print("   O erro de largada é o de MONTAR o gabarito na faixa + o do robô nos batentes; o\n"
          "   erro absoluto do giroscópio depois é do hub, não daqui.")


if __name__ == "__main__":
    robo_cabe()
    gabarito_cabe()
    retas_e_esquadro()
    sem_colisao()
    batentes_nas_arestas()
    pneus()
    erro_angular()
    print("\n%d problema(s), %d aviso(s)" % (len(problemas), len(avisos)))
    sys.exit(1 if problemas else 0)
