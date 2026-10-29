# CoopBot — configuração do robô
# ==============================
# Tudo que descreve o HARDWARE e os limites de movimento mora aqui. As missões
# nunca usam números de porta ou de geometria: elas falam com o tbr.py.
#
# Roda NO HUB (MicroPython/Pybricks). Dialeto do hub: formatação com %, sem
# f-strings, sem anotações de tipo.

from pybricks.parameters import Port, Direction

# --- Portas (informadas pela equipe) -----------------------------------------
PORTA_RODA_DIR = Port.D
PORTA_RODA_ESQ = Port.C
PORTA_ANEXO1 = Port.F
PORTA_ANEXO2 = Port.B
PORTA_COR_DIR = Port.A
PORTA_COR_ESQ = Port.E

# Os motores de tração são montados ESPELHADOS (CoopBot.pdf p.17): um dos dois
# é invertido para os dois empurrarem o robô para a frente com o mesmo sinal.
# Conferido na rotina "P" em 2026-10-28: com DIR=CLOCKWISE/ESQ=COUNTERCLOCKWISE o
# robô andava PARA TRÁS, então é o direito que fica invertido.
# Se o robô girar no lugar quando devia andar reto, só um dos dois está errado.
SENTIDO_RODA_DIR = Direction.COUNTERCLOCKWISE
SENTIDO_RODA_ESQ = Direction.CLOCKWISE
SENTIDO_ANEXO1 = Direction.CLOCKWISE
SENTIDO_ANEXO2 = Direction.CLOCKWISE

# --- Geometria padrão (usada enquanto não houver calibração gravada) ---------
# Roda grande do kit SPIKE (pneu azul-claro), transmissão direta: 56 mm.
# Bitola ESTIMADA pelo manual de montagem (~10 studs). Calibre com a rotina "B".
RODA_MM = 56.0
BITOLA_MM = 80.0

# Faixas de sanidade: um valor fora delas no storage é tratado como corrompido.
RODA_MIN, RODA_MAX = 40.0, 100.0
BITOLA_MIN, BITOLA_MAX = 50.0, 250.0

# Refletância padrão dos sensores de cor (0-100) até rodar a rotina "C" (Cor).
PRETO_PADRAO = 10
BRANCO_PADRAO = 90

# --- Velocidades (mm/s) --------------------------------------------------------
# Motor grande SPIKE ~1000 graus/s em vazio => ~480 mm/s com roda de 56 mm.
# Use RAPIDO só em trecho livre: patina e perde precisão.
VEL_LENTO = 150
VEL_NORMAL = 300
VEL_RAPIDO = 450
ACEL_RETA = 600         # mm/s^2
VEL_GIRO = 180          # graus/s no giro grosso
ACEL_GIRO = 720         # graus/s^2

# Velocidade dos anexos (graus/s de motor)
VEL_ANEXO = 500

# --- Giro: fechamento em duas fases (método do Baymax) -----------------------
# Erro maior que GIRO_GROSSO_MIN: manobra de posição (db.turn).
# Erro pequeno: "creep" por velocidade, proporcional ao erro, até GIRO_TOL_SAI.
GIRO_GROSSO_MIN = 8.0   # graus
GIRO_TOL_ENTRA = 2.0    # graus: só corrige acima disto
GIRO_TOL_SAI = 0.8      # graus: e para abaixo disto
CREEP_GANHO = 3.0       # graus/s de guinada por grau de erro
CREEP_TAXA_MIN = 15     # graus/s: abaixo disto o robô não sai do lugar
CREEP_TAXA_MAX = 60     # graus/s

# --- Seguidor de linha (controle PD sobre a refletância normalizada) --------
# Erro = refletância normalizada (0 preto .. 100 branco) - 50 (meio da borda).
SEGUIR_KP = 1.2         # graus/s de guinada por ponto de erro
SEGUIR_KD = 6.0
SEGUIR_VEL = 200        # mm/s padrão

# Limiar normalizado (0-100) para "estou vendo preto" / "estou vendo branco".
LIMIAR_PRETO = 25
LIMIAR_BRANCO = 75

# --- Segurança ----------------------------------------------------------------
PERIODO_MS = 10         # período dos laços de controle
STALL_ABORTA_MS = 700   # travado por mais que isto => aborta o movimento
TETO_MIN_MS = 2000      # nenhum movimento tem teto menor que isto
# Teto de cada movimento = TETO_FATOR x tempo teórico + TETO_MIN_MS.
TETO_FATOR = 3

# Duração da partida (s). O cronômetro começa na 1ª saída e não para.
PARTIDA_S = 120
