# Rampa fina do Bloco (v2), com a prateleira do motor da trava.
#
# Peça única, na ponta leste da bandeja (encosta na parede leste):
#   - placa inclinada (ANGULO_RAMPA) de 2 mm, com 3 nervuras e 2 trilhos baixos; passa
#     sobre a parede sul e termina num LÁBIO fora da bandeja, a LABIO_ALTURA do tapete;
#   - lateral LESTE em treliça (triângulo): a borda da placa, uma perna que desce da
#     ponta alta até o fundo da bandeja e uma barra da perna até o ASSENTO sobre a
#     parede sul. É a face que fica na mesa de impressão;
#   - lateral OESTE só com a borda e o trilho, com mãos-francesas a 45° por baixo (na
#     impressão ela fica no alto);
#   - de lado a lado: o ASSENTO com a ABA que desce por fora da parede (a parede fica
#     presa entre os dois, e a rampa não anda em y, sem cola nem fita), a TRAVESSA da
#     ponta alta e a PERNA larga, uma parede fina a 60° com uma janela em losango;
#   - PRATELEIRA do motor na lateral oeste, paralela à placa, com 4 furos de pino: o
#     motor médio fica deitado sobre ela (comprido para o oeste), com o eixo ao longo
#     da descida e o disco virado para baixo da rampa. A trava (viga LEGO 7M pinada no
#     disco) cruza o canal na frente do Bloco e abre girando para CIMA, como cancela.
#
# Referencial: o da bandeja (parametros.py). "s" é a distância ao longo da
# superfície, medida da ponta do lábio, subindo; "n" é a altura na normal da placa.
# local(): constrói em (x, s, n) e leva para a bandeja.
# Impressão: DEITADA sobre a lateral leste (a treliça inteira na mesa, ~75 mm de
# altura). Tudo o que não está na mesa é parede em pé ou rampa a 45°, sem suporte; as
# linhas de camada da placa correm ao longo da descida. (Em pé, com o lábio na mesa,
# a base era uma tira de 2 mm com 103 mm de altura: na A1 mini, que move a mesa, a
# peça solta.)

import math

import parametros as p
from geometria import (caixa, cilindro, cilindro_y, exportar, girar, mover, no_chao, prisma,
                       prisma_xz, prisma_yz, tan)

A = p.ANGULO_RAMPA
TAN, COS, SIN = tan(A), math.cos(math.radians(A)), math.sin(math.radians(A))
T = p.PAREDE_ESPESSURA
E = p.RAMPA_ESPESSURA
EV = E / COS                                      # espessura da placa na vertical
Z_U_EXT = p.Z_PAREDE + p.FOLGA_SOBRE_PAREDE       # face de baixo da placa em y = −T
Y_PONTA = -T - (Z_U_EXT - p.LABIO_ALTURA) / TAN   # ponta do lábio
L = p.LATERAL_ESPESSURA
B = p.BARRA
MEIA_VIGA = p.VIGA_SECAO / 2

# Canal do Bloco (x), encostado na parede leste.
XR1 = p.X_RAMPA_LESTE
XC1 = XR1 - L
XC0 = XC1 - (p.BLOCO + 2 * p.FOLGA_BLOCO)
XR0 = XC0 - L


def z_baixo(y):
    # Face de baixo da placa.
    return Z_U_EXT + (y + T) * TAN


def z_sup(y):
    # Superfície da placa (sem as nervuras).
    return z_baixo(y) + EV


Z0 = z_sup(Y_PONTA)                               # superfície na ponta do lábio


def ponto(s, n=0.0):
    # Ponto (y, z) a s da ponta, ao longo da superfície, e n acima dela (na normal).
    return Y_PONTA + s * COS - n * SIN, Z0 + s * SIN + n * COS


def local(peca):
    # (x, y=s, z=n) → bandeja.
    return mover(girar(peca, "x", A), y=Y_PONTA, z=Z0)


# --- Motor e trava -----------------------------------------------------------------------
# Eixo do motor ao longo da descida, a H_EIXO da superfície, em X_EIXO (fora do canal,
# a oeste). O motor fica deitado: comprimento para o oeste (a ponta curta, MOTOR_FRENTE,
# para o leste), largura (24) na normal, os 23,6 do corpo ao longo da descida, acima do
# disco. S_DISCO é o plano do disco (o corpo vai de S_DISCO a S_DISCO + MOTOR_ALTURA).
H_EIXO = p.TRAVA_ACIMA + MEIA_VIGA
X_EIXO = XR0 - 0.5 - p.MOTOR_FRENTE
FOLGA_HUB_MOTOR = 2.0                             # do fundo do motor ao topo do hub
Z_TOPO_HUB = p.Z_FUNDO + p.HUB_ESPESSURA


def _cabe(s_frente):
    s_disco = s_frente - 0.5 + p.MOTOR_DISCO_SALIENCIA
    # Fundo do motor (lado de baixo, na ponta mais baixa) acima do hub.
    z_motor = ponto(s_disco, H_EIXO - p.MOTOR_LARGURA / 2)[1]
    # Trava fechada dentro da bandeja (canto mais ao sul: ponta de baixo, em cima).
    y_trava = ponto(s_disco - p.MOTOR_DISCO_SALIENCIA - p.VIGA_SECAO,
                    H_EIXO + MEIA_VIGA)[0]
    return (s_frente >= p.BLOCO_CARREGADO_S and z_motor >= Z_TOPO_HUB + FOLGA_HUB_MOTOR
            and y_trava >= p.FOLGA_BANDEJA)


S_FRENTE = next(i * 0.25 for i in range(4000) if _cabe(i * 0.25))   # frente do Bloco
S_TRAS = S_FRENTE + p.BLOCO
S_DISCO = S_FRENTE - 0.5 + p.MOTOR_DISCO_SALIENCIA
S_FIM = S_TRAS + 2.0                              # ponta alta da placa
S_TRAVA = (S_DISCO - p.MOTOR_DISCO_SALIENCIA - p.VIGA_SECAO,
           S_DISCO - p.MOTOR_DISCO_SALIENCIA)     # trava: ao longo da descida

# Furos do motor que vão na prateleira: na face de baixo (n), em x a ±8 do eixo,
# a 4 e 20 mm do fundo do motor (o fundo é a face de cima da descida).
FUROS_MOTOR = [(X_EIXO + c, S_DISCO + p.MOTOR_ALTURA - h)
               for c in p.MOTOR_FUROS_COMPRIMENTO[:2] for h in p.MOTOR_FUROS_ALTURA]
PRATELEIRA_E = p.PRATELEIRA_ESPESSURA
N_PRATELEIRA = (H_EIXO - p.MOTOR_LARGURA / 2 - 0.3 - PRATELEIRA_E,
                H_EIXO - p.MOTOR_LARGURA / 2 - 0.3)


def _perna():
    # Linha da perna: a 60°, do fundo da bandeja até dentro da placa, 3 mm antes da
    # ponta alta. Devolve o ponto de cima (dentro da placa), a direção e o pé no fundo.
    u = (math.cos(math.radians(60)), math.sin(math.radians(60)))
    q = ponto(S_FIM - 3.0, -E / 2)
    t = (q[1] - p.Z_FUNDO) / u[1]
    return q, u, (q[0] - t * u[0], p.Z_FUNDO)


def _faixa(q, u, meia, z_pe):
    # Polígono (y, z) de uma faixa de meia-largura `meia` ao longo da linha (q, u), do
    # ponto q até o plano z = z_pe (pé horizontal).
    w = (-u[1], u[0])
    r = []
    for lado in (1, -1):
        a = (q[0] + lado * meia * w[0], q[1] + lado * meia * w[1])
        t = (a[1] - z_pe) / u[1]
        r.append((a, (a[0] - t * u[0], z_pe)))
    (a1, p1), (a2, p2) = r
    return [p1, a1, a2, p2]


def _laterais():
    # Lateral leste (treliça, na mesa de impressão), borda oeste e as peças de lado a
    # lado (assento com aba, travessa da ponta alta e perna larga).
    zp = p.Z_PAREDE
    yi = 0.5                                      # folga da face interna da parede sul
    ye = -T - 0.5                                 # face interna da aba
    nb = -E - B
    H = p.TRILHO_ALTURA
    # Borda: faixa de B abaixo da placa e o trilho. A faixa só desce abaixo da placa ao
    # norte da parede sul (no lábio, a lateral é só o trilho: nada abaixo de
    # LABIO_ALTURA fora da bandeja).
    s_ini = (yi - Y_PONTA - E * SIN) / COS
    borda = [ponto(0, -E), ponto(s_ini, -E), ponto(s_ini, nb), ponto(S_FIM, nb),
             ponto(S_FIM, H), ponto(0, H)]
    r = prisma_yz(borda, XC1, XR1)
    # Oeste: trilho e faixa com mãos-francesas a 45° para o leste (para baixo, na
    # impressão). A do trilho entra H no canal rente à placa; o Bloco fica acima das
    # nervuras e tem o chanfro de baixo, então passa (montagem.py confere).
    trilho = [(XR0, -E), (XR0, H), (XC0, H), (XC0 + H, 0.0), (XC0 + H, -E)]
    faixa = [(XR0, -E + 0.01), (XR0, nb), (XC0, nb), (XC0 + B, -E + 0.01)]
    r = r.fuse(local(prisma_xz(trilho, 0.0, S_FIM)))
    r = r.fuse(local(prisma_xz(faixa, s_ini, S_FIM)))
    # Assento sobre a parede e aba por fora, de lado a lado.
    assento = [(yi, zp + p.ASSENTO_FOLGA), (ye, zp + p.ASSENTO_FOLGA),
               (ye, zp - p.GANCHO_DESCIDA), (ye - p.GANCHO_ESPESSURA, zp - p.GANCHO_DESCIDA),
               (ye - p.GANCHO_ESPESSURA, z_baixo(ye - p.GANCHO_ESPESSURA) + 1.5),
               (yi + B, z_baixo(yi + B) + 1.5), (yi + B, zp + p.ASSENTO_FOLGA - B)]
    r = r.fuse(prisma_yz(assento, XR0, XR1))
    # Travessa da ponta alta, de lado a lado, sob a placa.
    r = r.fuse(local(caixa(XR0, XR1, S_FIM - p.TRAVESSA, S_FIM, nb, -E + 0.01)))
    # Perna: larga (B) na lateral leste; de lado a lado, uma parede fina com janela.
    q, u, pe = _perna()
    zf = p.Z_FUNDO
    r = r.fuse(prisma_yz(_faixa(q, u, 0.8 * B, zf), XC1, XR1))
    parede = prisma_yz(_faixa(q, u, p.PERNA_PAREDE / 2, zf), XR0, XR1)
    comp = math.hypot(q[0] - pe[0], q[1] - pe[1])
    m0, m1 = 4.0, 8.0                             # margens no pé e em cima
    dx = (XC1 - 3.0) - (XR0 + 3.0)
    dt = min(dx, comp - m0 - m1)                  # dt ≤ dx: lados a 45° ou mais em pé
    xc, tc = (XR0 + 3.0 + XC1 - 3.0) / 2, m0 + (comp - m0 - m1) / 2
    losango = prisma([(xc - dx / 2, tc), (xc, tc - dt / 2), (xc + dx / 2, tc), (xc, tc + dt / 2)],
                     -5, 5)
    parede = parede.cut(mover(girar(losango, "x", 60), y=pe[0], z=pe[1]))
    r = r.fuse(parede)
    # Barra do pé da perna até o assento (lateral leste).
    y_pe = pe[0]
    ya, za = yi + B / 2, zp + p.ASSENTO_FOLGA - B / 2
    d = math.hypot(y_pe - ya, zf + B / 2 - za)
    ny, nz = -(zf + B / 2 - za) / d * B / 2, (y_pe - ya) / d * B / 2
    barra = [(ya - ny, za - nz), (y_pe - ny, zf + B / 2 - nz), (y_pe + ny, zf + B / 2 + nz),
             (ya + ny, za + nz)]
    r = r.fuse(prisma_yz(barra, XC1, XR1))
    return r, y_pe


def _placa():
    # Placa com JANELAS entre as nervuras do meio (a borda da frente e a de trás do
    # Bloco correm apoiadas nas nervuras; as bordas laterais, nas faixas de fora, que
    # ficam cheias). Na impressão deitada o oeste fica em cima: cada janela é estreita
    # ao longo da descida e tem o topo (lado oeste) em ponta a 45°, sem ponte.
    # Nervuras com o lado de baixo da impressão (leste) a 45°.
    placa = caixa(XC0 - 0.01, XC1 + 0.01, 0.0, S_FIM, -E, 0.0)
    passo = (XC1 - XC0) / (p.NERVURAS + 1)
    h, w = p.NERVURA_ALTURA, p.NERVURA_LARGURA / 2
    xs = [XC0 + passo * (i + 1) for i in range(p.NERVURAS)]
    jl, jp = p.JANELA_LARGURA, p.JANELA_PASSO
    for xa, xb in zip(xs, xs[1:]):
        x0, x1 = xa + w + p.JANELA_MARGEM, xb - w - p.JANELA_MARGEM
        s = p.JANELA_PONTAS
        while s + jl <= S_FIM - p.JANELA_PONTAS:
            casa = [(x1, s), (x1, s + jl), (x0 + jl / 2, s + jl), (x0, s + jl / 2),
                    (x0 + jl / 2, s)]
            placa = placa.cut(prisma(casa, -E - 1, 1))
            s += jp
    for x in xs:
        perfil = [(x - w, -0.01), (x + w, -0.01), (x + w - h, h), (x - w, h)]
        placa = placa.fuse(prisma_xz(perfil, 0.0, S_FIM))
    return local(placa)


def _prateleira():
    # Sob o motor, paralela à placa da rampa, presa na borda oeste: 2 barras em x (uma
    # por fileira de furos) ligadas na ponta oeste, e uma mão-francesa. Na impressão
    # deitada, ela é uma parede em pé no alto da peça, com os furos deitados.
    x0 = X_EIXO - p.MOTOR_LARGURA / 2 - 1.0
    x1 = XR0 + 0.5
    n0, n1 = N_PRATELEIRA
    xs = sorted({x for x, _ in FUROS_MOTOR})
    ss = sorted({s for _, s in FUROS_MOTOR})
    m = p.PINO_FURO / 2 + 1.6
    corpo = None
    for s in ss:
        barra = caixa(x0, x1, s - m, s + m, n0, n1)
        corpo = barra if corpo is None else corpo.fuse(barra)
    corpo = corpo.fuse(caixa(x0, xs[0] + m, ss[0], ss[-1], n0, n1))
    w = x1 - x0
    s0 = ss[0] - m
    corpo = corpo.fuse(prisma([(x1, s0 + 0.01), (x0, s0 + 0.01), (x1, s0 - w)],
                              n0, n0 + p.MAO_ESPESSURA))
    for x, s in FUROS_MOTOR:
        corpo = corpo.cut(cilindro(p.PINO_FURO / 2, n0 - 1, n1 + 1, x, s))
    return corpo


def peca():
    lat, _ = _laterais()
    r = lat.fuse(_placa())
    return r.fuse(local(_prateleira()))


def impressao():
    # Deitada sobre a lateral leste: +90° em torno de y leva o leste (x máximo) para a
    # mesa.
    return no_chao(girar(peca(), "y", 90.0))


def motor_local():
    # Corpo e disco do motor, em (x, s, n).
    corpo = caixa(X_EIXO - p.MOTOR_TRAS, X_EIXO + p.MOTOR_FRENTE, S_DISCO,
                  S_DISCO + p.MOTOR_ALTURA, H_EIXO - p.MOTOR_LARGURA / 2,
                  H_EIXO + p.MOTOR_LARGURA / 2)
    disco = cilindro_y(p.MOTOR_DISCO_DIAM / 2, S_DISCO - p.MOTOR_DISCO_SALIENCIA, S_DISCO,
                       X_EIXO, H_EIXO)
    return corpo.fuse(disco)


def trava_local(graus=0.0):
    # Viga 7M pinada no disco (furos 1 e 3 nos furos do disco a ±8 do eixo, o furo 2 no
    # eixo). Fechada (0°): aponta para o leste, cruzando o canal. Abre girando para cima.
    n = p.TRAVA_FUROS
    viga = caixa(X_EIXO - p.PASSO_LEGO - MEIA_VIGA, X_EIXO + (n - 2) * p.PASSO_LEGO + MEIA_VIGA,
                 S_TRAVA[0], S_TRAVA[1], H_EIXO - MEIA_VIGA, H_EIXO + MEIA_VIGA)
    viga = mover(viga, x=-X_EIXO, z=-H_EIXO)
    viga = girar(viga, "y", -graus)               # leste → para cima (+n)
    return mover(viga, x=X_EIXO, z=H_EIXO)


if __name__ == "__main__":
    r = peca()
    bb = r.bounding_box()
    print("rampa: %.1f cm³, x %.1f–%.1f, y %.1f–%.1f, z %.1f–%.1f, válida=%s"
          % (r.volume / 1000, bb.min.X, bb.max.X, bb.min.Y, bb.max.Y, bb.min.Z, bb.max.Z,
             r.is_valid()))
    print("lábio: y %.1f, ponta a %.1f do tapete; Bloco de s %.1f a %.1f; disco em s %.1f"
          % (Y_PONTA, z_baixo(Y_PONTA), S_FRENTE, S_TRAS, S_DISCO))
    print("eixo do motor: x %.1f, n %.1f; furos da prateleira:" % (X_EIXO, H_EIXO), FUROS_MOTOR)
    print("gravado:", exportar(r, "rampa"))
