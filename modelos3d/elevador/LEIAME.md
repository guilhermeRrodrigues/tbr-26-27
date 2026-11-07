# Elevador e garra do CoopBot: modelos 3D (versão 2)

Anexo para as missões 4 e 2: um **elevador de fuso vertical** com uma **garra de pinça de 20 cm** com 3 ganchos.
Fontes paramétricos em build123d e 3MF para a **Bambu Lab A1 mini com PLA Lite**.
Todas as cotas ficam em `parametros.py`, e nenhuma peça tem cota fixa no código.

## O que mudou da v1 para a v2

| Item | v1 | v2 |
|---|---|---|
| Altura dos motores | considerados iguais (40 mm) | **F a 40 mm, B a 65 mm** (medido no teste) |
| Curso do elevador | 80 mm | **196 mm**: o fundo dos dedos vai de 1 a 20,6 cm |
| Dedos | 44 mm, integrados ao carro e à barra | **200 mm**, peças próprias com pinos; **3 ganchos** em x = −83, 0 e +83 (8,3 cm entre eles) |
| Hastes | inteiriças (107 mm) | **2 segmentos cada**, unidos por eixo LEGO curto |
| Haste da garra | sextavada | **quadrada** (a emenda em cruz tem simetria de 90°) |
| Mancais da travessa | folga de 0,4 (apertou) | **0,6** (escolhida na placa de teste) |
| Furo quadrado do pinhão | — | folga de **0,6** e alívio nos cantos (com 0,4 o toco entrou bem apertado) |
| Abertura da garra | sem batente (desengatava) | **pino de batente** no rasgo do carro |
| Torre | 1 peça | 2 colunas + portal, com espiga e pino |

**Validado na v1:** pinhão e cremalheira engrenaram, o carro rosqueou e correu no fuso, e o pinhão deslizou na haste.

## Limite do regulamento

Na **Middle 2**, o robô na posição de início precisa caber na base, uma caixa imaginária de **30 cm de altura** (Vade Mecum TBR 2025, Normas Gerais, p. 25–26; as atualizações 2026 V4 e V5 não mudam isso). Depois da largada, o robô pode crescer.

Com o carro embaixo, o ponto mais alto da torre fica a **289 mm**, e o `montagem.py` recusa qualquer coisa acima de 292. Por isso o curso é de 196 mm: com torre fixa, a altura útil não passa de ~21 cm.

## Como funciona

- **Motor B (porta B, Anexo2) = elevador.** O fuso de 4 entradas encaixa no eixo LEGO curto do B, a 65 mm do chão. O carro sobe 16 mm por volta, num curso de 196 mm (12,25 voltas).
- **Motor F (porta F, Anexo1) = garra.** A haste quadrada encaixa no eixo curto do F, a 40 mm. O pinhão (módulo 1, 22 dentes) desliza nela junto com o carro e move a barra-cremalheira de frente para trás: curso de 40 mm, cerca de 208° de motor. A garra abre 70 mm e fecha até 30 mm, mas só com o carro subido (veja **Garra e hub**, abaixo).
- **Pinça frente-trás.** O dedo fixo, com os 3 ganchos, encosta na frente do carro. O dedo móvel fica na ponta da barra. Cada dedo tem uma faixa de aperto de 200 × 36 mm embaixo e uma haste central até o carro.
- **Batente.** Um pino impresso de Ø 3 entra pelo rasgo da chapa de cima do carro num furo da barra. Com a garra aberta, ele bate na ponta da frente do rasgo, e a barra não desengata mais do pinhão. Com a garra fechada, bate na ponta de trás, porque o túnel é aberto atrás.

### Zonas livres (conferidas pelo `montagem.py`)

- **Hub e cabos:** nada passa de y = −35 mm acima das faces dos motores. O recuo máximo do carro é −34,5.
- **Descida dos cabos:** a faixa 22 < |x| < 34 mm ao lado dos motores fica livre.
- **Motores:** o fundo do carro fica 1 mm acima da face do B.

### Garra e hub

| Carro | Abre | Fecha até |
|---|---|---|
| A 3,2 cm ou mais do fundo | 7 cm | **3 cm**: a barra passa por cima do hub e para no pino |
| Embaixo | 7 cm | **~3,8 cm**: a traseira da barra encosta no hub |

- **Cuidado:** com a garra abaixo de ~3,8 cm, não desça o carro abaixo de 3,2 cm. A barra desceria sobre o hub com a força do fuso e pode quebrar. Abra a garra antes de descer.
- **Medidas estimadas:** a frente e o topo do hub (`Y_HUB`, `Z_TOPO_HUB`) vêm das fotos de 31/10. Confirme no robô, com os cabos longe da traseira da barra.

## Pratos

| Prato | Peças | Camada | Tempo | PLA Lite |
|---|---|---|---|---|
| `teste_mancal.3mf` (P0) | placa de teste + toco quadrado | 0,28 | 19 min | 9,5 g |
| `elevador_p1_hastes.3mf` | fuso (2 segmentos), haste quadrada (2), pinhão | 0,20 | 130 min | 39,9 g |
| `elevador_p2_carro_garra.3mf` | carro, barra da garra, pino do batente | 0,20 | 40 min | 20,0 g |
| `elevador_p2b_barra.3mf` (opcional, fora do total) | só a barra da garra, para trocar sem reimprimir o carro | 0,20 | 11 min | 4,5 g |
| `elevador_p2_reservas.3mf` (opcional, fora do total) | P2 com reservas: 2 barras, 3 pinos do batente e 1 pinhão, numa placa só | 0,20 | 58 min | 26,1 g |
| `elevador_p3_dedo_fixo.3mf` | dedo fixo (deitado, na diagonal) | 0,28 | 38 min | 33,3 g |
| `elevador_p4_dedo_movel.3mf` | dedo móvel (deitado, na diagonal) | 0,28 | 35 min | 31,7 g |
| `elevador_p5_torre.3mf` | 2 colunas + portal | 0,28 | 88 min | 57,7 g |
| **Total** | 13 peças | | **≈ 5,5 h** | **≈ 182 g** |

Os perfis são Bambu Lab A1 mini 0.4 nozzle e Bambu PLA Lite @BBL A1M, sem suporte. A rosca, as engrenagens, os soquetes e o túnel usam 0,20. Os dedos e a torre usam 0,28, porque os furos verticais não dependem da camada. Os furos de pino deitados dependem, e por isso a placa de teste também sai em 0,28.

**Imprima primeiro a placa de teste (P0).** Ajuste `FOLGA_MANCAL` e `PINO_FURO_DEITADO` no `parametros.py` antes de gerar o resto.

Os 2 furos de pino da frente do carro e os 2 da sapata da barra ficam a **8 mm** um do outro, o passo LEGO. Assim, uma viga Technic também encaixa ali, e o `montagem.py` confere isso. Até 1/11/2026 a distância era de 11 mm, e só os dedos impressos encaixavam.

Até 5/11/2026 a barra era 10 mm mais curta, e a garra ia de 30 a 60 mm. Em 5/11 a barra cresceu e a garra passou a ir de 40 a 70 mm, com o mesmo curso de 30 mm. Em 6/11 o curso passou a 40 mm, para ir de 30 a 70 mm: a barra ganhou 1 dente, o furo do batente foi a 13 mm da traseira, o túnel abriu atrás e o rasgo cresceu 10 mm. Para atualizar um robô já montado, imprima o `elevador_p2_carro_garra.3mf`: carro e barra têm de ser trocados juntos. O dedo móvel e o pino continuam os mesmos. **Não misture as peças:** a barra nova no carro antigo só abriria ~6 cm, e a barra antiga no carro novo abriria demais e desengataria do pinhão.

### Peças LEGO necessárias

- **12 pinos Technic** com atrito (2 módulos):
  - 6 nas vigas;
  - 2 na emenda da torre;
  - 2 no dedo fixo;
  - 2 no dedo móvel.
- **2 eixos LEGO curtos** de 3 ou 4 módulos, para as emendas das hastes.

## Placa de teste (P0)

| Teste | O que fazer | Parâmetro |
|---|---|---|
| Mancal do fuso | Girar o munhão Ø 8 já impresso nos furos .6 / .8 / 1.0 | `FOLGA_MANCAL` |
| Mancal da garra | O mesmo com o munhão Ø 6 | `FOLGA_MANCAL` |
| Pino deitado | Enfiar meio pino Technic nos furos 5,2 e 5,4 do bloco | `PINO_FURO_DEITADO` |
| Haste quadrada | Deslizar o toco de 10 mm no furo quadrado de 10,4 | `FOLGA_QUADRADO` |

Escolha a **menor folga que gira solta**. Depois, rode `montagem.py` e `gerar.py` de novo.

**Resultado:**

- **Mancal:** a melhor folga foi **.6**.
- **Quadrado de 10,4:** entrou bem apertado. A folga subiu para 0,6, com alívio de r 0,5 nos cantos do pinhão.
- **Pino deitado:** fica em 5,2 até confirmar.

## Montagem

O colar no topo de cada haste não passa pela porca nem pelo pinhão, então o **carro entra pela ponta de baixo das hastes**.

**Na bancada**

1. **Emendas:** una os 2 segmentos do fuso com um eixo LEGO curto, e os 2 da haste quadrada com outro. Qualquer orientação da cruz serve: a rosca de 4 entradas e o quadrado se repetem a cada 90°.
2. **Pinhão no carro:** ele entra deitado pela abertura lateral esquerda.
3. **Fuso no carro:** com o carro em pé, desça o fuso pelo furo de trás com a ponta do soquete do motor primeiro. Gire para rosquear; a rosca atravessa a emenda.
4. **Haste quadrada:** do mesmo jeito, pela frente do carro e pelo pinhão.
5. **Dedo fixo:** encoste-o na face da frente do carro e prenda com 2 pinos.
6. **Garra:** a barra entra pela janela do dedo fixo e pelo túnel, com o lado dos dentes primeiro. A sapata fica na frente.
7. **Batente:** com a barra no meio do curso, ponha o pino do batente pelo rasgo de cima do carro, dentro do furo da barra.
8. **Dedo móvel:** prenda-o na sapata da barra com 2 pinos.

**No robô**

9. **Pinos:** um pino Technic em cada furo livre das vigas (y = 0, −8 e −16 mm).
10. **Motores:** o eixo LEGO curto pode sair no máximo 26 mm da face de cada motor. O fuso desce sobre o **B** (trás, mais alto) e a haste quadrada sobre o **F** (frente).
11. **Colunas:** a de furos redondos vai na viga cinza (esquerda) e a de furos oblongos na viga preta (direita).
12. **Portal:** desça-o encaixando as espigas das colunas e os munhões das hastes nos mancais (redondo no fuso, oblongo na haste quadrada). Prenda com 1 pino deitado em cada coluna, atravessando a espiga.

### Teste à mão

- Girando o fuso, o carro corre 196 mm sem prender, inclusive na emenda.
- A garra abre até o batente (70 mm) e fecha até 30 mm com o carro a 3,2 cm ou mais do fundo. Com o carro embaixo, para no hub em ~38 mm.

## Limites para o código do hub

- **Elevador (porta B):**
  - 16 mm por volta;
  - curso de 196 mm (4410° de motor);
  - embaixo, o carro fica a 1 mm da face do B;
  - em cima, a 5 mm da travessa.
- **Garra (porta F):**
  - 40 mm de curso, cerca de 208° (raio primitivo 11 mm);
  - o pino do batente segura a abertura e o fechamento, e com o carro embaixo o hub segura o fechamento antes dele;
  - mesmo assim, limite em software e use força limitada.
- **O fuso não se auto-trava:** só o `hold` do motor B segura o carro.

## Arquivos

| Arquivo | Papel |
|---|---|
| `parametros.py` | Todas as cotas: robô, regulamento, folgas validadas, rosca, engrenagens, carro, dedos, torre. |
| `rosca.py` | Geometria comum: rosca de 4 entradas, porca, cruz LEGO, quadrado, sextavado, engrenagem evolvente, cremalheira, cilindros e prismas. |
| `eixo_fuso.py`, `eixo_garra.py` | Hastes em 2 segmentos (`pecas()`, `impressao()`). |
| `pinhao.py`, `carro.py`, `garra.py`, `batente.py` | Peças do carro e da garra. |
| `dedos.py` | Dedo fixo (com ganchos) e dedo móvel. |
| `torre.py` | Colunas esquerda e direita e portal. |
| `montagem.py` | Monta tudo em 5 posições (carro embaixo, subido e em cima, com a garra aberta e fechada) e confere interferência, zonas do robô, altura na largada e os dois batentes. |
| `gerar.py` | Exporta os STL e fatia os pratos P1 a P5. Recusa peça maior que 180 mm. |
| `fatiar.py` | Chama o CLI do Bambu Studio (veja a nota abaixo). Acusa quando as peças não cabem num prato só. |
| `teste_mancal.py` | Placa de teste P0. |
| `calibracao.py`, `fuso_teste.py` | Testes de encaixe da v1, já validados. |

### Nota sobre o CLI do Bambu Studio

1. **Herança dos perfis:** o CLI não resolve a cadeia `inherits` dos perfis de sistema. O `fatiar.py` achata cada perfil num arquivo temporário, com `inherits` apontando para o preset de sistema, que é o que a checagem de compatibilidade usa.
2. **Arquivos soltos:** o fatiamento acontece numa pasta temporária, porque o CLI deixa `result.json` e `plate_N.gcode` soltos.
3. **Pratos extras:** com `--arrange`, peças que não cabem juntas vão para outro prato, e só o primeiro é fatiado. O `fatiar.py` conta os pratos e acusa.

## Gerar

Use um ambiente de modelagem fora do `.venv` do hub, que é de Pybricks:

```
python -m venv <pasta fora do projeto>/modelagem
<pasta fora do projeto>/modelagem/bin/pip install build123d
<pasta fora do projeto>/modelagem/bin/python teste_mancal.py
<pasta fora do projeto>/modelagem/bin/python montagem.py      # precisa terminar sem problemas
<pasta fora do projeto>/modelagem/bin/python gerar.py [pasta_png] [filtro_de_prato]
```

## Ainda não testado

- **Torre de 229 mm acima das vigas**, com emenda: pode balançar. Se balançar, acrescentar uma diagonal atrás, fora da zona do hub.
- **Carro de 14 mm** com dedos de 20 cm carregados: pode inclinar. Se acontecer, `CARRO_ALTURA` = 18 (o curso cai 4 mm).
- **Dedos de 3 mm** com nervura: se fletirem, `DEDO_ESPESSURA` = 4.
- **Rosca passando na emenda:** a fase é conferida pelo `montagem.py`, mas a folga do eixo LEGO pode deixar um pequeno degrau.
- **Margem de 11 mm** sobre os 30 cm: medir o robô montado com o carro embaixo.
- **Gancho** na alça de 25 mm da missão 4.
- **Curso de 40 mm:** a posição do hub é estimada. O pino de Ø 3 passou a segurar também o fechamento, e a barra encosta no hub com o carro embaixo.
- **Boca traseira do túnel:** o carro sai sem suporte, de propósito: suporte ficaria preso num túnel de 6,6 mm. Por isso a boca é impressa no ar, com uma parede de 8,6 mm sem apoio, e cede para dentro. A cauda da barra é rebaixada 0,6 mm por baixo, nos últimos 11 mm, com rampa na ponta (`CAUDA_*`). Se ainda agarrar, raspe a rebarba da boca com um estilete.
- **Barra de 109 mm:** com a garra aberta, ela fica 73 mm em balanço depois do túnel (eram 63), o que dá cerca de 56% mais flexão. Se a ponta cair, reforçar a barra.

## Fontes

- Vade Mecum TBR 2025, Normas Gerais (Robô: p. 25; Base, com 30 cm para Middle 1, Middle 2, High, Technic e University: p. 26): https://www.torneiobrasilderobotica.com.br/docs/kids1/Vade%20Mecum%20TBR%20-%20Normas%20Gerais%20e%20Regras%20Gerais%202025.pdf
- Atualizações Oficiais TBR 2026, V4 (18/08/2026) e V5 (04/09/2026): https://www.torneiobrasilderobotica.com.br/docs/att/Atualizacoes_Oficiais_TBR_2026_V4.pdf e https://www.torneiobrasilderobotica.com.br/docs/att/Atualizacoes_Oficiais_TBR_2026_V5.pdf
- Eurobricks, impressão de peças Technic (eixo impresso de 4,8 mm torce e quebra): https://www.eurobricks.com/forum/forums/topic/181777-success-3d-printing-technic-parts
- Eurobricks, padrão de pino e eixo LEGO: https://www.eurobricks.com/forum/forums/topic/75308-lego-pin-and-axle-standard
- Printables, eixo Technic de 200 mm: https://www.printables.com/model/450922-lego-technic-axle-200mm
