# Gabarito de largada do CoopBot (TBR 2026, Middle 2)

Uma peça em **L**, impressa em PLA, que a equipe apoia no canto da base para largar o robô sempre no mesmo rumo e no mesmo lugar. Sem ela, o rumo de largada varia 1 a 3°, e 1° são 17,5 mm por metro.

**Todas as cotas são provisórias.** A equipe só mede a mesa e o robô amanhã. Tudo vem de `parametros.py`: troque os números, rode `montagem.py` e `gerar.py`.

## O conceito

```
 frente (+y)
   ^
   |        robô (retângulo)
   |       ┌──────────────┐
   |       │              │
 ┌─┤ janela│              │
 │ │       │              │
 │L│ ■ ←── batente lateral (1 ponto)
 │ │       │              │
 │ │       └──■────────■──┘   ← 2 batentes na traseira
 │ ├─ janela                          ■ = batente (fixo ou calço)
 │ └──────────────────────────────┐
 │  alça no canto      janela  ▯  │   ← aresta de trás
 └────────────────────────────────┘
 ↑ borda interna da faixa verde (as duas arestas externas do L ficam rentes a ela)
```

- **Duas arestas de referência perpendiculares**, de 168 mm, a de trás e a da esquerda. O operador as alinha rente à borda interna da faixa verde. O comprimento é o que dá a precisão: alinhar a ~0,5 mm em 168 mm vale 0,17°.
- **Janelas de mira.** Perto de cada ponta de aresta há um entalhe aberto para fora, de 10 × 6 mm, com um sulco de índice saindo do fundo. Olhando por cima, a linha verde tem de passar reta pelo entalhe, como continuação da aresta. Há duas por aresta (a 28 mm do canto e a 10 mm da ponta), então o desalinhamento aparece nas duas pontas.
- **Batentes:** dois na traseira do robô, afastados (±45 mm do centro, provisório), e um na lateral. Dois pontos definem o ângulo, e o terceiro, a posição lateral.
- **Retirada sem tocar no robô.** A placa termina 3 mm antes da face do robô, então nenhuma parte fina fica sob ele. Só os batentes avançam esses 3 mm, com a face vertical. O gabarito sai **levantando reto** pela **alça**, uma aba em pé na diagonal do canto, longe do robô, com furo em losango.
- **Por que não uma caixa fechada ou borda alta?** A mesa não tem parede. O L inteiro apoia na área branca e só os batentes sobem.
- **Peça única, sem divisão.** Com 168 mm cabe na mesa de 180 × 180 mm da A1 mini, e o esquadro vem de uma peça só. Dividir exigiria um encaixe, que é um lugar para o ângulo variar. Imprimir na diagonal encurtaria a aresta para ~127 mm.
- **Peso e tempo.** Placa de 3 mm com nervura de 3 × 3 mm ao longo de cada aresta externa. A nervura endurece o L, e o topo dela tem bisel de 45°, então a aresta que encosta na linha fica fina.

### Largadas viradas (90°, 180°, 270°)

O robô sempre se apoia no **mesmo canto** do L, com a mesma distância às bordas (`DIST_TRAS`, `DIST_LAT`); o que muda é qual face dele encosta onde.

| Giro | Face na aresta de trás | Batentes |
|---|---|---|
| 0° | traseira | **fixos**, impressos no L |
| 180° | frente | **os mesmos fixos**, se `FRENTE_U = TRAS_U` (o `layout.py` reaproveita os que coincidem a menos de 1 mm) |
| 90° e 270° | lateral | **calços** nos 2 furos da aresta de trás (x = 80 e 160 mm, provisório) |

Os calços (3 impressos, 1 sobressalente) são blocos de 12 mm que apoiam sobre a placa e avançam 3 mm além dela. Um **pino impresso de 4,8 mm** entra num furo de 5,0 mm, e um **lábio** de 1,2 mm encosta na aresta interna da placa. Empurrando o robô de leve para o canto, o lábio fecha em cima da aresta e a posição fica definida pela aresta, não pela folga do pino. Cada furo tem **pontos gravados** (1 ponto = 90°, 3 pontos = 270°).

**Por que calços impressos, e não pinos LEGO Technic?**
- Um pino LEGO de 16 mm numa placa de 3 mm sai 12 mm para algum lado. Embaixo, ele ergue a placa. Em cima, vira um batente alto e redondo.
- A placa teria de ter uma orelha sob o robô para segurar o pino.
- O calço dá uma face plana e vertical, 3 mm além da aresta, sem nada fino sob o robô.
- O furo mantém o diâmetro dos pinos do repositório (5,0 mm), e se a equipe preferir, o mesmo furo aceita um pino LEGO de teste.

Se a posição de largada virada ficar longe do canto (muda a missão), imprima uma segunda peça com outro `DIST_TRAS`/`DIST_LAT`.

## Ritual na mesa

1. **Apoie o L no canto da base**, com as duas arestas externas rentes à borda interna da faixa verde. Confira nas 4 janelas de mira: a linha tem de ficar reta, sem degrau entre a aresta e o que se vê no entalhe.
2. **Encoste o robô** nos 3 batentes, empurrando de leve para o canto. Para largadas viradas, coloque antes os calços nos furos do giro (pontos gravados).
3. **Retire o gabarito pela alça, levantando reto** e devagar, sem arrastar. Não toque no robô.
4. **Ligue o hub e veja o desvio do giroscópio** (luz verde). Aperte o botão.
5. Guarde o gabarito **fora da base** antes de o robô se mexer: o regulamento pede que seja solto/retirado antes.

## O que medir amanhã

Tudo em `parametros.py`, marcado `# MEDIR`.

1. `BASE_X`, `BASE_Y` e `FAIXA_LARG`: tamanho **interno** da base (de borda interna a borda interna da faixa) e largura da faixa.
2. `ROBO_L`, `ROBO_W`: comprimento e largura do robô na posição de largada (altura dos batentes, anexos recolhidos).
3. `TRAS_U`, `FRENTE_U`, `LADO_U`, `LATERAL_UNICO_U`: onde cada face do robô tem material para encostar, a partir do centro da face.
4. `BATENTE_Z0`, `BATENTE_Z1`, `H_BATENTE`: alturas do tapete em que o robô tem material nesses pontos. O `montagem.py` acusa se os batentes (9 mm de topo) não alcançam.
5. `ROBO_VAO_CHAO`: vão sob a face do robô nos contatos. A placa não fica sob o robô, mas confira.
6. `DIST_TRAS`, `DIST_LAT`: distância que a equipe quer do robô às bordas internas.
7. `RODA_LARG`, `RODA_F`: se um contato lateral cai na roda.
8. O contraste da faixa verde com a cor da placa, e se o tapete é liso (o gabarito escorrega pouco ou muito).

## Precisão teórica

Valores do `montagem.py`, com `TOL_ALINHAR` = 0,5 mm por janela e `TOL_BATENTE` = 0,1 mm (fixo) ou 0,25 mm (calço):

| Fonte | Base | Pior caso | Provável |
|---|---|---|---|
| Alinhar o L na faixa (janelas) | 130 mm | 0,44° | 0,31° |
| Alinhar só pela ponta | 168 mm | 0,17° | |
| Robô nos 2 batentes fixos | 90 mm | 0,13° | 0,09° |
| Robô nos 2 calços | 80 mm | 0,36° | 0,25° |
| **Total 0° / 180°** | | **0,57°** | **0,32°** |
| **Total 90° / 270°** | | **0,80°** | **0,40°** |

Contra os 1 a 3° de hoje, isso é uma melhora de 3 a 10 vezes. Quase tudo vem de alinhar o L **de olho**: se o erro de olho cair para 0,25 mm, o total cai pela metade.

## Limitações

- Nada disso foi testado na mesa nem com o robô: a conta é de geometria. O esquadro da peça impressa depende da A1 mini (~±0,03° esperado), então **confira com um esquadro de precisão** e rejeite a peça se passar de 0,1°.
- A janela é um recurso visual: a linha verde fica fora do L e se vê por cima. A precisão real depende do olho do operador e da luz.
- Se a face de trás do robô não for plana ou tiver pouco material na altura de 0 a 9 mm, os batentes não pegam. É o item 4 acima.
- O gabarito precisa ser **objeto estratégico permitido**. Veja as perguntas ao juiz.

## Perguntas para o juiz

1. O gabarito conta como "objeto estratégico" (peça da equipe, manuseada à mão, apenas dentro da base, para preparar ou mirar o robô inativo)?
2. Ele pode ficar **rente à borda interna da faixa** e **sobre a linha**? E se a faixa for considerada parte da base, ele pode encostar nela?
3. Ele deve estar fora da base e solto **antes** de o robô se mover. O juiz quer ver a retirada?
4. Um objeto de 27 mm de altura (a alça) dentro da base, antes da largada, é problema? A caixa imaginária é de 30 cm.

## Gerar e imprimir

Use o ambiente local desta pasta (`.venv`, já no `.gitignore`):

```
python3.12 -m venv .venv && .venv/bin/pip install build123d numpy pillow    # só uma vez
.venv/bin/python montagem.py     # precisa terminar sem problemas
.venv/bin/python gerar.py [pasta_png]   # STL, conferência, fatiamento e gabarito_topo.png
.venv/bin/python desenho.py gabarito_topo.png   # só o desenho
```

- `gabarito_impressao.3mf` é um prato só, com o L e 3 calços. É PLA Lite, camada 0,24 mm, **sem suporte**, sem brim (49 min, 28,9 g com a cota provisória).
- Ele reusa `../maker/imprimivel.py` e `../elevador/fatiar.py`, que usam o Bambu Studio instalado.
- `stl/gabarito_L.stl` é só o L.
- Os furos de 5,0 mm podem precisar de 4,9 mm, como no elevador: imprima um teste de calço antes.

| Arquivo | O que é |
|---|---|
| `parametros.py` | Todas as cotas e a lista "MEDIR AMANHÃ" |
| `layout.py` | Contatos do robô por giro (puro, sem build123d) |
| `gabarito.py` | Geometria: L, calços e prato de impressão |
| `montagem.py` | Conferências e erro angular |
| `gerar.py`, `desenho.py` | STL, conferência, 3mf e PNG |
