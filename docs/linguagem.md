# Linguagem de missões do CoopBot

Tudo vem de `from tbr import *` (arquivo `hub/tbr.py`). Unidades: **cm**, **graus**, **ms**.

## Referencial

- **Origem:** centro do eixo das rodas na posição de partida da saída. O menu zera a posição e o rumo ao iniciar cada saída.
- **Rumo 0:** para onde o robô apontava ao sair, ou seja, leste, saindo da base. **Positivo = horário (direita)**: 90 = sul, -90 = norte, 180 = oeste.
- **x:** cresce para a frente (leste); **y** cresce para a esquerda (norte).
- **O rumo é absoluto.** `girar(90); girar(90)` deixa o robô exatamente em 180, porque o erro de um giro não passa para o próximo.

## Retorno

Os movimentos devolvem `True` (terminou) ou `False` (travou ou estourou o tempo). Ninguém é obrigado a olhar o retorno, mas dá para reagir:

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
| `girar(graus)` | Giro no lugar, relativo ao rumo desejado. |
| `virar_para(rumo)` | Gira até o rumo absoluto pelo caminho mais curto. |
| `curva(raio_cm, graus, vel=NORMAL)` | Arco; o rumo muda `graus`. |
| `ir_para(x, y, vel=NORMAL, de_re=False)` | Vira e anda até o ponto, usando a posição estimada. |
| `voltar_base(vel=RAPIDO, de_re=False)` | `ir_para(0, 0)`. |
| `parar_tudo()` | Para a tração e os anexos. |

Velocidades (mm/s, ajustáveis no `config.py`): `LENTO` 150, `NORMAL` 300, `RAPIDO` 450.

## Linhas: o realinhamento numa mesa sem bordas

| Comando | O que faz |
|---|---|
| `ate_linha(cor_alvo=PRETO, sensor=QUALQUER, vel=LENTO, max_cm=50)` | Anda até `DIR`, `ESQ` ou `QUALQUER` sensor ver `PRETO`/`BRANCO`. Com `vel` negativa, procura de ré. |
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
| `definir_posicao(x, y)` | Corrige a estimativa (ex.: depois de alinhar numa linha de posição conhecida). |
| `zerar_posicao()` / `zerar_rumo()` | Volta a posição para (0, 0) / zera o rumo e a posição. |

A posição é odometria (encoders + giroscópio): o erro cresce com a distância. Realinhe nas linhas sempre que der.

## Anexos (anexo1 = porta F, anexo2 = porta B)

| Comando | O que faz |
|---|---|
| `anexo1(graus, vel=500, esperar=True)` | Gira relativo. `esperar=False` devolve na hora, e o anexo se mexe enquanto o robô anda. |
| `anexo1_ir_para(angulo, vel=500, esperar=True)` | Vai ao ângulo absoluto (0 = início da saída). |
| `anexo1_ate_travar(sentido=HORARIO, forca=50, teto_ms=3000)` | Empurra com `forca`% até travar (garra fechando, fim de curso) e segura. |
| `esperar_anexos(teto_ms=5000)` | Espera os anexos lançados com `esperar=False`. |
| `zerar_anexos()` · `angulo_anexo1()` | O menu zera os anexos no início de cada saída. |

Todos existem também como `anexo2...`. `sentido` é `HORARIO` ou `ANTI_HORARIO`.

## Hub

| Comando | O que faz |
|---|---|
| `esperar(ms)` | Pausa que continua respondendo ao abortar. |
| `esperar_botao()` | Espera ◀ ou ▶ (o central aborta). |
| `bipe(freq=600, ms=100)` · `mostrar(valor)` · `luz(Color.GREEN)` | Som, matriz e luz. |
| `tempo_partida()` · `tempo_restante()` | Cronômetro de 120 s, que começa na 1ª saída. |
| `hub`, `db` | Objetos do Pybricks (`PrimeHub`, `DriveBase`), para casos avançados. |

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
