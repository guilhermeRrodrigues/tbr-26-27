# Montagem do Dispositivo Maker v2 na bandeja, com as conferências do projeto.
#
# Posiciona a rampa impressa e o módulo LEGO (lego.py: hub, sensor, vigas, motor e
# trava, como caixas) no referencial da bandeja e confere:
#   - interferência entre cada par de peças, com a trava fechada, a 45° e aberta;
#   - bandeja: nada invade o fundo nem as paredes;
#   - fora da bandeja: só a rampa (aba e lábio) sai, e nada toca o tapete;
#   - feixe do ultrassônico: o cone de ±SENSOR_FEIXE passa livre até a parede sul e
#     por cima dela;
#   - trava: fechada segura o Bloco; girando de 15 em 15° não bate em nada; aberta,
#     o Bloco desce a rampa inteira sem bater e assenta no tapete fora da bandeja;
#   - pinos: cada pino cai num furo das duas peças que ele liga;
#   - Bloco entre o fechamento e a abertura da garra do elevador;
#   - peças impressas dentro do volume da impressora.
# Grava stl/montagem.stl (trava fechada, Bloco carregado) e stl/montagem_aberta.stl.
#
# Uso: python montagem.py   (sai com código 1 se houver problema)

import itertools
import math
import sys

from build123d import Compound, Cone, Location

import parametros as p
import bloco
import lego
import rampa
from geometria import caixa, exportar, girar, mover

LIMIAR = 0.5  # mm³: abaixo disto é ruído numérico (faces encostadas)
T = p.PAREDE_ESPESSURA
XC = (rampa.XC0 + rampa.XC1) / 2


def bandeja():
    fundo = caixa(-T, p.BANDEJA_X + T, -T, p.BANDEJA_Y + T, 0, p.Z_FUNDO)
    paredes = caixa(-T, p.BANDEJA_X + T, -T, p.BANDEJA_Y + T, p.Z_FUNDO - 0.01, p.Z_PAREDE)
    paredes = paredes.cut(caixa(0, p.BANDEJA_X, 0, p.BANDEJA_Y, 0, p.Z_PAREDE + 1))
    return fundo.fuse(paredes)


def tapete_fora():
    # O tapete em volta da bandeja (uma lâmina de 1 mm): nada pode encostar nele.
    t = caixa(-300, p.BANDEJA_X + 300, -300, p.BANDEJA_Y + 300, -1, 0.0)
    return t.cut(caixa(-T, p.BANDEJA_X + T, -T, p.BANDEJA_Y + T, -2, 1))


def bloco_em(s, n=None, envelope=True):
    # Bloco apoiado nas nervuras, com a face da frente (sul) a s da ponta.
    n = p.NERVURA_ALTURA if n is None else n
    b = bloco.envelope() if envelope else bloco.peca()
    b = girar(mover(b, y=p.BLOCO / 2), "x", p.ANGULO_RAMPA)
    y, z = rampa.ponto(s, n)
    return mover(b, XC, y, z)


def bloco_no_tapete():
    # Onde o Bloco assenta ao sair do lábio: logo ao sul da ponta, no tapete.
    return mover(bloco.envelope(), XC, rampa.Y_PONTA - p.BLOCO / 2 - 1.0, 0.0)


def pecas(graus_trava=0.0):
    r = {"rampa": rampa.peca()}
    r.update(lego.pecas(graus_trava))
    return r


def feixe(olho, comprimento):
    # Cone do olho (vértice no olho, eixo para o sul).
    raio = comprimento * math.tan(math.radians(p.SENSOR_FEIXE))
    c = Cone(0.01, raio, comprimento)               # eixo +z, de 0 a comprimento
    c = girar(c, "x", 90)                           # +z → −y
    return c.moved(Location(olho))


# --- Ferramentas de conferência --------------------------------------------------------------

def _vol(a, b):
    try:
        i = a.intersect(b)
    except Exception as e:  # booleano falhou: reportar, não esconder
        return float("nan"), str(e)
    if i is None:
        return 0.0, None
    # O build123d 0.13 pode devolver uma ShapeList em vez de uma peça só.
    pedacos = i if isinstance(i, list) else [i]
    return sum(s.volume for s in pedacos), None


def _sobrepoe(a, b):
    ba, bb = a.bounding_box(), b.bounding_box()
    return not (ba.max.X < bb.min.X or bb.max.X < ba.min.X or
                ba.max.Y < bb.min.Y or bb.max.Y < ba.min.Y or
                ba.max.Z < bb.min.Z or bb.max.Z < ba.min.Z)


def _bate(a, b):
    if not _sobrepoe(a, b):
        return 0.0, None
    return _vol(a, b)


def _confere(problemas, rotulo, a, b):
    v, erro = _bate(a, b)
    if erro or v > LIMIAR:
        problemas.append("%s (%s)" % (rotulo, erro or "%.2f mm³" % v))
    return v


def _perto(a, b, tol=0.05):
    return all(abs(x - y) <= tol for x, y in zip(a, b))


def checar():
    problemas = []
    tray = bandeja()
    fora = tapete_fora()

    # 1. Interferência (trava fechada, a 45° e aberta), bandeja e tapete.
    for graus in (0.0, 45.0, p.GIRO_ABERTURA):
        pos = pecas(graus)
        for (na, a), (nb, b) in itertools.combinations(pos.items(), 2):
            _confere(problemas, "trava a %.0f°: %s × %s" % (graus, na, nb), a, b)
        for nome, peca in pos.items():
            _confere(problemas, "trava a %.0f°: %s invade a bandeja" % (graus, nome), peca, tray)
            _confere(problemas, "trava a %.0f°: %s toca o tapete" % (graus, nome), peca, fora)
        print("checado: trava a %.0f°" % graus)

    # 2. Só a rampa sai da bandeja (para o sul), e nada desce abaixo do lábio lá fora.
    pos = pecas()
    for nome, peca in pos.items():
        if nome == "rampa":
            continue
        bb = peca.bounding_box()
        if bb.min.X < 0 or bb.max.X > p.BANDEJA_X or bb.min.Y < 0 or bb.max.Y > p.BANDEJA_Y:
            problemas.append("%s sai da bandeja: x %.1f–%.1f, y %.1f–%.1f"
                             % (nome, bb.min.X, bb.max.X, bb.min.Y, bb.max.Y))
    r = pos["rampa"]
    bb = r.bounding_box()
    fora_sul = r.intersect(caixa(-50, p.BANDEJA_X + 50, -100, -T - 0.01, -10, 200))
    # O build123d 0.13 pode devolver uma ShapeList em vez de uma peça só.
    pedacos = fora_sul if isinstance(fora_sul, list) else ([fora_sul] if fora_sul else [])
    z_min_fora = min((s.bounding_box().min.Z for s in pedacos), default=float("inf"))
    print("rampa: sai %.1f mm além da parede sul; ponto mais baixo lá fora a %.1f do tapete"
          % (-T - bb.min.Y, z_min_fora))
    if z_min_fora < p.LABIO_ALTURA - 0.05:
        problemas.append("rampa desce a %.1f do tapete fora da bandeja" % z_min_fora)
    if bb.min.X < 0 or bb.max.X > p.BANDEJA_X or bb.max.Y > p.BANDEJA_Y:
        problemas.append("rampa sai da bandeja a leste, oeste ou norte")

    # 3. Feixe do ultrassônico: cone livre até a face de fora da parede sul.
    comp = lego.SY0 + T
    obstaculos = dict(pos)
    del obstaculos["sensor"]
    obstaculos["bandeja"] = tray
    for olho in lego.OLHOS:
        cone = feixe(olho, comp)
        for nome, peca in obstaculos.items():
            _confere(problemas, "feixe do olho em x %.0f bate em %s" % (olho[0], nome), cone, peca)
        z_borda = olho[2] - comp * math.tan(math.radians(p.SENSOR_FEIXE))
        print("olho em x %.1f, z %.1f: raio mais baixo passa a %.1f sobre a parede (topo %.1f)"
              % (olho[0], olho[2], z_borda, p.Z_PAREDE))
        if z_borda < p.Z_PAREDE + 2.0:
            problemas.append("feixe do olho em x %.0f raspa a parede sul" % olho[0])
    z_olho = lego.OLHOS[0][2]
    if not 10 < z_olho < p.TRABALHADOR_ALTURA - 10:
        problemas.append("olhos a %.0f mm: fora da altura do trabalhador" % z_olho)
    d_min = p.TRABALHADOR_DIST[0] + lego.SY0 + T
    if d_min < p.SENSOR_ALCANCE[0]:
        problemas.append("trabalhador a %.0f mm do sensor: abaixo do alcance mínimo" % d_min)
    print("trabalhador de %.0f a %.0f mm da parede: %.0f a %.0f mm do sensor"
          % (p.TRABALHADOR_DIST[0], p.TRABALHADOR_DIST[1], d_min,
             p.TRABALHADOR_DIST[1] + lego.SY0 + T))

    # 4. Trava: fechada segura; girando, não bate; aberta, o Bloco desce sem bater.
    carregado = bloco_em(rampa.S_FRENTE)
    fixas = {k: v for k, v in pos.items() if k != "trava"}
    for nome, peca in list(fixas.items()) + [("trava fechada", pos["trava"])]:
        _confere(problemas, "Bloco carregado bate em %s" % nome, carregado, peca)
    v, _ = _vol(bloco_em(rampa.S_FRENTE - 2.0), pos["trava"])
    print("trava fechada: Bloco 2 mm abaixo entra %.1f mm³ na trava (tem que segurar)" % v)
    if not v > LIMIAR:
        problemas.append("trava fechada não segura o Bloco")
    alvos = dict(fixas)
    del alvos["motor"]                                 # a trava fica pinada no disco
    alvos["bandeja"] = tray
    alvos["Bloco carregado"] = carregado
    for graus in range(15, int(p.GIRO_ABERTURA) + 1, 15):
        tr = lego.pecas(float(graus))["trava"]
        for nome, peca in alvos.items():
            _confere(problemas, "trava a %d° bate em %s" % (graus, nome), tr, peca)
    v, _ = _vol(lego.pecas()["trava"], lego.pecas()["motor"])
    if v > LIMIAR:
        problemas.append("trava entra %.1f mm³ no motor" % v)
    print("giro da trava conferido de 0 a %.0f°" % p.GIRO_ABERTURA)
    aberta = lego.pecas(p.GIRO_ABERTURA)["trava"]
    s = rampa.S_FRENTE
    passos = 0
    while s > -p.BLOCO * 0.3:          # até o Bloco passar da ponta do lábio
        b = bloco_em(s)
        for nome, peca in list(fixas.items()) + [("trava aberta", aberta), ("a bandeja", tray)]:
            _confere(problemas, "Bloco descendo (s = %.0f) bate em %s" % (s, nome), b, peca)
        s -= 4.0
        passos += 1
    print("descida: %d posições do Bloco conferidas, de s = %.1f até a ponta"
          % (passos, rampa.S_FRENTE))
    final = bloco_no_tapete()
    for nome, peca in (("rampa", r), ("a bandeja", tray)):
        _confere(problemas, "Bloco no tapete bate em %s" % nome, final, peca)
    fb = final.bounding_box()
    print("Bloco no tapete: y %.1f a %.1f (Área Industrial, ao sul da parede em y = %.1f)"
          % (fb.min.Y, fb.max.Y, -T))

    # 5. Pinos: cada um num furo das duas peças.
    furos_hub = lego.furos_ponta_hub()
    furos = {
        "hub": furos_hub,
        "viga_sensor": [(lego.HX0, lego.VS_Y, z) for z in lego.VS_Z],
        "viga_encosto": [(lego.HX1, y, lego.VE_Z) for y in lego.VE_Y],
        "sensor": [(lego.SX0, lego.SY1 - p.SENSOR_FURO_PONTA_FUNDO, lego.SZC + d)
                   for d in p.SENSOR_FUROS_PONTA],
    }
    for a, b, ponto, _ in lego.pinos():
        for peca in (a, b):
            if not any(_perto(ponto, f) for f in furos[peca]):
                problemas.append("pino em %s não cai num furo de %s"
                                 % (tuple(round(c, 1) for c in ponto), peca))
    print("pinos conferidos: %d (mais 4 do motor e 2 da trava, na grade por construção)"
          % len(lego.pinos()))
    mb = pos["motor"].bounding_box()
    print("motor: z %.1f–%.1f; topo do hub a %.1f" % (mb.min.Z, mb.max.Z, lego.HZ1))

    # 6. Bloco na garra e peças na impressora.
    print("Bloco de %.0f mm; garra fecha até %.0f e abre %.0f"
          % (p.BLOCO, p.GARRA_FECHADA, p.GARRA_ABERTA))
    if not p.GARRA_FECHADA < p.BLOCO < p.GARRA_ABERTA:
        problemas.append("Bloco de %.0f mm fora da garra" % p.BLOCO)
    s = rampa.impressao().bounding_box().size
    print("rampa na impressão: %.1f × %.1f × %.1f mm" % (s.X, s.Y, s.Z))
    if max(s.X, s.Y, s.Z) > p.VOLUME_IMPRESSAO:
        problemas.append("rampa não cabe na impressora")

    vistas = dict(pos)
    vistas["bloco"] = bloco_em(rampa.S_FRENTE, envelope=False)
    print("gravado:", exportar(Compound(list(vistas.values())), "montagem"))
    abertas = pecas(p.GIRO_ABERTURA)
    abertas["bloco"] = final
    print("gravado:", exportar(Compound(list(abertas.values())), "montagem_aberta"))
    print("gravado:", exportar(tray, "bandeja"))
    return problemas


if __name__ == "__main__":
    problemas = checar()
    if problemas:
        print("\nPROBLEMAS (%d):" % len(problemas))
        for linha in problemas:
            print(" -", linha)
        sys.exit(1)
    print("\nSem problemas: interferência, bandeja, tapete, feixe, trava, descida e pinos "
          "conferidos.")
