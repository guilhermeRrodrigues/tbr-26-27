"""Sanidade de hub/config.py e do formato de calibração."""

import ast
import struct

from ferramentas import HUB
from ferramentas.hubconfig import constantes

C = constantes()


def teste_portas_nao_se_repetem():
    portas = [v for k, v in C.items() if k.startswith("PORTA_")]
    assert len(portas) == 6
    assert len(set(portas)) == len(portas), portas


def teste_mapa_de_portas_do_coopbot():
    assert C["PORTA_RODA_DIR"] == "Port.D"
    assert C["PORTA_RODA_ESQ"] == "Port.C"
    assert C["PORTA_ANEXO1"] == "Port.F"
    assert C["PORTA_ANEXO2"] == "Port.B"
    assert C["PORTA_COR_DIR"] == "Port.A"
    assert C["PORTA_COR_ESQ"] == "Port.E"


def teste_geometria_dentro_das_faixas():
    assert C["RODA_MIN"] <= C["RODA_MM"] <= C["RODA_MAX"]
    assert C["BITOLA_MIN"] <= C["BITOLA_MM"] <= C["BITOLA_MAX"]


def teste_velocidades_em_ordem():
    # ~480 mm/s é o limite do motor grande com roda de 56 mm.
    assert 0 < C["VEL_LENTO"] < C["VEL_NORMAL"] < C["VEL_RAPIDO"] <= 480


def teste_tolerancias_de_giro_em_ordem():
    assert 0 < C["GIRO_TOL_SAI"] < C["GIRO_TOL_ENTRA"] < C["GIRO_GROSSO_MIN"]
    assert 0 < C["CREEP_TAXA_MIN"] < C["CREEP_TAXA_MAX"]


def teste_limiares_de_linha():
    assert 0 < C["LIMIAR_PRETO"] < 50 < C["LIMIAR_BRANCO"] < 100
    assert C["PRETO_PADRAO"] < C["BRANCO_PADRAO"]


def teste_formato_de_calibracao_casa_com_os_campos():
    cal = {}
    for no in ast.parse((HUB / "calibracao.py").read_text(encoding="utf-8")).body:
        if isinstance(no, ast.Assign) and isinstance(no.targets[0], ast.Name):
            try:
                cal[no.targets[0].id] = ast.literal_eval(no.value)
            except ValueError:
                pass
    # magic + versao + um campo por nome em CAMPOS
    campos = struct.unpack(cal["FORMATO"], bytes(struct.calcsize(cal["FORMATO"])))
    assert len(campos) == 2 + len(cal["CAMPOS"])
