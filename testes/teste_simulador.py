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


def teste_giro_lento_demora_mais():
    t.virar_para(-180, t.RAPIDO)
    rapido = t.tempo()
    t.reiniciar()
    t.virar_para(-180, t.LENTO)
    assert t.tempo() > rapido
    assert t.rumo() == pytest.approx(180)    # -180 e 180 são o mesmo rumo


def teste_andar_no_rumo_segue_o_rumo_absoluto():
    t.girar(10)
    t.andar_no_rumo(20, 0)
    x, y, r = t.posicao()
    assert (x, y, r) == (pytest.approx(20), pytest.approx(0, abs=1e-9), 0)


def teste_andar_no_rumo_muito_torto_gasta_o_giro():
    t.andar_no_rumo(20, 0)
    reto = t.tempo()
    t.reiniciar()
    t.andar_no_rumo(20, 90)
    assert t.tempo() > reto
    x, y, _ = t.posicao()
    assert abs(x) < 1e-9 and y == pytest.approx(-20)


def teste_anexo_aumentar_soma_de_onde_esta():
    t.anexo1_ir_para(90)
    t.anexo1_aumentar(30)
    t.anexo2_aumentar(-45)
    assert (t.angulo_anexo1(), t.angulo_anexo2()) == (120, -45)


def teste_sacudir_volta_ao_ponto_e_gasta_o_tempo():
    t.andar(10)
    antes = t.tempo()
    t.sacudir(2000)
    assert t.posicao() == (pytest.approx(10), pytest.approx(0, abs=1e-9), 0)
    assert t.tempo() - antes >= 2.0


def teste_anexo_em_paralelo_nao_gasta_tempo():
    t.anexo1_ate_travar(esperar=False)
    t.anexo2(90, esperar=False)
    assert t.tempo() == 0
