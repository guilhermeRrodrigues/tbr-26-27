# Pino do batente de abertura da garra (novo na versão 2).
#
# Na v1, ao abrir demais, a barra passava do último dente e desengatava do
# pinhão: o motor não conseguia mais fechar a garra. Este pino entra pelo rasgo
# da chapa de cima do carro e fica no furo cego da barra (por gravidade). Com a
# garra aberta, bate na ponta da frente do rasgo; fechada, na ponta de trás (desde
# 6/11/2026 o túnel é aberto atrás, e a barra sai pela traseira do carro).
#
# Referencial: o da barra (x do robô; y = 0 na traseira da barra; z do carro).
# Impressão: em pé, de cabeça para baixo (cabeça na mesa).

import parametros as p
from garra import X_BARRA_CENTRO, Z_BARRA
from rosca import cilindro, de_cabeca_para_baixo, exportar

Z_BASE = Z_BARRA[1] - p.BATENTE_FURO_PROF + 0.3      # 0,3 acima do fundo do furo
Z_CABECA = p.CARRO_ALTURA + 0.5                        # 0,5 acima do topo do carro


def peca():
    x, y = X_BARRA_CENTRO, p.BATENTE_Y_BARRA
    haste = cilindro(p.BATENTE_DIAM / 2, Z_BASE, Z_CABECA + 0.01, x, y)
    cabeca = cilindro(p.BATENTE_CABECA / 2, Z_CABECA, Z_CABECA + p.BATENTE_CABECA_ALTURA, x, y)
    return haste.fuse(cabeca)


def impressao():
    return de_cabeca_para_baixo(peca())


if __name__ == "__main__":
    print("gravado:", exportar(impressao(), "batente"))
