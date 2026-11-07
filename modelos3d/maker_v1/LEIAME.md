# Dispositivo Maker do CoopBot (Missão 8): modelos 3D, v1

> **Versão antiga** (4 pratos, 185 g, 4,8 h), guardada para referência. A versão atual, econômica, está em `../maker/`.

É o dispositivo que fica sobre a bandeja amarela da **Missão Maker**. Ele usa um **2º hub SPIKE Prime**, um **motor médio** e o **sensor ultrassônico**: quando o sensor vê um trabalhador na Área Industrial, o motor abre uma comporta, e o **Bloco de Educação Tecnológica** desce por uma rampa até o tapete.

- Os fontes são paramétricos, em build123d, e geram 3MF para a **Bambu Lab A1 mini com PLA Lite**, no mesmo padrão de `../elevador/`.
- Todas as cotas ficam em `parametros.py`. Nenhuma peça tem cota fixa no código.
- **O programa do 2º hub é da equipe.** Veja [Limites para o programa](#limites-para-o-programa-da-equipe).

## A missão (Desafio Prático Middle 2, p. 17–19)

- O robô leva os trabalhadores até a **Área Industrial**, a região cinza-escura em volta da bandeja. Vale **7 pontos por trabalhador** que estiver TOCANDO a área.
- O dispositivo fica **SOBRE** a área da Missão Maker, **sem cola, fita adesiva ou similares**. Ele precisa detectar sozinho, por sensor ou mecanismo, **pelo menos 1 trabalhador** na Área Industrial e então liberar o Bloco. A regra permite **1 CLP adicional**, que aqui é o 2º hub.
- O robô só pode pegar o Bloco depois que ele estiver **TOCANDO o tapete**. O Bloco vale **20 pontos** se terminar na Área Industrial e **40 pontos** na Área Escolar.
- A validação é feita pelo juiz. **Leve o dispositivo ao treino e pergunte antes da partida** (observação 7):
  1. A aba e o lábio da rampa saem até **2,2 cm** além da parede sul da bandeja, sem tocar o tapete. Isso ainda conta como dispositivo "sobre a área"?
  2. O 2º hub SPIKE conta como o CLP adicional?
  3. O Bloco que desce a rampa e para no tapete conta como "liberado pelo dispositivo"?

## Como funciona

Visto de cima, no referencial da bandeja: x vai para o leste (210 mm internos), y para o norte (85 mm) e a Área Industrial fica ao sul.

```
 norte   x = 0                                                     x = 210
 ┌──────────────────────────────────────────────────────────────────┐
 │ [placa perfurada]   ┌hub┐            ┌motor┐ ║ rampa ║            │
 │  [ultrassônico]     │em │            │em pé│─╫─dente ║            │
 │   olhos → sul       │pé │ portas↓    └─────┘ ║ Bloco ║            │
 └──────────────────────────────────────────────╨───────╨───────────┘ parede sul
    trabalhador aqui ↓ (5–20 cm)                 ╲ lábio ╲ → Bloco no tapete
```

- **Base** (`base.py`). Fica encostada na parede oeste.
  - **Placa perfurada:** uma grade de furos Technic de 7 × 5, com mãos-francesas. O ultrassônico prende nela por 2 pinos nos furos de trás, olhando para o sul, com os olhos a **50 mm** do tapete. O feixe passa a 46 mm sobre a parede de 15 mm.
  - **Luva do hub:** o hub fica **em pé** sobre a ponta dos botões, com a tela e os botões virados para o oeste. Há 18 mm livres ali para o dedo. As portas ficam nas faces norte e sul; **use as do sul**. O USB fica em cima, então dá para carregar sem tirar o hub.
- **Rampa** (`rampa.py`). Fica encostada na parede leste.
  - **Placa e lábio:** a placa a **30°** tem nervuras e passa sobre a parede sul. O lábio termina a **3 mm do tapete**.
  - **Fixação:** as laterais apoiam no fundo da bandeja e prendem a parede sul entre elas e uma **aba** externa, então a rampa não anda.
  - **Suporte do motor:** na lateral oeste, um pé e uma placa com **6 furos** para pinos Technic.
- **Motor médio**. Fica **em pé** (o eixo em x, o disco virado para a rampa, o cabo saindo por cima). Um **eixo LEGO de 3 módulos** passa do disco pelo mancal da lateral até o dente.
- **Comporta** (`comporta.py`). É um dente com cubo em cruz, dentro do túnel da rampa.
  - **Fechado:** sai 10 mm pela fenda da placa e segura o Bloco.
  - **Aberto (90°):** fica paralelo à placa, por baixo dela. Ao abrir, a ponta se afasta do Bloco, então não o empurra rampa acima.
  - **Força:** o Bloco faz menos de 5 mN·m no eixo.
- **Bloco** (`bloco.py`). Cubo de **45 mm** com arestas chanfradas, engrenagem gravada no topo e chip gravado nas 4 laterais.
  - Ele cabe na garra do elevador, que fecha até 30 e abre 60 mm.
  - **Ponha a face lisa para baixo** na rampa.

### Onde o Bloco para

- Pelo `montagem.py`, sem contar o embalo, o Bloco sai do lábio e assenta no tapete **2,3 a 6,8 cm ao sul da parede sul**, entre x = 160 e 205 mm. Isso é Área Industrial, ou seja, 20 pontos se ficar ali.
- Na prática ele chega com velocidade e desliza mais um pouco. **Meça na mesa** antes de programar o robô para buscá-lo.
- Para levá-lo à Área Escolar (40 pontos), o robô precisa pegá-lo ou empurrá-lo dali. Os dedos de 20 cm da garra batem no lábio se o robô chegar pela frente com a garra aberta perto da bandeja. Planeje a aproximação: por exemplo, pegar o Bloco pela lateral ou puxá-lo para longe do lábio antes.

## Medidas

| Item | Medida | Fonte | Situação |
|---|---|---|---|
| Bandeja | 210 × 85 mm internos, paredes de 15 mm | medida pela equipe | ok |
| Espessura da parede e do fundo da bandeja | 3 mm cada | estimativa pelas fotos | **MEDIR** |
| Hub | 88 × 56 × 32 mm (11 × 7 × 4 módulos) | ficha LEGO + LDraw 45601 | confiável |
| Motor médio | 24 × 72 × 23,6 mm. O eixo fica a 11,6 mm de uma ponta. Disco de Ø 23,2, sobressaindo 8,4 mm. | LDraw 54696p02c01 | **MEDIR** |
| Furos laterais do motor | a −8, +8 e +56 mm do eixo; alturas de 4 e 20 mm | LDraw | **MEDIR** com o gabarito do P0 |
| Ultrassônico | 56 × 23,2 × 31,6 mm, olhos a 32 mm um do outro | LDraw 37316c01 | **MEDIR** |
| Furos de trás do sensor | x = ±24 mm, a 12 mm do fundo | LDraw | **MEDIR** com o gabarito do P0 |
| Alcance do sensor | 50 a 2000 mm, ângulo de entrada de ±35° | ficha LEGO | ok |
| Botões do hub | a ~12 mm da ponta de baixo | LDraw | **MEDIR** |
| Trabalhador | 80 mm de altura, base de 40 mm | estimativa pelas fotos | **MEDIR** |

As cotas do LDraw são de modelagem e não da LEGO. Por isso o P0 tem **gabaritos** com os furos exatos que a base e a rampa usam.

## Pratos

| Prato | Peças | Camada | Tempo | PLA Lite |
|---|---|---|---|---|
| `maker_p0_teste.3mf` | placa de teste da rampa, cunhas de 25°/30°/35°, gabarito do motor, gabarito do sensor | 0,28 | 68 min | 45,8 g |
| `maker_p1_base.3mf` | base (luva do hub + placa perfurada) | 0,28 | 76 min | 50,3 g |
| `maker_p2_rampa.3mf` | rampa (com o suporte do motor) + comporta | 0,20 | 95 min | 57,1 g |
| `maker_p3_bloco.3mf` | Bloco | 0,20 | 50 min | 31,9 g |
| **Total** | 10 peças | | **≈ 4,8 h** | **≈ 185 g** |

- Os perfis são Bambu Lab A1 mini 0.4 nozzle e Bambu PLA Lite @BBL A1M, sem suporte.
- A rampa sai deitada sobre a lateral leste. Assim a placa, o pé e a placa de pinos ficam em pé, e os furos de pino ficam deitados (5,2, validado no elevador).

**Ordem:** P0 → P3 → (testes) → P1 → P2.

1. **P0 (teste).** É o prato que mais pode mudar o resto: os gabaritos dizem se os furos do motor e do sensor batem. Enquanto o P3 imprime, dá para testar os gabaritos.
2. **P3 (Bloco).** Não depende de teste nenhum, e o teste de deslize do P0 precisa dele. Teste também o Bloco na garra do elevador.
3. Ajuste `parametros.py` com o resultado dos testes e rode `montagem.py` e `gerar.py` de novo.
4. **P1 (base).** Depende só da grade do sensor (que tolera erro) e da medida do hub. Com ela pronta, confira o hub na luva e a base na bandeja antes da rampa.
5. **P2 (rampa).** Por último, porque depende de tudo: o ângulo do deslize, os furos do motor e a posição da base.

O `maker_todos.3mf` tem os 4 pratos num projeto só, já nessa ordem e fatiados (camada de 0,28 ajustada por objeto no P0 e no P1). Ele é refeito pelo `gerar.py`.

### Testes do P0

| Teste | O que fazer | Parâmetro |
|---|---|---|
| Deslize | Ponha o Bloco na placa de teste, apoiada em cada cunha. Escolha o **menor** ângulo em que ele desce sozinho, partindo parado, 5 vezes em 5. | `ANGULO_RAMPA` |
| Motor | Prenda o gabarito na lateral do motor com 6 pinos. Os 6 têm que entrar juntos. | `MOTOR_FUROS_COMPRIMENTO`, `MOTOR_FUROS_ALTURA` |
| Sensor | Prenda o gabarito na traseira do sensor com 2 pinos. | `SENSOR_FUROS_TRAS_X` |

### Peças LEGO necessárias

- **8 pinos Technic** com atrito (2 módulos): 6 no motor e 2 no sensor.
- **1 eixo LEGO de 3 módulos**, do disco do motor até o dente.
- 2º hub SPIKE Prime, motor médio e sensor de distância.

## Montagem

1. **Sensor:** ponha 2 pinos nos furos de trás do sensor e encaixe-o na placa perfurada, olhando para o sul. Ele fica centrado na grade. Se a altura não servir, use outra linha da grade.
2. **Hub:** desça-o na luva, em pé, com os botões para baixo e a tela para o oeste (para o sensor). Ligue o sensor e o motor nas **portas do sul**.
3. **Motor:** ponha o eixo LEGO de 3 módulos no disco. Ponha os 6 pinos na placa do suporte e encoste o motor neles, em pé, com o disco virado para a rampa e o cabo para cima. O eixo passa pelo mancal da lateral.
4. **Comporta:** por baixo da rampa, que é aberta embaixo, encaixe o cubo do dente na ponta do eixo, dentro do túnel.
5. **Na bandeja:** a base vai encostada na parede oeste. A rampa vai na ponta leste, com a aba por fora da parede sul. **Nada é colado.**
6. **Feche a comporta antes de pôr o Bloco.** Depois ponha o Bloco na rampa, com a face lisa para baixo: ele escorrega até o dente.

### Teste à mão

- A comporta gira de 0° a 90° sem raspar.
- Fechada, segura o Bloco. Aberta, o Bloco desce e fica tocando o tapete fora da bandeja.
- O sensor mede um trabalhador posto de 5 a 20 cm ao sul da parede, na frente dele.

## Limites para o programa da equipe

- **Sensor:**
  - os olhos ficam a 50 mm do tapete;
  - o trabalhador fica de **55 a 205 mm** da face do sensor, se estiver de 5 a 20 cm da parede;
  - `distance()` devolve 2000 quando não há eco;
  - com ±35° de abertura, o feixe pode ver o tapete ao longe. **Meça a leitura com a área vazia** e use uma janela de distância e um tempo de confirmação (por exemplo, 3 leituras seguidas abaixo do limiar).
- **Comporta:**
  - **0°:** fechada (dente na normal da placa);
  - **90°:** aberta (dente sob a placa, apontando para baixo da rampa);
  - **batente:** o fim da fenda segura o dente a cerca de **−5°**, no sentido de fechar. Para zerar, feche até o batente com força baixa, **sem o Bloco na rampa**;
  - **sentido:** o sinal do ângulo no Pybricks depende do lado do disco. **Teste à mão** qual sentido abre;
  - **velocidade:** abra rápido, para o dente sair antes de o Bloco chegar ao fim da fenda.
- Depois de liberar, mantenha a comporta aberta. O Bloco não volta.

## Arquivos

| Arquivo | Papel |
|---|---|
| `parametros.py` | Todas as cotas: bandeja, trabalhador, Bloco, rampa, comporta, motor, hub, sensor e base. |
| `geometria.py` | Auxiliares de geometria copiados de `../elevador/rosca.py`. É cópia porque lá se importa outro `parametros`. |
| `base.py` | Luva do hub e placa perfurada do sensor. |
| `rampa.py` | Rampa, lábio, aba, fenda, mancal e suporte do motor. Calcula a posição do eixo e do Bloco. |
| `comporta.py` | Dente com cubo em cruz (0° fechado, 90° aberto). |
| `bloco.py` | Bloco de Educação Tecnológica. |
| `montagem.py` | Monta tudo na bandeja e confere: interferência (comporta fechada, aberta e girando de 15 em 15°), bandeja, tapete fora da bandeja, feixe, descida do Bloco, onde ele para, garra, eixo LEGO e grade do sensor. Grava `stl/montagem.stl`. |
| `teste_encaixe.py` | Peças do prato P0. |
| `gerar.py` | Exporta os STL e fatia os pratos, com o `fatiar.py` de `../elevador/`. Recusa peça maior que 180 mm. |
| `juntar_pratos.py` | Junta os 3MF de um prato só no `maker_todos.3mf` e fatia os 4 pratos pelo CLI. |

## Gerar

Use o mesmo ambiente de modelagem do elevador, fora do `.venv` do hub:

```
<modelagem>/bin/python montagem.py      # precisa terminar sem problemas
<modelagem>/bin/python gerar.py [pasta_png] [filtro_de_prato]
```

## Ainda não testado

- O ângulo de 30° com PLA Lite, que é o teste de deslize do P0.
- A posição dos furos do motor e do sensor (vieram do LDraw), que é o teste dos gabaritos do P0.
- A estabilidade do hub em pé na luva de 18 mm quando o robô esbarra na bandeja. Se ele balançar, `LUVA_ALTURA` = 25.
- A placa de pinos do motor, de 7,6 mm e presa só pela lateral e pelo pé. Se ela fletir, acrescente uma mão-francesa.
- O comportamento do Bloco ao sair do lábio: se ele tomba, rola ou desliza.
- A leitura do ultrassônico no boneco de MDF, que é fino, e no tapete vazio.

## Fontes

- TBR 2026, Desafio Prático Middle 1 e Middle 2, v4 (04/09/2026): Missão 8, p. 17–19; montagem da bandeja, p. 36.
- LDraw, peças oficiais de Philippe Hurbain (CC BY 4.0):
  - hub: https://library.ldraw.org/library/official/parts/45601.dat
  - motor: https://library.ldraw.org/library/official/parts/54696p02c01.dat
  - sensor: https://library.ldraw.org/library/official/parts/37316c01.dat
- Fichas técnicas LEGO Education:
  - [hub 45601](https://cdn.shopify.com/s/files/1/0539/2056/3365/files/SPIKE_Prime_Tech_fact_sheet_Large_Hub_45601.pdf)
  - [motor 45603](https://cdn.shopify.com/s/files/1/0539/2056/3365/files/SPIKE_Prime_Tech_fact_sheet_Medium_Angular_Motor_45603.pdf)
  - [sensor 45604](https://cdn.shopify.com/s/files/1/0539/2056/3365/files/SPIKE_Prime_Tech_fact_sheet_Distance_Sensor_45604.pdf)
- Pybricks, UltrasonicSensor: https://docs.pybricks.com/en/latest/pupdevices/ultrasonicsensor.html
- Folgas LEGO validadas no elevador (cruz 5,0 e pino 5,2): `../elevador/LEIAME.md`.
