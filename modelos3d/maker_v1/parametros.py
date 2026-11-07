# Parâmetros do Dispositivo Maker (Missão 8, TBR 2026 Middle 2). Tudo em mm.
#
# Referencial da BANDEJA amarela (usado em todas as peças e na montagem):
#   origem no canto sudoeste INTERNO da bandeja, no nível do tapete;
#   +x para o LESTE (ao longo dos 210 mm), +y para o NORTE (85 mm), +z para cima.
#   A parede sul fica em y de −PAREDE_ESPESSURA a 0; a Área Industrial, ao sul.
#
# Cotas marcadas "# MEDIR" são estimativas: confira com paquímetro antes de
# imprimir e rode montagem.py e gerar.py de novo.

# --- Folgas LEGO validadas no elevador (modelos3d/elevador/parametros.py) ---------
CRUZ_LARGURA = 5.0            # furo em cruz: 4,8 + 0,2 (validado)
BRACO_LARGURA = 2.0
PINO_FURO = 5.2               # furo de pino Technic (validado em pé e deitado)
PINO_PROFUNDIDADE = 8.0       # meio pino de 2 módulos
PASSO_LEGO = 8.0
FURO_EIXO_LIVRE = 5.4         # furo redondo onde um eixo cruz gira solto
FOLGA = 0.4                   # folga genérica entre peças impressas

# --- Impressora (Bambu Lab A1 mini) --------------------------------------------------
VOLUME_IMPRESSAO = 180.0

# --- Bandeja da Missão Maker (medida pela equipe: 21 × 8,5 cm, paredes de 1,5 cm) -
BANDEJA_X = 210.0             # comprimento interno (leste-oeste)
BANDEJA_Y = 85.0              # largura interna (norte-sul)
Z_PAREDE = 15.0               # topo das paredes, medido do tapete
PAREDE_ESPESSURA = 3.0        # MEDIR: MDF de 3 mm (estimado pelas fotos)
Z_FUNDO = 3.0                 # MEDIR: topo do fundo amarelo (MDF de 3 mm sobre o tapete)
FOLGA_BANDEJA = 1.0           # das peças até as paredes internas

# --- Trabalhador (boneco de MDF da TBR) ----------------------------------------------
TRABALHADOR_ALTURA = 80.0     # MEDIR: do tapete ao topo da cabeça
TRABALHADOR_BASE = 40.0       # MEDIR: base quadrada
TRABALHADOR_DIST = (50.0, 200.0)  # faixa em que o robô deixa o trabalhador (da parede sul)

# --- Bloco de Educação Tecnológica ---------------------------------------------------
BLOCO = 45.0                  # cubo: a garra do elevador abre 60 e fecha até 30
BLOCO_CHANFRO = 3.0           # arestas chanfradas: desliza sem enganchar
BLOCO_GRAVACAO = 0.8          # profundidade dos desenhos (baixo-relevo: faces lisas)
GARRA_ABERTA = 60.0           # elevador: abertura máxima
GARRA_FECHADA = 30.0          # elevador: fechamento mínimo

# --- Rampa ------------------------------------------------------------------------------
ANGULO_RAMPA = 30.0           # PLA sobre PLA: atrito ~0,3–0,4 (> 22°); testar no P0
RAMPA_ESPESSURA = 3.0         # placa (na normal)
RAMPA_PAREDE = 3.0            # paredes laterais
FOLGA_BLOCO = 1.5             # bloco no canal, por lado
TRILHO_ALTURA = 14.0          # paredes laterais acima da superfície
FOLGA_SOBRE_PAREDE = 0.5      # placa acima do topo da parede sul
ASSENTO_FOLGA = 0.3           # assento das laterais acima da parede (a rampa apoia no fundo)
GANCHO_DESCIDA = 6.0          # aba que desce por fora da parede sul (trava a rampa em y)
GANCHO_ESPESSURA = 3.0
LABIO_ALTURA = 3.0            # ponta do lábio: no mínimo isto acima do tapete
X_RAMPA_LESTE = BANDEJA_X - FOLGA_BANDEJA   # a rampa encosta na parede leste
NERVURA_LARGURA = 2.0         # nervuras na superfície (menos área de atrito)
NERVURA_ALTURA = 0.8
NERVURA_PASSO = 12.0
# --- Comporta (dente no eixo do motor, sobe por uma fenda da rampa) ---------------------
# O eixo do motor é horizontal (em x) e fica debaixo da placa. O dente gira no plano
# y-z: fechado, fica na normal da placa e sai DENTE_ACIMA pela fenda; para abrir,
# gira GIRO_ABERTURA para BAIXO da rampa (afasta-se do Bloco, não o empurra) e fica
# paralelo à placa, por baixo dela.
DENTE_ACIMA = 10.0            # quanto o dente sobe acima da superfície (fechado)
DENTE_ESPESSURA = 6.0         # ao longo da rampa
DENTE_LARGURA = 6.0           # em x
CUBO_DENTE_DIAM = 12.0        # cubo com furo em cruz
CUBO_DENTE_COMPRIMENTO = 8.0
DIST_EIXO_PLACA = 12.0        # do eixo à superfície da placa, na normal
GIRO_ABERTURA = 90.0          # graus de motor para abrir (o sinal no Pybricks: testar)
FOLGA_FENDA = 1.0             # por lado, dente na fenda
FOLGA_BLOCO_TRAS = 2.0        # do Bloco carregado à parede de trás da rampa
FOLGA_DENTE_TUNEL = 3.0       # dente aberto até o fundo e as paredes da bandeja

# --- Motor médio SPIKE (45603): cotas do LDraw 54696p02c01 ------------------------------
# Tijolo de 3 × 9 × 4 módulos. Deitado: base de 24 × 72, altura de 23,6 até o plano de
# cima, disco por cima. O eixo atravessa a altura, a 11,6 mm de uma ponta; o cabo sai
# pela outra ponta. No Maker ele fica EM PÉ, fora da lateral oeste da rampa: eixo em x,
# disco virado para a rampa, ponta curta embaixo e cabo saindo por cima.
MOTOR_LARGURA = 24.0          # MEDIR
MOTOR_FRENTE = 11.6           # MEDIR: do eixo à ponta curta
MOTOR_TRAS = 60.4             # MEDIR: do eixo à ponta do cabo (comprimento total 72)
MOTOR_ALTURA = 23.6           # MEDIR: do fundo ao plano de cima
MOTOR_DISCO_DIAM = 23.2       # MEDIR
MOTOR_DISCO_SALIENCIA = 8.4   # MEDIR: topo do disco acima do plano de cima
# Furos laterais (atravessam os 24 mm de largura), em relação ao eixo ao longo do
# comprimento, e alturas a partir do fundo. Usados pelos pinos do suporte.
MOTOR_FUROS_COMPRIMENTO = [-8.0, 8.0, 56.0]   # MEDIR
MOTOR_FUROS_ALTURA = [4.0, 20.0]              # MEDIR
EIXO_MOTOR_MODULOS = 3        # eixo LEGO do disco até o dente (3 = 24 mm)
SUPORTE_MOTOR_ESPESSURA = 7.6  # placa de pinos do suporte (pino entra 7,6 de 8)

# --- Hub SPIKE Prime (45601): 11 × 7 × 4 módulos (ficha LEGO + LDraw) --------------------
# EM PÉ sobre a ponta dos botões: 32 mm em x, 56 em y, 88 de altura. A tela e os botões
# ficam virados para o OESTE; as portas ficam nas faces de 88 × 32 (norte e sul): use as
# do SUL. O USB fica em cima (carrega sem tirar o hub).
HUB_COMPRIMENTO = 88.0        # na vertical
HUB_LARGURA = 56.0            # em y
HUB_ESPESSURA = 32.0          # em x
FOLGA_HUB = 0.8               # por lado, na luva
LUVA_ALTURA = 18.0            # paredes da luva acima da base
BOTOES_ALTURA = 12.0          # MEDIR: dos botões até a ponta de baixo do hub
VAO_BOTOES = 18.0             # espaço livre a oeste do hub, para o dedo nos botões
ESPACO_PLUGUES = 20.0         # ao sul do hub: plugues e cabos

# --- Ultrassônico SPIKE (45604): cotas do LDraw 37316c01 --------------------------------
# Deitado, olhando para o sul. Preso por 2 pinos nos furos de trás.
SENSOR_LARGURA = 56.0         # MEDIR: x
SENSOR_ALTURA = 23.2          # MEDIR: z
SENSOR_PROFUNDIDADE = 31.6    # MEDIR: y
SENSOR_OLHOS_ENTRE = 32.0     # MEDIR: centro a centro dos 2 olhos (a meia altura)
SENSOR_FUROS_TRAS_X = 24.0    # MEDIR: furos de trás em ±24, a 12 do fundo
SENSOR_FUROS_TRAS_Z = 12.0
SENSOR_ALCANCE = (50.0, 2000.0)  # ficha LEGO: 50 a 2000 mm (±20)
SENSOR_Z_CENTRO = 50.0        # centro dos olhos acima do tapete
SENSOR_FEIXE = 35.0           # ficha LEGO: ângulo de entrada de ±35°

# --- Base (luva do hub + placa perfurada do sensor) --------------------------------------
BASE_ESPESSURA = 3.0
PLACA_SENSOR_ESPESSURA = 7.6  # placa perfurada (pino entra 7,6 de 8)
GRADE_SENSOR = (7, 5)         # furos (colunas × linhas), passo 8: ajusta altura e lado
