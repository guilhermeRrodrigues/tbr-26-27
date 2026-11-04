# CoopBot — TBR 2026 Middle 2

Robô SPIKE Prime com Pybricks. Herdou o método do Baymax (`~/dev/baymax`): giroscópio com rumo absoluto, giro em duas fases (turn e creep), calibração no storage e watchdogs.

## Regras

1. **As missões são do usuário.** Não escreva resoluções das missões da mesa (passos, coordenadas, estratégia) em `hub/missoes.py` ou `hub/saidas.py`. O trabalho aqui é a linguagem, o menu, a calibração e as ferramentas.
2. **`hub/` roda no SPIKE e nunca é importado no PC.** O pacote `pybricks` está na `.venv`, então importar um arquivo de hub *executa* o programa. Não há `__init__.py` ali, e o PC lê `config.py` com `ast` (`ferramentas/hubconfig.py`). A única exceção é o gêmeo digital `ferramentas/simgiro/`, que *executa* `config.py`, `calibracao.py` e `tbr.py` com um Pybricks falso em `sys.modules` e restaura tudo no fim.
3. **Dialeto do hub:**
   - formatação com `%`, sem f-strings e sem anotações de tipo;
   - `ustruct`/`umath` em vez de `struct`/`math`.
   - O `tbr verificar` checa isso, porque o mpy-cross aceita f-string.
4. **Mudou a API de `hub/tbr.py`? Atualize `ferramentas/tbr_falso.py`**, com os mesmos nomes e parâmetros. O `testes/teste_api.py` falha se divergirem.
5. **Use `db.reset(distance=, angle=)`, nunca `hub.imu.reset_heading()`.** Com `use_gyro`, este levanta `OSError` desde o Pybricks 3.6.
6. Portas, sentidos, geometria, velocidades e tetos vivem só em `hub/config.py`.
7. Testes são `teste_*.py`, rodados com `.venv/bin/pytest`.

## Mapa

| Caminho | Papel |
|---|---|
| `hub/tbr.py` | A linguagem (movimento, linhas, posição, anexos, hub) |
| `hub/main.py` | Menu: saídas + rotinas P C G R B A D T Z |
| `hub/rotinas_cal.py` / `hub/calibracao.py` | Calibração e storage (MAGIC 0xCB, versão 1) |
| `hub/missoes.py` / `hub/saidas.py` | Código do usuário |
| `ferramentas/cli.py` | `tbr verificar / gravar / rodar / simular` |
| `ferramentas/tbr_falso.py` / `simular.py` | Dublê e simulador |
| `ferramentas/simgiro/` | Gêmeo digital: `tbr.py` real + física + Monte Carlo (`python -m ferramentas.simgiro`) |
| `docs/giroscopio.md` | Giro fino, largada, chaves de volta e protocolo de mesa |
| `modelos3d/gabarito/` | Gabarito de largada em L |

## Hardware

| Função | Porta |
|---|---|
| Roda direita | D |
| Roda esquerda | C (invertida) |
| Anexo1 | F |
| Anexo2 | B |
| Cor direita | A |
| Cor esquerda | E |

- Roda: 56 mm. Bitola: ~80 mm, estimada.
- O `heading_correction` persiste no hub via `imu.settings` e não fica no storage.
