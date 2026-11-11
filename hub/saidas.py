# CoopBot — as saídas da partida
# ==============================
# Uma saída = o robô sai da base, faz o que você programar e (em geral) volta.
# Entre saídas, na base, dá para trocar anexo e reposicionar o robô.
#
# SAIDAS define o menu: o item 1 é o primeiro da lista, e assim por diante.
# Cada entrada é (nome, função). Crie funções que chamem as missões na ordem
# que quiser, por exemplo:
#
#     def saida_norte():
#         m4_epis()
#         m8_maker()
#         voltar_base()
#
# Por enquanto há uma entrada por missão, só para o menu ter o que mostrar.

from tbr import *
from missoes import *


def saida_6():
    # MESA OFICIAL (plana). A versão do chão de treino é o item 10.
    giro_fino(False)    # esta saída não usa o ajuste fino...
    usar_creep(False)   # ...nem o creep: o rumo se corrige andando
    m6_carrinho_mesa0()


def saida_6_chao():
    # CHÃO de treino (descida de 1°): a mesma saída 6 com o rumo 321.
    giro_fino(False)
    usar_creep(False)
    m6_carrinho()


def saida_7():
    usar_creep(False)   # sem ajuste de rumo parado, creep nem fino
    m7_bandeira()


SAIDAS = (
    ("M1", m1_gangorra),
    ("M2", m2_blocos),
    ("M3", m3_rampa),
    ("M4", m4_epis),
    ("M5", m5_peca),
    ("M6 mesa0", saida_6),
    ("M7", saida_7),
    ("M8", m8_maker),
    ("M9", m9_patio),
    # Item 10: fica no fim para não renumerar 7 a 9. Depois da M9 completa,
    # o menu avança sozinho para ele.
    ("M6 chao", saida_6_chao),
)
