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
    andar(20)                     # cm para a frente (leste)
    virar_para(90, RAPIDO)
    andar(20)
    anexo1(-200)                  # VEL_ANEXO padrão (RAPIDO aqui seria 450°/s, mais lento)
    esperar(300)
    anexo1_ir_para(0, esperar=False)  # o braço volta durante a ré
    andar(-23)
    virar_para(0, RAPIDO)
    andar(-25)


def m2_blocos():
    """M2 Equilíbrio Dinâmico — até 100 pts (DP-Middle p.5-6).

    25 pts por bloco de alvenaria SOBRE o primeiro pavimento, com o pavimento
    em pé na posição inicial; +25 de bônus com os 3. Pavimento tombado = 0.
    """
    # Usado como saída 2, levando a peça da M5.
    # Ajuste fino na mesa: o recuo andar(-31) (lado norte do robô passando rente,
    # sem tocar o quadrado de cima do L) e o andar(24, LENTO) do empurrão final.
    # A peça solta fica 6 cm à frente do para-choque: os primeiros 6 cm do
    # empurrão só encostam nela.
    andar(8.5)
    virar_para(-23)
    andar(32, RAPIDO)                               # chega na peça
    anexo1_ate_travar(ANTI_HORARIO, forca=40, teto_ms=1500)   # prende sem esmagar
    andar(-31)                                      # y≈1,2
    virar_para(0, RAPIDO)
    andar_no_rumo(73, 0, RAPIDO)                               # x≈80: ainda longe do L
    anexo1_ir_para(0)                               # solta com o braço livre
    andar(24, LENTO)                                # encosta e leva a peça ~10 cm
    # Gira o braço e posiciona a caixa. Precisa de força 40: com 30 ele trava
    # logo e não gira. Se a engrenagem pular dente aqui, o recolher logo abaixo
    # refaz o 0.
    anexo1_ate_travar(ANTI_HORARIO, forca=40, teto_ms=1500)
    anexo1_aumentar(15.67)
    andar(-4)                                       # já no rumo 0: andar() alinha sozinho
    virar_ate_travar(-35)                           # para ao encostar
    andar(-7)
    anexo1_recolher(HORARIO, esperar=False)         # sobe até o batente e refaz o 0
    #FIM MISSÃO 5 - RUMO AO PROXIMO ALVO!
    virar_para(25, RAPIDO)
    # Reta + curva + reta: mesmo ponto final de andar(15); virar_para(0);
    # andar(36.5), sem parar no canto (passa até 0,7 cm por dentro dele).
    andar(8.35, parar=False)
    curva(30, -25)
    # +4 cm: devolve o que o andar_no_rumo(73) tirou (era 77). Daqui em diante o
    # carrinho, a alavanca e a volta ficam na geometria que já funcionava.
    andar(33.85)
    virar_para(-40)                                 # carrinho: era -35,5; mais negativo = mais ao norte
    andar(42, LENTO)
    anexo1_recolher(HORARIO, esperar=False)
    # Ré só até onde estava antes do carrinho (x≈150,8 y≈-10). A antiga
    # andar(-50) ia até (144,3, -14,6), colado no canto do pavimento (mesa
    # cinza), e o virar_para(0) ali derrubava a mesa.
    andar(-42, RAPIDO)
    #FIM MISSÃO NAO SEI O NUMERO - RUMO AO PROXIMO ALVO!
    ir_para(179.3, -14.6)                           # mesma parada de antes na alavanca, pelo norte
    virar_para(0)
    anexo1_ate_travar(ANTI_HORARIO, forca=40, teto_ms=1500, esperar=False)
    sacudir(1000)
    virar_ate_travar(90)
    # Braço para o 0 por posição (força total), não pelo recolher: encostado na
    # alavanca, o recolher achava que era o batente e "zerava" com o braço para
    # a frente. O ir_para(0) espera 0,7 s travado antes de desistir, tempo de
    # o robô girar e soltar a alavanca.
    anexo1_ir_para(0, esperar=False)
    # Volta de frente, refazendo a ida ao contrário, ao norte do pavimento:
    # 1) da alavanca ao ponto antes do carrinho. O giro continua no sentido
    #    HORÁRIO (de 90 para ~189), o mesmo que empurrou a alavanca: girar de
    #    volta arrastava a alavanca e a desativava;
    # 2) pela faixa y=-10 da ida, onde o pavimento fica mais longe;
    # 3) diagonal até a base. Chega com a frente para oeste: o x=10 deixa folga
    #    para o braço não passar da base (ajuste na mesa).
    ir_para(150.8, -10, RAPIDO)
    ir_para(116.9, -10, RAPIDO)
    ir_para(10, 0, RAPIDO)


def m3_rampa():
    """M3 Acessibilidade — 32 pts (DP-Middle p.7-8; errata Atualiz. p.7).

    Rampa TOCANDO as 3 áreas iniciais dos blocos de alvenaria.
    """
    andar_no_rumo(21, 0)
    anexo1_ate_travar(ANTI_HORARIO, forca=40, teto_ms=1500)
    andar_no_rumo(-40, 0)
    andar(20)
    virar_para(90, LENTO)
    andar(-2)
    anexo1_ir_para(0)


def m4_epis():
    """M4 Segurança no Trabalho — até 100 pts (DP-Middle p.9-10).

    EPI TOCANDO o suporte da mesma cor no pórtico: verde 37, azul 33,
    vermelho 30. Os EPIs ficam com a equipe na base e saem levados pelo robô.
    """
    anexo1_ate_travar(ANTI_HORARIO, forca=40, teto_ms=1500)
    anexo1_aumentar(35, esperar=False)  # o braço sobe enquanto sai
    andar_no_rumo(70, 0, RAPIDO)
    virar_para(25, RAPIDO)
    # Reta + curva + reta: mesmo ponto final de andar(40); virar_para(0);
    # andar(36), sem parar no canto (passa até 0,7 cm por dentro dele).
    andar(33.35, parar=False)
    curva(30, -25)
    andar(29.35)
    virar_para(-60, LENTO)
    andar_no_rumo(54, -55, RAPIDO)
    virar_para(-90, LENTO)
    anexo1_ir_para(0)
    andar(5)
    andar(-38, RAPIDO)
    virar_para(0, RAPIDO)
    andar(-200, RAPIDO)  # volta para a base


def m5_peca():
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
