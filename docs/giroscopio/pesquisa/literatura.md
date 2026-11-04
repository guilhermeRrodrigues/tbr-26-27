# Literatura: giro no lugar, retas e deriva de gyro (SPIKE Prime + Pybricks)

Legenda de evidência: [A] fonte primária (código/doc/datasheet) lida nesta pesquisa; [B] relato de comunidade/issue com número; [C] conhecimento de engenharia geral (não verificado nesta busca); [F] folclore/sem medição.
Limite honesto: a busca web não achou Allan variance publicada do LSM6DS3TR-C, nem medições de equipes de topo com "erro final <=0,5 graus". Onde isso falta, está dito.

## 1. O que o Pybricks realmente faz com o gyro (fonte primária)

Fonte: código `lib/pbio/src/imu.c` (https://raw.githubusercontent.com/pybricks/pybricks-micropython/master/lib/pbio/src/imu.c) e docs https://docs.pybricks.com/en/latest/hubs/primehub.html [A]. Resumo do que o fetch devolveu (resumido por modelo de leitura; confirmar constantes no fonte):

- Bias é uma média móvel atualizada SEMPRE que o hub está "parado": a cada atualização o peso é 1/n nas primeiras 20 (média cumulativa) e depois 0,05 fixo (constante de tempo ~20 atualizações). Parado exige: IMU parado (|omega|<2 deg/s e |a|<2500 mm/s2 por ~1 s, os defaults de `imu.settings`) E todos os motores em coast (`pbio_dcmotor_all_coasting`). Ou seja: motor segurando posição (hold) ou DriveBase ativa NÃO recalibra.
- `imu.ready()`: False após boot ou se passaram >10 min sem estar parado; aí o contador reseta e os novos dados têm peso alto.
- Bias inicial persistido: `angular_velocity_bias` é só valor inicial pós-boot; o bias continua sendo atualizado. Se a flag não estiver setada e houver >2 atualizações paradas, salva uma vez.
- Escala: omega_cal = (omega_raw - bias) * 360 / angular_velocity_scale[eixo]; heading 1D = -z * (360/heading_correction). Setters aceitam apenas valores dentro de 360 +-15.
- Temperatura: NENHUM tratamento no firmware (sem entrada de temperatura, sem compensação).
- Heading é integral do z calibrado, em float, SEM unwrap em +-180 (cresce).
- Issue #1886 (https://github.com/pybricks/support/issues/1886) [B/A]: arredondamento interno entre IMU e controle de motor gerava até ~1-2 graus de discrepância em giros grandes (720,3 virava 722). Corrigido em out/2024 (commit 900ae17). Lição: versões do firmware anteriores a esse fix tinham erro de heading no controlador do DriveBase; confira a versão (>=3.6 pós-fix). Maintainer: float no controlador é futuro (#1844).
- Issue #1032 (https://github.com/pybricks/support/issues/1032) [B]: DriveBase com gyro em velocidade alta corrige mal pequenos erros de rumo porque "os motores estão quase saturados só com feed-forward". Exemplo problemático: straight_speed 500-800 mm/s. Conclusão do mantenedor: comportamento esperado; mitigar limitando velocidade. Relevante para retas rápidas: o teto de velocidade deve deixar folga de ~20-30% de tensão para a correção de rumo [C: regra de dimensionamento].
- Docs: "In a noisy environment, such as a competition hall, you can raise the thresholds slightly so the robot gets a chance to calibrate" [A]. Não há número de deriva nas docs.
- Reddit r/FLL (via busca; https://redlib.andus.dev/r/FLL/comments/1hftii2/spike_361_degree_yaw_sensor_bug) [B]: relato de ~-3 graus por 360 graus num sentido no SPIKE app; solução recomendada = calibração de escala armazenada no hub (heading_correction do Pybricks). Só um relato.

Implicação para o CoopBot: como `hub.imu.reset_heading` falha com use_gyro e o repo usa `db.reset`, o bias continua sendo estimado só nos períodos com motores em coast e parados. Se a saída começa com o robô encostado "segurando" (hold) ou tocado pelo operador, o bias pode estar velho. Vale um `wait` em coast de >=1-2 s antes de cada saída, ou uma amostragem própria (ver 5).

## 2. Modelo de erro do gyro (LSM6DS3TR-C no SPIKE Prime; SPIKE usa a família LSM6DS3)

Fontes: datasheet LSM6DS3 (https://docs.arduino.cc/resources/datasheets/LSM6DS3-datasheet.pdf) e resumos (alldatasheet/flux.ai) [A, com ressalva: números vindos de agregadores, conferir no PDF da ST]:

| Parâmetro | Valor de datasheet (tip.) | Observação |
|---|---|---|
| Ruído de taxa (alto desempenho) | LSM6DS3: ~7 mdps/sqrt(Hz); LSM6DS3TR-C: ~5 mdps/sqrt(Hz) (agregador); DSL: ~4 | números de variantes divergem; usar 5-7 |
| Zero-rate level (offset de fábrica) | +-10 dps (DS3), +-3 dps (DSL) | grande! por isso a recalibração parado é obrigatória |
| Zero-rate change vs T | +-0,05 dps/C (DS3) | aquecimento de 15 C => até ~0,75 dps de offset (limite, não típico) |
| Sensibilidade (escala) tolerância | +-3% (DS3 tip.) e +-1% sobre -40..85 C | por isso há heading_correction por unidade |
| Faixa | +-125..2000 dps | |

Allan variance (ARW, bias instability): a ST NÃO publica para DS3/DSL (resposta em https://community.st.com/ ... "LSM6DSL factors not in datasheet") [A]; só plots em imagem para DSO/DSR. Métodos: MathWorks https://www.mathworks.com/help/nav/ug/inertial-sensor-noise-analysis-using-allan-variance.html.
Valores de simulação (derivados, [C]; tratar como a priori e substituir por medição do próprio hub):
- ARW: ruído de densidade 5-7 mdps/sqrt(Hz) => ARW = N ~ 0,005-0,007 dps/sqrt(Hz) = 0,3-0,42 deg/sqrt(h)... conversão: 0,006 dps/sqrt(Hz) * 60 = 0,36 deg/sqrt(h)*... (na prática MEMS de consumo mostram ARW 0,2-0,6 deg/sqrt(h) medidos em Allan). Em 1 s, sigma de ângulo ~ 0,006 deg; em 10 s ~ 0,019 deg. Ou seja, ruído branco é IRRELEVANTE para giros de 0,5 graus; o que importa é bias e escala.
- Bias instability (flicker): consumer MEMS ~ 3-30 deg/h (0,001-0,008 dps) no melhor ponto da curva de Allan; mas a "turn-on" e variação térmica dominam (centésimos de dps).
- Rate random walk: ~ 0,001-0,01 dps/sqrt(s) *[C, valor chute; medir]*. Útil só para simular deriva em minutos.
- Residual de bias após calibrar 1-2 s parado: sigma_bias = ARW_densidade/sqrt(T) em ruído branco = 0,006/sqrt(1 s) ~ 0,006 dps (para 1 s). Em 120 s a deriva por esse residual = 0,006*120 ~ 0,7 deg MAS é pior em prática: o bias real varia (T, vibração), então espere 0,01-0,05 dps de residual => 1,2-6 deg em 120 s. Medidas de comunidade: relatos FLL de "deriva ~1 grau/minuto" são comuns e vagos [F/B]; não achei medição citável. Meça: log de 5 min parado após 2 min de aquecimento.
- Quantização: 16 bits em +-2000 dps = 0,061 dps/LSB (se range 2000); em 1000 dps 0,031; Pybricks escolhe a faixa no driver (não confirmei). Com taxa de amostragem de 100s de Hz a quantização é dithered pelo ruído, então irrelevante.
- Não linearidade: datasheet DS3 ~ +-0,1 % FS [C]; efeito em giro de 90 graus a 200 dps: pequeno (<0,1 grau) se a calibração de escala for na faixa usada.
- g-sensitivity: ~0,1 dps/g (típico de MEMS consumo) [C]; para 1 g de aceleração contínua = 0,1 dps. Em frenagem de 0,5 g por 0,3 s, ~0,015 graus: desprezível. Vibração de rodas/engrenagem causa rectificação (viés DC induzido por vibração) — dá alguns centésimos de dps de offset enquanto motores rodam. Isso significa: o bias medido PARADO difere do bias EM MOVIMENTO [C, folclore plausível, sem medição citada]. Teste: girar rodas com robô suspenso e comparar bias.
- Temperatura/aquecimento: ΔT no hub é de alguns graus em 10-20 minutos de uso (bateria, motores) [C]; com +-0,05 dps/C no pior caso. Receita: bias recalibrar frequentemente, não confiar em bias de início de bateria. Sem fonte de equipes; é folclore razoável ("deixe o hub ligado 5 min antes") sem número medido.

## 3. Escala (heading_correction) e assimetria por sentido

- Procedimento oficial [A]: medir `hub.imu.rotation(-Axis.Z, calibrated=False)` numa volta real conhecida e inserir em `heading_correction` (perto de 360, +-15).
- Evidência de assimetria por sentido: o firmware aplica UM escalar por eixo (sem distinção de sinal). Em MEMS, a assimetria positiva/negativa da sensibilidade é tipicamente <0,1 % [C]. Mas o que parece "escala por sentido" em robôs reais costuma ser (i) bias residual (soma +bias em um sentido e -bias no outro, que parece escala diferente ao fazer voltas rápidas por tempos diferentes), (ii) derrapagem/ rodas, (iii) a medida da volta física (ponto de referência). Distinguir: com bias, o erro depende do TEMPO da volta (maior em giro lento); com escala, depende só do ANGULO. Experimento: N voltas CW e N CCW em 2 velocidades; regredir erro = a*angulo + b*tempo. [C: método proposto, não de fonte].
- Medição prática: use uma referência física (parede/gabarito), fazer 10 voltas completas (3600 graus) em cada sentido: erro/3600 dá escala com resolução ~0,01 % se o erro final for medido a ~0,3 graus (0,3/3600 = 0,008 %). Média CW+CCW cancela bias integrado (bias contribui com sinal oposto); a diferença CW-CCW dá estimativa do bias*tempo. [C, aritmética]
- Se de fato houver diferença residual por sentido: aplique ganho s+ e s- em software (multiplicar o delta de heading por s+ se omega>0, s- caso contrário) — requer o loop próprio integrar omega (imu.angular_velocity) e não usar heading nativo. Ganho esperado só vale se a diferença medida for >0,1 % (=0,36 graus por volta).
- Escala tolerance de fábrica +-1 a 3 % => um hub sem calibração erra 3,6-10,8 graus por volta. Com calibração: resíduo ~0,05-0,1 % => 0,2-0,4 graus por volta; um giro de 90 graus tem 0,05-0,1 graus de erro de escala, desprezível face a 0,5.

## 4. Controladores de giro no lugar

### O que o Pybricks DriveBase faz [A/B]
- `turn()` usa trajetória (aceleração/cruzeiro/desaceleração) + PID de rumo com feedforward; com `use_gyro` o rumo vem do gyro. Precisão típica relatada na comunidade FLL: ~1 grau, sem número de fonte citável; ver docs https://docs.pybricks.com/en/latest/robotics.html. Bugs de arredondamento (#1886) até ~1-2 graus, corrigidos. Não achei medição de equipe com erro <0,5 graus sustentado.
- Cursos FLL em geral: P puro estola perto do alvo ("the robot may stall before completing the turn"; fonte https://stemrobotics.cs.pdx.edu/node/7268.html) e a solução comum é velocidade mínima ou integral [B]. Esse é um ponto bem documentado: zona morta/atrito estático.

### Teoria (engenharia clássica [C], sem medição própria de equipes)
1. Perfil de tempo mínimo: omega_cmd = min(omega_max, sqrt(2*a_dec*|e|)) * sign(e), a_dec um pouco menor que a capacidade real (use 70-80 % da aceleração máxima medida). É a lei "bang-bang suavizada"; com laço a 10 ms e atraso de sensor tau, a lei vira omega_cmd = sqrt(2*a*max(|e_pred|-e_mrg,0)).
2. Predição de atraso: e_pred = e - omega*tau, tau = atraso total (filtro do gyro + amostragem 10 ms + latência do motor), tipicamente 10-30 ms. Para omega=300 dps e tau=20 ms: 6 graus de erro de predição, ou seja, não-trivial. Estimar tau pelo overshoot em open-loop: parada por comando de zero a partir de omega conhecido: ângulo adicional / omega = tau_eff (inclui inércia). Evidência: padrão em controle; nenhuma fonte FLL.
3. Overshoot por inércia: ângulo de frenagem = omega^2/(2*a_dec) quando em coast, mais omega*tau. Para omega=200 dps e a_dec=2000 dps2: 10 graus. Daí a lei sqrt.
4. Zona morta: motores pequenos do SPIKE (Spike medium/large) não giram com duty < ~5-10 % [C, medir]. Medir o menor duty (ou omega_cmd) que produz giro sustentado do chassi, com rampa lenta. Na fase fina use velocidade-alvo >= esse piso OU pulsos curtos ("nudges") de duração calibrada: kick de duty u_k por t_k que produz ~0,1-0,3 graus de passo. Nudges reduzem o erro de estacionamento abaixo do piso de taxa [C].
5. Settle: só declare fim quando |e|<tol E |omega|<omega_tol por N amostras consecutivas (ex.: 3-5 amostras = 30-50 ms) E depois "confirmar" lendo mais 100-200 ms (a roda ainda pode ceder). O gyro mede, o chassi ainda pode ter folga (backlash de engrenagens): o gyro já viu o rumo final; backlash é irrelevante ao gyro mas importa para a odometria de motor.
6. P vs PD na fase fina: com atraso, D em omega medido é amortecimento (usar -Kd*omega, não derivada do erro: sem ruído de derivada numérica). Gyro dá omega direto, então PD é grátis. Kp limitado por Kp*tau < ~0,5 para estabilidade com atraso [C].
7. Stiction limit-cycle: controlador com integral + zona morta oscila; preferir P(D) com piso de velocidade e saída final em pulso/ trava (hold) quando |e|<tol.

Números típicos: sem hardware de referência, os valores abaixo são metas de simulação, não de literatura: 90 graus em 0,45-0,6 s; erro final sigma 0,1-0,2 graus quando bias/escala calibrados. [C]

## 5. Retas com gyro

- P vs PD vs PI no rumo [C]: PI no rumo na reta é desaconselhado salvo para bias de assimetria de rodas (que o gyro P já compensa via erro permanente = bias_roda/Kp). Para erro lateral zero, P no rumo converge para rumo correto mas deixa deslocamento lateral; para cancelar lateral é preciso a malha externa (abaixo). PD ajuda em velocidade alta (erro de ressonância/ salto), com D em omega.
- Erro lateral (cross-track): y_ct = -sin(psi_ref)*(x-x0) + cos(psi_ref)*(y-y0) via odometria (rodas + heading do gyro). Stanley simplificado: delta_psi_cmd = psi_err + atan(k*y_ct/(v+v0)); pure pursuit em linha reta é equivalente a rumo-alvo = psi_ref - atan(y_ct/L). Para robô de bitola 80 mm e curso de 1 m, deslocamento lateral por erro de rumo 0,5 graus = 8,7 mm por metro, por isso o gyro é a base e a correção lateral é um refinamento. Com odometria + gyro, o erro de y_ct vem quase todo do rumo integral; a odometria de roda corrige pouco (derrapagem). [C]
- Frenagem brusca/patinagem: desaceleração limitada a ~mu*g; rodas de borracha em mesa de FLL mu~0,6-1 => 6-10 m/s2 teórico, muito acima do que o motor dá. O problema real é arrancada: torque de pico levanta a frente / patina uma roda mais que a outra, gera giro (yaw) de ~0,5-2 graus [F: relatos de equipes], mitigação = rampa de aceleração (o que o Pybricks já faz) e rumo-alvo mantido pelo gyro (que detecta o yaw e corrige).
- Efeito de saturação [B]: ver issue #1032: em alta velocidade, o motor satura só com FF e a correção de rumo some. Dê folga: velocidade máxima <= ~75 % da máxima do motor.

## 6. Técnicas "pouco conhecidas" e o que tem evidência

1. Medir bias com N amostras parado no início de cada saída [C + A parcial]: o firmware já faz média móvel quando parado e em coast, mas só com limiar de 1 s; uma amostragem própria de 0,5-1 s de `imu.angular_velocity()` (ou `imu.stationary()` como gate) e uma subtração de bias residual no próprio laço é barato. Erro do bias estimado = sigma_ruido/sqrt(N*fs_efetiva): com ruído medido por amostra ~0,03-0,1 dps (depende de ODR/filtro) e N=100, sigma = 0,003-0,01 dps; em 30 s de saída = 0,1-0,3 graus. Isso é ordem de grandeza útil (ganho alto, risco baixo), mas a deriva real de bias sobrepõe-se; verificar com experimento.
2. Reancoragem em parede/linha [B/A]: padrão FLL de equipes avançadas (alinhar na parede, `db.reset`/zerar heading no contato). Elimina deriva acumulada por saída. Evidência: prática ubíqua; ganho = zera o erro de integração; limite = precisão da parede (<1 graus se o robô encosta com 2 pontos de contato). Boa relação ganho/risco. Linha: usar 2 sensores de cor e alinhar até ambos verem a borda: precisão ~0,5 graus para espaçamento de 80-100 mm entre sensores e resolução de 1 mm (arctan(1/100)=0,57 graus) [C].
3. Filtro complementar encoder+gyro [C]: serve para detectar patinagem e como sanidade, não para melhorar rumo em condições normais, pois o gyro (bias pequeno) é melhor que o encoder (bitola estimada ~80 mm e deslizamento). Pode corrigir a deriva do gyro em retas longas: se não há patinagem, d(psi_encoder) = (dR-dL)/bitola é uma segunda medida; combinar com ganho baixíssimo (constante de tempo >10 s) estima o bias em movimento. Risco: bitola errada vira escala. Ganho esperado pequeno (<0,3 grau por minuto) e requer bitola calibrada a 0,3 %.
4. Calibrar a bitola efetiva com o gyro [C, mas é prática sólida]: girar 10 voltas com odometria só de roda e comparar com gyro (ou 3600 graus): bitola_efetiva = bitola * (rotação_roda_odom/rotação_gyro). Reduz erro de odometria em giros pequenos e curvas. Alto ganho para curvas em arco.
5. Acelerômetro para detectar choque/patinagem [C]: |a| fora de 1 g +-0,3 g ou jerk alto durante a arrancada; usar como flag para descartar a integração do gyro? Pouca evidência; g-sensitivity (0,1 dps/g) torna o impacto no gyro desprezível, então o benefício é só diagnóstico. Baixo ganho.
6. Compensar escala por sentido: ver seção 3; só se medido >0,1 %.
7. Dormir (coast) antes do giro: já que o Pybricks só calibra com motores em coast, uma pausa de 1 s em coast antes da saída é gratuita. [A+C]

## 7. Proposta de simulação Monte Carlo (parâmetros a priori)

- Gyro: omega_medido = (1+s)*omega + b(t) + n; s ~ N(0, 0,003) por unidade antes de calibrar (0,0005 após), assimetria opcional +-0,001; b0 residual ~ N(0, 0,03 dps) após auto-cal (sem T) e passeio b(t) com RRW 0,002 dps/sqrt(s) + rampa térmica 0,01 dps/min nos primeiros 10 min; n ruído branco 0,05 dps por amostra a 100 Hz (inclui quantização/filtro; ajustar ao ARW medido); g-sensitivity 0,1 dps/g em fases de aceleração.
- Atuador: zona morta de omega_cmd 15-40 dps (medir); atraso tau 15-30 ms; a_max 1500-3000 dps2; folga de engrenagem 0,5-2 graus por roda; atrito estático com stick-slip.
- Medição de sucesso: erro final p95 <= 0,5 graus em giros de 15-180 graus, 1000 execuções, e deriva em 120 s.
Todos [C]: substituir por medição do próprio robô assim que houver hardware (Allan variance de 30 min parado é o experimento de maior valor).

## 8. Ranqueamento de recomendações (ganho esperado / risco)

1. Calibrar heading_correction com 10 voltas CW e CCW contra referência física; média; documentar. Ganho: de 1-3 % para ~0,05-0,1 % de erro de escala. Risco: nenhum. [A+C]
2. Reancorar em parede/linha ao fim de cada trecho longo e zerar rumo. Ganho: elimina deriva acumulada. Risco: baixo, depende da mecânica.
3. Garantir 1-2 s de coast parado antes de cada saída (o firmware só recalibra bias nessa condição) e medir bias residual próprio com N amostras. Ganho: ordem de 0,01-0,05 dps => 0,3-1,5 graus em 30 s. Risco: baixo. [A+C]
4. Giro com perfil sqrt(2*a*e) com predição de atraso e_pred = e - omega*tau e velocidade-piso medida; settle com |omega|<tol por 3-5 amostras. Ganho: erro final de ~1 grau para 0,2-0,5. Risco: médio (parametrização do tau e piso). [C]
5. Fase fina com PD usando omega do gyro (não derivada numérica) ou nudges de pulso curto abaixo do piso. Ganho: elimina oscilação de limite de ciclo. [C]
6. Retas: P no rumo com saída limitada, velocidade <=75 % da máxima (issue #1032), rampa de arrancada, correção de cross-track só em trechos >50 cm. Ganho: lateral <5 mm/m com calibração. [B+C]
7. Calibrar a bitola efetiva comparando odometria e gyro em 10 voltas. Ganho médio, risco baixo.
8. Filtro complementar encoder+gyro e uso do acelerômetro: ganho pequeno/incerto; fazer por último e só se Allan e testes mostrarem deriva em movimento.
9. Compensação de escala por sentido: só se a medição mostrar >0,1 %; senão é sobreajuste.
10. Aquecimento/temperatura: sem tratamento no firmware, sem dado de equipes; folclore. Mitigar com recalibração frequente; medir a rampa em 20 min de log.

## 9. Fontes
- Pybricks Prime Hub docs: https://docs.pybricks.com/en/latest/hubs/primehub.html
- Pybricks imu.c: https://raw.githubusercontent.com/pybricks/pybricks-micropython/master/lib/pbio/src/imu.c
- Issue 1886: https://github.com/pybricks/support/issues/1886
- Issue 1032: https://github.com/pybricks/support/issues/1032
- Pybricks robotics docs: https://docs.pybricks.com/en/latest/robotics.html
- LSM6DS3 datasheet: https://docs.arduino.cc/resources/datasheets/LSM6DS3-datasheet.pdf
- ST community (Allan não publicado): https://community.st.com/mems-sensors-48/i-would-like-to-know-some-factors-of-lsm6dsl-which-is-not-mentioned-in-datasheet-1-bias-random-walk-noise-standard-deviation-of-accelerometer-gyroscope-3-measurement-noise-standard-deviation-of-accelerometer-gyroscope-59756
- MathWorks Allan variance: https://www.mathworks.com/help/nav/ug/inertial-sensor-noise-analysis-using-allan-variance.html
- Reddit r/FLL SPIKE yaw bug: https://redlib.andus.dev/r/FLL/comments/1hftii2/spike_361_degree_yaw_sensor_bug
- PID turn stall: https://stemrobotics.cs.pdx.edu/node/7268.html
- Quirkycort DriveBase vs Move Steering: https://quirkycort.github.io/tutorials/110-Pybricks-Basics/99-Special-Topics/10-DriveBase-vs-Move-Steering.html
Nota: algumas contas na seção 2 (ARW em deg/sqrt(h)) estão como ordem de grandeza e foram escritas sem verificação numérica rigorosa; refazer com a medição do hub.
