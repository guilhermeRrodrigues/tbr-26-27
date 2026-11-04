# Linguagem de missões do CoopBot

Tudo vem de `from tbr import *` (arquivo `hub/tbr.py`). Unidades: **cm**, **graus**, **ms**.

## Referencial

- **Origem:** centro do eixo das rodas na posição de partida da saída. O menu zera a posição ao iniciar cada saída. O rumo também é zerado, mas com `LARGADA_COMPENSADA` ele começa no quanto o robô foi solto torto, e o 1º movimento corrige (ver *Largada* e `docs/giroscopio.md`).
- **Rumo 0:** para onde o robô apontava ao sair, ou seja, leste, saindo da base. **Positivo = horário (direita)**: 90 = sul, -90 = norte, 180 = oeste.
- **x:** cresce para a frente (leste); **y** cresce para a esquerda (norte).
- **O rumo é absoluto.** `girar(90); girar(90)` deixa o robô exatamente em 180, porque o erro de um giro não passa para o próximo.

## Retorno

Os movimentos devolvem `True` (terminou) ou `False` (travou ou estourou o tempo). Nas retas e curvas, "travou" também é **andar sem sair do lugar**: menos de `PROGRESSO_MIN_MM` (1 cm) em `STALL_ABORTA_MS` (0,7 s), como quando o robô empurra algo encostado que cede um pouco e as rodas não chegam a parar. Ninguém é obrigado a olhar o retorno, mas dá para reagir:

```python
if not ate_linha(max_cm=40):
    voltar_base()
    return
```

O **botão central durante uma saída** aborta tudo e volta ao menu.

## Movimento

| Comando | O que faz |
|---|---|
| `andar(cm, vel=NORMAL, parar=True)` | Reta no rumo **desejado** (o do último giro), pelo giroscópio. Com `ANDAR_NO_RUMO` é um `andar_no_rumo(cm, rumo desejado)`. Valor negativo anda de ré. `parar=False` emenda no próximo movimento sem frear. |
| `andar_no_rumo(cm, rumo, vel=NORMAL, parar=True)` | Reta no rumo **absoluto** `rumo`, corrigindo a direção o tempo todo: se sair do rumo no caminho, guina de volta andando. Se começar mais de 8° torto (`RUMO_VIRAR_ANTES`), vira no lugar antes. Negativo anda de ré, com a frente no `rumo`. |
| `girar(graus, vel=NORMAL)` | Giro no lugar, relativo ao rumo desejado. |
| `virar_para(rumo, vel=NORMAL)` | Gira até o rumo absoluto pelo caminho mais curto. Num giro de exatamente 180° o sentido depende do ruído: se importar, peça 179 ou -179. |
| `andar_ate_travar(max_cm, vel=LENTO, ms=250)` | Anda no rumo atual até encostar em algo (as rodas não avançam 3 mm em `ms` ms), no máximo `max_cm` (negativo = de ré). Corrige a direção andando. Devolve `True` se travou, `False` se chegou ao limite sem encostar; o log mostra `encostou em X cm` ou `AVISO: ... chegou a X cm sem encostar`. Roda que patina conta como avanço: encoste devagar. |
| `virar_ate_travar(rumo, vel=LENTO, ms=250)` | Como `virar_para`, mas para se o giro travar (o rumo não muda 1° em `ms` ms). O rumo onde parou vira o rumo desejado. Devolve `True` se travou. |
| `sacudir(ms, cm=1, graus=6)` | Sacode por `ms` milissegundos: vai e volta `cm` para a frente e para trás e vira `graus` para cada lado, em torno do ponto e do rumo onde começou, e no fim volta para eles. Para assentar uma peça, soltar um anexo enroscado ou encaixar algo. `cm=0` só vira; `graus=0` só vai e volta. |
| `curva(raio_cm, graus, vel=NORMAL, parar=True)` | Arco; o rumo muda `graus` (+ = direita). `parar=False` emenda no próximo movimento sem frear: `andar`/`curva`/`andar` com `parar=False` viram um caminho contínuo. |
| `ir_para(x, y, vel=NORMAL, de_re=False)` | Vira e anda até o ponto, usando a posição estimada. |
| `voltar_base(vel=RAPIDO, de_re=False)` | `ir_para(0, 0)`. |
| `parar_tudo()` | Para a tração e os anexos. |

Velocidades (ajustáveis no `config.py`):

| | reta (mm/s) | giro (graus/s) |
|---|---|---|
| `LENTO` | 150 | 90 |
| `NORMAL` | 300 | 180 |
| `RAPIDO` | 450 | 300 |

No giro, também vale um número em graus/s: `virar_para(-180, 60)`. Giro mais lento é mais preciso, principalmente carregando objetos.

## Linhas: o realinhamento numa mesa sem bordas

| Comando | O que faz |
|---|---|
| `ate_linha(cor_alvo=PRETO, sensor=QUALQUER, vel=LENTO, max_cm=50)` | Anda até `DIR`, `ESQ` ou `QUALQUER` sensor ver `PRETO`/`BRANCO`/`VERDE`/`BORDA` (a moldura verde-escura da base). Com `vel` negativa, procura de ré. Devolve `True` se achou. |
| `alinhar_na_linha(vel=LENTO, max_cm=30, rumo=None, fino=True)` | Cada roda para quando o seu sensor vê o preto, e o robô fica perpendicular à linha. Com `rumo=...`, **reescreve o giroscópio** com o rumo conhecido da linha, o que zera o erro acumulado. |
| `alinhar_na_base(rumo=0, vel=LENTO, max_cm=30, fino=True)` | Como `alinhar_na_linha`, mas na **moldura verde-escura da base** (cor `BORDA`, limiar `LIMIAR_BORDA`): sai da base, esquadreja na borda e reescreve o rumo e a referência da mesa. Para as saídas críticas: tira o erro da mão (~0,3°) por ~2 s. |
| `seguir_linha(cm, sensor=DIR, borda=ESQ, vel=200, kp=None, kd=None)` | Segue a borda da linha por `cm` (controle PD). |
| `seguir_linha_ate_cruzamento(sensor=DIR, borda=ESQ, vel=200, max_cm=150, ...)` | Segue com um sensor até o **outro** ver preto (cruzamento ou barra no fim da linha). |
| `reflexao(sensor)` | 0 (preto) a 100 (branco), normalizada pela calibração. |
| `reflexao_crua(sensor)` / `cor(sensor)` | Leitura bruta / `Color.BLACK`, `Color.GREEN`... |

**Bordas:**
- `borda=ESQ` segue a borda esquerda da faixa preta, com o preto à direita do sensor.
- As linhas do tapete TBR são faixas preta + branca lado a lado. A borda entre as duas tem o melhor contraste.

**Depois de `seguir_linha`**, o rumo desejado passa a ser o da linha.

## Posição

| Comando | O que faz |
|---|---|
| `posicao()` | `(x, y, rumo)` estimados. |
| `rumo()` | Rumo medido pelo giroscópio. |
| `odometro()` | Centímetros que as rodas já andaram (ré desconta). A diferença entre duas leituras diz quanto um movimento andou. |
| `definir_posicao(x, y)` | Corrige a estimativa (ex.: depois de alinhar numa linha de posição conhecida). |
| `zerar_posicao()` / `zerar_rumo()` | Volta a posição para (0, 0) / zera o rumo e a posição (o rumo da mesa continua valendo). |

A posição é odometria (encoders + giroscópio): o erro cresce com a distância. Realinhe nas linhas sempre que der.

### Largada e rumo da mesa

O giroscópio lembra para onde o robô aponta **na mesa** entre uma saída e outra. A 1ª largada da partida (ou a rotina Z do menu) fixa essa referência, de preferência com o gabarito.

| Comando | O que faz |
|---|---|
| `largar(nominal=None)` | O menu chama ao apertar: zera a posição, e o rumo começa no desvio em relação à direção `nominal` da saída (padrão: o múltiplo de 90° mais perto), fundindo o que a mão garante (`LARGADA_SIGMA_MAO`) com o que o giroscópio viu. Acima de `LARGADA_MAX_DESVIO` (8°) não compensa. |
| `rumo_mesa()` | Rumo na mesa (0 = direção da referência), ou `None` sem referência. |
| `desvio_largada(nominal=None)` | `(desvio, nominal)` que o `largar()` usaria agora, ou `None`. É o que a luz de mira mostra. |
| `definir_mesa(nominal=0)` | O robô, parado, aponta exatamente para `nominal` na mesa: vira a referência. |

No menu, numa saída, a luz é a **mira**: verde = desvio ≤ 0,5° e giroscópio parado; amarela = até 2°; vermelha = mais. Uma saída em diagonal declara a direção com um 3º item: `("M9", m9_patio, 45)`.

## Anexos (anexo1 = porta F, anexo2 = porta B)

| Comando | O que faz |
|---|---|
| `anexo1(graus, vel=500, esperar=True)` | Gira relativo. `esperar=False` devolve na hora, e o anexo se mexe enquanto o robô anda. |
| `anexo1_aumentar(graus, vel=500, esperar=True)` | Soma `graus` ao ângulo **medido agora** (negativo diminui). Use quando o anexo pode ter sido empurrado ou cedido com peso: o `anexo1()` parte do alvo anterior e acumula essa diferença. |
| `anexo1_ir_para(angulo, vel=500, esperar=True)` | Vai ao ângulo absoluto (0 = início da saída). |
| `anexo1_ate_travar(sentido=HORARIO, forca=50, teto_ms=3000, esperar=True)` | Empurra com `forca`% até travar (garra fechando, fim de curso) e segura. |
| `anexo1_recolher(sentido=HORARIO, forca=30, teto_ms=1500, esperar=True)` | Leva o anexo até o batente (`sentido` = lado do batente) e faz dali o ângulo 0. Use depois de forçar o braço: engrenagem que pula dente faz o motor girar sem o braço, e o 0 antigo fica errado. Se o batente aparecer a mais de 30° do 0, o log avisa. |
| `esperar_anexos(teto_ms=5000)` | Espera os anexos lançados com `esperar=False`. |
| `zerar_anexos()` · `angulo_anexo1()` | O menu zera os anexos no início de cada saída. |

Todos existem também como `anexo2...`. `sentido` é `HORARIO` ou `ANTI_HORARIO`.

### Anexo enquanto o robô se mexe

Todo comando de anexo aceita `esperar=False`: devolve na hora e o anexo se mexe **junto** com o próximo comando (andar, girar, curva, seguir linha, sacudir, esperar...). Ele continua vigiado: se travar ou estourar o tempo, para e segura sozinho, sem parar o robô.

```python
anexo1(-90, esperar=False)            # baixa o braço...
andar(30)                             # ...enquanto anda
anexo2_ate_travar(HORARIO, esperar=False)
sacudir(1500)                         # fecha a garra sacudindo
esperar_anexos()                      # garante que os dois terminaram
```

Os dois anexos podem estar em movimento ao mesmo tempo. Um novo comando no mesmo anexo substitui o anterior.

## Elevador (porta B) e garra (porta F)

Comandos em **centímetros** para o elevador de fuso e a garra de pinça (`modelos3d/elevador`). Por baixo são os mesmos motores dos anexos (elevador = `anexo2`, garra = `anexo1`): `esperar=False` e `esperar_anexos()` valem igual.

| Comando | O que faz |
|---|---|
| `subir(cm=None, vel=NORMAL, forca=100, esperar=True)` | Sobe `cm` a partir da altura medida agora. Sem `cm`, vai ao topo (19,6 cm). |
| `descer(cm=None, vel=NORMAL, forca=100, esperar=True)` | Desce `cm`. Sem `cm`, vai até embaixo (altura 0). Com força baixa, desce sem esmagar: se encostar, avisa e para ali. |
| `elevador_ir_para(cm, vel=NORMAL, forca=100, esperar=True)` | Vai à altura absoluta `cm` (0 = embaixo). |
| `abrir(cm=None, vel=NORMAL, forca=30, esperar=True)` | Abre `cm`. Sem `cm`, abre até o batente e faz dali o 0. |
| `fechar(cm=None, vel=NORMAL, forca=40, esperar=True)` | Fecha `cm` por posição. Sem `cm`, fecha até travar na peça (ou no fim do curso) e segura: é o jeito de **pegar**. |
| `apertar(forca=25, vel=LENTO, esperar=True)` | Fecha e **fica apertando**: se a peça escorregar ou ceder, a garra fecha mais sozinha, sempre com no máximo `forca`%. Só para com outro comando de garra (`abrir`, `fechar`, `garra_ir_para`, `anexo1_...`) ou no fim da saída. `esperar=True` devolve quando encosta na peça; o aperto continua. |
| `garra_ir_para(cm, vel=NORMAL, forca=40, esperar=True)` | Deixa `cm` entre os dedos (de 3 a 6). |
| `altura_elevador()` · `abertura_garra()` | Altura do carro e distância entre os dedos, em cm. |

- **`vel`** é `LENTO`, `NORMAL` ou `RAPIDO` (traduzidos para graus/s de motor no `config.py`) ou um número em graus/s.
- **`forca`** é o % do torque do motor (10 a 100). Vale para o movimento **e para o que vem depois**: a garra continua apertando e o elevador continua segurando com essa força. Encostou em algo que a força não vence? O movimento para ali, segura e avisa "travado" (devolve `False`). Os padrões ficam no `config.py` (`ELEVADOR_FORCA`, `GARRA_FORCA`, `GARRA_FORCA_ABRIR`).
- **Limites.** Nada passa do curso: um pedido fora dele vai até o limite e o log avisa. O 0 é o do início da saída, então **comece com o carro embaixo e a garra aberta**, ou chame `abrir()` primeiro.
- **O fuso não se segura sozinho.** Só o motor B, travado em posição, segura o carro: com peso e força baixa ele pode ceder. Se a saída abortar, o carro pode descer.
- Se `subir()` descer ou `fechar()` abrir, troque `ELEVADOR_SOBE` ou `GARRA_FECHA` no `config.py`.

```python
abrir()                               # garante a garra aberta e o 0 certo
subir(5, esperar=False)               # sobe 5 cm...
andar(30)                             # ...enquanto anda
descer(4, LENTO)                      # desce devagar até a peça
apertar()                             # pega e fica apertando...
subir(8, RAPIDO)                      # levanta a peça
andar(40)                             # ...enquanto leva a peça
abrir(1)                              # solta (encerra o aperto)
```

## Hub

| Comando | O que faz |
|---|---|
| `esperar(ms)` | Pausa que continua respondendo ao abortar. |
| `esperar_botao()` | Espera ◀ ou ▶ (o central aborta). |
| `bipe(freq=600, ms=100)` · `mostrar(valor)` · `luz(Color.GREEN)` | Som, matriz e luz. |
| `tempo_partida()` · `tempo_restante()` | Cronômetro de 120 s, que começa na 1ª saída. |
| `hub`, `db` | Objetos do Pybricks (`PrimeHub`, `DriveBase`), para casos avançados. |

### Onde vai o tempo de uma saída

Com `CRONOMETRO = True` no `config.py`, cada comando imprime no terminal do `tbr rodar` quanto levou **no robô de verdade**:

```
T    812 ms  andar(77, 450)
T    164 ms  anexo1_ir_para(0)
T   1640 ms  andar(24, 150)
```

Só o comando de fora aparece: um `ir_para()` vira uma linha só, mesmo chamando `virar_para()` e `andar()` por dentro. Os números são o que conta para otimizar, porque o `tbr simular` não sabe quanto tempo o robô passa corrigindo o rumo nem quanto um anexo demora para travar.

## Exemplo de saída

```python
# hub/saidas.py
def saida_exemplo():
    ate_linha(PRETO, QUALQUER, max_cm=30)
    alinhar_na_linha(rumo=0)
    seguir_linha(60, DIR, ESQ)
    anexo1(-90)
    voltar_base()

SAIDAS = (
    ("Exemplo", saida_exemplo),
)
```
