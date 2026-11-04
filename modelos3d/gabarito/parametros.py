# Parâmetros do Gabarito de Largada do CoopBot (TBR 2026 Middle 2). Tudo em mm.
#
# Referencial da BASE (usado em todo o projeto):
#   origem no canto INTERNO de trás-esquerda da base, isto é, onde a borda interna
#   da faixa verde de trás encontra a da esquerda; +x para a DIREITA (lateral),
#   +y para a FRENTE (vista de cima, o robô olhando para +y no giro 0°).
#   Ângulos de giro do robô: sentido anti-horário visto de cima, a partir de +y.
#
# ====================================================================================
# MEDIR AMANHÃ (tudo o que está marcado "# MEDIR" abaixo é PROVISÓRIO)
#   1. BASE_X, BASE_Y     tamanho INTERNO da base (borda interna da faixa verde, de
#                         lado a lado). Hoje: 300 × 300, chute.
#   2. FAIXA_LARG         largura da faixa verde (só para o desenho e as janelas).
#   3. ROBO_L, ROBO_W     comprimento (frente-trás) e largura do robô, medidos na
#                         altura dos batentes, com os anexos recolhidos na posição de
#                         largada.
#   4. TRAS_U / FRENTE_U  onde a traseira (e a frente) do robô tem MATERIAL para
#                         encostar: duas posições, o mais afastadas que der, medidas
#                         a partir do centro da face (+ = esquerda do robô).
#   5. LADO_U e LATERAL_UNICO_U   idem para as laterais (+ = para a frente).
#   6. BATENTE_Z0, BATENTE_Z1     altura (do tapete) em que a face do robô tem
#                         material nesses pontos. Os batentes precisam cobrir essa
#                         faixa de alturas.
#   7. ROBO_VAO_CHAO      vão livre sob a traseira/lateral do robô nos pontos de
#                         contato (a placa de 3 mm NÃO pode ficar sob o robô).
#   8. DIST_TRAS, DIST_LAT   distância que a equipe QUER entre o robô e a borda
#                         interna da faixa (trás e esquerda). É a posição de largada
#                         que as missões assumem.
#   9. Largura da roda (RODA_LARG) e a posição das rodas ao longo do robô, para saber
#                         se um batente lateral cai na roda.
#  10. A cor/contraste real da faixa verde-escura contra a placa (PLA branco, cinza ou
#      claro dá mais contraste do que preto) e se o tapete é fosco (escorrega pouco).
#  11. Perguntar ao juiz: o gabarito é "objeto estratégico" permitido? Pode encostar
#      na faixa? (ver LEIAME.md)
# ====================================================================================

# --- Impressora (Bambu Lab A1 mini) -----------------------------------------------------
VOLUME_IMPRESSAO = 180.0
MARGEM_PRATO = 5.0            # folga de cada lado do prato (borda, limpeza do bico)

# --- Base no tapete ---------------------------------------------------------------------
BASE_X = 300.0                # MEDIR: lado interno da base, na direção x (largura)
BASE_Y = 300.0                # MEDIR: lado interno da base, na direção y (profundidade)
FAIXA_LARG = 12.0             # MEDIR: largura da faixa verde-escura (10 a 15 mm)

# --- Robô (SPIKE Prime, retângulo que envolve o chassi na posição de largada) -----------
ROBO_L = 190.0                # MEDIR: comprimento frente-trás
ROBO_W = 140.0                # MEDIR: largura
RODA_DIAM = 56.0              # roda do CoopBot
RODA_LARG = 25.0              # MEDIR: largura do pneu
RODA_F = 0.0                  # MEDIR: posição do eixo das rodas a partir do centro do robô (+ = frente)
ROBO_VAO_CHAO = 6.0           # MEDIR: vão sob a face do robô nos pontos de contato
BATENTE_Z0 = 6.0              # MEDIR: o robô tem material de z = Z0 ...
BATENTE_Z1 = 20.0             # MEDIR: ... até z = Z1 nos pontos de contato

# --- Onde a equipe quer o robô (posição de largada nominal) ------------------------------
DIST_TRAS = 25.0              # MEDIR/DECIDIR: da borda interna de trás até a face do robô
DIST_LAT = 25.0               # MEDIR/DECIDIR: da borda interna da esquerda até a lateral

# --- Pontos de contato no robô, a partir do CENTRO de cada face ---------------------------
# Face de trás/frente: u > 0 é a ESQUERDA do robô. Faces laterais: u > 0 é a FRENTE.
TRAS_U = 45.0                 # MEDIR: dois contatos na traseira, em ±TRAS_U
FRENTE_U = 45.0               # MEDIR: dois contatos na frente, em ±FRENTE_U
LADO_U = 40.0                 # MEDIR: dois contatos numa lateral que encoste na aresta de trás
# Contato ÚNICO quando a face encosta na aresta lateral (esquerda da base):
LATERAL_UNICO_U = {"tras": -5.0, "frente": 5.0, "esq": -30.0, "dir": 30.0}   # MEDIR (chute)

# --- Giros de largada suportados ---------------------------------------------------------
ORIENTACOES = (0, 90, 180, 270)   # graus anti-horário a partir de +y; 0 = batentes fixos

# --- Gabarito (L) ---------------------------------------------------------------------------
ARESTA_COMP = 168.0           # comprimento das duas arestas de referência (cabe no prato)
PLACA = 3.0                   # espessura da placa
FOLGA_PLACA = 3.0             # a placa termina FOLGA_PLACA antes da face do robô; o batente
                              # avança esses mm (a placa nunca fica sob o robô)
NERV_LARG = 3.0               # nervura ao longo da aresta de referência (largura)
NERV_ALT = 3.0                # altura da nervura acima da placa
BISEL = 2.0                   # bisel de 45° no topo da face externa da aresta (fica fina)
JANELA_COMP = 10.0            # comprimento do entalhe de mira (ao longo da aresta)
JANELA_FUNDO = 6.0            # profundidade do entalhe para dentro da placa
JANELA_S_PERTO = 28.0         # centro da janela perto do canto, medido do canto externo
JANELA_S_PONTA = 10.0         # centro da janela perto da ponta, medido a partir da ponta
INDICE_LARG = 0.6             # marca de índice: sulco que sai da janela
INDICE_FUNDO = 0.5
INDICE_COMP = 4.0

# Alça de levantar (aba em pé na diagonal do canto, com furo em losango sem suporte)
ALCA_COMP = 26.0              # ao longo da diagonal
ALCA_ESP = 4.0
ALCA_ALT = 24.0
ALCA_FURO = 7.0               # meia-diagonal do losango

H_BATENTE = 6.0               # MEDIR: altura da face de contato ACIMA da placa (topo a 9 mm do tapete);
                              # tem de cair dentro de BATENTE_Z0..Z1 do robô

# Batentes (calços): bloco que vai por cima da placa e avança além da aresta interna.
CALCO_LARG = 12.0             # ao longo da aresta
CALCO_RECUO = 10.0            # quanto o calço apoia sobre a placa, atrás da aresta
CALCO_PEG = 4.8               # pino impresso (mesmo diâmetro do pino LEGO Technic)
FURO_PEG = 5.0                # furo (4,9–5,0 como no resto do repositório)
CALCO_PEG_V = 6.0             # posição do pino, atrás da aresta interna
CALCO_LABIO = 1.2             # espessura do lábio que desce e encosta na aresta interna
MARCA_DIAM = 2.4              # pontos gravados que dizem qual giro é cada furo
MARCA_FUNDO = 0.4

# --- Tolerâncias para a conta de ângulo (montagem.py) --------------------------------------
TOL_ALINHAR = 0.5             # erro de olho ao alinhar a aresta na linha, em cada janela
TOL_BATENTE = 0.25            # folga/erro de contato por batente (peg 0,2 + robô 0,05)
