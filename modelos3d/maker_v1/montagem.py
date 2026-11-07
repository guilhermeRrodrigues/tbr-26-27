# Montagem do Dispositivo Maker na bandeja, com as conferências do projeto.
#
# Posiciona as peças impressas e os elementos LEGO (hub, motor, sensor, eixo,
# como caixas) no referencial da bandeja e confere:
#   - interferência entre cada par de peças, com a comporta fechada e aberta;
#   - bandeja: nada invade o fundo nem as paredes;
#   - fora da bandeja: só a rampa (aba e lábio) sai, e nada toca o tapete;
#   - feixe do ultrassônico passa acima da parede sul e alcança o trabalhador;
#   - comporta: fechada segura o Bloco; aberta, o Bloco desce a rampa inteira
#     sem bater em nada; ao sair do lábio, assenta no tapete fora da bandeja;
#   - Bloco entre o fechamento e a abertura da garra do elevador;
#   - peças dentro do volume da impressora.
# Grava stl/montagem.stl (comporta fechada, Bloco carregado) para visualizar.
#
# Uso: python montagem.py   (sai com código 1 se houver problema)

import itertools
import math
import sys

from build123d import Compound

import parametros as p
import base
import bloco
import comporta
import rampa
from geometria import caixa, cilindro_x, exportar, girar, mover

LIMIAR = 0.5  # mm³: abaixo disto é ruído numérico (faces encostadas)
T = p.PAREDE_ESPESSURA


# --- Elementos que não são impressos ------------------------------------------------------

def bandeja():
    fundo = caixa(-T, p.BANDEJA_X + T, -T, p.BANDEJA_Y + T, 0, p.Z_FUNDO)
    paredes = caixa(-T, p.BANDEJA_X + T, -T, p.BANDEJA_Y + T, p.Z_FUNDO - 0.01, p.Z_PAREDE)
    paredes = paredes.cut(caixa(0, p.BANDEJA_X, 0, p.BANDEJA_Y, 0, p.Z_PAREDE + 1))
    return fundo.fuse(paredes)


def tapete_fora():
    # O tapete em volta da bandeja (uma lâmina de 1 mm): nada pode encostar nele.
    t = caixa(-300, p.BANDEJA_X + 300, -300, p.BANDEJA_Y + 300, -1, 0.0)
    return t.cut(caixa(-T, p.BANDEJA_X + T, -T, p.BANDEJA_Y + T, -2, 1))


def motor():
    # Motor médio em pé: corpo de 23,6 (x) × 24 (y) × 72 (z) e o disco virado para
    # a lateral oeste da rampa.
    corpo = caixa(rampa.XM0, rampa.XM_TOPO, rampa.YM0, rampa.YM1, rampa.ZM0, rampa.ZM1)
    disco = cilindro_x(p.MOTOR_DISCO_DIAM / 2, rampa.XM_TOPO - 0.01,
                       rampa.XM_TOPO + p.MOTOR_DISCO_SALIENCIA, rampa.Y_EIXO, rampa.Z_EIXO)
    return corpo.fuse(disco)


def eixo_lego():
    # Eixo LEGO (como cilindro de 4,8): do fim do cubo do dente para dentro do motor.
    comp = p.EIXO_MOTOR_MODULOS * p.PASSO_LEGO
    return cilindro_x(2.4, rampa.X_CUBO[1] - comp, rampa.X_CUBO[1], rampa.Y_EIXO, rampa.Z_EIXO)


def caixa_de(limites):
    return caixa(*limites)


def bloco_em(s, n=None):
    # Bloco apoiado nas nervuras, com a face da frente (sul) a s da ponta.
    n = p.NERVURA_ALTURA if n is None else n
    b = girar(mover(bloco.peca(), y=p.BLOCO / 2), "x", p.ANGULO_RAMPA)
    y, z = rampa.ponto(s, n)
    return mover(b, (rampa.XC0 + rampa.XC1) / 2, y, z)


def bloco_no_tapete():
    # Onde o Bloco assenta ao sair do lábio: logo ao sul da ponta, no tapete.
    return mover(bloco.peca(), (rampa.XC0 + rampa.XC1) / 2,
                 rampa.Y_PONTA - p.BLOCO / 2 - 1.0, 0.0)


def pecas(graus_comporta=0.0):
    return {
        "base": base.peca(),
        "rampa": rampa.peca(),
        "comporta": comporta.montada(graus_comporta),
        "hub": caixa_de(base.HUB),
        "sensor": caixa_de(base.SENSOR),
        "motor": motor(),
    }


# --- Ferramentas de conferência --------------------------------------------------------------

def _vol(a, b):
    try:
        i = a.intersect(b)
    except Exception as e:  # booleano falhou: reportar, não esconder
        return float("nan"), str(e)
    return (i.volume if i is not None else 0.0), None


def _sobrepoe(a, b):
    ba, bb = a.bounding_box(), b.bounding_box()
    return not (ba.max.X < bb.min.X or bb.max.X < ba.min.X or
                ba.max.Y < bb.min.Y or bb.max.Y < ba.min.Y or
                ba.max.Z < bb.min.Z or bb.max.Z < ba.min.Z)


def _bate(a, b):
    if not _sobrepoe(a, b):
        return 0.0, None
    return _vol(a, b)


# Pares que se encostam de propósito (face com face): não contam.
ENCOSTAM = set()


def checar():
    problemas = []
    tray = bandeja()
    fora = tapete_fora()

    # 1. Interferência, comporta fechada e aberta.
    for graus in (0.0, p.GIRO_ABERTURA):
        pos = pecas(graus)
        for (na, a), (nb, b) in itertools.combinations(pos.items(), 2):
            if (na, nb) in ENCOSTAM or (nb, na) in ENCOSTAM:
                continue
            v, erro = _bate(a, b)
            if erro or v > LIMIAR:
                problemas.append("comporta a %.0f°: %s × %s = %s"
                                 % (graus, na, nb, erro or "%.2f mm³" % v))
        # 2 e 3. Bandeja e tapete.
        for nome, peca in pos.items():
            for nz, zona in (("a bandeja", tray), ("o tapete fora da bandeja", fora)):
                v, erro = _bate(peca, zona)
                if erro or v > LIMIAR:
                    problemas.append("comporta a %.0f°: %s invade %s (%s)"
                                     % (graus, nome, nz, erro or "%.2f mm³" % v))
        print("checado: comporta a %.0f°" % graus)

    # Eixo LEGO: alcança o fundo do cubo e entra no disco do motor.
    xe0 = rampa.X_CUBO[1] - p.EIXO_MOTOR_MODULOS * p.PASSO_LEGO
    no_motor = rampa.XM_TOPO + p.MOTOR_DISCO_SALIENCIA - xe0
    print("eixo LEGO de %d módulos: %.1f mm dentro do motor (a partir do topo do disco)"
          % (p.EIXO_MOTOR_MODULOS, no_motor))
    if no_motor < 6.0:
        problemas.append("eixo LEGO entra só %.1f mm no motor" % no_motor)
    if xe0 < rampa.XM0 + 1.0:
        problemas.append("eixo LEGO atravessa o motor inteiro")

    # Só a rampa sai da bandeja (para o sul), e nada desce abaixo do lábio lá fora.
    pos = pecas()
    for nome, peca in pos.items():
        bb = peca.bounding_box()
        if nome == "rampa":
            continue
        if bb.min.X < 0 or bb.max.X > p.BANDEJA_X or bb.min.Y < 0 or bb.max.Y > p.BANDEJA_Y:
            problemas.append("%s sai da bandeja: x %.1f–%.1f, y %.1f–%.1f"
                             % (nome, bb.min.X, bb.max.X, bb.min.Y, bb.max.Y))
    bb = pos["rampa"].bounding_box()
    fora_sul = pos["rampa"].intersect(caixa(-50, p.BANDEJA_X + 50, -100, -T - 0.01, -10, 200))
    z_min_fora = fora_sul.bounding_box().min.Z if fora_sul else float("inf")
    print("rampa: sai %.1f mm além da parede sul; ponto mais baixo lá fora a %.1f do tapete"
          % (-T - bb.min.Y, z_min_fora))
    if z_min_fora < p.LABIO_ALTURA - 0.05:
        problemas.append("rampa desce a %.1f do tapete fora da bandeja" % z_min_fora)
    if bb.min.X < 0 or bb.max.X > p.BANDEJA_X or bb.max.Y > p.BANDEJA_Y:
        problemas.append("rampa sai da bandeja a leste, oeste ou norte")

    # Comprimentos de impressão.
    for nome in ("base", "rampa", "comporta"):
        s = pos[nome].bounding_box().size
        print("%s: %.1f × %.1f × %.1f mm" % (nome, s.X, s.Y, s.Z))
    if base.X1 - base.X0 > p.VOLUME_IMPRESSAO:
        problemas.append("base de %.1f mm não cabe na impressora" % (base.X1 - base.X0))

    # 4. Feixe do ultrassônico.
    meia = math.radians(p.SENSOR_FEIXE)
    for x, z in base.SENSOR_OLHOS:
        d = base.SENSOR_Y_FRENTE + T          # da frente do sensor à face externa da parede
        z_borda = z - d * math.tan(meia)
        print("olho em z = %.1f: raio mais baixo passa a %.1f sobre a parede (topo %.1f)"
              % (z, z_borda, p.Z_PAREDE))
        if z_borda < p.Z_PAREDE + 2.0:
            problemas.append("feixe do olho a z %.1f raspa a parede sul" % z)
    zs = [z for _, z in base.SENSOR_OLHOS]
    if min(zs) > p.TRABALHADOR_ALTURA - 10 or max(zs) < 10:
        problemas.append("olhos fora da altura do trabalhador (%s)" % zs)
    d_min = p.TRABALHADOR_DIST[0] + base.SENSOR_Y_FRENTE + T
    if d_min < p.SENSOR_ALCANCE[0]:
        problemas.append("trabalhador a %.0f mm do sensor: abaixo do alcance mínimo" % d_min)
    print("trabalhador de %.0f a %.0f mm da parede: %.0f a %.0f mm do sensor"
          % (p.TRABALHADOR_DIST[0], p.TRABALHADOR_DIST[1], d_min,
             p.TRABALHADOR_DIST[1] + base.SENSOR_Y_FRENTE + T))

    # 5. Comporta: fechada segura; aberta, o Bloco desce sem bater.
    r = rampa.peca()
    fechada = comporta.montada(0.0)
    aberta = comporta.montada(p.GIRO_ABERTURA)
    carregado = bloco_em(rampa.S_BLOCO_FRENTE)
    for nome, peca in (("rampa", r), ("comporta fechada", fechada)):
        v, erro = _vol(carregado, peca)
        if erro or v > LIMIAR:
            problemas.append("Bloco carregado bate na %s (%s)" % (nome, erro or "%.2f mm³" % v))
    v, _ = _vol(bloco_em(rampa.S_BLOCO_FRENTE - 2.0), fechada)
    print("comporta fechada: Bloco 2 mm abaixo entra %.1f mm³ no dente (tem que segurar)" % v)
    if not v > LIMIAR:
        problemas.append("comporta fechada não segura o Bloco")
    # Giro da comporta, de 15 em 15°: não bate na rampa, na bandeja nem no Bloco
    # carregado (ao abrir, o dente se afasta do Bloco).
    tray_e_bloco = (("rampa", r), ("a bandeja", tray), ("o Bloco carregado", carregado))
    for graus in range(15, int(p.GIRO_ABERTURA), 15):
        c = comporta.montada(float(graus))
        for nome, peca in tray_e_bloco:
            v, erro = _bate(c, peca)
            if erro or v > LIMIAR:
                problemas.append("comporta a %d° bate em %s (%s)"
                                 % (graus, nome, erro or "%.2f mm³" % v))
    print("giro da comporta conferido de 0 a %.0f°" % p.GIRO_ABERTURA)
    s = rampa.S_BLOCO_FRENTE
    passos = 0
    while s > -p.BLOCO * 0.3:          # até o Bloco passar da ponta do lábio
        b = bloco_em(s)
        for nome, peca in (("rampa", r), ("comporta aberta", aberta), ("a bandeja", tray)):
            v, erro = _bate(b, peca)
            if erro or v > LIMIAR:
                problemas.append("Bloco descendo (s = %.0f) bate em %s (%s)"
                                 % (s, nome, erro or "%.2f mm³" % v))
        s -= 4.0
        passos += 1
    print("descida: %d posições do Bloco conferidas, de s = %.1f até a ponta"
          % (passos, rampa.S_BLOCO_FRENTE))
    final = bloco_no_tapete()
    for nome, peca in (("rampa", r), ("a bandeja", tray)):
        v, erro = _bate(final, peca)
        if erro or v > LIMIAR:
            problemas.append("Bloco no tapete bate em %s (%s)" % (nome, erro or "%.2f mm³" % v))
    fb = final.bounding_box()
    print("Bloco no tapete: y %.1f a %.1f (Área Industrial, ao sul da parede em y = %.1f)"
          % (fb.min.Y, fb.max.Y, -T))

    # Motor longe do fundo da bandeja.
    mb = motor().bounding_box()
    print("motor: z %.1f–%.1f (fundo da bandeja a %.1f)" % (mb.min.Z, mb.max.Z, p.Z_FUNDO))

    # 6. Bloco na garra.
    print("Bloco de %.0f mm; garra fecha até %.0f e abre %.0f"
          % (p.BLOCO, p.GARRA_FECHADA, p.GARRA_ABERTA))
    if not p.GARRA_FECHADA < p.BLOCO < p.GARRA_ABERTA:
        problemas.append("Bloco de %.0f mm fora da garra" % p.BLOCO)

    # Grade do sensor no passo LEGO, com os 2 furos de trás do sensor nela.
    xs = sorted({x for x, _ in base.FUROS_PLACA})
    if any(abs((b - a) - p.PASSO_LEGO) > 1e-6 for a, b in zip(xs, xs[1:])):
        problemas.append("grade do sensor fora do passo LEGO")
    grade = {(round(x, 3), round(z, 3)) for x, z in base.FUROS_PLACA}
    for x, z in base.FUROS_SENSOR:
        if (round(x, 3), round(z, 3)) not in grade:
            problemas.append("furo do sensor em (%.1f, %.1f) fora da grade da placa" % (x, z))

    pos["bloco"] = carregado
    pos["eixo"] = eixo_lego()
    print("gravado:", exportar(Compound(list(pos.values())), "montagem"))
    print("gravado:", exportar(tray, "bandeja"))
    return problemas


if __name__ == "__main__":
    problemas = checar()
    if problemas:
        print("\nPROBLEMAS (%d):" % len(problemas))
        for linha in problemas:
            print(" -", linha)
        sys.exit(1)
    print("\nSem problemas: interferência, bandeja, tapete, feixe, comporta e descida conferidos.")
