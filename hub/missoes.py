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
    andar_no_rumo(20, 0)          # cm para a frente (leste)
    virar_para(90, RAPIDO)
    andar_no_rumo(20, 90)
    anexo1(-200)                  # VEL_ANEXO padrão (RAPIDO aqui seria 450°/s, mais lento)
    esperar(300)
    anexo1_ir_para(0, esperar=False)  # o braço volta durante a ré
    # Volta: ré curta e reta para o braço sair da gangorra antes de girar, depois
    # ré em diagonal direto à origem. A diagonal fica por dentro do L da ida
    # (0,0)→(20,0)→(20,-20). Era andar(-23); virar_para(0); andar(-25).
    andar_no_rumo(-8, 90)
    voltar_base(RAPIDO, de_re=True)
    andar_no_rumo(-15, rumo())     # segue a diagonal da volta (rumo ≈ 31)


def m2_blocos():
    """M2 Equilíbrio Dinâmico — até 100 pts (DP-Middle p.5-6).

    25 pts por bloco de alvenaria SOBRE o primeiro pavimento, com o pavimento
    em pé na posição inicial; +25 de bônus com os 3. Pavimento tombado = 0.
    """
    # Usado como saída 2, levando a peça da M5.
    # Ajuste fino na mesa: o recuo andar_no_rumo(-31, -21) (lado norte do robô
    # passando rente, sem tocar o quadrado de cima do L) e o
    # andar_no_rumo(24, 0, LENTO) do empurrão final.
    # A peça solta fica 6 cm à frente do para-choque: os primeiros 6 cm do
    # empurrão só encostam nela.
    andar_no_rumo(8.5, 0)
    virar_para(-17)
    andar_no_rumo(32, -18, RAPIDO)                               # chega na peça
    anexo1_ate_travar(ANTI_HORARIO, forca=67, teto_ms=1500)   # prende sem esmagar
    andar_no_rumo(-31, -21)                                      # y≈1,2
    virar_para(0, RAPIDO)
    andar_no_rumo(73, 0, RAPIDO)                               # x≈80: ainda longe do L
    anexo1_ir_para(0)                               # solta com o braço livre
    andar_no_rumo(24, 0, LENTO)                     # encosta e leva a peça ~10 cm
    # Gira o braço e posiciona a caixa. Força 50: com 60 a engrenagem pula dente
    # (rodou -694° sem travar na mesa); com 30 trava logo e não gira. Se pular
    # dente mesmo assim, o recolher logo abaixo refaz o 0.
    anexo1_ate_travar(ANTI_HORARIO, forca=67, teto_ms=1500)
    anexo1_aumentar(20.67)
    andar_no_rumo(-4, 0)                            # já no rumo 0: alinha sozinho
    virar_ate_travar(-25)                           # para ao encostar
    # rumo(), não -35: o robô parou onde encostou (muda a cada partida), e com
    # -35 a ré tentaria completar o giro.
    andar_no_rumo(-7, rumo())
    # Garra para o 0 por posição (força total), não pelo recolher: com força 30
    # ela não levanta do fundo, o recolher achava o "batente" logo ali (-177°)
    # e zerava com a garra embaixo. O 0 ainda vale aqui porque a descida
    # travou sem pular dente; o recolher do carrinho, já no batente, refina.
    anexo1_ir_para(0, esperar=False)
    #FIM MISSÃO 5 - RUMO AO PROXIMO ALVO!
    virar_para(25, RAPIDO)
    # Reta + curva + reta: mesmo ponto final de andar(15); virar_para(0);
    # andar(36.5), sem parar no canto (passa até 0,7 cm por dentro dele).
    andar_no_rumo(8.35, 25, parar=False)
    curva(30, -25)
    # +4 cm: devolve o que o andar_no_rumo(73) tirou (era 77). Daqui em diante o
    # carrinho, a alavanca e a volta ficam na geometria que já funcionava.
    andar_no_rumo(33.85, 0)
    virar_para(-42)                                 # carrinho: era -35,5; mais negativo = mais ao norte
    andar_no_rumo(40, -42, LENTO)                   # era 42: o carrinho passava 2-5 cm da área verde
    anexo1_recolher(HORARIO, esperar=False)
    # Ré só até onde estava antes do carrinho (x≈150,8 y≈-10), com a mesma
    # distância do empurrão. A antiga andar(-50) ia até (144,3, -14,6), colado
    # no canto do pavimento (mesa cinza), e o virar_para(0) ali derrubava a mesa.
    # Em NORMAL, não RAPIDO: com RAPIDO a ré travou ("sem progresso"), as rodas
    # patinaram e a odometria errou a alavanca e a base.
    andar_no_rumo(-40, -42)
    virar_para(-40)
    print("POS apos re do carrinho x=%.1f y=%.1f rumo=%.1f (esperado 150.8, -10)" % posicao())
    #FIM MISSÃO NAO SEI O NUMERO - RUMO AO PROXIMO ALVO!
    ir_para(181.3, -14.6)                           # mesma parada de antes na alavanca, pelo norte
    virar_para(0)
    anexo1_ate_travar(ANTI_HORARIO, forca=67, teto_ms=1500, esperar=False)
    virar_ate_travar(90)
    # Braço para o 0 por posição (força total), não pelo recolher: encostado na
    # alavanca, o recolher achava que era o batente e "zerava" com o braço para
    # a frente. O ir_para(0) espera 0,7 s travado antes de desistir, tempo de
    # o robô girar e soltar a alavanca.
    anexo1_ir_para(0, esperar=False)
    # Volta fluida: um giro no lugar e depois um caminho contínuo, sem parar,
    # pelo mesmo corredor da volta antiga (alavanca → faixa y=-10 → base):
    # 1) giro no sentido HORÁRIO (90 → 195), o mesmo que empurrou a alavanca:
    #    girar de volta arrastava a alavanca e a desativava;
    # 2) reta e curva até a faixa y=-10 da ida (x≈158), onde o pavimento fica
    #    mais longe; passa ~1 cm AO NORTE da reta antiga, nunca ao sul;
    # 3) reta na faixa e curva aberta (raio 1 m) até apontar para a base;
    # 4) reta até (10, 5). Era (10, 0), mas o robô parou à direita (sul) da
    #    partida: o y=5 compensa. Parou ainda ao sul? Aumente o 7.99 da curva
    #    e diminua a última reta (refaça a conta). Ao norte? Diminua.
    #    Antes: ir_para(150.8,-10) → ir_para(116.9,-10) → ir_para(10,0),
    #    3 giros e 3 paradas.
    virar_para(195, RAPIDO)
    andar_no_rumo(13.82, 195, RAPIDO, parar=False)
    curva(30, -15, RAPIDO, parar=False)             # rumo 180 em y=-10, x≈158,2
    andar_no_rumo(34.3, 180, RAPIDO, parar=False)
    curva(100, 7.99, RAPIDO, parar=False)           # aponta para (10, 5)
    andar_no_rumo(55.5, 187.99, RAPIDO)
    virar_para(90)
    andar(17.69)
    anexo1(-200)
    anexo1_ir_para(0)
    andar(-17)
    virar_para(0)
    andar(-25)



def m3_rampa():
    """M3 Acessibilidade — 32 pts (DP-Middle p.7-8; errata Atualiz. p.7).

    Rampa TOCANDO as 3 áreas iniciais dos blocos de alvenaria.
    """
    andar_no_rumo(21, 0)
    anexo1_ate_travar(ANTI_HORARIO, forca=69, teto_ms=1500)
    andar_no_rumo(-38, 0)
    virar_para(63)
    andar(69)
    virar_para(60)
    andar(28)
    virar_para(90)
    andar(27)
    anexo1_ir_para(0)
    andar_ate_travar(20)
    avisar_maker()
    andar(-25)
    voltar_base(de_re=True)


def m4_epis():
    """M4 Segurança no Trabalho — até 100 pts (DP-Middle p.9-10).

    EPI TOCANDO o suporte da mesma cor no pórtico: verde 37, azul 33,
    vermelho 30. Os EPIs ficam com a equipe na base e saem levados pelo robô.
    """
    anexo1_ate_travar(ANTI_HORARIO, forca=50, teto_ms=1500)
    anexo1_aumentar(35, esperar=False)  # o braço sobe enquanto sai
    andar_no_rumo(70, 0, RAPIDO)
    virar_para(25, RAPIDO)
    # Reta + curva + reta: mesmo ponto final de andar(40); virar_para(0);
    # andar(36), sem parar no canto (passa até 0,7 cm por dentro dele).
    andar_no_rumo(33.35, 25, parar=False)
    curva(30, -25)
    andar_no_rumo(29.35, 0)
    virar_para(-55, LENTO)
    andar_no_rumo(54, -55, RAPIDO)
    virar_para(-90, LENTO)
    andar_no_rumo(-3.5, -90)
    avisar_maker()                                  # bonecos entregues: o Maker passa a olhar
    anexo1_ir_para(0)
    andar_no_rumo(-47.5, -90, RAPIDO)
    voltar_base()
    


def m6_carrinho():
    apertar(esperar=False)                          # a garra fecha enquanto anda
    andar_no_rumo(36.69, 0, RAPIDO)
    virar_para(316)
    # Chega rápido e só encosta devagar. O andar_ate_travar(35) não encostava,
    # então o alvo está a mais de 35 cm: o robô passa de RAPIDO para LENTO
    # nos ~11 cm depois dos 25 e chega a ~36 cm já devagar. Com a linha
    # "encostou em X cm" do log, dá para trocar o 25 por (25 + X) - 5 e o 20
    # por uns 10.
    andar_no_rumo(17.69, 318, RAPIDO)
    andar_ate_travar(16)
    # Os dois anexos ao mesmo tempo
    anexo1_ate_travar(ANTI_HORARIO, forca=100, teto_ms=1500, esperar=False)
    anexo2_ate_travar(HORARIO, forca=100, teto_ms=1500)
    esperar_anexos()
    # Se a peça escorregar na ré, volte estas duas para NORMAL.
    andar_no_rumo(-35.5, 321, RAPIDO)
    virar_para(0)
    andar_no_rumo(-40, 0)
    anexo1_ate_travar(HORARIO, forca=100, teto_ms=1500, esperar=True)



def m5_peca():
    """M6 Acesso Seguro — 40 / 17 pts (DP-Middle p.13-14).

    Carrinho DENTRO da área verde: totalmente 40, parcialmente 17.
    """
    andar_no_rumo(69, 0)
    virar_para(90)
    andar_no_rumo(16.5, 90)
    anexo1_ate_travar(ANTI_HORARIO, forca=50, teto_ms=1500, esperar=True)
    andar_no_rumo(-14, 90)
    anexo1_aumentar(35.5)
    virar_para(65)
    anexo1_aumentar(-35.5)
    virar_para(180)
    andar_no_rumo(45, 190)
    anexo1_ir_para(0, esperar=True)
    virar_para(0)
    andar_no_rumo(44.5, 0)
    virar_para(90)
    andar_no_rumo(25.69, 90)
    anexo1_ate_travar(ANTI_HORARIO, forca=65, teto_ms=1500, esperar=True)
    andar_no_rumo(-30, 90)
    anexo1_aumentar(50)
    virar_para(65)
    anexo1_aumentar(-50)
    virar_para(180)
    andar_no_rumo(46.69, 180)
    anexo1_ir_para(0)
    virar_para(0)
    andar_no_rumo(46.69, 0)
    virar_para(90)
    andar_no_rumo(32.80, 90)
    anexo1_ate_travar(ANTI_HORARIO, forca=65, teto_ms=1500, esperar=True)
    andar_no_rumo(-30, 90)
    anexo1_aumentar(35)
    virar_para(65)
    anexo1_aumentar(-35)
    virar_para(180)
    andar_no_rumo(50, 180)
    anexo1_ir_para(0, esperar=False)
    voltar_base(RAPIDO, de_re=True)
    




def m7_bandeira():
    #apertar(forca=100, esperar=True)
    #esperar(1000)
    #
    #anexo1_ate_travar(ANTI_HORARIO, forca=100, teto_ms=1500, esperar=True)
    apertar(forca=100, esperar=True)
    esperar()
    andar_no_rumo(80, 0)
    virar_para(20)
    andar_no_rumo(62.5, 20)
    virar_para(70)
    andar_no_rumo(3, 70)
    parar_tudo()
    anexo1_ate_travar(ANTI_HORARIO, forca=100, teto_ms=1500, esperar=True)
    anexo2_ate_travar(HORARIO, forca=100, teto_ms=1500, esperar=True)
    andar_no_rumo(-5, 70)
    voltar_base(RAPIDO, de_re=True)
    anexo1_ate_travar(HORARIO, forca=100, teto_ms=1500, esperar=False)
    andar_no_rumo(-5, rumo())     # segue a diagonal da volta (rumo ≈ 8)




def m8_maker():
    andar(34)
    virar_para(-90)
    andar(-39)
    virar_para(-180)
    andar(-100, RAPIDO)
    voltar_base(RAPIDO)


def m9_patio():
    avisar_maker()