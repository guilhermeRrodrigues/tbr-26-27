# Parâmetros do elevador do CoopBot (versão 2). Tudo em mm, salvo onde indicado.
#
# Referencial do robô (usado em todas as peças e na montagem):
#   origem no eixo do motor F, no chão;
#   +y para a FRENTE (para-choque), +x para a DIREITA do robô, +z para cima.
#   O eixo do motor B fica em (0, -DIST_F_B).
#
# Medidas do robô vêm do usuário e das fotos IMG_1616 a IMG_1640. Ajuste aqui;
# nenhuma peça tem cota fixa no código.
#
# Versão 2 (depois do teste da v1): motores em alturas diferentes (B 25 mm acima
# do F), dedos de 20 cm com 3 ganchos, curso de ~20 cm dentro do limite de 30 cm
# de altura na largada (Vade Mecum TBR, Middle 2), hastes e torre emendadas para
# caber na A1 mini.

# --- Eixo LEGO (cruz de 4,8 mm, braço de 1,8 mm) ------------------------------
# Folga somada à cota nominal. Validada: 0,2 mm entrou bem na placa.
CRUZ_NOMINAL = 4.8
BRACO_NOMINAL = 1.8
FOLGA_EIXO = 0.2

CRUZ_LARGURA = CRUZ_NOMINAL + FOLGA_EIXO    # 5.0
BRACO_LARGURA = BRACO_NOMINAL + FOLGA_EIXO  # 2.0

# --- Pino Technic --------------------------------------------------------------
# Furo vertical validado: 5,2 mm entrou firme (5,0 não entrou).
PINO_FURO = 5.2
PINO_PROFUNDIDADE = 8.5       # metade do pino de 2 módulos (8 mm) + folga
# Furo deitado (eixo horizontal na impressão): a confirmar na placa de teste
# (teste_mancal.py, furos de 5,2 e 5,4).
PINO_FURO_DEITADO = 5.2

# --- Impressora (Bambu Lab A1 mini) ---------------------------------------------
VOLUME_IMPRESSAO = 180.0      # cubo útil; gerar.py recusa peça maior

# --- Regulamento: limite de altura na largada ----------------------------------
ALTURA_MAX_INICIO = 300.0     # Middle 2: base de 30 cm de altura (Vade Mecum TBR)
MARGEM_ALTURA = 8.0           # nada passa de 292 mm com o carro embaixo

# --- Motores (fuso no B, garra no F) ------------------------------------------
MOTOR_FUSO = "B"              # porta B (Anexo2): elevador
MOTOR_GARRA = "F"             # porta F (Anexo1): garra
DIST_F_B = 25.0               # centro a centro em y (validado)
Y_EIXO_F = 0.0
Y_EIXO_B = -DIST_F_B
Z_MOTOR_F = 40.0              # face giratória do F (de baixo)
Z_MOTOR_B = 65.0              # face giratória do B: 25 mm acima do F (teste da v1)
RAIO_MOTOR = 12.0             # disco giratório (3 módulos de diâmetro)
RAIO_CORPO_MOTOR = 12.5       # corpo do motor abaixo da face (zona proibida)

# --- Robô: vigas, para-choque, hub e cabos -------------------------------------
Z_VIGAS = 60.0                # topo das vigas preta e cinza
X_VIGA = 42.5                 # vigas a ±42,5 (85 mm entre si); cinza em −x, preta em +x
FUROS_VIGA_Y = [0.0, -8.0, -16.0]  # furos livres: linha do F e para trás

Y_FRENTE = 25.0               # frente do para-choque
FRENTE_ALTURA_CENTRO = 35.0   # topo do para-choque no centro
FRENTE_ALTURA_LATERAL = 55.0  # molduras magenta laterais
X_LATERAL = 55.0              # a partir daqui valem as molduras laterais
FOLGA_FRENTE = 4.0            # folga pedida sobre o para-choque
LARGURA_ROBO = 135.0

Y_HUB = -35.0                 # hub e cabos atrás disto (≈10 mm atrás do B)
Z_TOPO_HUB = 95.0             # topo do hub, ESTIMADO pelas fotos de 31/10: medir no robô
X_CABOS = 22.0                # cabos descem ao lado dos motores em |x| > 22
X_CABOS_FIM = 34.0            # largura da faixa reservada aos cabos

# --- Elevador -----------------------------------------------------------------
Z_CARRO_MIN = Z_MOTOR_B + 1.0  # 66: fundo do carro embaixo, 1 mm acima da face do B
CURSO_ELEVADOR = 196.0        # múltiplo do passo (a fase da rosca se repete)
Z_DEDO_FUNDO_BAIXO = 10.0     # fundo dos dedos com o carro embaixo
# Fundo dos dedos: de 10 (embaixo) a 206 mm (em cima). Pedido: 20 cm.

# --- Garra ----------------------------------------------------------------------
ABERTURA_GARRA = 70.0         # abertura máxima entre os dedos (7 cm; era 6 até 5/11/2026)
CURSO_GARRA = 40.0            # fecha de 70 até 30 mm (era 30 de curso até 6/11/2026).
                              # Aberta, a cremalheira está no último dente. Fechada, a
                              # traseira da barra passa 8 mm da frente do hub: até 30 mm
                              # só com o carro SUBIDA_FECHAR_TUDO acima do fundo; com o
                              # carro embaixo, o hub para a barra em ~38 mm
SUBIDA_FECHAR_TUDO = 32.0     # carro acima do fundo: a barra passa sobre o hub. Múltiplo
                              # do passo do fuso, para a rosca casar na montagem.py
ALCA_MISSAO4 = 25.0           # vão da alça da missão 4 (2,5 cm)

# --- Fuso (rosca trapezoidal de 4 entradas, validada) --------------------------
PASSO_FUSO = 4.0              # passo axial de uma entrada
ENTRADAS_FUSO = 4
AVANCO_FUSO = PASSO_FUSO * ENTRADAS_FUSO  # 16 mm por volta
DIAM_FUSO = 14.0
DIAM_RAIZ_FUSO = 10.0
MEIA_LARGURA_DENTE_FUSO = PASSO_FUSO / 2 - 0.1  # 1,9: dente de 3,8 mm na raiz
MEIA_CRISTA_FUSO = 0.4
FOLGA_ROSCA = 0.3             # folga radial da porca (validada)
COMPRIMENTO_TESTE_FUSO = 15.0 # fuso de teste (fuso_teste.py)

# --- Hastes impressas (em 2 segmentos, unidos por eixo LEGO curto) -------------
# Cada haste encaixa, pelo soquete em cruz, no eixo LEGO curto do motor. Os dois
# segmentos se unem por um eixo LEGO de 3 ou 4 módulos nos soquetes da emenda;
# a cruz tem simetria de 90°, igual à rosca de 4 entradas (girar 90° = 1 passo)
# e à haste quadrada: qualquer orientação de encaixe serve.
SOQUETE_PROFUNDIDADE = 26.0   # no eixo curto do motor
EMENDA_PROFUNDIDADE = 17.0    # de cada lado da emenda (eixo de 4 módulos = 32)
ROSCA_COMPRIMENTO = 212.0     # rosca de z 65 a 277 (53 passos)
ROSCA_SEG1 = 108.0            # 1º segmento do fuso (27 passos): emenda em z 173
GARRA_SEG1 = 120.0            # 1º segmento da haste da garra: emenda em z 160
Z_TOPO_HASTES = Z_MOTOR_B + ROSCA_COMPRIMENTO  # 277: topo da rosca e da haste quadrada
QUADRADO_GARRA = 10.0         # haste da garra: quadrado de 10 mm (era sextavado)
COLAR_ALTURA = 3.0            # colar acima da rosca/quadrado (fica 1 mm sob a travessa)
DIAM_COLAR_FUSO = 11.0
DIAM_COLAR_GARRA = 12.0
DIAM_MUNHAO_FUSO = 8.0        # munhão do fuso na travessa
DIAM_MUNHAO_GARRA = 6.0       # munhão da haste da garra na travessa
MUNHAO_COMPRIMENTO = 8.0
FOLGA_MANCAL = 0.6            # diametral: 0,4 da v1 prendeu; 0,6 ficou melhor na placa de teste
FOLGA_QUADRADO = 0.6          # entre faces: 0,4 entrou bem apertado na placa de teste
ALIVIO_CANTO_QUADRADO = 0.5   # raio do alívio nos cantos do furo quadrado do pinhão
FOLGA_FURO_HASTE = 0.6        # diametral, haste passando pelo carro
TOLERANCIA_F_B = 1.5          # rasgo em y para o eixo F (erro na distância F–B)

# --- Carro (porca, pinhão, túnel, braço, batente, encaixe do dedo fixo) --------
CARRO_ALTURA = 14.0           # 3,5 passos engrenados (validado)
CARRO_X = (-15.0, 20.5)
CARRO_Y = (-34.5, 33.0)       # traseira a 0,5 mm da zona do hub
CARRO_CHAPA_BAIXO = 4.0       # chapa de baixo; acima dela, bolso do pinhão e túnel
VAO_ALTURA = 6.6              # altura do bolso do pinhão e do túnel
PAREDE_CARRO = 2.5            # parede mínima nos alívios do carro
FAIXA_DEDO_Y = 22.0           # faixa da frente do carro (y 22..33): pinos do dedo fixo
# Pares de pinos no passo LEGO (8 mm): uma viga Technic também encaixa no carro
# e na sapata. Com 11 mm, só os dedos impressos encaixavam.
PASSO_LEGO = 8.0
PINOS_DEDO_FIXO_X = [-7.5, 0.5]  # pinos deitados (em y), à esquerda do túnel
Z_PINOS_DEDO_FIXO = 7.0       # altura dos pinos no carro (acima do fundo)

# --- Pinhão e cremalheira (módulo 1) -------------------------------------------
MODULO = 1.0
DENTES_PINHAO = 22            # raio primitivo 11 mm
PINHAO_ALTURA = 6.0
FOLGA_DENTE = 0.1             # espessura retirada de cada dente (validada)
FOLGA_BOLSO = 0.5             # raio, pinhão no bolso do carro

BARRA_LARGURA = 6.0           # corpo da barra atrás da raiz dos dentes
BARRA_ALTURA = 6.0
FOLGA_TUNEL = 0.3             # barra no túnel, por lado
DENTES_CREMALHEIRA = 15       # 47 mm de dentes: cobre o curso de 40 mm
Y_BARRA_ABERTA = -3.0         # traseira da barra com a garra aberta
Y_BARRA_FECHADA = Y_BARRA_ABERTA - CURSO_GARRA  # −43: 8,5 mm atrás do carro
# Cauda da barra: a ponta sai pela traseira do carro, e essa boca do túnel é impressa
# no ar (a parede atravessa 8,6 mm sem apoio e cede para dentro do túnel). O trecho
# que passa por ela fica mais baixo, com rampa na ponta. Só na face de baixo: o topo
# da barra fica na mesa de impressão. Medidas a partir da traseira da barra.
CAUDA_COMPRIMENTO = 11.0      # fechada, 9 mm da barra passam da boca; o furo do pino
                              # começa em 11,3 e precisa do fundo inteiro
CAUDA_ALIVIO = 0.6            # rebaixo: a folga por baixo sobe de 0,3 para 0,9 mm
CAUDA_RAMPA = 1.2             # chanfro de 45° na ponta, além do rebaixo

# --- Batente de abertura (a v1 desengatava ao abrir demais) --------------------
# Pino impresso que entra pelo rasgo da chapa de cima do carro num furo cego da
# barra. A barra tem 6 mm de largura: Ø 3 deixa parede de 1,3 mm. O túnel é aberto
# atrás, então o pino também é o batente de fechamento, na outra ponta do rasgo.
BATENTE_Y_BARRA = 13.0        # furo do batente: 13 mm da traseira da barra (era 3:
                              # fechada, o pino sairia pela traseira do carro)
BATENTE_DIAM = 3.0
BATENTE_FURO = 3.4            # furo cego na barra
BATENTE_FURO_PROF = 5.0
BATENTE_RASGO = 3.8           # largura do rasgo na chapa de cima do carro
BATENTE_CABECA = 6.0          # Ø da cabeça (fica 0,5 mm acima do carro)
BATENTE_CABECA_ALTURA = 1.5

# --- Dedos (peças próprias, presas por pinos Technic deitados em y) ------------
# Cada dedo é uma placa vertical de 200 mm. Os pinos entram pela frente: no
# dedo fixo, da face da frente do carro; no móvel, da sapata na ponta da barra.
# A nervura de rigidez e os ressaltos dos pinos ficam na FRENTE de cada placa,
# acima da área de aperto (que fica abaixo do carro).
DEDO_LARGURA = 200.0          # 3 caixas lado a lado (18 cm) com folga
DEDO_ESPESSURA = 3.0
DEDO_DESCIDA = Z_CARRO_MIN - Z_DEDO_FUNDO_BAIXO  # 56: fundo do dedo abaixo do fundo do carro
NERVURA_Y = 5.0               # nervura de topo, na frente de cada dedo (rigidez)
NERVURA_Z = 3.0
# A placa só tem os 200 mm na faixa de aperto de baixo; acima dela, uma haste
# central com mãos-francesas a 45° liga a faixa ao carro (menos material).
FAIXA_APERTO = 36.0           # altura da faixa larga (pega caixas de 5 cm)
HASTE_DEDO_X = (-17.0, 26.0)  # haste central (cobre os pinos, a janela e a sapata)
MAO_FRANCESA = 30.0           # cateto das mãos-francesas a 45°
RESSALTO_PINO = 8.0 - DEDO_ESPESSURA  # ressalto na frente da placa: 8 mm de pino no dedo
Y_DEDO_FIXO = CARRO_Y[1]      # 33: face de trás do dedo fixo, encostada no carro
GANCHOS_X = [-83.0, 0.0, 83.0]  # 1,7, 10 e 18,3 cm da ponta esquerda do dedo
GANCHO_LARGURA = 16.0         # cabe no vão de 25 mm da alça
GANCHO_COMPRIMENTO = 7.0      # para a frente, a partir do dedo fixo
GANCHO_ESPESSURA = 3.0
SAPATA_X = (6.0, 24.0)        # sapata na ponta da barra, onde prende o dedo móvel
SAPATA_Y = 8.5                # comprimento da sapata (profundidade do pino)
SAPATA_Z = (2.3, 10.3)        # altura da sapata (carro: z 0 no fundo)
PINOS_DEDO_MOVEL_X = [11.0, 19.0]  # passo LEGO, centrado na sapata

# --- Torre (2 colunas emendadas + portal com a travessa) -----------------------
TRAVESSA_ESPESSURA = 8.0
Z_TRAVESSA = Z_TOPO_HASTES + COLAR_ALTURA + 1.0  # 281: 1 mm acima dos colares
TRAVESSA_Y = (-32.0, 6.0)
COLUNA_LARGURA = 14.0         # x do bloco de pinos e da coluna
COLUNA_Y = (-22.0, 6.0)       # bloco de pinos: cobre os 3 furos da viga
BLOCO_PINOS_ALTURA = 10.0
COLUNA_SECAO = 14.0           # y da coluna, centrada em Y_COLUNA
Y_COLUNA = -8.0
TRAVESSA_VIGA_Y = 10.0        # largura em y da viga transversal da travessa
TRAVESSA_MIOLO_X = 9.0        # meia largura da parte central (mancais F e B)
RASGO_VIGA_X = 2.0            # rasgo ±2 nos furos da coluna direita (medida de 85 mm)
Z_EMENDA_TORRE = 175.0        # topo das colunas de baixo (início do portal)
ESPIGA_X = 9.0                # espiga da coluna de baixo, dentro do portal
ESPIGA_Y = 10.0
ESPIGA_ALTURA = 16.0
FOLGA_ESPIGA = 0.4            # total, espiga no encaixe
