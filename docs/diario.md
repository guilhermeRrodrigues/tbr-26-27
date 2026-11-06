# Diário do CoopBot — TBR 2026 Middle 2

O que foi feito em cada dia, montado a partir de:

- `git log` (7 commits);
- timeline local do VS Code (`~/Library/Application Support/Code/User/History`);
- as 10 sessões do Claude Code deste projeto (`~/.claude/projects/-Users-guilherme-dev-tbr-26-27/`);
- datas dos arquivos em `fotos/` e `modelos3d/`.

Horários no fuso de Brasília (GMT-3). "Testado na mesa" significa que houve log ou vídeo do robô real. O resto só passou no `pytest`, no `tbr verificar` e no simulador.

---

## Quarta, 28/10 — nasce o sistema (20h23 – 21h45)

**Pedido:** criar, com base no Baymax e nos manuais da TBR Middle 2, um sistema para programar o robô nas missões da mesa.

- Leitura do repositório do Baymax e dos PDFs da TBR (regras: robô autônomo, partida de 120 s, mesa sem bordas, 9 missões, 500 pts, e os alunos precisam saber explicar o código).
- Definida a regra de que **as missões são da equipe**: o rascunho com passos e coordenadas foi apagado e ficaram 9 funções vazias. A regra foi para o `CLAUDE.md` e para a memória.
- **Commit `44a4ad9` (20h54), o primeiro do repositório**, com 21 arquivos e 2.370 linhas:
  - `hub/tbr.py`: a linguagem em português (andar, girar, virar_para, curva, ir_para, voltar_base, ate_linha, alinhar_na_linha, anexos com teto e detecção de travamento);
  - `hub/main.py`: menu com as saídas e as rotinas de calibração P, C, G, R e B, gravadas no storage;
  - `ferramentas/`: comando `tbr` (verificar, gravar, rodar, simular) e o dublê `tbr_falso.py`;
  - 23 testes sem hardware.
- Primeiro teste no robô: andou 50 cm certinho, mas para trás.
- **Commit `a1e9660` (21h08):** sentido das rodas corrigido e diagnóstico no boot (sentidos, calibração e settings do IMU).
- O `virar_para(90)` girava para o lado errado e travava em −216°. A causa eram as portas das rodas trocadas: direita e esquerda passaram para C e D. Também entrou uma proteção que para o robô se o erro de rumo crescer mais de 30° durante um giro.
- `girar` e `virar_para` passaram a aceitar `vel` (LENTO, NORMAL, RAPIDO ou graus/s).
- O `tbr verificar` passou a rodar todas as saídas no simulador. Assim, erros de nome como `espera(300)` e `andar_32` aparecem no PC, antes de chegar ao robô.
- Exemplo de missão escrito na `m1_gangorra()` para mostrar onde a equipe escreve o código.

## Quinta, 29/10 — saída 2 e a peça na área vermelha (15h36 – 17h19)

**Pedido:** fazer a missão 5 (colocar a peça na área vermelha do "L") dentro do código da saída 2, analisando vídeos da mesa.

- Análise dos vídeos `IMG_1557` a `IMG_1560`:
  - a linha de chegada estava uns 4 cm ao sul;
  - um `andar(20, RAPIDO)` dava tranco;
  - o robô batia no quadrado de cima do "L", girava, e o anexo da porta F chegou a se soltar (problema de montagem, que a equipe corrigiu).
- Após a montagem ser refeita, foi planejada a versão "definitiva": prender com `anexo1_ate_travar`, passar com o lado norte rente ao "L" e empurrar até o braço leste segurar a peça.
- Ajustes finos do empurrão final (6 → 13 → 16 cm), porque a peça parava ~7 cm antes da área vermelha.
- Um arquivo antigo aberto no VS Code foi salvo por cima da versão nova; a versão nova foi restaurada.
- **Novo comando `virar_ate_travar(graus)`:** gira devagar e para quando o rumo não muda 1° em 0,25 s. Foi usado no giro de −25° da saída 2.

## Sexta, 30/10 — parar no verde (16h10 – 16h12)

- Edição do `hub/main.py` no VS Code às 15h39 (timeline).
- `ate_linha` passou a aceitar `VERDE`: `ate_linha(VERDE, QUALQUER, max_cm=50)` anda até um dos sensores ver verde, com no máximo 50 cm.
- **Novo comando `odometro()`.** Com ele, o pedido escrito no comentário da linha 78 virou código: voltar de ré o que andou até o verde, mais 5 cm.

## Sábado, 31/10 — o anexo elevador impresso em 3D (13h54 – 23h59)

**Pedido:** projetar um anexo de elevador e garra para as missões 4 e 2, impresso na Bambu Lab A1 mini com PLA Lite e encaixado no CoopBot de LEGO. Na época a equipe já tinha concluído as missões 1, 5, 6 e 7 com um anexo e duas saídas.

- 9 fotos do robô copiadas para `fotos/` (13h51).
- Toda a modelagem em `modelos3d/elevador/`, em Python com build123d. As cotas ficam em `parametros.py` e as instruções em `LEIAME.md`.
- **Testes de encaixe, impressos e medidos pela equipe:**
  - o pinhão de teste em módulo 1,5 foi descartado: a cremalheira LEGO é módulo 1;
  - placa de calibração (reduzida de 1h09 para 25 min de impressão): a folga de **0,2 mm na cruz** e o **furo de 5,2 mm para o pino Technic** foram validados;
  - fuso de teste com rosca trapezoidal de 4 entradas (passo 4 mm, avanço de 16 mm por volta), reduzido para ~24 min;
  - placa de teste de mancal: ficou melhor com folga de 0,6 mm.
- Erro de conceito corrigido antes de imprimir: um sem-fim vertical não abre a garra na horizontal. A garra passou a usar um pinhão reto e uma cremalheira horizontal.
- Correção do fatiamento: o CLI do Bambu ignorava a altura de camada. Os tempos estimados caíram de 8,5 h para os reais.
- **Versão 1** em 3 pratos (~3 h, 68 g). Impressa, deu dois problemas: o mancal de cima ficou apertado, e os motores B e F ficam a 2,5 cm de altura um do outro.
- **Versão 2** em 5 pratos (~5,5 h, 182 g):
  - motores com as alturas reais (F a 40 mm, B a 65 mm);
  - curso de 196 mm, com os dedos de 1 a 20,6 cm do chão, para caber nos 30 cm de altura da largada (Vade Mecum);
  - dedos de 20 cm, com ganchos, que levam até 3 caixas;
  - o `montagem.py` confere que não há interferência em 4 posições.
- **Manual de montagem** com 12 passos ilustrados, publicado como página no claude.ai.
- Na linguagem (outra sessão, à noite):
  - **`andar_no_rumo(cm, rumo)`**: anda corrigindo o tempo todo para um rumo absoluto;
  - **`anexo1_aumentar` / `anexo2_aumentar`**: somam graus à posição real do motor.

## Domingo, 01/11

### Madrugada (00h19 – 05h43): fechamento do elevador e otimização das saídas

**Modelos 3D**
- Furos dos dedos passaram de 11 para 8 mm entre si, para casar com as vigas LEGO.
- Ganchos do dedo fixo a 8,5 cm e depois a 8,3 cm entre si, com o do meio centralizado.
- Revisão final antes de imprimir os 5 pratos. O STL da coluna foi regerado às 05h00.

**Linguagem**
- **`sacudir(ms, cm, graus)`**: vai e vem e vira um pouco para os lados, sem sair do lugar.
- Anexos com `esperar=False`, para rodarem enquanto o robô anda.

**Otimização** (pedido: "otimizar meus códigos no missoes.py")
- **Commit `ca89b1d` (03h00):** estado das missões M1–M4 da equipe antes da otimização.
- **Commit `3e25b08` (03h18), testado na mesa:**
  - aceleração da reta de 600 para 800 e do giro de 720 para 1000;
  - curvas no lugar de "reta + giro + reta", RAPIDO e anexos em paralelo;
  - `CRONOMETRO`, que imprime o tempo real de cada comando;
  - no simulador, M1–M4 caíram de 76,5 s para 69,0 s.

**Depuração da saída 2** (vídeos `IMG_1662`, `IMG_1674` e `IMG_1676` e os logs do cronômetro)
- A alavanca falhava porque o `andar_no_rumo(73)` deixava a saída 4 cm mais a oeste.
- O braço "girava para o lado errado" depois da 1ª vez porque a engrenagem pulava dente e o zero se perdia.
  - Novo `anexo1_recolher` / `anexo2_recolher`, que levam o braço ao batente e zeram ali.
  - Nova rotina **A** no menu, para medir o braço.
- O pavimento caía por causa do giro logo após a ré do carrinho, encostado no canto.
- Nova vigia de progresso: retas e curvas abortam quando o robô anda sem sair do lugar.
- **Commit `fc5685b` (05h13), testado na mesa:** saída 2 sem derrubar o pavimento e com volta pelo caminho da ida.
- **Commit `0173bf3` (05h29):**
  - descidas do anexo com mais força (40 → 50 e 50 → 60);
  - volta da M1 em diagonal, de ré.
- Até 05h43:
  - a garra passou a voltar ao 0 depois da caixa;
  - empurrão do carrinho 38 cm;
  - volta da M2 com curvas emendadas.
  - Essas mudanças entraram no commit da noite.

### Tarde e noite (17h08 – 22h39): comandos do elevador e saída 5

**Anexo montado no robô.** Comandos em centímetros:
- **`subir`, `descer`, `elevador_ir_para`** para o elevador;
- **`abrir`, `fechar`, `garra_ir_para`** para a garra;
- todos com `forca`, porque no primeiro teste "faltou força pra tudo";
- **`apertar()`**: a garra fica apertando com pouca força até outro comando de garra;
- **`andar_ate_travar(max_cm)`**: anda até encostar, com limite em cm, e diz no log se encostou ou chegou ao limite.

**Saída que funcionou na mesa (19h08).** O `andar_ate_travar(35)` não encostava. O limite subiu para 45 cm.

**Commit `cfcccb7` (19h18):** elevador e garra em cm, `apertar()`, `andar_ate_travar`, `curva(parar=False)`, ajustes da M2 e a M5 da equipe.

**Depois do commit (não commitado ainda):**
- Otimizações dessa saída: `andar(..., RAPIDO, parar=False)` emendado num `andar_ate_travar`, garra fechando enquanto anda e RAPIDO. No log, caiu de ~13,4 s para 11,7 s.
- Descoberta pelo `DIAG_GIRO`: o `db.turn` dava o giro por concluído com ~15° faltando, depois de ~1,4 s.
  - Novo **giro grosso por velocidade** fechado no giroscópio (`GIRO_POR_VELOCIDADE`).
  - Vale para todas as saídas que giram.

**Saída 5: levar os 3 blocos da fila para a base** (fotos `IMG_1698` a `IMG_1701`, convertidas para JPEG)
- A versão escrita pelo Claude não pegava nenhum bloco. A equipe pediu para voltar ao código dela (21h04).
- Correção do creep: todo giro terminava ~1,8° curto, porque o grosso entregava a 2° e o creep só corrigia acima de 2°. Agora o creep sempre fecha até 0,8°.
- Todos os `andar()` da M5 viraram `andar_no_rumo()` (21h56).
- A equipe escreveu a M5 no VS Code entre 21h19 e 22h39, com mais de 50 salvamentos na timeline.
- A otimização da M5 (curvas de raio 6 cm em RAPIDO) chegou a 29,4 s no simulador, mas na mesa as curvas saíam do arco e o braço batia no bloco.
- Duas reversões. A M5 voltou ao código da equipe (34,7 s no simulador).
- Ficou registrado um ponto: se a M5 da equipe errar agora, a causa provável é a correção do giro, porque as distâncias foram medidas quando os giros paravam 1,8° antes.

## Segunda, 02/11

- Este diário.

---

## Quinta, 05/11 — saída 6 errando para os dois lados

**Log com 7 tentativas, largadas com gabarito impresso.** Só a de 93.1 s deu certo. Nas outras, o robô passou à esquerda ou à direita dos blocos.

- **Causa principal:** `LARGADA_SIGMA_MAO = 1.5` ainda assumia largada a olho. O robô "corrigia" de +0,8° a −1,1° um erro de manuseio do giroscópio, até 13 mm no alvo. A tentativa que deu certo teve −0,1°.
- **Mudança:** `LARGADA_SIGMA_MAO = 0.15`. A pior correção daquele log cairia para ~2 mm.
- **Telemetria nova:** `DIAG_POSE` (pose na linha `T`), `DIAG fim da reta` e o valor sem peso na linha `Largada`.
- **Ainda sem explicação:**
  - `andar(33.5)` de 3145 ms na 1ª tentativa;
  - `andar(18)` de 1693 ms na tentativa que deu certo;
  - giro de ida com o dobro do tempo do giro de volta;
  - falha da tentativa 2, com só 3,5 mm de desvio.
- **Situação:** passou no `pytest` e no simulador, ainda **não testado na mesa**. O critério é 10 acertos em 10.
- **Creep desligado na saída 6:** nova `usar_creep(False)` (`config.CREEP`), que vale só para a saída. No gêmeo (300 robôs), a ida fica ~26 ms mais rápida e o rumo final não muda, porque a reta corrige andando. Sem creep, giros abaixo de 8° passaram a ser feitos pelo grosso e ficam imprecisos; a saída 6 não tem nenhum.

**Garra abrindo 1 cm a mais (limite físico).**

- **Por que não aumentar o curso:** aberta, a cremalheira está no último dente, e fechada, a barra chega à zona do hub.
- **Mudança:** barra de 99 para 109 mm, e a garra passou de 3–6 cm para **4–7 cm** (`ABERTURA_GARRA`, `GARRA_ABERTA_CM`). O dedo móvel fica 1 cm mais à frente em todas as posições.
- **Impressão:** só a barra, no novo prato `elevador_p2b_barra.3mf` (11 min). O dedo móvel impresso continua igual.
- **Ferramentas:** `gerar.py` e os `montagem.py` do elevador e do Maker passaram a funcionar com o build123d 0.13.
- **Situação:** `montagem.py`, `pytest` e `tbr verificar` passaram, ainda **não testado na mesa**. Conferir as distâncias da M6 e da M7, o que o `apertar()` segura e se a garra aberta cabe na base.

**Todas as retas das missões com `andar_no_rumo`.**

- **Mudança:** nenhum `andar()` sobrou em `hub/missoes.py`. Como o `andar()` já andava no rumo desejado (`ANDAR_NO_RUMO`), o ângulo só ficou explícito. Os valores vieram do rumo que cada reta usa no `tbr.py` real, medido no gêmeo.
- **Exceção:** 3 retas usam `rumo()`, porque o ângulo só existe na hora: depois de `virar_ate_travar(-35)` na M2 e depois do `voltar_base(de_re=True)` na M1 e na M7.
- **Bug corrigido na M2:** `andar_no_rumo(32, RAPIDO, -21)` estava com os argumentos trocados. O robô virava para o rumo 450 (= 90, sul) e andava a 21 mm/s. Agora é `andar_no_rumo(32, -21, RAPIDO)`.
- **Situação:** nas 53 retas, distância, velocidade e emenda são as mesmas, e o rumo muda no máximo 0,02° no gêmeo. `pytest` e `tbr verificar` passaram, ainda **não testado na mesa**.

**Chão plano: a M2 não concluiu (primeiro log fora da garagem).** A suspeita era o desnível. Só a M2 foi analisada; as outras saídas ainda não têm log neste chão.

- **Causa certa:** `andar_no_rumo(24, 358,5, LENTO)`. A vírgula virou `vel=5` e `parar=150`, a vigia abortou e o empurrão de 24 cm não aconteceu: POS 127,2 contra 150,8 esperado. O gêmeo repete o aviso no mesmo comando e, com `358.5`, dá POS (150,1; -11,9).
- **Provável cascata:** o carrinho ficou 24 cm antes, a alavanca travou o `virar_ate_travar(90)` em 31° e vieram 5 avisos de "sem progresso".
- **Hipótese, não confirmada:** a curva emendada perdeu o `_creep()` em 05/11, no mesmo período da troca de chão. Na garagem a POS foi x=155,2, ~5 cm além da conta. No gêmeo, 250 ms a mais dão x=156,9. A M2 e a M4 têm esse padrão. Para testar: nova chave `EMENDA_SEM_AJUSTE`.
- **Efeito medido do chão (uma corrida):** em RAPIDO o robô puxa ~0,8° para a esquerda (5 a 10 mm por trecho), e em NORMAL e LENTO fica em 1 mm ou menos. Sem pose no log da garagem, não dá para saber se já existia lá. O ajuste fino ficou mais lento (mediana de 92 para 574 ms). A velocidade das retas não mudou.
- **Sem explicação:** a M5 ganhou +8 e +4 cm entre 18h08 e a noite, com a equipe informando que só o chão mudou.
- **Mudanças:**
  - `358,5` → `358.5`, a única edição na missão;
  - o `tbr verificar` recusa `parar` que não seja True/False e `vel` negativa ou abaixo de 40 mm/s. É a 2ª vez no dia que isso aparece, e o `hub/tbr.py` continua aceitando;
  - `EMENDA_SEM_AJUSTE` em `hub/config.py`;
  - linha `DIAG fino pulso` no `_fino`, sob `DIAG_GIRO`.
- **Situação:** **testado na mesa** na mesma noite (`m2_a.txt`). Com a chave em `True`, a M2 foi até o fim e a equipe confirmou que funcionou, com POS (152,1; -8,8). A hipótese da curva não foi medida, porque não foi preciso desligar a chave. Na 2ª corrida do mesmo log, a largada avisou -8,2° e a reta parou em "sem progresso" logo no início; a equipe abortou, e a causa não foi vista. As outras saídas seguem sem log neste chão.
- **Atrito, visto pela telemetria:** o 1º pulso do ajuste fino leva de 300 a 960 ms, e dois pulsos de ~540 ms não moveram o robô (guinada 0). O ajuste consome ~9 s dos 39,5 s da M2: custa tempo, não precisão.

---

## O que está sem commit (02/11)

| Arquivo | Mudança |
|---|---|
| `hub/tbr.py` | `_giro_por_velocidade`, creep que sempre fecha após o grosso, `DIAG giro`, `andar_ate_travar` emendável |
| `hub/config.py` | `GIRO_POR_VELOCIDADE`, `GIRO_GROSSO_SAI`, `DIAG_GIRO` |
| `hub/missoes.py` | M5 da equipe com `andar_no_rumo` |
| `fotos/`, `modelos3d/`, `result.json` | fora do repositório de propósito (o `modelos3d/` tem 81 MB) |

## Linha do tempo dos commits

| Data | Hora | Commit | Resumo |
|---|---|---|---|
| 28/10 | 20h54 | `44a4ad9` | Linguagem, menu, calibração e ferramentas |
| 28/10 | 21h08 | `a1e9660` | Sentido das rodas e diagnóstico no boot |
| 01/11 | 03h00 | `ca89b1d` | M1–M4 da equipe, `andar_no_rumo`, `sacudir`, anexos concorrentes |
| 01/11 | 03h18 | `3e25b08` | Aceleração maior, curvas, RAPIDO, cronômetro |
| 01/11 | 05h13 | `fc5685b` | Saída 2 sem derrubar o pavimento, `recolher`, vigia de progresso |
| 01/11 | 05h29 | `0173bf3` | Anexo com mais força, volta da M1 em diagonal |
| 01/11 | 19h18 | `cfcccb7` | Elevador e garra em cm, `apertar()`, `andar_ate_travar`, M5 |

Entre 29/10 e 31/10 não houve commit. O que foi feito nesses dias (`virar_ate_travar`, `VERDE`, `odometro`, `andar_no_rumo`, `anexoN_aumentar`) entrou no `ca89b1d`.
