"""Todo o código do hub compila com o mpy-cross e respeita o dialeto do hub."""

import ast

from ferramentas import HUB
from ferramentas.cli import _dialeto, verificar


def teste_hub_compila():
    assert verificar(silencioso=True)


def teste_dialeto_pega_fstring_e_anotacao():
    codigo = "def f(a: int) -> int:\n    return f'{a}'\nimport struct\n"
    problemas = [m for _, m in _dialeto(None, ast.parse(codigo))]
    assert any("f-string" in m for m in problemas)
    assert any("parâmetro" in m for m in problemas)
    assert any("retorno" in m for m in problemas)
    assert any("struct" in m for m in problemas)


def teste_hub_nao_tem_init():
    # hub/ não pode virar pacote: o pytest e os imports tentariam executá-lo.
    assert not (HUB / "__init__.py").exists()
