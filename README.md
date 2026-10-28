# CoopBot — TBR 2026 · Middle 2

Sistema para programar o robô da equipe (CoopBot, SPIKE Prime + firmware [Pybricks](https://pybricks.com)) nas missões do Desafio Prático. É composto de:

- **`hub/tbr.py`:** a linguagem, funções em português sobre o Pybricks com giroscópio, linha e anexos. Referência em [`docs/linguagem.md`](docs/linguagem.md).
- **`hub/main.py`:** o menu do hub, que escolhe a saída, roda e avança sozinho para a próxima.
- **`hub/rotinas_cal.py`:** calibração pelo menu (portas, cor, giroscópio, reta, bitola).
- **`hub/missoes.py` e `hub/saidas.py`:** onde as missões são escritas.
- **`tbr`:** linha de comando do PC para verificar, gravar, rodar e simular.

## Instalar

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -e ".[dev]"
```

O hub precisa estar com o **firmware Pybricks** (instale por [code.pybricks.com](https://code.pybricks.com)).

## Usar

```bash
.venv/bin/tbr verificar          # confere sintaxe e dialeto do código do hub
.venv/bin/tbr simular            # roda as saídas no PC: passos, posição e tempo
.venv/bin/tbr simular 2 3        # só as saídas 2 e 3
.venv/bin/tbr gravar             # grava no hub por Bluetooth (sem rodar)
.venv/bin/tbr gravar --usb       # pelo cabo
.venv/bin/tbr rodar              # grava, roda e mostra os print() do hub
.venv/bin/pytest                 # testes (sem robô)
```

## No hub

| Botão | Ação |
|---|---|
| ◀ ▶ | Escolhem o item: números são as saídas; **P C G R B** são as calibrações |
| Central | Roda o item. **Durante uma saída, aborta** e volta ao menu |
| Bluetooth | Encerra o programa |

**Luz:**
- amarela: esperando o giroscópio (deixe o robô parado);
- verde: saída;
- magenta: calibração;
- vermelha: abortou.

Um **"!"** no boot quer dizer que ainda não há calibração gravada.

## Primeira vez com o robô

O manual de montagem não informa portas nem medidas. Por isso esta ordem:

1. **P — Portas.** Cada roda gira para a frente, os anexos giram, e o robô anda 10 cm **reto**. Depois, ◀ ▶ mostram a refletância dos sensores. Se o robô girar em vez de andar reto, troque os `SENTIDO_RODA_*` em `hub/config.py`.
2. **G — Giro.** Gire o robô à mão 5 voltas exatas.
3. **C — Cor.** Comece 5 cm antes de uma linha preta e branca.
4. **B — Bitola.**
5. **R — Reta.** Anda 50 cm. Meça, informe a diferença em mm com ◀ ▶ e confirme com o central.

Os valores ficam gravados no hub e valem a partir do próximo início do programa.

## Escrever as missões

- Uma função por missão em `hub/missoes.py`.
- Agrupe as missões em saídas em `hub/saidas.py`. A lista `SAIDAS` define a ordem do menu.
- Rode `tbr simular` para pegar erros antes de ir à mesa.
