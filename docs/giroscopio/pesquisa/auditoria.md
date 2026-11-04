# Auditoria do giroscópio / rumo — hub/tbr.py, rotinas_cal.py, main.py

Premissas numéricas (marcadas "premissa" quando não medidas): laço real = PERIODO_MS 10 + execução ~1-3 ms
=> ~12 ms; db.angle() atualiza no laço de controle do pbio (~5 ms); latência efetiva de detecção 10-17 ms.
Lateral de um erro de rumo e (graus) em L: L*tan(e) = 17,5 mm por grau por metro.
Itens sobre comportamento interno do Pybricks marcados [VERIFICAR] não foram confirmados no firmware.

## Conclusões sobre os exemplos do pedido
- "_creep termina do outro lado e nunca corrige": DERRUBADO como risco do creep em si. O creep para quando
  restante <= 0,8 (tbr.py:279), vindo de baixo a 15 °/s ele precisa de >1,1° para cruzar o zero, e não cruza.
  O viés real é o oposto: sempre PARA CURTO em ~0,3-0,5° (ver F2). O "outro lado" acontece só no hand-off do giro
  grosso (overshoot), e aí o creep corrige (tol_entra=0,8, tbr.py:367). Mas andar()/curva()/ate_linha chamam
  _creep() com tol 2,0 e aceitam qualquer erro de ±2° sem corrigir (F1).
- CREEP_GANHO*erro < 15 para erro < 5°, então abaixo de 5° o "P" é só a taxa mínima constante 15 °/s (bang-bang).
- Giro grosso: estimativa de parada ver F2 (sobra ~2,4° de curso após o gatilho contra 2,0° disponíveis).
- andar(): db.straight com use_gyro herda o rumo MEDIDO no início (db.stop()/coast antes => referência = estado
  medido) [VERIFICAR], não _rumo_alvo. Erro de 0,7° na partida => 0,7° de reta inteira => 12 mm/m. Confirmado como risco.
- andar_no_rumo: lateral por erro inicial e0 com ganho k=3 1/s: L = v*e0(rad)/k. 1° a 300 mm/s = 1,75 mm
  (desprezível); 20° (RUMO_VIRAR_ANTES) = 35 mm. Ré: sinal da guinada independe do sentido da marcha (yaw do
  corpo), correto. Falta só um termo lateral/integral para perturbação constante, mas o laço interno do pbio com
  giroscópio já rejeita viés de rumo, então P puro basta.
- db.brake() no fim: a 40 mm/s (RUMO_VEL_FINAL) o efeito no rumo é ~0,1-0,3°, irrelevante. Em ate_linha/_seguir/
  andar_ate_travar (150-300 mm/s) freia em 5-15 mm e o rumo lido logo depois ainda muda (F5).
- Normalização ±180 e acúmulo de _rumo_alvo: sem bug de acúmulo (rumo absoluto, db.angle() não é embrulhado,
  _erro_rumo normaliza). Único ponto: erro exatamente ±180 decide a direção pelo ruído do giroscópio (baixo).
- Laço de controle: _vigiar_anexos soma ~0,3-0,6 ms por tarefa ativa (premissa: ~4 chamadas MicroPython a
  50-100 us). Período real passa de ~11 para ~12-13 ms; não é crítico, mas faz o KD do seguidor (por amostra,
  não por segundo) variar com anexos ativos (F-seguir).

## Tabelas por função (falha | evidência | impacto | sev | correção)

### _erro_rumo / _atualizar_pose / zerar_rumo / boot
| Falha | Evidência | Impacto | Sev | Correção |
|---|---|---|---|---|
| zerar_rumo não confere se o robô está parado nem refaz o bias; saída começa logo depois do clique do botão central | tbr.py:952-961, main.py:67 | deriva de bias típica 0,02-0,05 °/s (premissa) x 20-40 s de saída = 0,4-2° no fim; nunca foi medida | Média | Rotina "D" (deriva): robô parado 120 s imprimindo heading a cada 10 s; no zerar_rumo esperar hub.imu.stationary() ~300 ms |
| imu.ready() sem timeout nem aviso; só luz amarela | tbr.py:66-71 | travado "no amarelo" se o robô se mexe no boot, sem mensagem | Baixa | imprimir/mostrar "!" após 3 s; considerar imu.settings(angular_velocity_threshold=...) se nunca fica pronto na mesa |
| _atualizar_pose usa heading no fim do passo, não a média | tbr.py:153-162 | em curva de 90° em 1 s e passo 12 ms: erro de posição < 1 mm; desprezível | Baixa | usar (h_ant+h)/2 se quiser |
| heading sem compensação de inclinação [VERIFICAR] | n/a (gangorra M1) | se imu.heading integra o eixo Z do hub, cos(15°)=0,966 => 3,4% a menos de giro em rampa | Baixa/Média | testar giro de 90° em cima da gangorra e comparar |

### _creep
| Falha | Evidência | Impacto | Sev | Correção |
|---|---|---|---|---|
| Para em restante <= 0,8 sem compensar latência e coast: erro final sempre CURTO | tbr.py:279,301 | 15 °/s x ~25 ms (laço+sensor) = 0,35° + coast ~0,1-0,2° => para a ~0,3-0,5° do alvo, sempre no sentido do giro. Com tol_sai 0,8: faixa final +0,3..+0,8° | Média | tol_sai efetivo = max(0,2, taxa*0,03) ou 0,3; ou parar a 0,5 e esperar 60 ms |
| Taxa mínima 15 °/s vale para todo erro < 5° (3*erro < 15) | tbr.py:295-298 | sem desaceleração real; tempo ~80-280 ms; atrito estático pode atrasar a partida (premissa) | Baixa | OK; só saber que o ganho 3 é morto |
| teto = 3*t_teórico + 2000 ms sem limite superior | tbr.py:269 | creep após giro/curva abortado com 50° de erro: teto 12 s se o pbio não marcar stalled | Média | teto = min(teto, 1500) e abortar se erro > 15° (sinal de que algo travou) |
| tol_entra 2,0 padrão | tbr.py:259-260 | aceita erro de até 2° (35 mm/m) | Média | ver F1 |

### _giro_por_velocidade / _ir_ate_rumo
| Falha | Evidência | Impacto | Sev | Correção |
|---|---|---|---|---|
| Rampa sqrt(1000*restante) sem compensar atraso; sai a 2° ainda a ~45 °/s (+15 °/s de atraso de seguimento) | tbr.py:338-341 | curso após o gatilho: latência 11 ms*55 = 0,6° + drive(0,0) a 1000 °/s2 => 55²/2000 = 1,5° + seguimento 0,3° ≈ 2,4° contra 2,0° disponíveis => overshoot médio -0,4°, faixa -1,0..+0,6° | Média | gatilho em GIRO_GROSSO_SAI + w*0,02; ou rampa com 0,6*ACEL; medir com DIAG (campo "sobrou") |
| _creep logo após drive(0,0): lê o erro com o robô ainda desacelerando (~45 ms, ~1°) | tbr.py:341,361,367 | decisão "já está bom" (<=0,8) ou "corrige" tomada com valor transitório; ~30-40% dos giros vão pro creep reverso (premissa) | Média | esperar settle: while abs(db.state()[3]) > 5: wait(5) (ou 50 ms fixos) antes de medir; custa ~50 ms, tira viés e giros desnecessários |
| Erro final efetivo do giro: ±0,8° (não 0,8 máx. um lado) | tbr.py:367 | 14 mm/m depois do giro | Média | F2 |
| db.settings(...) em _aplicar_vel chamado em _ir_ate_rumo com robô em movimento (após andar parar=False) | tbr.py:141-146,354 | [VERIFICAR] se o firmware para/solta o DriveBase ao mudar settings; no mínimo db.drive(0,w) com o robô a 300 mm/s freia em 56 mm numa curva | Média | exigir parar=True antes de giro, ou log de db.state()[1] antes/depois de settings |
| Giros de 2-8° vão pelo _creep puro (≤ 60 °/s e P=3): 0,3-0,5 s | tbr.py:352,369 | tempo; baixo | Baixa | GIRO_GROSSO_MIN=4 |
| Hipótese: db.turn parava 15° curto (M5) pode indicar bitola errada (BITOLA 80 estimada) | config.py:55-58; diario | com use_gyro a bitola só é feed-forward, mas errada em 30% gera erro permanente de seguimento que o done() aceita | Média | rodar B e olhar DIAG de boot ("PADRAO" ou "GRAVADA") |

### andar / curva / ate_linha
| Falha | Evidência | Impacto | Sev | Correção |
|---|---|---|---|---|
| andar() "segura o rumo atual": db.straight parte do rumo medido, _creep só corrige acima de 2° | tbr.py:453-458 | 0-2° herdados => 0-35 mm por metro (0,7° = 12 mm/m); doc diz "rumo absoluto" | Alta | andar() = andar_no_rumo(cm, _rumo_alvo) (mantém rampa e HOLD final via _creep), ou creep com tol 0,5 antes de retas > 30 cm |
| _creep final com tol 2,0 aceita 2° ao fim da reta | tbr.py:458 | idem, vira o rumo de partida do próximo comando | Média | tol 1,0 no fim |
| curva(): db.curve parte do rumo medido; _rumo_alvo += graus mesmo se abortada | tbr.py:734,740 | curva abortada (travou) => _creep tenta completar o giro no lugar contra o obstáculo; teto até 12 s | Média | só somar se ok; senão _rumo_alvo = db.angle() |
| curva parar=False + andar seguinte: _creep() no início roda com o robô em movimento (db.drive(0,..) freia a reta) se erro > 2° | tbr.py:453,734 | quebra a "emenda", ~50 mm de arco | Baixa | pular _creep se db.state()[1] > 5 (como andar_ate_travar) |
| ate_linha: P para _rumo_alvo (bom) mas freia 5-10 mm depois da linha (12 ms*150 mm/s = 1,8 mm + sensor ~1,5 + brake) | tbr.py:819-821 | posição ~3-8 mm além | Baixa | vel menor perto; ok |

### andar_no_rumo
| Falha | Evidência | Impacto | Sev | Correção |
|---|---|---|---|---|
| RUMO_VIRAR_ANTES=20°: corrige até 20° andando em curva | tbr.py:476; config.py | lateral = v*e0/k = 300*0,35/3 = 35 mm (20°), 8,7 mm (5°) | Média | RUMO_VIRAR_ANTES 6-8° (custa ~0,3 s, economiza 15-30 mm) |
| Rampa de frenagem v=sqrt(2*ACEL_RETA*d) usa 100% da aceleração, sem folga (diferente do giro, que usa 50%) | tbr.py:516-517 | com atraso 12 ms a 450 mm/s sobram ~7 mm e v 12 mm/s acima; na prática +0,7 mm | Baixa | 0,8*ACEL_RETA |
| db.brake() (não HOLD) + db.stop() no final | tbr.py:522,526 | em rampa (gangorra) pode rolar após o coast | Baixa | db.stop(Stop.HOLD) quando precisar parado |
| Fim em ok=False não confere o rumo | tbr.py:521-527 | aceitável | Baixa | n/a |

### andar_ate_travar / virar_ate_travar
| Falha | Evidência | Impacto | Sev | Correção |
|---|---|---|---|---|
| Ao travar, _rumo_alvo fica o antigo; o próximo comando faz _creep e gira o robô para longe da parede | tbr.py:576-586 | por projeto; pode girar até 2° ou mais se o robô alinhou na parede | Baixa | opcional: _rumo_alvo = db.angle() ao travar (flag) |
| virar_ate_travar não faz creep depois; sai por restante <= 0,8 a 90 °/s e db.stop() coast | tbr.py:640,654 | overshoot: 90 °/s*12 ms=1,1° + coast ~1° => final -1..-3° além do alvo, nunca corrigido (<2° é aceito pelo próximo andar) | Média | no ramo sem travar, chamar _creep(tol_entra=GIRO_TOL_SAI) |
| virar_ate_travar retorna sem log quando _giro_invertido | tbr.py:638-639 | silêncio | Baixa | retornar e imprimir |
| Estol exige 1°/250 ms mas partida do repouso com 1000 °/s2 — ok; teto vem de erro/taxa | tbr.py:646-650 | ok | n/a | n/a |

### girar / virar_para / ir_para / voltar_base
| Falha | Evidência | Impacto | Sev | Correção |
|---|---|---|---|---|
| _traduzir_vel confunde número com constante: virar_para(x, 300) -> 180 °/s; 150 -> 90; 450 -> 300 | tbr.py:126-134 | usuário pede 300 °/s e recebe 180: sem erro, tempo +67% | Média | constantes de giro próprias (GIRO_RAPIDO...) ou aceitar só nomes |
| ir_para usa andar() (rumo medido), não andar_no_rumo(rumo da rota) | tbr.py:759-760 | resíduo do virar_para ±0,8° + 0..2° => 14-35 mm/m, e o x,y da odometria usa o heading medido (então pose correta, mas destino errado) | Média | andar_no_rumo(dist, rumo) |
| Erro de ±180 exatos escolhe sentido pelo ruído | tbr.py:181-184 | giro de 180° para lado imprevisível (perto de obstáculo) | Baixa | parâmetro sentido= em virar_para |
| girar(): _rumo_alvo += graus mesmo se o giro falhou (travou) | tbr.py:596-598 | próximo comando tenta completar o giro (creep, até 12 s) | Média | se not ok: _rumo_alvo = db.angle() |

### sacudir
| Falha | Evidência | Impacto | Sev | Correção |
|---|---|---|---|---|
| Volta ao _rumo_alvo, não ao rumo onde começou (doc diz "onde começou") | tbr.py:711,716 | até 2° de diferença | Baixa | usar h0 = db.angle() |
| db.turn de ±6° na zona morta já relatada pelo autor | tbr.py:711; config.py:74-80 | amplitude real menor que a pedida (premissa) | Baixa | medir com log |

### alinhar_na_linha / _quadrar / _seguir
| Falha | Evidência | Impacto | Sev | Correção |
|---|---|---|---|---|
| alinhar com rumo= faz db.reset(angle=rumo) assumindo robô perpendicular, mas _quadrar para cada roda com ~10 ms de atraso a 150 mm/s (1,5 mm) e a segunda passada a 50 mm/s (0,5 mm) | tbr.py:868-885 | erro angular ±atan(1,5/spacing) com spacing ~80 mm (premissa) = ±1,1° na passada grossa, ±0,4° na fina; fino=False deixa ±1° como "verdade" | Média | usar fino=True sempre quando rumo= for passado; medir o espaçamento real dos sensores |
| _quadrar: limite max_cm usa db.distance médio com UMA roda andando (anda o dobro) | tbr.py:837 | max_cm efetivo é 2x | Baixa | limitar por roda |
| Motor.run()/hold() logo após db.straight(HOLD), sem db.stop() [VERIFICAR] | tbr.py:873-876 | possível EBUSY se o DriveBase mantém os servos | Baixa | db.stop() antes de _quadrar |
| _seguir: _rumo_alvo = db.angle() instantâneo, logo após brake, durante a oscilação do PD | tbr.py:921-924 | amplitude de guinada do seguidor ±2-5° (premissa): o rumo "da linha" é amostrado em fase aleatória; próximo andar()/girar() herda 2-5° (35-87 mm/m) | Alta | média de db.angle() nos últimos 150-300 ms, ou não redefinir (usar rumo conhecido) |
| KD por amostra (erro - erro_ant), não por segundo | tbr.py:917 | ganho derivativo varia com o período real (10 vs 13 ms: +30%) | Baixa | dividir por dt real |
| Leitura de 2 sensores por laço em seguir_ate_cruzamento aumenta período | tbr.py:907,946 | +1 ms | Baixa | n/a |

### rotinas G / B e main
| Falha | Evidência | Impacto | Sev | Correção |
|---|---|---|---|---|
| G: HC_MIN/MAX 300-800 aceita contagem errada de voltas (3 voltas dá 600; 4 dá 450 e passam) | rotinas_cal.py:23,171 | heading_correction errado em 25-100% e gravado ("persiste no hub") | Alta | faixa de 340-380 em torno do valor do DIAG imu atual; pedir confirmação se diferir > 2% |
| G: uma medição, só horário, sem repetição nem desvio | rotinas_cal.py:163-169 | assimetria de escala não medida (premissa: <0,3%); leitura da marca ±2° em 1800° = 0,11% (0,1° em 90°) | Média | 3 tentativas, mediana, exibir dispersão; fazer horário e anti-horário |
| G: rotation(calibrated=False) pode vir sem compensação de bias [VERIFICAR]; 25 s a 0,05 °/s = 1,25° = 0,07%; inclinação do robô nas mãos: tilt 5° => cos = 0,996 (0,4%) | rotinas_cal.py:163,168 | erro sistemático até ~0,5% (mais que o erro de leitura da marca) | Média | girar apoiado no tapete (sem levantar); medir bias parado 10 s antes e subtrair |
| G: gravar settings imediatamente muda a escala na sessão em curso | rotinas_cal.py:174 | DriveBase/rumo inconsistente até reiniciar (a mensagem já avisa) | Baixa | n/a |
| B: depende de heading_correction correto (nova bitola = b*1080/medido; erro de escala de e% vira e% em b: 0,3% de 80 mm = 0,24 mm) | rotinas_cal.py:206-217 | pequeno; mas só 1 medição e inclui o patinar do tapete | Baixa | 2 medições |
| B: com use_gyro True a bitola só vale como feed-forward e em db.curve; se nunca rodou B, BITOLA=80 estimada pode estar 20-40% errada (rodas 56 mm: bitolas típicas 90-120 mm) | config.py:55-58, rotinas_cal.py:198 | curvas de raio 6 cm (M5) com R < b/2: roda interna inverte; o relato "curvas saíam do arco" bate | Alta | rodar B e conferir o DIAG de boot; prioridade |
| main: nenhum aviso se heading_correction está no padrão | main.py:34 | rumo com erro de escala de até alguns % se G nunca foi feito | Média | avisar no menu quando imu.settings() não difere do padrão |

### Cronômetro / DIAG / concorrência
| Falha | Evidência | Impacto | Sev | Correção |
|---|---|---|---|---|
| print de CRONOMETRO e DIAG_GIRO em todo comando (BLE/USB conectado) | config.py:158-165 | 10-50 ms por print com PC conectado (premissa), 0 sem PC | Baixa | desligar na competição |
| _vigiar_anexos + _checar a cada laço: +~1 ms/laço; sem erro de lógica | tbr.py:165-172,1045-1097 | período 12-13 ms vs 11 ms | Baixa | n/a |
