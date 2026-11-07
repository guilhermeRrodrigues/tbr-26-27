# Parâmetros do Dispositivo Maker v2 (Missão 8, TBR 2026 Middle 2). Tudo em mm.
#
# v2 = versão econômica: só a rampa fina e o Bloco são impressos; hub, sensor,
# motor e trava ficam presos com peças LEGO do kit SPIKE Prime (45678).
# A v1 (base, comporta, prato de teste) está em ../maker_v1/.
#
# Referencial da BANDEJA amarela (usado em todas as peças e na montagem):
#   origem no canto sudoeste INTERNO da bandeja, no nível do tapete;
#   +x para o LESTE (ao longo dos 210 mm), +y para o NORTE (85 mm), +z para cima.
#   A parede sul fica em y de −PAREDE_ESPESSURA a 0; a Área Industrial, ao sul.
#
# Cotas marcadas "# MEDIR" são estimativas: confira com paquímetro e rode
# montagem.py e gerar.py de novo.

# --- LEGO Technic ---------------------------------------------------------------------
# Passo de 8 mm: consenso (e o LDraw usa 20 LDU = 8 mm). As posições dos furos do hub,
# do motor e do sensor vêm do LDraw e caem exatamente nessa grade: LEGO com LEGO
# encaixa sem gabarito. A seção da viga é nominal (fontes citam 7,4 a 7,8): usamos o
# maior valor como envelope de colisão.
PASSO_LEGO = 8.0
VIGA_SECAO = 7.8              # MEDIR: viga grossa (liftarm), altura e espessura
PINO_LADO = 8.0               # pino de 2 módulos: 8 mm de cada lado do colar
PINO_DIAM = 4.8
EIXO_DIAM = 4.8
# Folgas impressas validadas no elevador (modelos3d/elevador/parametros.py).
PINO_FURO = 5.2               # furo de pino Technic impresso (em pé e deitado)
CRUZ_LARGURA = 5.0            # furo em cruz: 4,8 + 0,2
BRACO_LARGURA = 2.0
FOLGA = 0.4                   # folga genérica entre peças

# --- Impressora (Bambu Lab A1 mini) ------------------------------------------------------
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
TRABALHADOR_DIST = (50.0, 200.0)  # faixa em que o robô deixa o trabalhador (da parede sul)

# --- Bloco Overclock (caixa oca, aberta embaixo) --------------------------------------
BLOCO = 45.0                  # cubo: a garra do elevador abre 70 e fecha até 30
BLOCO_TOPO = 1.6              # espessura do topo (fica na mesa de impressão)
BLOCO_PAREDE = 1.2            # laterais (3 linhas de 0,4)
BLOCO_CHANFRO = 2.0           # arestas de fora chanfradas (desliza sem enganchar)
LOGO_LADO = 36.0              # o logo cabe num quadrado deste lado em cada face
LOGO_LINHAS_TOPO = 0.8        # baixo-relevo das linhas no topo
LOGO_CORPO_TOPO = 0.4         # baixo-relevo do corpo da chave no topo
LOGO_LINHAS_LADO = 0.6        # laterais: linhas (sobra 0,6 de parede)
LOGO_CORPO_LADO = 0.3         # laterais: corpo da chave
GARRA_ABERTA = 70.0           # elevador: abertura máxima
GARRA_FECHADA = 30.0          # elevador: fechamento mínimo (com o carro subido)

# --- Rampa fina ---------------------------------------------------------------------------
ANGULO_RAMPA = 30.0           # PLA sobre PLA: atrito ~0,3–0,4 (> 22°); testar antes (LEIAME)
RAMPA_ESPESSURA = 1.6         # placa (na normal): 4 linhas de 0,4
TRILHO_ALTURA = 3.5           # trilhos acima da superfície (a mão-francesa do oeste
                              # entra isto no canal: até ~4 o Bloco ainda passa)
LATERAL_ESPESSURA = 2.0       # lateral leste (treliça), borda oeste e trilhos
BARRA = 3.5                   # largura das barras da treliça
PERNA_PAREDE = 2.0            # perna larga (de lado a lado): espessura da parede
TRAVESSA = 4.0                # travessa da ponta alta, ao longo da descida
JANELA_LARGURA = 5.0          # janelas da placa, ao longo da descida
JANELA_PASSO = 7.5            # de uma janela à próxima (barra de 2,5)
JANELA_MARGEM = 1.0           # da nervura até a janela
JANELA_PONTAS = 6.0           # das pontas da placa até a primeira janela
PRATELEIRA_ESPESSURA = 5.0    # prateleira do motor (o pino entra 5 de 8)
MAO_ESPESSURA = 2.0           # mão-francesa da prateleira
FOLGA_BLOCO = 1.5             # Bloco no canal, por lado
FOLGA_SOBRE_PAREDE = 0.5      # placa acima do topo da parede sul
ASSENTO_FOLGA = 0.3           # assento das laterais acima da parede
GANCHO_DESCIDA = 6.0          # aba que desce por fora da parede sul (trava a rampa em y)
GANCHO_ESPESSURA = 2.4
LABIO_ALTURA = 3.0            # ponta do lábio: no mínimo isto acima do tapete
X_RAMPA_LESTE = BANDEJA_X - FOLGA_BANDEJA   # a rampa encosta na parede leste
NERVURA_LARGURA = 2.0         # nervuras na superfície (menos área de atrito)
NERVURA_ALTURA = 0.8
NERVURAS = 3
BLOCO_CARREGADO_S = 40.0      # MÍNIMO da frente do Bloco carregado, da ponta do lábio (s)

# --- Trava (viga LEGO no eixo do motor, gira no plano da placa) ---------------------------
TRAVA_FUROS = 7               # viga 7M: furos 1 e 3 no disco, furo 2 no eixo

TRAVA_ACIMA = 8.0             # face de baixo da viga acima da superfície (passa sobre o trilho)
GIRO_ABERTURA = 90.0          # graus de motor para abrir (sentido no Pybricks: testar)

# --- Motor médio SPIKE (45603): cotas do LDraw 54696p02c01 -------------------------------
# Corpo de 24 × 72 × 23,6 (fundo até o plano do disco); disco de Ø 23,2 sobressaindo 8,4.
# O eixo atravessa os 23,6, a 11,6 mm de uma ponta. Furos laterais (atravessam os 24) a
# −8, +8 e +56 mm do eixo ao longo do comprimento, a 4 e 20 mm do fundo.
MOTOR_LARGURA = 24.0          # MEDIR
MOTOR_FRENTE = 11.6           # MEDIR: do eixo à ponta curta
MOTOR_TRAS = 60.4             # MEDIR: do eixo à ponta do cabo
MOTOR_ALTURA = 23.6           # MEDIR: do fundo ao plano do disco
MOTOR_DISCO_DIAM = 23.2       # MEDIR
MOTOR_DISCO_SALIENCIA = 8.4   # MEDIR
MOTOR_FUROS_COMPRIMENTO = [-8.0, 8.0, 56.0]
MOTOR_FUROS_ALTURA = [4.0, 20.0]

# --- Hub SPIKE Prime (45601): 88 × 56 × 32 (ficha LEGO); furos do LDraw -----------------
HUB_COMPRIMENTO = 88.0
HUB_LARGURA = 56.0
HUB_ESPESSURA = 32.0
# Pontas (faces de 56 × 32): furos a ±16 mm do meio da largura, a 4, 12 e 20 do fundo.
HUB_FUROS_PONTA = [-16.0, 16.0]
HUB_FUROS_ALTURA = [4.0, 12.0, 20.0]
# Faces longas (88 × 32): furos a ±16 e ±32 do meio do comprimento, mesmas alturas.
HUB_FUROS_LONGA = [-32.0, -16.0, 16.0, 32.0]

# --- Ultrassônico SPIKE (45604): cotas do LDraw 37316c01 ---------------------------------
SENSOR_LARGURA = 56.0         # MEDIR: entre as pontas
SENSOR_ALTURA = 23.2          # MEDIR
SENSOR_PROFUNDIDADE = 31.6    # MEDIR: da frente dos olhos à traseira
SENSOR_OLHOS_ENTRE = 32.0     # MEDIR: centro a centro dos 2 olhos (a meia altura)
SENSOR_FURO_PONTA_FUNDO = 4.0  # MEDIR: furos das pontas a isto da traseira (LDraw)
SENSOR_FUROS_PONTA = [-8.0, 8.0]  # nas pontas: alturas em relação ao meio
SENSOR_ALCANCE = (50.0, 2000.0)   # ficha LEGO: 50 a 2000 mm
SENSOR_FEIXE = 35.0           # ficha LEGO: ângulo de entrada de ±35°
