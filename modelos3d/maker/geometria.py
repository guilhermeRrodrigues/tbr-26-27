# Geometria comum do Dispositivo Maker.
#
# Cópia dos auxiliares genéricos de ../elevador/rosca.py. É cópia e não import
# porque rosca.py faz "import parametros", e aqui o parametros é outro (o do
# Maker): o nome colidiria. Só furo_cruz mudou: recebe a cruz por parâmetro.
#
# Tudo devolve sólidos build123d em mm. Booleanos com .fuse()/.cut() explícitos.

import math
import os

from build123d import Align, Axis, Box, Cylinder, Face, Location, Vector, Wire, extrude

import parametros as p


def caixa(x0, x1, y0, y1, z0, z1):
    # Caixa alinhada aos eixos, dada pelos limites.
    return Box(x1 - x0, y1 - y0, z1 - z0,
               align=(Align.MIN, Align.MIN, Align.MIN)).moved(Location((x0, y0, z0)))


def cilindro(raio, z0, z1, x=0.0, y=0.0):
    return Cylinder(raio, z1 - z0,
                    align=(Align.CENTER, Align.CENTER, Align.MIN)).moved(Location((x, y, z0)))


def cilindro_y(raio, y0, y1, x=0.0, z=0.0):
    # Cilindro deitado, eixo em y.
    c = Cylinder(raio, y1 - y0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return c.rotate(Axis.X, -90).moved(Location((x, y0, z)))


def cilindro_x(raio, x0, x1, y=0.0, z=0.0):
    # Cilindro deitado, eixo em x.
    c = Cylinder(raio, x1 - x0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return c.rotate(Axis.Y, 90).moved(Location((x0, y, z)))


def prisma(pontos_xy, z0, z1):
    # Extrusão vertical de um polígono do plano XY.
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


def furo_cruz(z0, z1, x=0.0, y=0.0):
    # Furo para eixo cruz LEGO com a folga validada no elevador (5,0 × 2,0 mm).
    c, b = p.CRUZ_LARGURA / 2, p.BRACO_LARGURA / 2
    a = caixa(-c, c, -b, b, z0, z1)
    return a.fuse(caixa(-b, b, -c, c, z0, z1)).moved(Location((x, y, 0)))


def no_chao(peca):
    # Assenta a peça em z = 0 (para o prato de impressão).
    return peca.moved(Location((0, 0, -peca.bounding_box().min.Z)))


def girar(peca, eixo, graus):
    # Gira em torno de um eixo que passa pela origem ("x", "y" ou "z").
    d = {"x": (1, 0, 0), "y": (0, 1, 0), "z": (0, 0, 1)}[eixo]
    return peca.moved(Location((0, 0, 0), d, graus))


def mover(peca, x=0.0, y=0.0, z=0.0):
    return peca.moved(Location((x, y, z)))


def exportar(peca, nome):
    # Grava stl/<nome>.stl com a malha que o Bambu aceita sem STL gigante.
    from build123d import export_stl
    pasta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stl")
    os.makedirs(pasta, exist_ok=True)
    destino = os.path.join(pasta, nome + ".stl")
    export_stl(peca, destino, tolerance=0.01, angular_tolerance=0.2)
    return destino


def tan(graus):
    return math.tan(math.radians(graus))
