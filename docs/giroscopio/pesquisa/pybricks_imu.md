# Giroscópio e DriveBase no código-fonte do Pybricks (v4.1.2)

Fonte: `pybricks-micropython`, tag v4.1.2 (2026-10-25, commit 511f6c2).
Caminhos relativos a `lib/pbio/`, salvo indicação.
Legenda: [C] confirmado no código; [I] inferido; [?] não verificado.

## 1. Versões
- A última estável é a v4.1.2. Os stubs da .venv são da 4.1.1, da mesma linha.
- 3.6.0b3: introduziu a orientação 3D por quaternion, `imu.orientation()`, `calibrated=` e as calibrações de bias, escala e aceleração. O heading 1D continuava sendo o padrão.
- 4.0.0b3: o 3D virou o padrão de `imu.heading()` e de `use_gyro`.
- 4.0.0b5: entraram `turn(angle, absolute=True)` e `move_by`, e o heading passou a ser zerado ao iniciar o programa.
- 4.1.2: `heading()` não aceita argumento e chama sempre o 3D (`pybricks/common/pb_type_imu.c:300`). `use_gyro(True)` seleciona o 3D (`pybricks/robotics/pb_type_drivebase.c:456-458`). O 1D não tem acesso pelo Python.

## 2. Pipeline da IMU
### Hardware (`drv/imu/imu_lsm6ds3tr_c_stm32.c`) [C]
- LSM6DS3TR-C ligado por I2C. Giroscópio e acelerômetro a **833 Hz** (l.72-74).
- Giroscópio com fundo de ±2000 dps, ou **0,07 °/s por LSB**. Acelerômetro com ±8 g.
- O driver não configura LPF nem HPF: ficam os padrões do chip. A leitura é feita por interrupção de data-ready, em burst.
- O `sample_time` é remedido a cada janela parada, como Δt_real/n. Isso corrige o erro do relógio do ODR.

### Integração do heading (`src/imu.c`) [C]
- **3D (o que `heading()` e `use_gyro` usam):**
  - O quaternion é integrado por Euler (l.299-303). A entrada é ω_cal mais uma correção de gravidade, que só atua em roll e pitch. O yaw é integração pura do giroscópio [I].
  - O heading é `atan2(-x.y, x.x)` do eixo X do robô projetado no plano horizontal. Um contador de voltas desembrulha o salto de ±180°.
  - **Consequência:** levantar ou inclinar o robô NÃO corrompe o rumo [I, pela construção].
- **Retorno:** `(rotações·360 + projeção) · 360/heading_correction − offset` (l.681-687). O sentido horário é positivo.
- **ω_cal:** `(ω_raw·0,07 − bias)·360/angular_velocity_scale` (l.242).

### Imobilidade e bias [C]
- **Critério de parado** (driver, l.282-332):
  - as 6 componentes ficam dentro de ±limiar de uma amostra de referência por **833 amostras seguidas (~1 s)**;
  - os limiares padrão são 2,0 °/s e 2500 mm/s² (`imu.c:147-148`);
  - quando o critério falha, a referência vira a média das últimas 125 amostras.
- **`pbio_imu_is_stationary()`:** só é verdadeiro se o driver estiver parado **e todos os motores estiverem em coast** (`imu.c:455-457`). Com qualquer motor em HOLD, torque ou brake, o bias **nunca** é reestimado.
- **Atualização do bias:**
  - a cada janela parada, durante o programa todo: `bias = bias·(1−w) + w·média`;
  - `w = 1/n` até n=20, depois 0,05, o que dá τ ≈ 20 janelas (~20 s de imobilidade acumulada);
  - após 10 min sem janela parada, n volta a 0.
- **`imu.ready()`:** houve ao menos uma janela parada nos últimos 10 min. Não quer dizer "parado agora"; para isso existe `imu.stationary()`.

### `imu.settings()` [C]
- **`angular_velocity_threshold` e `acceleration_threshold`:** os limiares do critério de parado.
- **`heading_correction`:**
  - padrão 360, aceito só na faixa 360±15;
  - funciona como "graus brutos medidos numa volta real";
  - é **um único fator para os dois sentidos** de giro, aplicado ao 3D e ao 1D.
- **`angular_velocity_bias`:** só o valor inicial no boot. **`angular_velocity_scale`:** um por eixo. **`acceleration_correction`:** 6 valores.
- As configurações persistem no storage do sistema e são apagadas quando a versão do firmware muda.

## 3. DriveBase com `use_gyro(True)`
- **Fonte do rumo:**
  - `get_state_control` (`drivebase.c:164-191`) troca o rumo e a taxa medidos pelos encoders pelos do giroscópio;
  - o termo **D do PID usa o `speed_estimate` dos encoders** (`control.c`), não a taxa do giroscópio (issue #1192, aberta) [C].
- **Laço de controle de 5 ms** (`include/pbio/config.h:16`) [C].
- **Dois controladores de posição com trajetória trapezoidal:**
  - um para a distância (média das rodas) e outro para o heading ((esq−dir)/2);
  - `drive()` é controle por velocidade com integrador;
  - `turn()` cria a trajetória de heading e mantém a distância parada (`drivebase.c:666-718`).
- **Ganhos padrão:**
  - `kp_db` = metade do kp do servo, e ki=0;
  - aceleração = 3/4 de 2000 °/s² de roda;
  - `actuation_max_heading` = 2× a da distância.
- **Quando `done()` vira verdadeiro** (`control.c:94-150`), as três condições abaixo precisam valer:
  1. o tempo da trajetória já acabou (ele pausa quando o torque satura);
  2. |velocidade| ≤ speed_tolerance;
  3. |erro| ≤ position_tolerance.
- **Tolerâncias do drivebase** (`drivebase.c:80-82`): `position_tolerance = actuation_max/kp`, que dá ~26 graus de roda. Com roda de 56 e bitola de 80, isso equivale a **~18,5° de rumo do robô** e **~13 mm de distância**. A tolerância de velocidade é de ~35 °/s de robô.
  - **Explica a medição da M5:** o `db.turn` era dado por concluído com ~15° faltando.
  - **API de ajuste:** `db.heading_control.target_tolerances(speed, position)` e `db.distance_control.target_tolerances(...)`.
- **`db.reset(angle=)`:** para o drivebase em COAST e ajusta o heading da IMU. **`use_gyro()`:** para em COAST quando o modo muda.
- **`stop()` e `brake()`:** param o controle. `hold()` = `drive_straight(0)` com HOLD.

## 4. Issues relevantes (github.com/pybricks/support)
- #1687: deriva de 13-20°/min com o hub quente; recalibra sobretudo na 1ª parada.
- #1840: giro lento era tomado por "parado" e corrompia o bias. Corrigido exigindo motores em coast.
- #1105: limiares de parado; ficaram em 2,0 °/s e 2500 mm/s².
- #1962: heading 3D para dirigir.
- #1907: calibração da IMU pelo usuário.
- #1678: origem do `heading_correction`.
- #2500: `target_tolerances` e o arredondamento na distância; discussão sobre turn(360).
- #1500: esteiras girando 340 em vez de 360.
- #1032: com use_gyro em alta velocidade, a correção de rumo é lenta.
- #1818: `turn` com HOLD esquecia o reset do heading. Daí vem o OSError do `reset_heading` com o gyro ativo.
- #1192: pedido para usar a taxa do giroscópio no termo D.

## 5. Sensor
- Os valores abaixo vêm de memória e de agregadores; ainda precisam ser conferidos no PDF da ST:
  - ruído ~7 mdps/√Hz;
  - offset de fábrica de ±10 dps;
  - deriva térmica de ±0,05 dps/°C;
  - sensibilidade de ±1-3%.
- Para giros, o ruído branco é desprezível. Quem manda é o bias (com a temperatura) e a escala.
