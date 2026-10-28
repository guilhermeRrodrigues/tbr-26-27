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


SAIDAS = (
    ("M1", m1_gangorra),
    ("M2", m2_blocos),
    ("M3", m3_rampa),
    ("M4", m4_epis),
    ("M5", m5_peca),
    ("M6", m6_carrinho),
    ("M7", m7_bandeira),
    ("M8", m8_maker),
    ("M9", m9_patio),
)
