# Linguagem de missões do CoopBot

Tudo vem de `from tbr import *` (arquivo `hub/tbr.py`). Unidades: **cm**, **graus**, **ms**.

## Referencial

- **Origem:** centro do eixo das rodas na posição de partida da saída. O menu zera a posição e o rumo ao iniciar cada saída.
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
| `andar(cm, vel=NORMAL, parar=True)` | Reta segurando o rumo pelo giroscópio. Valor negativo anda de ré. `parar=False` emenda no próximo movimento sem frear. |
| `andar_no_rumo(cm, rumo, vel=NORMAL, parar=True)` | Reta no rumo **absoluto** `rumo`, corrigindo a direção o tempo todo: se sair do rumo no caminho, guina de volta andando. Se começar mais de 20° torto (`RUMO_VIRAR_ANTES`), vira no lugar antes. Negativo anda de ré, com a frente no `rumo`. |
| `girar(graus, vel=NORMAL)` | Giro no lugar, relativo ao rumo desejado. |
| `virar_para(rumo, vel=NORMAL)` | Gira até o rumo absoluto pelo caminho mais curto. |
| `virar_ate_travar(rumo, vel=LENTO, ms=250)` | Como `virar_para`, mas para se o giro travar (o rumo não muda 1° em `ms` ms). O rumo onde parou vira o rumo desejado. Devolve `True` se travou. |
| `sacudir(ms, cm=1, graus=6)` | Sacode por `ms` milissegundos: vai e volta `cm` para a frente e para trás e vira `graus` para cada lado, em torno do ponto e do rumo onde começou, e no fim volta para eles. Para assentar uma peça, soltar um anexo enroscado ou encaixar algo. `cm=0` só vira; `graus=0` só vai e volta. |
| `curva(raio_cm, graus, vel=NORMAL)` | Arco; o rumo muda `graus`. |
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
| `ate_linha(cor_alvo=PRETO, sensor=QUALQUER, vel=LENTO, max_cm=50)` | Anda até `DIR`, `ESQ` ou `QUALQUER` sensor ver `PRETO`/`BRANCO`/`VERDE`. Com `vel` negativa, procura de ré. Devolve `True` se achou. |
| `alinhar_na_linha(vel=LENTO, max_cm=30, rumo=None, fino=True)` | Cada roda para quando o seu sensor vê o preto, e o robô fica perpendicular à linha. Com `rumo=...`, **reescreve o giroscópio** com o rumo conhecido da linha, o que zera o erro acumulado. |
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
| `zerar_posicao()` / `zerar_rumo()` | Volta a posição para (0, 0) / zera o rumo e a posição. |

A posição é odometria (encoders + giroscópio): o erro cresce com a distância. Realinhe nas linhas sempre que der.

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
