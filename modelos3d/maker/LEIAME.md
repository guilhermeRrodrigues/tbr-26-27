# Dispositivo Maker do CoopBot (Missão 8): modelos 3D, v2 econômica

Este é o dispositivo que fica sobre a bandeja amarela da **Missão Maker**. Ele usa um **2º hub SPIKE Prime**, um **motor médio** e o **sensor ultrassônico**. Quando o sensor vê um trabalhador na Área Industrial, o motor levanta a **trava**, e o **Bloco Overclock** desce pela rampa até o tapete.

A v2 imprime só **a rampa fina e o Bloco**, num prato só. O hub, o sensor, o motor e a trava ficam presos com peças LEGO do kit SPIKE Prime (45678).

| | v1 (`../maker_v1/`) | **v2** |
|---|---|---|
| Pratos | 4 (teste, base, rampa, Bloco) | **1** |
| PLA Lite | 185 g | **40 g** (−78%) |
| Tempo | 4,8 h | **1,5 h** (88 min) |
| O que é impresso | base com luva, placa perfurada, rampa com túnel, comporta, Bloco maciço e prato de teste | rampa fina e Bloco oco |
| Peças LEGO | 8 pinos e 1 eixo | 3 vigas e 12 pinos |

- Os fontes são paramétricos, em build123d, e todas as cotas ficam em `parametros.py`.
- **O programa do 2º hub é da equipe.** Veja [Limites para o programa](#limites-para-o-programa-da-equipe).

## A missão (Desafio Prático Middle 2, p. 17–19)

- O robô leva os trabalhadores até a **Área Industrial**, a região cinza-escura em volta da bandeja. Cada trabalhador que estiver TOCANDO a área vale **7 pontos**.
- O dispositivo fica **SOBRE** a área da Missão Maker, **sem cola, fita adesiva ou similares**.
  - Ele precisa detectar sozinho, por sensor ou mecanismo, **pelo menos 1 trabalhador** e então liberar o Bloco.
  - A regra permite **1 CLP adicional**, que aqui é o 2º hub.
- O robô só pode pegar o Bloco depois que ele estiver **TOCANDO o tapete**. O Bloco vale **20 pontos** na Área Industrial e **40 na Área Escolar**.
- A validação é do juiz. **Pergunte no treino, antes da partida** (observação 7):
  1. A aba e o lábio da rampa saem até 2,4 cm além da parede sul, sem tocar o tapete. Isso ainda conta como estar "sobre a área"? Pela definição do Vade Mecum (p. 37), "sobre" é ter 100% do peso apoiado, e todo o peso fica na bandeja.
  2. O 2º hub SPIKE conta como o CLP adicional? O Vade Mecum (p. 28) diz "apenas um CLP para a ARENA", e a Missão 8 abre a exceção.
  3. O Bloco que desce a rampa e para no tapete conta como "liberado pelo dispositivo"?
  4. A aba que desce por fora da parede, com folga e sem prender, é aceita? Ela não é cola nem fita, e o juiz consegue levantar a rampa sem força.
  5. O programa do 2º hub pode ser iniciado na preparação, antes da contagem? Depois do início, a equipe não pode tocar no dispositivo.
- **Limites de material (Vade Mecum, p. 28):** os motores e sensores do dispositivo contam junto com os do robô. Hoje são 5 motores de 6 (4 do robô e 1 da trava) e 3 sensores de 8.
- **Para o programa da equipe:** o robô passa na frente do sensor ao deixar os trabalhadores. Só abra a trava depois que ele sair, quando a leitura continuar firme sem o robô. Senão, quem disparou o dispositivo foi o robô, e não um trabalhador.

## Como funciona

Visto de cima, no referencial da bandeja: x vai para o leste (210 mm internos), y para o norte (85 mm), e a Área Industrial fica ao sul.

```
 norte  x = 0                                                         x = 210
 ┌──────────────────────────────────────────────────────────────────────┐
 ║┌───────────── hub deitado (tela p/ cima) ─────┐╓┐                   │
 ║│ ┌─── sensor por cima ───┐                    │║│   ┌─────┬─────┐   │
 ║│ │                       │   ┌──── motor ─────┼╫┼───┤prat.│ ║ ║ │   │
 ║│ └── olhos → sul ────────┘   └────────────────┼╫┼─ disco ═trava═╬═╗  │
 ║└──────────────────────────────────────────────┘║│   │ rampa Bloco  │  │
 viga do sensor                          encosto 9M  └──────╨──────╨──┘ parede sul
    trabalhador aqui ↓ (5–20 cm)                           ╲ lábio → Bloco no tapete
```

- **Hub** (LEGO). Fica deitado no fundo da bandeja, com a tela para cima, encostado na parede norte e na ponta oeste.
  - A **viga de encosto** (9M) vai pinada na ponta leste do hub e desce até 4 mm da parede sul, então o hub não anda em y.
- **Sensor** (LEGO). Fica deitado **sobre o hub**, olhando para o sul, preso pela ponta numa **viga 7M em pé** na ponta oeste do hub.
  - Os olhos ficam a **47 mm** do tapete.
  - O cone de ±35° passa livre e cruza a parede sul a 36 mm de altura.
- **Rampa** (`rampa.py`, impressa). Fica encostada na parede leste.
  - **Placa:** 1,6 mm a **30°**, com 3 nervuras e trilhos de 3,5 mm. Há janelas entre as nervuras do meio, por onde a borda do Bloco não corre.
  - **Lateral leste:** é em treliça, um triângulo com a borda da placa, uma perna até o fundo e uma barra até o assento. É a face que vai na mesa de impressão.
  - **Lateral oeste:** tem só a borda e o trilho, com mãos-francesas a 45° por baixo.
  - **De lado a lado:** o assento com a aba, a travessa da ponta alta e uma perna larga, que é uma parede fina com janela em losango.
  - **Fixação:** o assento apoia no topo da parede sul, e uma **aba** desce por fora dela, então a rampa não anda.
  - **Lábio:** termina a 3 mm do tapete, fora da bandeja.
  - **Prateleira do motor:** fica na borda oeste, com **4 furos de pino**.
- **Motor** (LEGO). Fica deitado sobre a prateleira, preso por 4 pinos, com o corpo para o oeste por cima do hub (2 mm acima da tela).
  - O eixo fica ao longo da descida, com o disco virado para baixo da rampa.
- **Trava** (LEGO). É uma **viga 7M pinada no disco** do motor, que funciona como **cancela**.
  - **Fechada (0°):** fica deitada através do canal, 8 mm acima da placa, e entra 30 mm no canal na frente do Bloco.
  - **Aberta (90°):** gira para **cima** e fica em pé, fora do canal.
  - O Bloco empurra a viga **ao longo do eixo** do motor, então o motor **não faz força** para segurar.
- **Bloco** (`bloco.py`, impresso). Caixa oca de **45 mm**, aberta embaixo, com paredes de 1,2 mm e topo de 1,6 mm.
  - O **logo da Overclock** fica em baixo-relevo no topo e nas 4 laterais, de pé para quem olha de fora.
  - A borda de baixo é chanfrada e desliza nas nervuras.
  - Ele cabe na garra do elevador, que fecha até 30 e abre 70 mm. **A boca aberta fica para baixo** na rampa.

### Onde o Bloco para

- Pelo `montagem.py`, sem contar o embalo, o Bloco sai do lábio e assenta no tapete **2,3 a 6,8 cm ao sul da parede sul**, entre x = 161 e 206 mm. Isso é Área Industrial.
- Na prática ele chega com velocidade e desliza mais um pouco. **Meça na mesa** antes de programar o robô para buscá-lo.

## Peças LEGO (kit 45678)

- 1× **viga 7M** (reta, 7 furos), em pé na ponta oeste do hub, para segurar o sensor.
- 1× **viga 9M** (reta, 9 furos), deitada na ponta leste do hub, como encosto contra a parede sul.
- 1× **viga 7M** (reta, 7 furos), como trava, pinada no disco do motor.
- 12× **pino com atrito, 2 módulos (preto)**, distribuídos assim:

  | Ligação | Pinos |
  |---|---|
  | Hub e viga do sensor | 2 |
  | Viga do sensor e sensor | 2 |
  | Hub e encosto | 2 |
  | Motor e prateleira | 4 |
  | Trava e disco | 2 |

- O 2º hub SPIKE Prime, o motor médio e o sensor de distância.

## Montagem

O manual ilustrado, com uma figura por passo, está em `manual/manual.html`. O resumo vem abaixo.

Os furos são contados a partir da ponta de baixo ou da ponta norte de cada viga.

1. **Viga do sensor:** pine a viga 7M **em pé** na ponta oeste do hub.
   - Use o furo do lado **sul** dessa ponta (com o hub deitado, a tela para cima e a ponta oeste à sua esquerda).
   - Os furos 1 e 3 da viga vão nos furos de 4 e 20 mm do fundo do hub.
2. **Sensor:** pine a ponta do sensor nos furos **5 e 7** da viga, com os olhos para o sul e o sensor deitado sobre a tela do hub. Ele fica 0,4 mm acima da tela.
3. **Encosto:** pine a viga 9M **deitada** na ponta leste do hub.
   - Os furos 1 e 5 da viga vão nos 2 furos de baixo (4 mm) da ponta.
   - O furo 1 fica do lado norte, e a viga desce para o sul.
4. **Motor:** pine o motor na prateleira da rampa com 4 pinos, nos furos de uma das faces largas (os de −8/+8 do eixo, a 4 e 20 mm do fundo).
   - O disco fica para baixo da rampa (sul) e o cabo para o oeste.
5. **Trava:** pine a viga 7M no disco com 2 pinos, nos furos 1 e 3 da viga, que ficam nos furos do disco a ±8 do eixo. O furo 2 da viga fica sobre o eixo.
   - Na posição fechada, a viga aponta para o leste, por cima do canal.
6. **Na bandeja:**
   - O hub vai no canto noroeste, com a viga do sensor encostada na parede oeste.
   - A rampa vai na ponta leste, com a aba por fora da parede sul.
   - Ligue o sensor e o motor no hub.
   - **Nada é colado.**
7. **Carregar:** feche a trava e ponha o Bloco na rampa com a boca para baixo. Ele escorrega até a trava.

## Impressão

São dois pratos, ambos com perfil 0.24mm Draft, PLA Lite e sem suporte:

- `maker_impressao.3mf` tem a rampa e o Bloco e leva **88 min e 40,3 g**.
- `maker_rampa.3mf` tem só a rampa, para quem já imprimiu o Bloco, e leva **57 min e 25,6 g**.

| Peça | Orientação | Volume |
|---|---|---|
| Rampa | **deitada sobre a lateral leste**, com a treliça na mesa (a placa fica em pé e a prateleira do motor fica no alto, com os furos de pino deitados) | 21,1 cm³ |
| Bloco | **de cabeça para baixo** (o topo com o logo na mesa) | 10,9 cm³ |

- **Por que deitada:** a 1ª versão da v2 imprimia em pé, com 103 mm de altura sobre uma tira de 2 mm (128 mm² de primeira camada). Na A1 mini, que move a mesa, ela não imprimiu. Deitada, a primeira camada tem 1205 mm², a peça tem 77 mm de altura sobre uma base de 57 mm e não precisa de brim.
- **Conferência:** o `gerar.py` roda o `imprimivel.py` em cada peça e recusa a que tiver primeira camada pequena, que for alta demais para a base ou que tiver balanço sem suporte.
- **Furos de pino:** o furo de 5,2 foi validado no elevador com camada de 0,20, e aqui a camada é de 0,24. Se os pinos ficarem duros ou frouxos na prateleira, ajuste `PINO_FURO`. Com camada de 0,20, o tempo sobe.

### Antes de imprimir: teste de deslize sem gastar nada

O ângulo de 30° precisa fazer o Bloco descer sozinho.

1. Imprima **só o Bloco** primeiro, ou use qualquer peça de PLA com face lisa.
2. Ponha o Bloco sobre outra face lisa de PLA.
3. Incline devagar, medindo com o **nivelador do celular**.
4. Anote o **menor** ângulo em que ele desce sozinho, partindo parado, 5 vezes em 5.
5. Ponha esse valor, mais 3°, em `ANGULO_RAMPA`.

## Limites para o programa da equipe

- **Sensor:**
  - os olhos ficam a 47 mm do tapete;
  - o trabalhador fica de **65 a 215 mm** da face do sensor, se estiver de 5 a 20 cm da parede;
  - `distance()` devolve 2000 sem eco.
  - O cone de ±35° pode ver o tapete ao longe. **Meça a leitura com a área vazia** e use uma janela de distância e um tempo de confirmação (por exemplo, 3 leituras seguidas abaixo do limiar).
- **Trava:**
  - **0°:** fechada, com a viga deitada sobre o canal;
  - **90°:** aberta, com a viga em pé, para cima;
  - **para zerar:** feche a trava à mão e zere o ângulo no programa;
  - **sentido:** o sinal do ângulo no Pybricks depende do lado do disco. **Teste à mão** qual sentido levanta a viga. No sentido errado, ela bate na placa uns 12° abaixo de 0.
  - O Bloco não força a trava (a força é ao longo do eixo), então o motor pode ficar solto (`stop()`) enquanto espera.
- Depois de liberar, deixe a trava aberta. O Bloco não volta.

## Arquivos

| Arquivo | Papel |
|---|---|
| `parametros.py` | Todas as cotas: LEGO, bandeja, trabalhador, Bloco, logo, rampa, trava, motor, hub e sensor. |
| `geometria.py` | Auxiliares de geometria copiados de `../elevador/rosca.py`. É cópia porque lá se importa outro `parametros`. |
| `logo.py` | Vetoriza o PNG do logo (`~/Downloads/overclock logo1.png`) em `logo_overclock.json` e gera uma prévia. Só precisa rodar de novo se o logo mudar. |
| `bloco.py` | Bloco Overclock: caixa oca com o logo em baixo-relevo. |
| `rampa.py` | Rampa fina, prateleira do motor, e a posição do motor e da trava (calcula a posição do Bloco). |
| `lego.py` | Módulo LEGO: hub, sensor, vigas, motor e trava como sólidos, com os pinos e a lista de peças. |
| `montagem.py` | Monta tudo na bandeja e confere interferência (trava a 0°, 45° e 90° e girando de 15 em 15°), bandeja, tapete fora da bandeja, cone do feixe, trava que segura, descida do Bloco, onde ele para, pinos nos furos, garra e impressora. Grava `stl/montagem.stl` e `stl/montagem_aberta.stl`. |
| `imprimivel.py` | Confere, no STL na orientação de impressão, a primeira camada, a altura em relação à base e o balanço sem suporte. |
| `manual.py` | Gera as figuras do manual de montagem (`manual/*.png`) a partir do próprio modelo. A página é `manual/manual.html`. |
| `gerar.py` | Exporta os STL na orientação de impressão, confere cada um com o `imprimivel.py` e fatia os 2 pratos pelo `fatiar.py` de `../elevador/`. |

## Gerar

Use o mesmo ambiente de modelagem do elevador, fora do `.venv` do hub:

```
<modelagem>/bin/python logo.py [png] [pasta_previa]   # só se o logo mudar
<modelagem>/bin/python montagem.py                    # precisa terminar sem problemas
<modelagem>/bin/python gerar.py [pasta_png]
```

## Medidas

| Item | Medida | Fonte | Situação |
|---|---|---|---|
| Passo LEGO | 8,0 mm | consenso; LDraw (20 LDU) | ok |
| Furos do hub, do motor e do sensor | na grade de 8 mm | LDraw (conectores) | ok, LEGO com LEGO |
| Viga grossa | seção de 7,8 mm (as fontes citam 7,4 a 7,8) | nominal | **MEDIR** (usada como envelope) |
| Hub | 88 × 56 × 32 mm | ficha LEGO | ok |
| Motor médio | 24 × 72 × 23,6 mm; disco de Ø 23,2, sobressaindo 8,4 | LDraw | **MEDIR** |
| Sensor | 56 × 23,2 × 31,6 mm; furos das pontas a 4 mm da traseira e ±8 mm na altura | LDraw | **MEDIR** |
| Bandeja | 210 × 85 internos, paredes de 15 mm | equipe | ok |
| Espessura da parede e do fundo da bandeja | 3 mm cada | estimativa pelas fotos | **MEDIR** |
| Trabalhador | 80 mm de altura | estimativa | **MEDIR** |

## Ainda não testado

- A rampa deitada: o fatiador e o `imprimivel.py` aprovam, mas ela ainda não foi impressa. Confira se a prateleira do motor, que fica no alto, sai firme.
- O ângulo de 30° com o Bloco oco (veja o teste de deslize acima).
- Os pinos na prateleira impressa com camada de 0,24.
- A firmeza do sensor preso só por uma ponta. Ele fica 0,4 mm acima da tela do hub; se balançar, apoie a outra ponta num calço.
- A firmeza do hub quando o robô esbarra na bandeja. Ele só fica livre para o leste, e se andar, a viga do sensor deixa de encostar na parede oeste.
- O comportamento do Bloco ao sair do lábio: se ele tomba, rola ou desliza.
- A leitura do ultrassônico no boneco de MDF, que é fino, e no tapete vazio.

## Fontes

- TBR 2026, Desafio Prático Middle 1 e Middle 2, v4 (04/09/2026): Missão 8, p. 17–19; montagem da bandeja, p. 36.
- LDraw, peças oficiais de Philippe Hurbain (CC BY 4.0):
  - hub: https://library.ldraw.org/library/official/parts/45601.dat
  - motor: https://library.ldraw.org/library/official/parts/54696p02c01.dat
  - sensor: https://library.ldraw.org/library/official/parts/37316c01.dat
- Cotas LEGO:
  - https://github.com/fa-mc/vibe-cading/blob/main/docs/lego-technic.md, que cita Cailliau;
  - https://techmaps.uk/lego-technic-dimensions-mm-complete-guide-to-lego/
- Inventário do kit 45678: https://brickset.com/inventories/45678-1
- Folgas LEGO validadas no elevador (cruz 5,0 e pino 5,2): `../elevador/LEIAME.md`.
