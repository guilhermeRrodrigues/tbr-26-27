# Plaquinha de calibração do encaixe: eixo cruz LEGO e pino Technic.
#
# Versão enxuta: só o que ainda falta testar.
#   - 2 furos em cruz (folga de 0,2 mm, já validada) a 25 mm entre si, para
#     conferir a distância dos motores F e B;
#   - 3 furos redondos para pino Technic de 5,2 / 5,4 / 5,6 mm. O pino com atrito
#     tem aletas até 5,2 mm (LDraw confric.dat), e o furo de 5,0 mm ficou justo.
#
# Uso (no ambiente de modelagem, fora do .venv do hub):
#     python calibracao.py  -> grava calibracao.stl ao lado deste arquivo

import os

from build123d import (
    BuildPart,
    BuildSketch,
    Circle,
    Location,
    Locations,
    Mode,
    Plane,
    Rectangle,
    export_stl,
    extrude,
)

import parametros as p

# Diâmetros testados no furo redondo de pino (mm).
PINOS_DIAMETROS = [5.2, 5.4, 5.6]
PINOS_X = [38.0, 46.0, 54.0]
# Distância entre os eixos dos motores F e B (mm), a confirmar.
DIST_F_B = 25.0

ESPESSURA = 6.0  # encaixe do eixo cruz; basta para testar a folga
LARGURA = 66.0   # x: de -6 a 60
CENTRO_X = 27.0  # centro da placa em x
ALTURA = 12.0    # y: de -6 a 6


def _furo_cruz(x, folga):
    # Cruz de eixo LEGO centrada em (x, 0), com a folga somada às cotas nominais.
    span = p.CRUZ_NOMINAL + folga
    braco = p.BRACO_NOMINAL + folga
    with BuildPart() as furo:
        with BuildSketch(Plane.XY):
            Rectangle(span, braco)
            Rectangle(braco, span, mode=Mode.ADD)
        extrude(amount=ESPESSURA, both=True)
    return furo.part.moved(Location((x, 0, 0)))


def _furo_pino(x, diametro):
    with BuildPart() as furo:
        with BuildSketch(Plane.XY):
            with Locations((x, 0)):
                Circle(diametro / 2)
        extrude(amount=ESPESSURA, both=True)
    return furo.part


def placa():
    with BuildPart() as corpo:
        with BuildSketch(Plane.XY):
            with Locations((CENTRO_X, 0)):
                Rectangle(LARGURA, ALTURA)
        extrude(amount=ESPESSURA)

    peca = corpo.part

    # Par de cruzes a 25 mm (eixos F e B), com a folga do projeto.
    peca = peca - _furo_cruz(0.0, p.FOLGA_EIXO)
    peca = peca - _furo_cruz(DIST_F_B, p.FOLGA_EIXO)

    # Três furos redondos para pino.
    for x, d in zip(PINOS_X, PINOS_DIAMETROS):
        peca = peca - _furo_pino(x, d)

    return peca


if __name__ == "__main__":
    peca = placa()
    destino = os.path.join(os.path.dirname(os.path.abspath(__file__)), "calibracao.stl")
    export_stl(peca, destino)
    print("gravado:", destino)
    bb = peca.bounding_box()
    print("dimensões (mm):", round(bb.size.X, 2), round(bb.size.Y, 2), round(bb.size.Z, 2))
