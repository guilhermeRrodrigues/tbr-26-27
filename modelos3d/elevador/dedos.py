# Dedos da garra (versão 2): placas de 200 mm, presas por pinos Technic.
#
# dedo_fixo (referencial do carro: x e y do robô, z = 0 no fundo do carro)
#   - faixa de aperto de 200 × 36 mm embaixo (desce 56 mm abaixo do fundo do
#     carro) e haste central até o carro, com mãos-francesas a 45°; a placa
#     encosta na face da frente do carro (o aperto empurra o dedo contra ele);
#   - 2 pinos Technic deitados (em y) ligam a placa à faixa da frente do carro;
#   - janela para a barra da garra passar;
#   - 3 ganchos em cunha no pé, em x = −83, 0 e +83 (1,7, 10 e 18,3 cm da ponta
#     esquerda), para as alças da missão 4.
# dedo_movel (referencial da barra: x do robô, y = 0 na traseira da barra)
#   - placa igual, presa por 2 pinos deitados na sapata da ponta da barra.
# Nos dois, as nervuras de rigidez e os ressaltos dos pinos ficam na frente.
#
# Impressão: DEITADOS (face de trás na mesa, frente para cima), girados 45° no
# prato: 200 mm só cabem na diagonal da A1 mini. Assim nada fica em balanço e
# os furos de pino saem verticais (5,2, validado).

from build123d import Location

import parametros as p
from carro import X_TUNEL, Z_VAO
from garra import Y_DEDO_MOVEL, Z_PINOS_SAPATA
from rosca import (
    caixa,
    cilindro_y,
    exportar,
    girar_no_prato,
    prisma_xz,
    prisma_yz,
)

MEIA = p.DEDO_LARGURA / 2
Z_FUNDO = -p.DEDO_DESCIDA            # −56
Z_TOPO_FIXO = p.CARRO_ALTURA         # 14
Z_TOPO_MOVEL = p.SAPATA_Z[1] + 1.7   # 12


def _placa(y_tras, z_topo, z_pinos, pinos_x, z_ressalto):
    # Faixa de aperto de 200 mm embaixo; haste central até o topo, com
    # mãos-francesas a 45°; nervuras na frente (a da faixa chanfrada a 45°, para
    # imprimir sem suporte de cabeça para baixo); ressaltos e furos dos pinos.
    yf = y_tras + p.DEDO_ESPESSURA
    hx0, hx1 = p.HASTE_DEDO_X
    z_faixa = Z_FUNDO + p.FAIXA_APERTO
    m = p.MAO_FRANCESA
    corpo = caixa(-MEIA, MEIA, y_tras, yf, Z_FUNDO, z_faixa)
    corpo = corpo.fuse(caixa(hx0, hx1, y_tras, yf, z_faixa - 0.01, z_topo))
    for perfil in ([(hx0 - m, z_faixa - 0.01), (hx0 + 0.01, z_faixa - 0.01), (hx0 + 0.01, z_faixa + m)],
                   [(hx1 - 0.01, z_faixa - 0.01), (hx1 + m, z_faixa - 0.01), (hx1 - 0.01, z_faixa + m)]):
        corpo = corpo.fuse(prisma_xz(perfil, y_tras, yf))
    # Nervura da faixa: chanfro a 45° no lado de CIMA (vira o de baixo na
    # impressão de cabeça para baixo).
    n, nz = p.NERVURA_Y, p.NERVURA_Z
    corpo = corpo.fuse(prisma_yz([(yf - 0.01, z_faixa - n - nz), (yf + n, z_faixa - n - nz),
                                  (yf + n, z_faixa - n), (yf - 0.01, z_faixa)], -MEIA, MEIA))
    corpo = corpo.fuse(caixa(hx0, hx1, yf - 0.01, yf + n, z_topo - p.NERVURA_Z, z_topo))
    for x in pinos_x:
        r = p.PINO_FURO / 2 + 1.9
        corpo = corpo.fuse(caixa(x - r, x + r, yf - 0.01, yf + p.RESSALTO_PINO,
                                 z_ressalto, z_topo - p.NERVURA_Z + 0.01))
    for x in pinos_x:
        # Furo vertical na impressão (peça deitada): usa o 5,2 validado.
        corpo = corpo.cut(cilindro_y(p.PINO_FURO / 2, y_tras - 1.0,
                                     yf + p.RESSALTO_PINO + 1.0, x, z_pinos))
    return corpo


def dedo_fixo():
    yb = p.Y_DEDO_FIXO
    yf = yb + p.DEDO_ESPESSURA
    zp = p.Z_PINOS_DEDO_FIXO
    corpo = _placa(yb, Z_TOPO_FIXO, zp, p.PINOS_DEDO_FIXO_X, zp - 5.0)
    # Janela da barra (com os dentes), na altura do túnel.
    corpo = corpo.cut(caixa(X_TUNEL[0] - 0.3, X_TUNEL[1] + 0.3, yb - 1.0,
                            yf + p.NERVURA_Y + 1.0, Z_VAO[0] - 0.3, Z_VAO[1] + 0.3))
    # Ganchos: cunha para a frente no pé do dedo (topo a 45°: imprime sem
    # suporte de cabeça para baixo).
    c, e = p.GANCHO_COMPRIMENTO, p.GANCHO_ESPESSURA
    perfil = [(yf - 0.5, Z_FUNDO), (yf + c, Z_FUNDO), (yf + c, Z_FUNDO + e),
              (yf - 0.5, Z_FUNDO + e + c + 0.5)]
    for xg in p.GANCHOS_X:
        meio = p.GANCHO_LARGURA / 2
        corpo = corpo.fuse(prisma_yz(perfil, xg - meio, xg + meio))
    return corpo


def dedo_movel():
    zp = Z_PINOS_SAPATA
    return _placa(Y_DEDO_MOVEL, Z_TOPO_MOVEL, zp, p.PINOS_DEDO_MOVEL_X, p.SAPATA_Z[0])


def pecas():
    return {"dedo_fixo": dedo_fixo(), "dedo_movel": dedo_movel()}


def deitado(peca):
    # Gira 90° em x: a frente (+y) aponta para cima e a face de trás vai à mesa.
    return peca.moved(Location((0, 0, 0), (1, 0, 0), 90))


def impressao():
    return {nome: girar_no_prato(deitado(s), 45) for nome, s in pecas().items()}


if __name__ == "__main__":
    for nome, s in impressao().items():
        print("gravado:", exportar(s, nome))
