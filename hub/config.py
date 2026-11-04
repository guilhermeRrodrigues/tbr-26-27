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

# --- Elevador (anexo2, porta B) e garra (anexo1, porta F) ----------------------
# Cotas de modelos3d/elevador (LEIAME.md, "Limites para o código do hub").
# Elevador: fuso de 4 entradas, 16 mm por volta => 360 / 1,6 = 225 graus por cm.
# Curso de 19,6 cm (4410 graus). 0 = carro embaixo, onde ele tem de estar na
# largada (caixa de 30 cm). O fuso NÃO se auto-trava: só o hold do B segura.
ELEVADOR_GRAUS_CM = 225.0
ELEVADOR_CURSO_CM = 19.6
# Sinal do motor que SOBE: +1 = horário visto de cima (rosca direita com o
# eixo do B para cima). Se subir() descer, troque para -1.
ELEVADOR_SOBE = 1
# Velocidades do elevador (graus/s de motor) para LENTO / NORMAL / RAPIDO.
# 800 graus/s = 3,6 cm/s: o curso inteiro em ~5,5 s.
ELEVADOR_LENTO = 400
ELEVADOR_NORMAL = 800
ELEVADOR_RAPIDO = 1000
# Força padrão (% do torque). O hold do B é o que segura o carro com peso:
# abaixo de 100 ele pode ceder.
ELEVADOR_FORCA = 100

# Garra: pinhão de 22 dentes (raio primitivo 11 mm) na cremalheira =>
# 180 / (pi x 1,1) = 52,1 graus por cm. Curso de 3 cm (~156 graus): abre até
# 6 cm entre os dedos (batente) e fecha até 3 cm (fundo do túnel).
GARRA_GRAUS_CM = 52.1
GARRA_CURSO_CM = 3.0
GARRA_ABERTA_CM = 6.0
# Sinal do motor que FECHA: +1 = horário visto de cima (o pinhão puxa a barra
# para trás). Se fechar() abrir, troque para -1.
GARRA_FECHA = 1
# Velocidades da garra (graus/s de motor) para LENTO / NORMAL / RAPIDO.
GARRA_LENTO = 150
GARRA_NORMAL = 300
GARRA_RAPIDO = 600
# Força padrão (% do torque do motor) de cada comando. Vale também para o hold
# que segura depois. A garra é de PLA: comece baixo e suba só se não segurar.
GARRA_FORCA = 40            # fechar() e garra_ir_para()
GARRA_FORCA_ABRIR = 30      # abrir(): sem carga, e no batente não precisa mais
GARRA_FORCA_APERTAR = 25    # apertar(): fica empurrando sem parar, então pouca

# --- Giro: fechamento em duas fases (método do Baymax) -----------------------
# Erro maior que GIRO_GROSSO_MIN: manobra de posição (db.turn).
# Erro pequeno: "creep" por velocidade, proporcional ao erro, até GIRO_TOL_SAI.
GIRO_GROSSO_MIN = 8.0   # graus
# Giro grosso por velocidade fechado no giroscópio (True) ou pelo db.turn
# (False, o método antigo: na M5 ele parava com ~15 graus faltando, depois de
# ~1,4 s, e o creep levava mais ~0,7 s para fechar). O grosso por velocidade
# entrega o giro ao creep a GIRO_GROSSO_SAI graus do alvo.
GIRO_POR_VELOCIDADE = True
GIRO_GROSSO_SAI = 2.0   # graus
GIRO_TOL_ENTRA = 2.0    # graus: só corrige acima disto
GIRO_TOL_SAI = 0.8      # graus: e para abaixo disto
CREEP_GANHO = 3.0       # graus/s de guinada por grau de erro
CREEP_TAXA_MIN = 15     # graus/s: abaixo disto o robô não sai do lugar
CREEP_TAXA_MAX = 60     # graus/s

# --- Precisão do rumo (branch giroscopio-fino; ver docs/giroscopio.md) -------
# Cada chave abaixo, com False, volta EXATAMENTE ao comportamento anterior.
#
# GIRO_FINO: o giro termina com FREIO (db.brake), não com coast, e depois,
# com o robô PARADO, mede o erro de verdade e corrige com pulsos curtos nos
# dois sentidos até GIRO_TOL_FINAL. Aprende sozinho quanto o robô ainda gira
# depois do freio e freia antes. Motivo (pbio control.c): com o controle
# ativo, um db.drive novo continua da REFERÊNCIA antiga, e o atraso acumulado
# no giro grosso virava 1 a 6 graus de passada depois do creep.
GIRO_FINO = True
GIRO_TOL_FINAL = 0.5        # graus
FINO_TENTATIVAS = 4         # pulsos de correção, no máximo
FINO_TETO_MS = 1500         # o ajuste fino nunca passa disto
FINO_PARADO = 3.0           # graus/s: abaixo disto o robô parou de girar
FINO_FREIO_MS = 30          # palpite inicial do tempo de freio (ele aprende)
# Com GIRO_FINO, o grosso freia mirando a FINO_GROSSO_SAI do alvo (no lugar de
# GIRO_GROSSO_SAI). Simulador: 0,5 dá p95 de 0,65 grau real e +90 ms por giro
# em relação ao método antigo; 1,0 é ~40 ms mais lento, 0,25 ~25 ms mais
# rápido, com a mesma precisão (docs/giroscopio.md).
FINO_GROSSO_SAI = 0.5

# ANDAR_NO_RUMO: andar() anda pelo andar_no_rumo() no rumo DESEJADO. O
# db.straight segurava o rumo MEDIDO no começo da reta (até 2 graus errado,
# ~35 mm em 1 m) e dava a reta por concluída até ~13 mm antes do fim.
ANDAR_NO_RUMO = True
# RETA_PREVE_FREIO: andar_no_rumo (e andar) freia quando o que falta é o que o
# robô ainda anda depois do freio (velocidade x tempo de freio, aprendido a
# cada reta). Sem isto a reta passava ~4 mm do ponto (simulador).
RETA_PREVE_FREIO = True
RETA_FREIO_MS = 25          # palpite inicial (ele aprende)
# RETA_LIMITE_RODA: nas retas com correção de rumo, a roda mais rápida nunca
# passa disto (mm/s). O motor grande dá ~415-510 mm/s (conforme a bateria);
# em RAPIDO (450) a roda saturava e a reta entortava sem conseguir corrigir.
# 0 = sem limite.
RETA_LIMITE_RODA = 400

# TOLERANCIAS_DB: aperta o "concluído" do DriveBase (curva, sacudir,
# rotinas). O padrão do pbio para roda 56 / bitola 80 é ~18 graus e ~13 mm:
# era o "db.turn parava 15 graus antes". Se o robô parar perto do alvo sem
# chegar à tolerância (atrito), o movimento é aceito parado depois do tempo
# teórico, em vez de esperar o teto.
TOLERANCIAS_DB = True
TOL_DB_RUMO = 2.0           # graus
TOL_DB_RUMO_VEL = 15        # graus/s
TOL_DB_DIST = 3             # mm
TOL_DB_DIST_VEL = 20        # mm/s

# CORRECOES_RUMO:
#  - virar_para(180) a partir de 0 podia NÃO GIRAR (o ruído levava o erro de
#    +180 a -179,99 e o giro achava que já tinha passado): o caminho agora é
#    escolhido uma vez só, no começo do giro;
#  - girar/curva que abortam não deixam o rumo desejado adiantado;
#  - virar_ate_travar fecha o giro quando não travou;
#  - seguir_linha termina com o rumo MÉDIO dos últimos ~200 ms;
#  - a 2ª passada de alinhar_na_linha é mais lenta (ALINHAR_VEL_FINA).
CORRECOES_RUMO = True
ALINHAR_VEL_FINA = 15       # mm/s na passada fina (simulador: p95 0,33 grau, +0,4 s)
# Alinhar que gira mais que isto é esquadro falso (um sensor já começou sobre
# a cor, ou uma roda patinou): devolve False e NÃO reescreve o rumo.
ALINHAR_MAX_GIRO = 15.0     # graus

# --- Largada: o rumo da MESA -------------------------------------------------
# LARGADA_COMPENSADA: o rumo 3D do firmware 4.x acompanha o robô quando ele é
# levantado e posto de volta na base, então a cada largada há DUAS medidas de
# para onde o robô aponta na mesa:
#   - a MÃO de quem soltou ("está na direção da saída"), com erro de
#     LARGADA_SIGMA_MAO graus (a olho ~1,5; com o gabarito ~0,3);
#   - o GIROSCÓPIO ("está d graus torto"), cujo erro cresce com o tempo desde
#     a última referência (deriva do bias + escala no manuseio).
# As duas são FUNDIDAS pelo peso de cada uma (filtro de Kalman de um estado):
# o robô assume que está w.d graus torto, com w = sigma_mao^2 /
# (sigma_mao^2 + sigma_giro^2), e isso vira a nova referência. Simulador: a
# fusão é melhor que só a mão e que só o giroscópio em todas as largadas.
# A 1ª saída (ou a rotina Z) fixa a referência. A direção nominal é o
# múltiplo de LARGADA_PASSO mais perto (0, 90, 180, -90) ou o 3º item da
# tupla em saidas.SAIDAS.
LARGADA_COMPENSADA = True
LARGADA_SIGMA_MAO = 1.5     # graus (1 sigma): 1,5 a olho (hoje); 0,3 quando usarem o GABARITO
LARGADA_DERIVA = 2.0        # graus/min (1 sigma) do rumo da mesa: a rotina D
                            # mede a parte parada; com missões, ~2x o medido
LARGADA_PASSO = 90.0
LARGADA_MAX_DESVIO = 8.0    # graus: mais torto que isto não compensa (avisa)
LARGADA_REF_MAX_S = 600     # referência da mesa mais velha que isto não vale
# Mira no menu: com uma saída selecionada, a luz mostra o desvio ESTIMADO da
# largada (já fundido). Verde: abaixo de LARGADA_MIRA_OK com o giroscópio
# parado; amarela: abaixo de LARGADA_MIRA_PERTO; vermelha: acima.
LARGADA_MIRA = True
LARGADA_MIRA_OK = 0.5
LARGADA_MIRA_PERTO = 2.0

# alinhar_na_base(): esquadreja na MOLDURA da base. Refletância normalizada
# (0 preto .. 100 branco) abaixo da qual o sensor saiu do branco da base.
LIMIAR_BORDA = 60

# --- andar_no_rumo: reta corrigindo para um rumo absoluto --------------------
# Enquanto anda, a guinada é CREEP_GANHO x erro (saturada em CREEP_TAXA_MAX).
# Se o robô começar mais torto que RUMO_VIRAR_ANTES, vira no lugar antes de
# sair (corrigir só andando desviaria muito para o lado: com 20 graus, ~35 mm).
RUMO_VIRAR_ANTES = 8.0  # graus (era 20)
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
# Diagnóstico do giro: cada virar_para/girar imprime quanto levou o giro
# grosso e quanto levou o creep. Serve para acelerar os giros; depois, False.
DIAG_GIRO = True

# Duração da partida (s). O cronômetro começa na 1ª saída e não para.
PARTIDA_S = 120
