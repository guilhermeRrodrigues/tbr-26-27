# CoopBot — configuração do robô
# ==============================
# Tudo que descreve o HARDWARE e os limites de movimento mora aqui. As missões
# nunca usam números de porta ou de geometria: elas falam com o tbr.py.
#
# Roda NO HUB (MicroPython/Pybricks). Dialeto do hub: formatação com %, sem
# f-strings, sem anotações de tipo.

from pybricks.parameters import Port, Direction

# --- Portas (informadas pela equipe) -----------------------------------------
# D e C TROCADAS em relação ao informado: com D como direita, o robô girava ao
# contrário do giroscópio (virar_para(90) terminou em -216 graus, travado). A
# rotina "P" confere isso sozinha e acusa "X" se ainda estiver invertido.
PORTA_RODA_DIR = Port.C
PORTA_RODA_ESQ = Port.D
PORTA_ANEXO1 = Port.F
PORTA_ANEXO2 = Port.B
PORTA_COR_DIR = Port.A
PORTA_COR_ESQ = Port.E

# Os motores de tração são montados ESPELHADOS (CoopBot.pdf p.17): um dos dois
# é invertido para os dois empurrarem o robô para a frente com o mesmo sinal.
# Os sentidos acompanham o MOTOR, não o lado: a porta D é COUNTERCLOCKWISE e a C
# é CLOCKWISE (conferido em 2026-10-28: assim o robô anda para a frente).
# Se o robô girar no lugar quando devia andar reto, só um dos dois está errado.
SENTIDO_RODA_DIR = Direction.CLOCKWISE           # porta C
SENTIDO_RODA_ESQ = Direction.COUNTERCLOCKWISE    # porta D
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
# Aceleração: quanto maior, menos tempo arrancando e freando em cada comando.
# 800 / 1000 conferido na mesa (era 600 / 720). Próximo degrau: 1000 / 1200;
# se patinar na arrancada ou a peça escorregar no anexo, volte um degrau.
ACEL_RETA = 800         # mm/s^2
VEL_GIRO = 180          # graus/s no giro grosso (padrão = NORMAL)
# girar(90, LENTO) / virar_para(-180, RAPIDO): as constantes de velocidade da
# reta valem também no giro, traduzidas para estes graus/s. Um número que não
# seja uma das três constantes é usado direto como graus/s.
GIRO_LENTO = 90
GIRO_NORMAL = VEL_GIRO
GIRO_RAPIDO = 300
ACEL_GIRO = 1000        # graus/s^2

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

# --- andar_no_rumo: reta corrigindo para um rumo absoluto --------------------
# Enquanto anda, a guinada é CREEP_GANHO x erro (saturada em CREEP_TAXA_MAX).
# Se o robô começar mais torto que RUMO_VIRAR_ANTES, vira no lugar antes de
# sair (corrigir só andando desviaria muito para o lado).
RUMO_VIRAR_ANTES = 20.0 # graus
RUMO_VEL_FINAL = 40     # mm/s: velocidade mínima da rampa de frenagem

# --- sacudir: vai e vem curtinho para assentar/soltar/encaixar ---------------
# Amplitudes padrão (a missão pode passar outras). Acelerações mais altas que
# as da reta e do giro: com as normais, um vai e vem de 1 cm mal sai do lugar.
SACUDIR_CM = 1.0        # cm para a frente e para trás
SACUDIR_GRAUS = 6.0     # graus para cada lado
SACUDIR_ACEL_RETA = 1500    # mm/s^2
SACUDIR_ACEL_GIRO = 1500    # graus/s^2

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
# Andando sem sair do lugar (encostado em algo que cede): menos que isto em
# STALL_ABORTA_MS => aborta a reta ou a curva.
PROGRESSO_MIN_MM = 10
TETO_MIN_MS = 2000      # nenhum movimento tem teto menor que isto
# Teto de cada movimento = TETO_FATOR x tempo teórico + TETO_MIN_MS.
TETO_FATOR = 3

# Cronômetro por comando: com True, cada comando da linguagem imprime quanto
# levou (aparece no terminal do `tbr rodar`). Sem PC conectado o print não
# vai a lugar nenhum, mas na competição pode deixar False.
CRONOMETRO = True

# Duração da partida (s). O cronômetro começa na 1ª saída e não para.
PARTIDA_S = 120
