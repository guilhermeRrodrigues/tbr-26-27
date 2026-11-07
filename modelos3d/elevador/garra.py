# Barra da garra (versão 2): cremalheira + sapata do dedo móvel.
#
# A barra corre de frente para trás no túnel do carro, ao lado do pinhão do F.
# Os dentes (cremalheira de módulo 1) ficam na face −x, voltados para o pinhão.
#   - furo cego do batente perto da traseira: o pino do batente (batente.py)
#     entra por ele e pelo rasgo do carro, e impede que a garra abra demais e
#     desengate do pinhão (falha da v1);
#   - sapata na ponta da frente, com 2 furos de pino deitados (em y): o dedo
#     móvel (dedos.py) encaixa pela frente. Com a garra aberta, a face de trás
#     do dedo móvel fica a 70 mm da face da frente do dedo fixo; fechada, a 30;
#   - cauda rebaixada na face de baixo, com rampa na ponta: ela passa sem bater
#     pela boca traseira do túnel, que é impressa no ar e cede.
#
# Referencial local: x do robô; y = 0 na traseira da barra; z igual ao do carro
# (z = 0 no fundo do carro). Na montagem, a traseira fica em Y_BARRA_ABERTA
# (aberta) ou Y_BARRA_FECHADA (fechada).
# Impressão: de cabeça para baixo (topo da barra na mesa).

import parametros as p
from rosca import (
    caixa,
    cilindro,
    cilindro_y,
    cremalheira,
    de_cabeca_para_baixo,
    exportar,
    prisma_yz,
)

RAIO_PRIMITIVO = p.MODULO * p.DENTES_PINHAO / 2
X_RAIZ = RAIO_PRIMITIVO + 1.25 * p.MODULO
X_COSTAS = X_RAIZ + p.BARRA_LARGURA
X_BARRA_CENTRO = (X_RAIZ + X_COSTAS) / 2
Z_BARRA = (p.CARRO_CHAPA_BAIXO + (p.VAO_ALTURA - p.BARRA_ALTURA) / 2,
           p.CARRO_CHAPA_BAIXO + (p.VAO_ALTURA + p.BARRA_ALTURA) / 2)
# Face da frente do dedo fixo (global) + abertura = face de trás do dedo móvel;
# em coordenadas da barra, descontada a traseira com a garra aberta.
Y_FRENTE_DEDO_FIXO = p.Y_DEDO_FIXO + p.DEDO_ESPESSURA
Y_DEDO_MOVEL = Y_FRENTE_DEDO_FIXO + p.ABERTURA_GARRA - p.Y_BARRA_ABERTA   # 109
Z_PINOS_SAPATA = (p.SAPATA_Z[0] + p.SAPATA_Z[1]) / 2


def peca():
    dentes = cremalheira(p.MODULO, RAIO_PRIMITIVO, 0.0, p.DENTES_CREMALHEIRA, X_COSTAS,
                         Z_BARRA[0], Z_BARRA[1], folga_dente=p.FOLGA_DENTE)
    corpo = caixa(X_RAIZ, X_COSTAS, 0.0, Y_DEDO_MOVEL, Z_BARRA[0], Z_BARRA[1])
    corpo = corpo.fuse(dentes)

    # Sapata do dedo móvel, na ponta (sempre fora do carro).
    y_sapata = Y_DEDO_MOVEL - p.SAPATA_Y
    sapata = caixa(p.SAPATA_X[0], p.SAPATA_X[1], y_sapata, Y_DEDO_MOVEL,
                   p.SAPATA_Z[0], p.SAPATA_Z[1])
    corpo = corpo.fuse(sapata)
    for x in p.PINOS_DEDO_MOVEL_X:
        corpo = corpo.cut(cilindro_y(p.PINO_FURO_DEITADO / 2, y_sapata - 1.0,
                                     Y_DEDO_MOVEL + 1.0, x, Z_PINOS_SAPATA))

    # Furo cego do batente, de cima para baixo.
    corpo = corpo.cut(cilindro(p.BATENTE_FURO / 2, Z_BARRA[1] - p.BATENTE_FURO_PROF,
                               Z_BARRA[1] + 1.0, X_BARRA_CENTRO, p.BATENTE_Y_BARRA))

    # Cauda: rebaixo na face de baixo, com a ponta em rampa e o fim do rebaixo a 45°.
    z0, a, r, c = Z_BARRA[0], p.CAUDA_ALIVIO, p.CAUDA_RAMPA, p.CAUDA_COMPRIMENTO
    perfil = [(-1.0, z0 - 1.0), (c, z0 - 1.0), (c, z0), (c - a, z0 + a),
              (r, z0 + a), (0.0, z0 + a + r), (-1.0, z0 + a + r)]
    return corpo.cut(prisma_yz(perfil, X_RAIZ - 3.0, X_COSTAS + 1.0))


def impressao():
    return de_cabeca_para_baixo(peca())


if __name__ == "__main__":
    print("gravado:", exportar(impressao(), "garra"))
