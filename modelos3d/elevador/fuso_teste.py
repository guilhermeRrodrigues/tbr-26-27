# Fuso de teste: 3 cm de rosca trapezoidal de 4 entradas, com furo em cruz
# para o eixo LEGO, e uma porca de teste com a rosca em negativo.
#
# Objetivo: confirmar que a rosca em PLA Lite desliza, que o avanço é de
# 16 mm por volta e que a porca não prende. Não é a peça final.
#
# A rosca é uma extrusão com rotação: a seção transversal tem os dentes
# (período = passo axial de 4 mm, uma entrada por período) e a rotação de
# 360° a cada 16 mm dá o avanço. Assim as 4 entradas saem da mesma seção,
# sem varreduras de hélice (que davam sobreposição e falha nos booleanos).
#
# Uso (no ambiente de modelagem, fora do .venv do hub):
#     python fuso_teste.py  -> grava fuso_teste.stl ao lado deste arquivo

import math
import os

from build123d import (
    Align,
    BuildPart,
    BuildSketch,
    Compound,
    Cylinder,
    Face,
    Location,
    Mode,
    Plane,
    Rectangle,
    Solid,
    Spline,
    Vector,
    Wire,
    export_stl,
    extrude,
)

import parametros as p
from rosca import rosca_solida as _rosca_solida  # rosca validada, fonte única

COMPRIMENTO = p.COMPRIMENTO_TESTE_FUSO  # 15 mm
ALTURA_PORCA = 6.0                      # porca curta: ~0,4 volta da rosca, o suficiente para testar o deslize
RAIO_PORCA = 8.5                        # parede de 1,2 mm em volta da rosca
X_PORCA = 25.0                          # posição da porca no mesmo prato


def fuso():
    rr = p.DIAM_RAIZ_FUSO / 2
    re = p.DIAM_FUSO / 2
    a = p.PASSO_FUSO / 2 - 0.1  # meia largura do dente na raiz (passo/2 menos folga)
    c = 0.4                     # meia largura da crista
    corpo = _rosca_solida(rr, re, a, c, COMPRIMENTO)

    # Furo em cruz para o eixo LEGO, passando por todo o comprimento.
    with BuildPart() as furo:
        with BuildSketch(Plane.XY):
            Rectangle(p.CRUZ_LARGURA, p.BRACO_LARGURA)
            Rectangle(p.BRACO_LARGURA, p.CRUZ_LARGURA, mode=Mode.ADD)
        extrude(amount=COMPRIMENTO + 2)
    return corpo.cut(furo.part.moved(Location((0, 0, -1))))


def porca():
    rr = p.DIAM_RAIZ_FUSO / 2
    re = p.DIAM_FUSO / 2
    a = p.PASSO_FUSO / 2 - 0.1
    c = 0.4
    f = p.FOLGA_ROSCA
    # Negativo da rosca: folga só no sentido radial. Alargar os dentes também em z
    # faria as entradas vizinhas se sobreporem (passo de 4 mm, dente de 3,8 mm).
    cavidade = _rosca_solida(rr + f, re + f, a, c, ALTURA_PORCA)
    bloco = Cylinder(RAIO_PORCA, ALTURA_PORCA, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return bloco.cut(cavidade)


if __name__ == "__main__":
    pecas = Compound([fuso(), porca().moved(Location((X_PORCA, 0, 0)))])
    destino = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fuso_teste.stl")
    # Tolerância de malha: a rosca é uma spline, e a malha fina gera STL de 24 MB.
    export_stl(pecas, destino, tolerance=0.01, angular_tolerance=0.2)
    print("gravado:", destino)
    bb = pecas.bounding_box()
    print("dimensões (mm):", round(bb.size.X, 2), round(bb.size.Y, 2), round(bb.size.Z, 2))
