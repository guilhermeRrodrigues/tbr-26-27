"""O simulador roda as saídas e a geometria do tbr falso está certa."""

import pytest

from ferramentas import simular
from ferramentas import tbr_falso as t


@pytest.fixture(autouse=True)
def _limpo():
    t.reiniciar()


def teste_todas_as_saidas_rodam():
    for nome, funcao in simular.carregar_saidas():
        _, _, erro = simular.simular_saida(nome, funcao)
        assert erro is None, "%s: %s" % (nome, erro)


def teste_andar_para_leste():
    t.andar(30)
    x, y, r = t.posicao()
    assert (round(x, 6), round(y, 6), r) == (30, 0, 0)


def teste_rumo_90_e_sul():
    t.girar(90)
    t.andar(10)
    x, y, _ = t.posicao()
    assert abs(x) < 1e-9 and y == pytest.approx(-10)


def teste_virar_para_pelo_caminho_curto():
    t.girar(170)
    t.virar_para(-170)
    assert t.rumo() == pytest.approx(190)      # +20 graus, não -340


def teste_curva_a_direita():
    t.curva(20, 90)
    x, y, r = t.posicao()
    assert (x, y, r) == (pytest.approx(20), pytest.approx(-20), 90)


def teste_curva_a_esquerda():
    t.curva(20, -90)
    x, y, r = t.posicao()
    assert (x, y, r) == (pytest.approx(20), pytest.approx(20), -90)


def teste_ir_para_e_voltar_base():
    t.ir_para(40, 30)
    x, y, _ = t.posicao()
    assert (x, y) == (pytest.approx(40), pytest.approx(30))
    t.voltar_base()
    x, y, _ = t.posicao()
    assert (x, y) == (pytest.approx(0, abs=1e-9), pytest.approx(0, abs=1e-9))


def teste_tempo_cresce_com_a_distancia():
    t.andar(10)
    curto = t.tempo()
    t.reiniciar()
    t.andar(100)
    assert t.tempo() > curto
