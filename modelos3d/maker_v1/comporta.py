# Comporta: dente com cubo em cruz, no eixo do motor médio.
#
# O eixo é horizontal (em x) e fica debaixo da placa da rampa, dentro do túnel.
# O dente gira no plano y-z:
#   fechado (0°): na normal da placa, sai DENTE_ACIMA pela fenda e segura o Bloco;
#   aberto (GIRO_ABERTURA): gira para BAIXO da rampa e fica paralelo à placa, por
#   baixo dela. Ao abrir, a ponta se afasta do Bloco: não o empurra rampa acima.
# O Bloco faz ~0,25 N ao longo da rampa: menos de 5 mN·m no eixo (o motor segura
# com folga).
#
# Um eixo LEGO de verdade liga o disco do motor ao cubo (eixo impresso torce).
#
# Referencial local: eixo em z (cubo de z = 0 a CUBO_DENTE_COMPRIMENTO), dente para +y.
# Impressão: em pé sobre a face do cubo, furo em cruz na vertical.

import parametros as p
import rampa
from geometria import caixa, cilindro, exportar, furo_cruz, girar, mover, no_chao

R = rampa.R_DENTE
L = p.CUBO_DENTE_COMPRIMENTO


def peca():
    w = p.DENTE_LARGURA / 2
    corpo = cilindro(p.CUBO_DENTE_DIAM / 2, 0, L)
    z0 = (L - p.DENTE_ESPESSURA) / 2
    # A espessura do dente (DENTE_ESPESSURA) fica ao longo da rampa; a largura
    # (DENTE_LARGURA) ao longo do eixo. Aqui: x local = ao longo da rampa.
    dente = caixa(-p.DENTE_ESPESSURA / 2, p.DENTE_ESPESSURA / 2, 0, R, z0, z0 + 2 * w)
    corpo = corpo.fuse(dente)
    return corpo.cut(furo_cruz(-1, L + 1))


def montada(graus=0.0):
    # z local → +x da bandeja; depois o dente (+y local) vai para a normal da placa
    # (fechado) e gira 'graus' para baixo da rampa.
    c = girar(peca(), "y", 90)
    c = girar(c, "x", 90 + p.ANGULO_RAMPA + graus)
    return mover(c, rampa.X_CUBO[0], rampa.Y_EIXO, rampa.Z_EIXO)


def impressao():
    return no_chao(peca())


if __name__ == "__main__":
    c = peca()
    print("comporta: dente de %.1f mm (do eixo à ponta), %.1f cm³, válida=%s"
          % (R, c.volume / 1000, c.is_valid()))
    print("gravado:", exportar(impressao(), "comporta"))
