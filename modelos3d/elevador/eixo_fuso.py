# Haste do fuso (motor B, elevador), em 2 segmentos.
#
# Substitui o eixo LEGO longo. O segmento de baixo encaixa, pelo soquete em
# cruz, no eixo curto do motor B; os segmentos se unem por um eixo LEGO de 3 ou
# 4 módulos nos soquetes da emenda. A emenda fica num múltiplo do passo e a
# rosca de 4 entradas repete a cada 90°: qualquer orientação da cruz casa.
#
# Referencial local: eixo na origem, z = 0 na face do motor B.
#   baixo:  z   0–108  rosca; soquete do motor embaixo, soquete da emenda em cima
#   cima:   z 108–212  rosca (fase 108); colar 212–215; munhão Ø 8 215–223
# Impressão: os dois em pé, soquete para baixo, com brim.

import parametros as p
from rosca import cilindro, exportar, furo_cruz, fuso_solido, no_chao

L1 = p.ROSCA_SEG1
L = p.ROSCA_COMPRIMENTO
Z_MUNHAO = L + p.COLAR_ALTURA
Z_TOPO = Z_MUNHAO + p.MUNHAO_COMPRIMENTO
E = p.EMENDA_PROFUNDIDADE


def baixo():
    corpo = fuso_solido(L1, fase=0.0)
    corpo = corpo.cut(furo_cruz(-1.0, p.SOQUETE_PROFUNDIDADE))
    return corpo.cut(furo_cruz(L1 - E, L1 + 1.0))


def cima():
    from build123d import Location
    corpo = fuso_solido(L - L1, fase=L1).moved(Location((0, 0, L1)))
    # O colar começa exatamente no topo da rosca: sobrepor a superfície torcida
    # deixava dois sólidos separados na união.
    corpo = corpo.fuse(cilindro(p.DIAM_COLAR_FUSO / 2, L, Z_MUNHAO))
    corpo = corpo.fuse(cilindro(p.DIAM_MUNHAO_FUSO / 2, Z_MUNHAO - 0.5, Z_TOPO))
    return corpo.cut(furo_cruz(L1 - 1.0, L1 + E))


def pecas():
    return {"fuso_baixo": baixo(), "fuso_cima": cima()}


def impressao():
    return {nome: no_chao(s) for nome, s in pecas().items()}


if __name__ == "__main__":
    for nome, s in impressao().items():
        print("gravado:", exportar(s, nome))
