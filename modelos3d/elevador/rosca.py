# Geometria comum do elevador: rosca do fuso, furos e engrenagens.
#
# Tudo devolve sólidos build123d em mm, no referencial local da peça.
# Booleanos sempre com .fuse()/.cut() explícitos (a união dentro de BuildPart
# descartava material na rosca).

import math

from build123d import (
    Align,
    Box,
    Cylinder,
    Face,
    Location,
    Solid,
    Spline,
    Vector,
    Wire,
    extrude,
)

import parametros as p

PONTOS_SECAO = 180  # resolução da seção da rosca


# --- Rosca trapezoidal de várias entradas -------------------------------------

def _raio_secao(theta, rr, re, a, c, fase):
    # Raio da seção da rosca no ângulo theta.
    # Superfície: r = g((z + fase - avanço·theta/2π) mod passo), dente centrado
    # em 0, crista de meia largura c e flanco até meia largura a na raiz.
    passo = p.PASSO_FUSO
    z = (fase - p.AVANCO_FUSO * theta / (2 * math.pi)) % passo
    dz = abs(((z + passo / 2) % passo) - passo / 2)
    if dz <= c:
        return re
    if dz <= a:
        return re - (re - rr) * (dz - c) / (a - c)
    return rr


def rosca_solida(rr, re, a, c, altura, fase=0.0):
    # Seção com os dentes extrudada com rotação (360° a cada avanço).
    # 'fase' (mm) desloca a rosca em z: uma peça que começa na altura global
    # z0 casa com o fuso (que começa em Z_HASTE) se fase = z0 - Z_HASTE.
    pontos = []
    for i in range(PONTOS_SECAO):
        theta = 2 * math.pi * i / PONTOS_SECAO
        r = _raio_secao(theta, rr, re, a, c, fase)
        pontos.append(Vector(r * math.cos(theta), r * math.sin(theta), 0))
    contorno = Wire([Spline(*pontos, periodic=True)])
    angulo = 360.0 * altura / p.AVANCO_FUSO
    return Solid.extrude_linear_with_rotation(
        contorno, Vector(0, 0, 0), Vector(0, 0, altura), angulo
    )


def fuso_solido(altura, fase=0.0):
    # Rosca externa do fuso (cotas do teste validado).
    return rosca_solida(
        p.DIAM_RAIZ_FUSO / 2, p.DIAM_FUSO / 2,
        p.MEIA_LARGURA_DENTE_FUSO, p.MEIA_CRISTA_FUSO, altura, fase,
    )


def porca_cavidade(altura, fase=0.0):
    # Negativo da rosca com folga só radial (folga em z sobreporia as entradas).
    f = p.FOLGA_ROSCA
    return rosca_solida(
        p.DIAM_RAIZ_FUSO / 2 + f, p.DIAM_FUSO / 2 + f,
        p.MEIA_LARGURA_DENTE_FUSO, p.MEIA_CRISTA_FUSO, altura, fase,
    )


# --- Prismas simples ----------------------------------------------------------

def caixa(x0, x1, y0, y1, z0, z1):
    # Caixa alinhada aos eixos, dada pelos limites.
    return Box(
        x1 - x0, y1 - y0, z1 - z0,
        align=(Align.MIN, Align.MIN, Align.MIN),
    ).moved(Location((x0, y0, z0)))


def cilindro(raio, z0, z1, x=0.0, y=0.0):
    return Cylinder(
        raio, z1 - z0, align=(Align.CENTER, Align.CENTER, Align.MIN)
    ).moved(Location((x, y, z0)))


def cilindro_y(raio, y0, y1, x=0.0, z=0.0):
    # Cilindro deitado, eixo em y (furo de pino horizontal, por exemplo).
    from build123d import Axis
    c = Cylinder(raio, y1 - y0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return c.rotate(Axis.X, -90).moved(Location((x, y0, z)))


def cilindro_x(raio, x0, x1, y=0.0, z=0.0):
    # Cilindro deitado, eixo em x.
    from build123d import Axis
    c = Cylinder(raio, x1 - x0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return c.rotate(Axis.Y, 90).moved(Location((x0, y, z)))


def prisma(pontos_xy, z0, z1):
    # Extrusão vertical de um polígono no plano XY.
    # Direção explícita: sem ela, um polígono em sentido horário extruda para −z.
    face = Face(Wire.make_polygon([Vector(x, y, z0) for x, y in pontos_xy], close=True))
    return extrude(face, amount=z1 - z0, dir=(0, 0, 1))


def prisma_yz(perfil_yz, x0, x1):
    # Extrusão de um polígono do plano YZ ao longo de x, de x0 a x1.
    face = Face(Wire.make_polygon([Vector(x0, y, z) for y, z in perfil_yz], close=True))
    return extrude(face, amount=x1 - x0, dir=(1, 0, 0))


def prisma_xz(perfil_xz, y0, y1):
    # Extrusão de um polígono do plano XZ ao longo de y, de y0 a y1.
    face = Face(Wire.make_polygon([Vector(x, y0, z) for x, z in perfil_xz], close=True))
    return extrude(face, amount=y1 - y0, dir=(0, 1, 0))


def estadio(raio, meio_comprimento, z0, z1, x=0.0, y=0.0, eixo="y"):
    # Furo oblongo: círculo de 'raio' alongado ±meio_comprimento no eixo dado.
    if meio_comprimento <= 0:
        return cilindro(raio, z0, z1, x, y)
    if eixo == "y":
        dx, dy = 0.0, meio_comprimento
        miolo = caixa(x - raio, x + raio, y - dy, y + dy, z0, z1)
    else:
        dx, dy = meio_comprimento, 0.0
        miolo = caixa(x - dx, x + dx, y - raio, y + raio, z0, z1)
    return (
        miolo.fuse(cilindro(raio, z0, z1, x - dx, y - dy))
        .fuse(cilindro(raio, z0, z1, x + dx, y + dy))
    )


def furo_cruz(z0, z1, x=0.0, y=0.0):
    # Furo para eixo cruz LEGO, com a folga validada (5,0 × 2,0 mm).
    a = caixa(-p.CRUZ_LARGURA / 2, p.CRUZ_LARGURA / 2,
              -p.BRACO_LARGURA / 2, p.BRACO_LARGURA / 2, z0, z1)
    b = caixa(-p.BRACO_LARGURA / 2, p.BRACO_LARGURA / 2,
              -p.CRUZ_LARGURA / 2, p.CRUZ_LARGURA / 2, z0, z1)
    return a.fuse(b).moved(Location((x, y, 0)))


def quadrado(lado, z0, z1, x=0.0, y=0.0):
    # Prisma de seção quadrada, faces em ±x e ±y.
    return caixa(x - lado / 2, x + lado / 2, y - lado / 2, y + lado / 2, z0, z1)


def sextavado(entre_faces, z0, z1, x=0.0, y=0.0):
    # Prisma hexagonal com faces planas em ±y (cantos em ±x).
    r = entre_faces / math.sqrt(3)
    pts = [(x + r * math.cos(math.radians(60 * i)), y + r * math.sin(math.radians(60 * i)))
           for i in range(6)]
    return prisma(pts, z0, z1)


# --- Engrenagem reta evolvente e cremalheira (módulo 1) ------------------------

def _inv(alfa):
    return math.tan(alfa) - alfa


def engrenagem_reta(modulo, dentes, z0, z1, folga_dente=0.0, angulo_pressao=20.0):
    # Engrenagem reta evolvente centrada na origem. Um dente aponta para +x.
    # folga_dente: espessura retirada de cada dente no círculo primitivo (mm).
    ap = math.radians(angulo_pressao)
    rp = modulo * dentes / 2
    rb = rp * math.cos(ap)
    ra = rp + modulo
    rf = rp - 1.25 * modulo
    s = math.pi * modulo / 2 - folga_dente          # espessura no primitivo
    meio_p = s / (2 * rp)                            # meio ângulo no primitivo

    def meio_angulo(r):
        r = max(r, rb)
        return meio_p + _inv(ap) - _inv(math.acos(rb / r))

    n = 10
    raios = [max(rf, rb) + (ra - max(rf, rb)) * i / n for i in range(n + 1)]
    pts = []
    for k in range(dentes):
        tc = 2 * math.pi * k / dentes
        if rf < rb:
            pts.append((rf, tc - meio_angulo(rb)))
        for r in raios:                               # flanco subindo
            pts.append((r, tc - meio_angulo(r)))
        for r in reversed(raios):                     # flanco descendo
            pts.append((r, tc + meio_angulo(r)))
        if rf < rb:
            pts.append((rf, tc + meio_angulo(rb)))
    xy = [(r * math.cos(t), r * math.sin(t)) for r, t in pts]
    return prisma(xy, z0, z1)


def cremalheira(modulo, x_primitivo, y0, n_dentes, costas_x, z0, z1,
                folga_dente=0.0, angulo_pressao=20.0):
    # Cremalheira com dentes apontando para −x, linha primitiva em x_primitivo.
    # Dentes centrados em y0 + passo/2 + k·passo; corpo até x = costas_x.
    passo = math.pi * modulo
    t = math.tan(math.radians(angulo_pressao))
    s2 = (passo / 2 - folga_dente) / 2                # meia espessura no primitivo
    x_ponta = x_primitivo - modulo
    x_raiz = x_primitivo + 1.25 * modulo
    meia_ponta = s2 - modulo * t
    meia_raiz = s2 + 1.25 * modulo * t
    pts = [(costas_x, y0)]
    pts.append((x_raiz, y0))
    for k in range(n_dentes):
        yc = y0 + passo / 2 + k * passo
        pts += [
            (x_raiz, yc - meia_raiz),
            (x_ponta, yc - meia_ponta),
            (x_ponta, yc + meia_ponta),
            (x_raiz, yc + meia_raiz),
        ]
    y_fim = y0 + n_dentes * passo
    pts += [(x_raiz, y_fim), (costas_x, y_fim)]
    return prisma(pts, z0, z1)


# --- Impressão ----------------------------------------------------------------

def no_chao(peca):
    # Assenta a peça em z = 0 (para o prato de impressão).
    bb = peca.bounding_box()
    return peca.moved(Location((0, 0, -bb.min.Z)))


def de_cabeca_para_baixo(peca):
    # Gira 180° em torno de x e assenta em z = 0.
    return no_chao(peca.moved(Location((0, 0, 0), (1, 0, 0), 180)))


def girar_no_prato(peca, graus):
    # Gira em torno de z (peça longa na diagonal do prato) e assenta em z = 0.
    return no_chao(peca.moved(Location((0, 0, 0), (0, 0, 1), graus)))


def exportar(peca, nome):
    # Grava stl/<nome>.stl com a malha que o Bambu aceita sem STL gigante.
    import os
    from build123d import export_stl
    pasta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stl")
    os.makedirs(pasta, exist_ok=True)
    destino = os.path.join(pasta, nome + ".stl")
    export_stl(peca, destino, tolerance=0.01, angular_tolerance=0.2)
    return destino
