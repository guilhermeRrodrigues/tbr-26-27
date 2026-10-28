# CoopBot — as 9 missões da mesa TBR 2026 (Middle 1/2)
# =====================================================
# Uma função por missão, VAZIA: a resolução é escrita pela equipe com os
# comandos do tbr.py (referência em docs/linguagem.md). A docstring resume a
# regra e a pontuação do manual (DP-Middle v4 + Atualizações Oficiais v5).
#
# Sistema de coordenadas (o mesmo do tbr.py):
#   origem = centro do eixo das rodas na posição de partida, dentro da base
#   x = para LESTE (para onde o robô aponta ao sair), y = para NORTE
#   rumo 0 = leste, 90 = sul, -90 = norte, 180 = oeste (positivo = horário)

from tbr import *


def m1_gangorra():
    """M1 Balanço Controlado — 30 pts (DP-Middle p.3-4).

    Pontua com o lado LESTE (menino) tocando o tapete E o apoio central (peças
    azuis) tocando a área verde-escura. A gangorra é solta, sem fixação.
    """
    pass


def m2_blocos():
    """M2 Equilíbrio Dinâmico — até 100 pts (DP-Middle p.5-6).

    25 pts por bloco de alvenaria SOBRE o primeiro pavimento, com o pavimento
    em pé na posição inicial; +25 de bônus com os 3. Pavimento tombado = 0.
    """
    pass


def m3_rampa():
    """M3 Acessibilidade — 32 pts (DP-Middle p.7-8; errata Atualiz. p.7).

    Rampa TOCANDO as 3 áreas iniciais dos blocos de alvenaria.
    """
    pass


def m4_epis():
    """M4 Segurança no Trabalho — até 100 pts (DP-Middle p.9-10).

    EPI TOCANDO o suporte da mesma cor no pórtico: verde 37, azul 33,
    vermelho 30. Os EPIs ficam com a equipe na base e saem levados pelo robô.
    """
    pass


def m5_peca():
    """M5 Conexão do Conhecimento — 48 / 22 pts (DP-Middle p.11-12).

    Peça faltante DENTRO da área vermelha do quebra-cabeça: totalmente 48,
    parcialmente 22. Orientação livre.
    """
    pass


def m6_carrinho():
    """M6 Acesso Seguro — 40 / 17 pts (DP-Middle p.13-14).

    Carrinho DENTRO da área verde: totalmente 40, parcialmente 17.
    """
    pass


def m7_bandeira():
    """M7 Abertura do Saber — 30 pts (DP-Middle p.15-16).

    Haste da bandeira TOCANDO o tapete no fim da partida.
    """
    pass


def m8_maker():
    """M8 Missão Maker — até 68 pts (DP-Middle p.17-19).

    7 pts por trabalhador TOCANDO a Área Industrial. O Dispositivo Maker
    detecta o trabalhador e libera o Bloco; depois de TOCAR o tapete, o robô
    pode levá-lo: Área Industrial 20 ou Área Escolar 40.
    """
    pass


def m9_patio():
    """M9 Entrada Inclusiva — 52 pts (DP-Middle p.20-21).

    Robô termina SOBRE o pátio elevado (100% do peso no pátio).
    """
    pass
