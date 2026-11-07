# Montagem do elevador no robô (versão 2), com checagem de interferência e folgas.
#
# Posiciona as peças no referencial do robô em 5 situações:
#   carro embaixo: garra aberta / fechada até o hub
#   carro SUBIDA_FECHAR_TUDO acima do fundo: garra fechada até o fim
#   carro em cima: garra aberta / fechada até o fim
# e verifica:
#   - interferência entre cada par de peças (volume da interseção);
#   - invasão das zonas do robô (motores, vigas, para-choque, laterais, hub,
#     faixa dos cabos, chão);
#   - altura na largada (limite de 30 cm da Middle 2, menos a margem);
#   - fundo dos dedos, abertura, batentes da barra e recuo máximo em y.
# Grava stl/montagem.stl (carro embaixo, garra aberta) só para visualizar.
#
# Uso: python montagem.py   (sai com código 1 se houver problema)

import itertools
import math
import sys

from build123d import Compound, Location

import parametros as p
import batente
import carro
import dedos
import eixo_fuso
import eixo_garra
import garra
import pinhao
import torre
from rosca import caixa, cilindro, exportar

LIMIAR = 0.5  # mm³: abaixo disto é ruído numérico (faces encostadas)


def _girado(peca, graus, x, y, z):
    return peca.moved(Location((0, 0, 0), (0, 0, 1), graus)).moved(Location((x, y, z)))


def carregar():
    s = {}
    s.update(eixo_fuso.pecas())
    s.update(eixo_garra.pecas())
    s.update(dedos.pecas())
    s.update(torre.pecas())
    s["pinhao"] = pinhao.peca()
    s["carro"] = carro.peca()
    s["garra"] = garra.peca()
    s["batente"] = batente.peca()
    return s


def posicionar(pecas, z_carro, y_barra):
    # Ângulo do pinhão (e da haste F) que casa os dentes com a barra.
    rp = p.MODULO * p.DENTES_PINHAO / 2
    graus = math.degrees(y_barra / rp)
    no_carro = Location((0, 0, z_carro))
    na_barra = Location((0, y_barra, z_carro))
    pos = {
        "fuso_baixo": pecas["fuso_baixo"].moved(Location((0, p.Y_EIXO_B, p.Z_MOTOR_B))),
        "fuso_cima": pecas["fuso_cima"].moved(Location((0, p.Y_EIXO_B, p.Z_MOTOR_B))),
        "garra_baixo": _girado(pecas["garra_baixo"], graus, 0, p.Y_EIXO_F, p.Z_MOTOR_F),
        "garra_cima": _girado(pecas["garra_cima"], graus, 0, p.Y_EIXO_F, p.Z_MOTOR_F),
        "pinhao": _girado(pecas["pinhao"], graus, 0, p.Y_EIXO_F, z_carro + garra.Z_BARRA[0]),
        "carro": pecas["carro"].moved(no_carro),
        "dedo_fixo": pecas["dedo_fixo"].moved(no_carro),
        "garra": pecas["garra"].moved(na_barra),
        "dedo_movel": pecas["dedo_movel"].moved(na_barra),
        "batente": pecas["batente"].moved(na_barra),
    }
    for nome in ("coluna_esq", "coluna_dir", "portal"):
        pos[nome] = pecas[nome]
    return pos


def zonas_do_robo():
    zx = p.X_VIGA
    return {
        "motor F": cilindro(p.RAIO_CORPO_MOTOR, 0, p.Z_MOTOR_F - 0.1, 0, p.Y_EIXO_F),
        "motor B": cilindro(p.RAIO_CORPO_MOTOR, 0, p.Z_MOTOR_B - 0.1, 0, p.Y_EIXO_B),
        "viga cinza": caixa(-zx - 4, -zx + 4, -24, 12, p.Z_VIGAS - 8, p.Z_VIGAS - 0.1),
        "viga preta": caixa(zx - 4, zx + 4, -24, 12, p.Z_VIGAS - 8, p.Z_VIGAS - 0.1),
        "para-choque": caixa(-p.X_LATERAL, p.X_LATERAL, 8, p.Y_FRENTE, 0,
                             p.FRENTE_ALTURA_CENTRO + p.FOLGA_FRENTE),
        "lateral esq": caixa(-p.LARGURA_ROBO / 2, -p.X_LATERAL, -60, p.Y_FRENTE, 0,
                             p.FRENTE_ALTURA_LATERAL),
        "lateral dir": caixa(p.X_LATERAL, p.LARGURA_ROBO / 2, -60, p.Y_FRENTE, 0,
                             p.FRENTE_ALTURA_LATERAL),
        "hub e cabos": caixa(-70, 70, -100, p.Y_HUB, p.Z_MOTOR_F, p.Z_TOPO_HUB),
        "cabos esq": caixa(-p.X_CABOS_FIM, -p.X_CABOS, p.Y_HUB, 0, p.Z_MOTOR_F, 140),
        "cabos dir": caixa(p.X_CABOS, p.X_CABOS_FIM, p.Y_HUB, 0, p.Z_MOTOR_F, 140),
        "chão": caixa(-150, 150, -150, 250, -10, 0),
    }


def _vol(a, b):
    try:
        i = a.intersect(b)
    except Exception as e:  # booleano falhou: reportar, não esconder
        return float("nan"), str(e)
    if i is None:
        return 0.0, None
    # O build123d 0.13 pode devolver uma ShapeList em vez de uma peça só.
    pedacos = i if isinstance(i, list) else [i]
    return sum(s.volume for s in pedacos), None


def _sobrepoe(a, b):
    # Descarta pares longe um do outro pela caixa envolvente (rápido).
    ba, bb = a.bounding_box(), b.bounding_box()
    return not (ba.max.X < bb.min.X or bb.max.X < ba.min.X or
                ba.max.Y < bb.min.Y or bb.max.Y < ba.min.Y or
                ba.max.Z < bb.min.Z or bb.max.Z < ba.min.Z)


def checar():
    pecas = carregar()
    zonas = zonas_do_robo()
    z_baixo = p.Z_CARRO_MIN
    z_subido = p.Z_CARRO_MIN + p.SUBIDA_FECHAR_TUDO
    z_cima = p.Z_CARRO_MIN + p.CURSO_ELEVADOR
    casos = [("embaixo, aberta", z_baixo, p.Y_BARRA_ABERTA),
             ("embaixo, fechada até o hub", z_baixo, p.Y_HUB),
             ("subido, fechada", z_subido, p.Y_BARRA_FECHADA),
             ("em cima, aberta", z_cima, p.Y_BARRA_ABERTA),
             ("em cima, fechada", z_cima, p.Y_BARRA_FECHADA)]
    problemas = []
    for nome, zc, yb in casos:
        pos = posicionar(pecas, zc, yb)
        for (na, a), (nb, b) in itertools.combinations(pos.items(), 2):
            if not _sobrepoe(a, b):
                continue
            v, erro = _vol(a, b)
            if erro or v > LIMIAR:
                problemas.append("%s: %s × %s = %s" % (nome, na, nb, erro or "%.2f mm³" % v))
        for np_, peca in pos.items():
            for nz, zona in zonas.items():
                if not _sobrepoe(peca, zona):
                    continue
                v, erro = _vol(peca, zona)
                if erro or v > LIMIAR:
                    problemas.append("%s: %s invade %s (%s)" % (nome, np_, nz, erro or "%.2f mm³" % v))
        print("checado:", nome)

    # Altura na largada (carro embaixo): limite do regulamento menos a margem.
    largada = posicionar(pecas, z_baixo, p.Y_BARRA_ABERTA)
    topo = max(s.bounding_box().max.Z for s in largada.values())
    limite = p.ALTURA_MAX_INICIO - p.MARGEM_ALTURA
    print("altura na largada: %.1f | limite %.0f (regulamento %.0f)"
          % (topo, limite, p.ALTURA_MAX_INICIO))
    if topo > limite:
        problemas.append("altura na largada %.1f passa de %.0f" % (topo, limite))

    # Batente: um pouco além do aberto, o pino tem que bater no carro.
    alem = posicionar(pecas, z_baixo, p.Y_BARRA_ABERTA + 0.3 + 0.5)
    v, _ = _vol(alem["batente"], alem["carro"])
    print("batente: abrir 0,8 mm além do aberto prende %.1f mm³ do pino no carro" % v)
    if not v > LIMIAR:
        problemas.append("batente não segura a abertura")
    # O mesmo no fechamento: o túnel é aberto atrás, e só o pino para a barra.
    alem = posicionar(pecas, z_subido, p.Y_BARRA_FECHADA - 0.5 - 0.5)
    v, _ = _vol(alem["batente"], alem["carro"])
    print("batente: fechar 1,0 mm além do fechado prende %.1f mm³ do pino no carro" % v)
    if not v > LIMIAR:
        problemas.append("batente não segura o fechamento")

    # Pares de pinos no passo LEGO (uma viga Technic tem que encaixar).
    for nome, xs in (("carro", p.PINOS_DEDO_FIXO_X), ("sapata", p.PINOS_DEDO_MOVEL_X)):
        d = xs[1] - xs[0]
        print("pinos do %s: x = %s, distância %.1f mm" % (nome, xs, d))
        if abs(d / p.PASSO_LEGO - round(d / p.PASSO_LEGO)) > 1e-6:
            problemas.append("pinos do %s a %.1f mm: fora do passo LEGO de %.0f mm"
                             % (nome, d, p.PASSO_LEGO))

    # Folgas e alturas.
    h = p.CARRO_ALTURA
    print("topo do carro em cima: %.1f | travessa: %.1f | folga %.1f"
          % (z_cima + h, p.Z_TRAVESSA, p.Z_TRAVESSA - (z_cima + h)))
    fundo = lambda zc: zc + dedos.Z_FUNDO
    print("fundo dos dedos: %.1f (embaixo) a %.1f (em cima)" % (fundo(z_baixo), fundo(z_cima)))
    print("fundo do carro embaixo: %.1f | face do motor B: %.1f" % (z_baixo, p.Z_MOTOR_B))
    fechada = posicionar(pecas, z_subido, p.Y_BARRA_FECHADA)
    recuo = min(s.bounding_box().min.Y for s in fechada.values())
    print("recuo máximo com o carro subido (y): %.1f | zona do hub começa em %.1f"
          % (recuo, p.Y_HUB))
    print("barra com o carro subido %.0f mm: fundo em z %.1f | topo do hub %.1f"
          % (p.SUBIDA_FECHAR_TUDO, z_subido + garra.Z_BARRA[0], p.Z_TOPO_HUB))
    frente_fixo = p.Y_DEDO_FIXO + p.DEDO_ESPESSURA
    abertura = lambda yb: (yb + garra.Y_DEDO_MOVEL) - frente_fixo
    print("abertura dos dedos: %.1f (aberta) / %.1f (fechada, carro embaixo) / %.1f (fechada, carro subido)"
          % (abertura(p.Y_BARRA_ABERTA), abertura(p.Y_HUB), abertura(p.Y_BARRA_FECHADA)))
    print("ganchos em x = %s, largura dos dedos %.0f" % (p.GANCHOS_X, p.DEDO_LARGURA))
    avanco = max(s.bounding_box().max.Y for s in largada.values()) - p.Y_FRENTE
    print("garra aberta avança %.1f mm além do para-choque" % avanco)

    print("gravado:", exportar(Compound(list(largada.values())), "montagem"))
    return problemas


if __name__ == "__main__":
    problemas = checar()
    if problemas:
        print("\nPROBLEMAS (%d):" % len(problemas))
        for linha in problemas:
            print(" -", linha)
        sys.exit(1)
    print("\nSem interferência nas 5 posições; altura e batentes conferidos.")
