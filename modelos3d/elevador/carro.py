# Carro do elevador (versão 2): uma peça só.
#
#   - porca da rosca em volta do eixo B (altura toda do carro = engrenamento);
#   - passagem da haste QUADRADA do F, em rasgo de ±1,5 mm em y (tolera erro
#     na distância F–B; o engrenamento corre em y e não muda);
#   - bolso do pinhão, aberto pela lateral esquerda (o pinhão entra por ali);
#   - túnel da barra da garra à direita (x ≈ 9,5–18,6), aberto nas duas pontas:
#     com a garra toda fechada, a traseira da barra sai atrás do carro;
#   - rasgo do batente na chapa de cima, sobre o túnel: o pino do batente
#     (batente.py) entra na barra e bate nas pontas do rasgo, com a garra aberta
#     e com a garra fechada;
#   - faixa da frente (y 22–33) com 2 furos de pino deitados (em y), onde o
#     dedo fixo (dedos.py) encaixa, encostado na face da frente.
#
# Referencial local: x e y do robô (origem no eixo F), z = 0 no fundo do carro.
# Na montagem, o fundo fica em Z_CARRO_MIN (embaixo) ou + CURSO_ELEVADOR (em cima).
# Impressão: de cabeça para baixo (topo na mesa), sem suporte.

import parametros as p
from rosca import (
    caixa,
    cilindro_y,
    de_cabeca_para_baixo,
    estadio,
    exportar,
    porca_cavidade,
)

H = p.CARRO_ALTURA
Z_VAO = (p.CARRO_CHAPA_BAIXO, p.CARRO_CHAPA_BAIXO + p.VAO_ALTURA)  # bolso e túnel
RAIO_PRIMITIVO = p.MODULO * p.DENTES_PINHAO / 2
# Barra: dentes de x = rp − m até a raiz rp + 1,25 m; corpo até + BARRA_LARGURA.
X_RAIZ = RAIO_PRIMITIVO + 1.25 * p.MODULO
X_COSTAS = X_RAIZ + p.BARRA_LARGURA
X_BARRA_CENTRO = (X_RAIZ + X_COSTAS) / 2
X_TUNEL = (RAIO_PRIMITIVO - p.MODULO - 0.5, X_COSTAS + p.FOLGA_TUNEL)
Y_TUNEL_FUNDO = p.Y_BARRA_FECHADA - 0.2          # além da traseira do carro: túnel aberto
# Rasgo do batente: o pino (Ø BATENTE_DIAM) está a BATENTE_Y_BARRA da traseira
# da barra. Na frente, o rasgo para a barra 0,3 mm além da posição aberta; atrás,
# 0,5 mm além da fechada.
R_BATENTE = p.BATENTE_DIAM / 2
Y_RASGO = (p.Y_BARRA_FECHADA + p.BATENTE_Y_BARRA - R_BATENTE - 0.5,
           p.Y_BARRA_ABERTA + p.BATENTE_Y_BARRA + R_BATENTE + 0.3)
Y_PINOS_DEDO = p.CARRO_Y[1] - p.PINO_PROFUNDIDADE


def peca():
    x0, x1 = p.CARRO_X
    y0, y1 = p.CARRO_Y
    corpo = caixa(x0, x1, y0, y1, 0.0, H)

    # Porca: negativo da rosca, passando 1 mm acima e abaixo; a fase casa com o
    # fuso, que começa na face do B (o curso é múltiplo do passo).
    fase = (p.Z_CARRO_MIN - 1.0) - p.Z_MOTOR_B
    porca = porca_cavidade(H + 2.0, fase).moved(_loc(0.0, p.Y_EIXO_B, -1.0))
    corpo = corpo.cut(porca)

    # Haste do F: furo redondo pelo canto do quadrado, em rasgo y ±1,5.
    r_haste = p.QUADRADO_GARRA / 2 ** 0.5 + p.FOLGA_FURO_HASTE / 2
    corpo = corpo.cut(estadio(r_haste, p.TOLERANCIA_F_B, -1.0, H + 1.0, 0.0, p.Y_EIXO_F))

    # Bolso do pinhão, aberto para a esquerda (entrada do pinhão).
    r_bolso = RAIO_PRIMITIVO + p.MODULO + p.FOLGA_BOLSO
    bolso = estadio(r_bolso, p.TOLERANCIA_F_B, Z_VAO[0], Z_VAO[1], 0.0, p.Y_EIXO_F)
    meia = r_bolso + p.TOLERANCIA_F_B
    bolso = bolso.fuse(caixa(x0 - 1.0, 0.0, -meia, meia, Z_VAO[0], Z_VAO[1]))
    corpo = corpo.cut(bolso)

    # Túnel da barra: atravessa o carro de ponta a ponta.
    corpo = corpo.cut(caixa(X_TUNEL[0], X_TUNEL[1], Y_TUNEL_FUNDO, y1 + 1.0, Z_VAO[0], Z_VAO[1]))

    # Rasgo do batente na chapa de cima, sobre o corpo da barra.
    rb = p.BATENTE_RASGO / 2
    corpo = corpo.cut(caixa(X_BARRA_CENTRO - rb, X_BARRA_CENTRO + rb, Y_RASGO[0], Y_RASGO[1],
                            Z_VAO[1] - 0.1, H + 1.0))

    # Alívios (menos material e tempo): o braço só precisa das paredes do túnel
    # e da faixa da frente, onde o dedo fixo encaixa; o canto traseiro
    # esquerdo só precisa da parede da porca.
    y_alivio = meia + p.PAREDE_CARRO
    corpo = corpo.cut(caixa(x0 - 1.0, X_TUNEL[0] - p.PAREDE_CARRO,
                            y_alivio, p.FAIXA_DEDO_Y, -1.0, H + 1.0))
    r_porca = p.DIAM_FUSO / 2 + p.FOLGA_ROSCA + p.PAREDE_CARRO
    corpo = corpo.cut(caixa(x0 - 1.0, -r_porca, y0 - 1.0, -meia - 1.0, -1.0, H + 1.0))

    # Furos dos pinos do dedo fixo: deitados, entrando pela face da frente.
    for x in p.PINOS_DEDO_FIXO_X:
        corpo = corpo.cut(cilindro_y(p.PINO_FURO_DEITADO / 2, Y_PINOS_DEDO, y1 + 1.0,
                                     x, p.Z_PINOS_DEDO_FIXO))
    return corpo


def _loc(x, y, z):
    from build123d import Location
    return Location((x, y, z))


def impressao():
    return de_cabeca_para_baixo(peca())


if __name__ == "__main__":
    print("gravado:", exportar(impressao(), "carro"))
