# Haste da garra (motor F), em 2 segmentos.
#
# Haste QUADRADA de 10 mm em que o pinhão desliza junto com o carro (na v1 era
# sextavada; a cruz da emenda tem simetria de 90°, e o sextavado montado a 90°
# deixaria um degrau que trava o pinhão). Encaixa pelo soquete em cruz no eixo
# LEGO curto do motor F; os segmentos se unem por um eixo LEGO de 3 ou 4 módulos.
#
# Referencial local: eixo na origem, z = 0 na face do motor F.
#   baixo:  z   0–120  quadrado; soquete do motor embaixo, da emenda em cima
#   cima:   z 120–237  quadrado; colar 237–240; munhão Ø 6 240–248
# Impressão: os dois em pé, soquete para baixo, com brim.

import parametros as p
from rosca import cilindro, exportar, furo_cruz, no_chao, quadrado

L1 = p.GARRA_SEG1
L = p.Z_TOPO_HASTES - p.Z_MOTOR_F        # 237
Z_MUNHAO = L + p.COLAR_ALTURA
Z_TOPO = Z_MUNHAO + p.MUNHAO_COMPRIMENTO
E = p.EMENDA_PROFUNDIDADE


def baixo():
    corpo = quadrado(p.QUADRADO_GARRA, 0.0, L1)
    corpo = corpo.cut(furo_cruz(-1.0, p.SOQUETE_PROFUNDIDADE))
    return corpo.cut(furo_cruz(L1 - E, L1 + 1.0))


def cima():
    corpo = quadrado(p.QUADRADO_GARRA, L1, L)
    corpo = corpo.fuse(cilindro(p.DIAM_COLAR_GARRA / 2, L - 0.5, Z_MUNHAO))
    corpo = corpo.fuse(cilindro(p.DIAM_MUNHAO_GARRA / 2, Z_MUNHAO - 0.5, Z_TOPO))
    return corpo.cut(furo_cruz(L1 - 1.0, L1 + E))


def pecas():
    return {"garra_baixo": baixo(), "garra_cima": cima()}


def impressao():
    return {nome: no_chao(s) for nome, s in pecas().items()}


if __name__ == "__main__":
    for nome, s in impressao().items():
        print("gravado:", exportar(s, nome))
