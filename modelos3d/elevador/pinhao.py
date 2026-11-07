# Pinhão da garra: engrenagem reta evolvente, módulo 1, 22 dentes.
#
# Furo quadrado: desliza na haste quadrada da garra (eixo_garra) junto com o
# carro e gira com ela. Fica no bolso do carro, preso em z pelas chapas.
# Referencial local: eixo na origem, z = 0 na face de baixo; um dente aponta
# para +x (para a cremalheira).
# Impressão: deitado, como está.

import parametros as p
from rosca import cilindro, engrenagem_reta, exportar, quadrado


def peca():
    corpo = engrenagem_reta(p.MODULO, p.DENTES_PINHAO, 0.0, p.PINHAO_ALTURA,
                            folga_dente=p.FOLGA_DENTE)
    lado = p.QUADRADO_GARRA + p.FOLGA_QUADRADO
    furo = quadrado(lado, -1.0, p.PINHAO_ALTURA + 1.0)
    # Alívio nos cantos: a impressão arredonda o canto do furo, e o canto vivo
    # da haste prendia (placa de teste).
    for sx in (-1, 1):
        for sy in (-1, 1):
            furo = furo.fuse(cilindro(p.ALIVIO_CANTO_QUADRADO, -1.0, p.PINHAO_ALTURA + 1.0,
                                      sx * lado / 2, sy * lado / 2))
    return corpo.cut(furo)


def impressao():
    return peca()


if __name__ == "__main__":
    print("gravado:", exportar(impressao(), "pinhao"))
