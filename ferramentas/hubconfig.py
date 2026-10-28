"""Lê as constantes de hub/config.py SEM importá-lo.

O config.py é MicroPython (importa pybricks.parameters). Aqui ele é lido com
`ast`: só as atribuições de valor literal (números, strings) viram constantes.
Assim o simulador e os testes usam exatamente os números que vão para o hub.
"""

import ast

from ferramentas import HUB


def constantes(caminho=HUB / "config.py"):
    """{NOME: valor} das atribuições literais de config.py (inclui `A, B = 1, 2`)."""
    arvore = ast.parse(caminho.read_text(encoding="utf-8"))
    saida = {}
    for no in arvore.body:
        if not isinstance(no, ast.Assign):
            continue
        for alvo in no.targets:
            try:
                valor = ast.literal_eval(no.value)
            except ValueError:
                # Valor não literal (ex.: Port.D). Guarda a expressão como texto.
                valor = ast.unparse(no.value)
            if isinstance(alvo, ast.Name):
                saida[alvo.id] = valor
            elif isinstance(alvo, ast.Tuple) and isinstance(valor, tuple):
                for nome, v in zip(alvo.elts, valor):
                    saida[nome.id] = v
    return saida
