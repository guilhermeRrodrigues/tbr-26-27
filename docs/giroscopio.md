# Giroscópio fino e largada certa (branch `giroscopio-fino`)

Trabalho da madrugada de 04/11/2026 para a competição de **07/11**. Tudo foi feito sem o robô, com pesquisa, leitura do código-fonte do Pybricks 4.1.2 e um gêmeo digital que roda o `hub/tbr.py` de verdade. **Nada disso foi validado na mesa.** O [protocolo de mesa](#protocolo-de-mesa-dias-5-e-6) dos dias 5 e 6 é a validação real.

Tudo está **ligado**. Cada mudança tem uma chave em `hub/config.py` que volta ao comportamento de antes (ver [Chaves de volta](#chaves-de-volta)).

## Resumo para a equipe

1. **A largada era o maior erro.** Soltar o robô a olho dá 1 a 3° de erro de rumo, e cada grau vira ~17 mm de desvio por metro. A solução tem três camadas:
   - o **gabarito em L** (`modelos3d/gabarito/`), que leva o erro da mão para ~0,3°;
   - a **luz de mira** no menu: verde significa robô alinhado e giroscópio parado;
   - o **`largar()`**, que usa o giroscópio para saber o quanto o robô foi solto torto e corrige no primeiro movimento.
2. **Giros:** o erro real caiu de p95 5,5° para **0,65°**. Também caiu o caso raro de 180°, em que o giro parava sem girar. Cada giro custa ~90 ms a mais.
3. **Retas:** o viés de distância caiu de +4 mm para ~0, e o desvio lateral máximo de 78 mm para ~5 mm. O tempo subiu 2%.
4. **`alinhar_na_base()`** é uma ferramenta nova para as saídas críticas. Ela esquadreja o robô na moldura verde ao sair da base e zera o rumo a ~0,3°.
5. Como `andar()` agora segue o rumo planejado e para mais certinho, **distâncias ajustadas na mesa podem mudar alguns milímetros.** Rodem todas as saídas no dia 5.

## Ritual de largada (cabe nos 2 minutos)

1. **Primeira saída da partida:** o robô vai no gabarito, na direção 0. Essa largada define a "mesa", a referência de rumo de todas as outras. A rotina **Z** do menu faz o mesmo de forma explícita.
2. **Cada saída:**
   - apoie o L no canto da base, rente à borda interna da moldura verde, e confira as janelas de mira;
   - encoste o robô nos batentes, com calços se a saída for virada;
   - tire o gabarito pela alça, levantando reto;
   - **olhe a luz do hub** (a mira compara o rumo atual com a direção nominal da saída):
     - **verde:** desvio ≤ 0,5° e o giroscópio vê o robô parado;
     - **amarela:** até 2°. Dá para largar, mas um ajuste de mão melhora;
     - **vermelha:** mais de 2°. Reposicione. Se o desvio passar de 8° (`LARGADA_MAX_DESVIO`), o robô não compensa: assume que é uma saída diagonal não declarada e avisa no console.
   - **aperte.** O menu chama `tbr.largar(nominal)`.
3. **Espere a luz verde** quando der: o firmware só reestima o bias do giroscópio com o robô parado ~1 s e os motores soltos. O menu já deixa tudo solto entre saídas.

**Direção nominal:** o padrão é o múltiplo de 90° mais perto (`LARGADA_PASSO`), o que já cobre as saídas viradas. Uma saída em diagonal pode declarar a direção com um 3º item em `SAIDAS`, por exemplo `("M9", m9_patio, 45)`.

**`LARGADA_SIGMA_MAO` tem de refletir como a equipe larga:**

| Como larga | `LARGADA_SIGMA_MAO` |
|---|---|
| Com o gabarito | **0,3** (padrão) |
| A olho | **1,5** |

O valor diz ao filtro o quanto confiar na mão contra o giroscópio. Errar para menos não quebra nada, mas a compensação rende menos (ver a tabela da largada).

## Resultados do gêmeo digital

Monte Carlo com 300 a 400 robôs sorteados, cada um com erro de escala, assimetria por sentido, bias, deriva, folgas e atrito diferentes. As saídas brutas ficam no scratchpad da sessão; para repetir, veja [Como rodar](#como-rodar-o-simulador). Erros contra a **verdade** do mundo simulado, não contra o que o giroscópio acha.

### Giro (`virar_para`, 2400 giros de 5° a 180°)

| | erro p50 | erro p95 | erro máx | tempo médio |
|---|---|---|---|---|
| Antes (`main`) | 1,27° | 5,51° | **179,8°** (bug do 180°) | 633 ms |
| Agora | **0,22°** | **0,65°** | 1,45° | 720 ms |

O que sobra é erro do **sensor** (escala e bias), não do controle: o giroscópio acha que errou só p95 0,43°. Para melhorar mais, só calibrando bem a escala com a rotina G.

### Reta (`andar` e `andar_no_rumo`, 30 a 120 cm)

| | viés de distância | distância p95 | lateral p95 | lateral máx | tempo |
|---|---|---|---|---|---|
| Antes | +4,1 mm | 9,4 mm | 4,4 mm | 78 mm | 2431 ms |
| Agora | **+0,1 mm** | 6,3 mm | **1,4 mm** | **4,8 mm** | 2482 ms |

### Largada (4 saídas por partida, erro a 1 m da base)

| Estratégia | rumo p95 | lateral p95 a 1 m |
|---|---|---|
| A olho, como hoje | 2,87° | 52 mm |
| A olho + `largar()` com `SIGMA_MAO` 0,3 (valor errado para o olho) | 2,63° | 47 mm |
| A olho + `largar()` com `SIGMA_MAO` 1,5 | 2,43° | 42 mm |
| **Gabarito** | **0,45°** | **7 mm** |
| Gabarito + `largar()` (padrão) | 0,50° | 8 mm |
| Ancorar na moldura (`alinhar_na_base`) | 0,53° | 9 mm |

**Leitura honesta:**
- O que mais rende é o **gabarito**, de 6 a 7 vezes melhor.
- O `largar()` ajuda quem larga a olho, mas não faz milagre: o giroscópio também acumula erro a cada vez que o robô é pego e girado à mão (p95 de 1,3° na 2ª largada, 2,7° na 3ª, 4,3° na 4ª). Por isso o filtro **funde** as duas fontes em vez de confiar só no giroscópio.
- Com o gabarito, o `largar()` é quase neutro (0,45° contra 0,50°). Ele fica como rede de segurança e mantém a **luz de mira**, que avisa quando o gabarito escorregou.
- `alinhar_na_base` dá a mesma precisão sem depender da mão. Custa ~1,8 s e uma faixa reta à frente.

## O que mudou

### Largada

- **`largar(nominal=None)`**: chamado pelo menu ao apertar.
  - O rumo inicial é o desvio em relação à direção nominal, e não zero. O primeiro `virar_para`/`andar` corrige.
  - O desvio vem de um **filtro de Kalman de um estado**: o peso do giroscópio é `w = σ_mão² / (σ_mão² + σ_giro²)`, e a variância do giroscópio cresce com o tempo desde a última referência (`LARGADA_DERIVA`, em graus por minuto).
  - Na 1ª largada, ou com a referência mais velha que `LARGADA_REF_MAX_S`, a largada vira a nova referência.
- **`zerar_rumo()`** continua do jeito que era (rumo atual = 0 e posição = (0, 0)), mas agora **preserva o rumo da mesa**. Pode ser chamado no meio de uma saída.
- **`rumo_mesa()`**, **`desvio_largada(nominal)`** e **`definir_mesa(nominal)`**: consultas e referência explícita, usadas pela rotina Z.
- **`alinhar_na_base(rumo=0, vel=LENTO, max_cm=30, fino=True)`**: anda até os dois sensores verem a moldura verde (cor `BORDA`, limiar `LIMIAR_BORDA`), esquadreja como o `alinhar_na_linha` e reancora o rumo e a referência da mesa.
- **Menu:** a luz de mira (`_cor_mira`), a direção nominal opcional em `SAIDAS` e `DIAG firmware` no boot.

### Giro

- **Giro fino** (`GIRO_FINO`):
  - o grosso sai antes, já descontando o quanto o robô ainda vai deslizar (`FINO_GROSSO_SAI + |w|·freio`);
  - depois o robô **espera parar**, mede e dá pulsos curtos até ficar dentro de `GIRO_TOL_FINAL` (0,5°);
  - o tempo de freio é **aprendido** a cada giro (média móvel), o que se adapta ao tapete e à bateria;
  - a fase fina tem tetos: `FINO_TENTATIVAS` e `FINO_TETO_MS`.
- **Tolerâncias do DriveBase** (`TOLERANCIAS_DB`): o padrão do Pybricks considera "chegou" a ~18° e ~13 mm do alvo por causa da geometria 56/80. Agora são 2° e 3 mm. Para não travar, o `_esperar_db` também aceita "parado" depois do tempo teórico + 300 ms.
- **Correções de rumo** (`CORRECOES_RUMO`):
  - o alvo é "desembrulhado", o que acabou com o bug do 180°;
  - `girar` e `curva` abortados não deixam o alvo adiantado;
  - `virar_ate_travar` fecha com o giro fino quando não trava;
  - o rumo final do `_seguir` é a média das últimas 20 leituras, e não uma leitura solta.
- **`RUMO_VIRAR_ANTES`** de 20° para 8°: o `andar_no_rumo` gira antes se o erro passar disso, em vez de corrigir andando, o que causava até 35 mm de desvio lateral.

### Reta

- **`andar()` segue o rumo planejado** (`ANDAR_NO_RUMO`): passa por `andar_no_rumo(cm, _rumo_alvo)`, e não pelo rumo medido no começo, que herdava até 2° do giro anterior.
- **Freio previsto** (`RETA_PREVE_FREIO`): começa a parar a `|v|·freio` antes do fim, com o freio aprendido. Era a origem dos +4 mm.
- **`RETA_LIMITE_RODA`**: em RAPIDO, a roda de fora saturava ao corrigir o rumo e o robô fazia curvas de até 80 mm. Agora a velocidade de avanço cede espaço para a correção.

### Calibração (menu)

- **G (giro):** 5 voltas para cada lado, com média. Aceita só valores de 345 a 375 e avisa se a assimetria entre os sentidos passar de 0,5°.
- **D (deriva):** 60 s parado. Mede quantos graus por minuto o rumo anda sozinho. Bom: < 0,3°/min.
- **T (teste de giro):** bateria de giros com erro final e tempo de cada um.
- **Z (referência da mesa):** robô no gabarito, na direção 0; fixa a mesa.

## O bug do 180° (e a M5)

O erro de rumo é normalizado para (−180, 180]. Num giro de quase exatamente 180°, um centésimo de grau de ruído faz o erro saltar de +180 para −179,99: o controle "chega" na hora e o robô para sem girar. No Monte Carlo isso aparecia como erro máximo de 179,8°.

**A M5 é exposta:** ela faz `andar_no_rumo(..., 180)` seguido de `virar_para(0)`, três vezes. Agora o alvo é desembrulhado a partir do rumo real (`_desembrulhar_alvo`) e o giro sempre acontece. **Atenção:** num giro de exatamente 180°, o sentido (horário ou anti-horário) depende de um décimo de grau de ruído. Se o robô roçar em algo num dos sentidos, a saída precisa de um alvo que não seja ambíguo (179 ou −179, por exemplo). A decisão é da equipe.

## Impacto nas missões

As chamadas mais usadas em `hub/missoes.py` são `andar` (37), `virar_para` (30), `andar_no_rumo` (18), `ir_para` (5) e `curva` (4).

- **Distâncias:** o `andar()` antigo passava, em média, ~4 mm do pedido na simulação. Agora para no ponto. Distâncias que foram "acertadas na mesa" podem ter embutido esse excesso. Se uma saída chegar alguns milímetros curta, de forma consistente, ajustem a distância. A outra saída é desligar `ANDAR_NO_RUMO` e `TOLERANCIAS_DB`, que juntas devolvem o `andar()` antigo.
- **Rumo depois de giros:** como o `andar()` agora segue o rumo planejado, sequências como `virar_para(25); andar(...)` saem no 25 de verdade, e não no 24 ou 26 que o giro deixou.
- **`curva(..., parar=False)` encadeadas** (M2, M4): o alvo de rumo depois da curva agora é o da curva. Validem na mesa.
- **M5:** ver o bug do 180°.
- **`virar_ate_travar`** (M2): quando não trava, agora fecha no ângulo pedido com o giro fino, em vez de parar onde o motor parou.

## Chaves de volta

Todas em `hub/config.py`. `False` volta ao comportamento de antes desta branch.

| Chave | O que desliga | Quando desligar |
|---|---|---|
| `LARGADA_COMPENSADA` | a compensação do `largar()` (volta a zerar o rumo a cada saída) | a luz fica vermelha sem motivo; as saídas viradas saem tortas |
| `LARGADA_MIRA` | a luz de mira (fica sempre verde) | a luz confunde a equipe |
| `GIRO_FINO` | o giro fino (volta ao creep antigo) | giros lentos demais, ou o robô "tremendo" no fim |
| `TOLERANCIAS_DB` | as tolerâncias apertadas do DriveBase | `andar`/`curva` travam até o watchdog |
| `ANDAR_NO_RUMO` | `andar()` pelo rumo planejado (volta ao `db.straight`) | distâncias mudaram e não há tempo de reajustar |
| `RETA_PREVE_FREIO` | o freio previsto nas retas | retas param curtas |
| `CORRECOES_RUMO` | desembrulhar o alvo e as correções de abort, `virar_ate_travar` e `_seguir` | algum giro vai para o lado inesperado |

Os valores numéricos de antes:
- `RUMO_VIRAR_ANTES = 20`;
- `RETA_LIMITE_RODA`: um número alto, como 10000, desliga o limite;
- `GIRO_TOL_FINAL`: 1,0 ou mais deixa o fino mais frouxo e mais rápido.

**Regra do dia:** mexam numa chave por vez, rodem a saída 3 vezes e anotem.

## Protocolo de mesa (dias 5 e 6)

### Dia 5: medir o robô

1. **Firmware:** confira `DIAG firmware` no console. Tem de ser 4.x.
2. **G (giro), duas vezes:**
   - os dois resultados devem ficar a menos de 0,3 de distância;
   - a assimetria deve ficar abaixo de 0,5°.
   - Se não ficarem, o pneu está escorregando ou a contagem de voltas está errada. Repitam devagar.
3. **D (deriva):**
   - < 0,3°/min: ótimo;
   - 0,3 a 1°/min: aceitável;
   - mais que isso: deixem o hub parado ligado por 1 min antes da partida e repitam.
4. **T (teste de giro):** erro final p95 < 0,5° e tempo médio < 1 s. Se o tempo passar, `GIRO_TOL_FINAL = 0.8`.
5. **10 largadas medidas, em cada uma das 4 combinações:**
   - com e sem gabarito;
   - com `LARGADA_COMPENSADA` `True` e `False`.

   Em cada largada:
   - grave uma saída de teste com `andar_no_rumo(100, 0)`;
   - meça com régua o desvio lateral no fim. Cada 17 mm equivale a 1°.

   Esperado: gabarito < 10 mm p95; a olho, 30 a 50 mm. Se a olho com compensação não for melhor que sem, ponham `LARGADA_SIGMA_MAO = 1.5` e repitam.
6. **C (cor) na moldura verde:** anote a reflexão do verde. Ajuste `LIMIAR_BORDA` para o meio entre o branco e o verde.
7. **`alinhar_na_base`:** em 5 largadas propositalmente tortas (3 a 5°), meça o desvio a 1 m. Esperado < 10 mm.

### Dia 6: as saídas reais

1. Rodem cada saída **3 vezes** com tudo ligado. Anotem o que acontece.
2. Se uma saída que funcionava passou a falhar **sempre do mesmo jeito**:
   - **para curta ou longa por poucos mm:** ajustem a distância, ou desliguem `ANDAR_NO_RUMO` + `TOLERANCIAS_DB`;
   - **gira para o lado errado:** procurem um `virar_para` de ±180° (ver M5) ou desliguem `CORRECOES_RUMO`;
   - **lenta demais:** subam `GIRO_TOL_FINAL` ou desliguem `GIRO_FINO`.
3. Se uma saída falha **de forma aleatória**: na grande maioria das vezes é a largada. Larguem com o gabarito e esperem a luz verde.
4. **Critério de passa/falha por chave:** a chave fica ligada se a saída acertou ≥ 3 de 3 com ela e não acertou mais sem ela.
5. **Antes de ir embora:** `.venv/bin/tbr verificar`, gravem o hub e anotem o commit gravado.

## Gabarito

Projeto paramétrico em `modelos3d/gabarito/`. O `LEIAME.md` dali tem os detalhes, a precisão teórica e como gerar.
- **Peça:** L de 168 mm, com janelas de mira, batentes fixos, 3 calços para saídas viradas e alça. Impressão de 49 min, 29 g.
- **Precisão provável:** ~0,3° (pior caso 0,57°) em 0°/180°, e ~0,4° em 90°/270°.
- **Medidas para amanhã:** todas as linhas `# MEDIR` de `parametros.py`. As principais:
  - o lado interno da base e a largura da faixa;
  - o comprimento e a largura do robô;
  - onde a traseira e a lateral têm material de 6 a 20 mm do chão;
  - a distância desejada até as bordas.
- **Depois de imprimir:** confiram o esquadro com um esquadro de precisão e rejeitem a peça se passar de 0,1°.

### Perguntas ao juiz

1. O gabarito conta como "objeto estratégico" (peça da equipe, manuseada à mão, só dentro da base, para preparar o robô inativo)?
2. Ele pode encostar na borda interna da faixa verde ou ficar sobre ela?
3. Tem de estar fora da base e solto antes de o robô se mover. O juiz quer ver a retirada?
4. A alça de 27 mm de altura dentro da base, antes da largada, é problema?

## Limitações

- **O simulador não é a mesa.** Os parâmetros do robô (bias, deriva, escala, atrito, folga, coast) são suposições baseadas no datasheet do LSM6DS3TR-C, no código do Pybricks e em relatos de equipes. Os números relativos (antes contra depois) são mais confiáveis que os absolutos.
- **O tapete real, a bateria e um pneu gasto** mudam o freio. O freio aprendido se adapta, mas só na mesa dá para ter certeza.
- **A fusão depende de `LARGADA_DERIVA`**, que inclui o erro de escala nos giros feitos à mão entre saídas. O valor 2,0 é uma estimativa. Se a rotina G mostrar escala muito boa, ele pode cair.
- **`alinhar_na_base`** foi testado no simulador com uma moldura reta e uniforme. Moldura com emenda, sujeira ou luz forte pede um `LIMIAR_BORDA` medido.

## Pesquisa

Relatórios completos em `docs/giroscopio/pesquisa/`:
- `pybricks_imu.md`: o que o firmware 4.1.2 faz, lido no código-fonte:
  - quaternion 3D;
  - reestimativa do bias só com o hub parado e os motores soltos;
  - `heading_correction`;
  - as tolerâncias do `done()`;
  - o laço de 5 ms.
- `literatura.md`: modelo de erro do giroscópio, controladores de giro, retas e técnicas usadas por equipes FLL/WRO.
- `auditoria.md`: a auditoria função por função do `hub/tbr.py` antes desta branch.

Fontes principais:
- Código-fonte do Pybricks: `lib/pbio/src/imu.c`, `drivebase.c` e `control.c` ([pybricks-micropython](https://github.com/pybricks/pybricks-micropython));
- [Documentação do PrimeHub](https://docs.pybricks.com/en/latest/hubs/primehub.html) e [DriveBase](https://docs.pybricks.com/en/latest/robotics.html);
- issues [pybricks/support#1032](https://github.com/pybricks/support/issues/1032) e [#1886](https://github.com/pybricks/support/issues/1886);
- [datasheet do LSM6DS3](https://docs.arduino.cc/resources/datasheets/LSM6DS3-datasheet.pdf);
- [variância de Allan (MathWorks)](https://www.mathworks.com/help/nav/ug/inertial-sensor-noise-analysis-using-allan-variance.html).

## Como rodar o simulador

```
.venv/bin/python -m ferramentas.simgiro giro -n 400
.venv/bin/python -m ferramentas.simgiro reta -n 400
.venv/bin/python -m ferramentas.simgiro largada -n 300 -k gabarito=True
.venv/bin/python -m ferramentas.simgiro largada -n 300 -k ancorar=True
.venv/bin/python -m ferramentas.simgiro giro -c GIRO_FINO=False     # comportamento antigo
```

- `-c` sobrescreve constantes do `config.py`;
- `-k` passa opções ao cenário.

O gêmeo executa o `hub/tbr.py` real com um Pybricks falso **em tempo virtual**, em que 400 robôs levam segundos. `testes/teste_simgiro.py` guarda os limites deste documento como regressão.
