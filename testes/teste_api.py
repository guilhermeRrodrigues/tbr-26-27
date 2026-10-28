"""O tbr falso (simulador) e o tbr real (hub) precisam ter a MESMA API.

Se alguém criar ou mudar uma função em hub/tbr.py e esquecer do dublê, o
simulador passaria a mentir. Lê os dois com `ast` (o real não pode ser
importado no PC: ele executaria o hardware).
"""

import ast
import builtins

from ferramentas import HUB, RAIZ


def _api(caminho):
    """{nome: [parâmetros]} das funções públicas + nomes públicos de nível de módulo."""
    arvore = ast.parse(caminho.read_text(encoding="utf-8"))
    funcoes, nomes = {}, set()
    for no in arvore.body:
        if isinstance(no, ast.FunctionDef) and not no.name.startswith("_"):
            funcoes[no.name] = [a.arg for a in no.args.args]
        elif isinstance(no, ast.ClassDef) and not no.name.startswith("_"):
            nomes.add(no.name)
        elif isinstance(no, ast.Assign):
            for alvo in no.targets:
                if isinstance(alvo, ast.Name) and not alvo.id.startswith("_"):
                    nomes.add(alvo.id)
    return funcoes, nomes


REAL_F, REAL_N = _api(HUB / "tbr.py")
FALSO_F, FALSO_N = _api(RAIZ / "ferramentas" / "tbr_falso.py")


def teste_mesmas_funcoes():
    assert sorted(REAL_F) == sorted(set(FALSO_F) - {"reiniciar", "tempo"})


def teste_mesmos_parametros():
    for nome, params in REAL_F.items():
        assert FALSO_F[nome] == params, "parâmetros de %s divergem" % nome


def teste_mesmas_constantes():
    # hub, db, cal, cal_gravada e as constantes da linguagem.
    faltando = (REAL_N | {"SaidaAbortada"}) - FALSO_N - {"SaidaAbortada"}
    assert not faltando, faltando


def _nomes_soltos(caminho, disponiveis):
    """Nomes lidos no arquivo que não vêm de lugar nenhum."""
    arvore = ast.parse(caminho.read_text(encoding="utf-8"))
    definidos = set(disponiveis) | set(dir(builtins))
    for no in ast.walk(arvore):
        if isinstance(no, (ast.FunctionDef, ast.ClassDef)):
            definidos.add(no.name)
            if isinstance(no, ast.FunctionDef):
                definidos.update(a.arg for a in no.args.args)
        elif isinstance(no, ast.Name) and isinstance(no.ctx, ast.Store):
            definidos.add(no.id)
        elif isinstance(no, ast.arg):
            definidos.add(no.arg)
    usados = {n.id: n.lineno for n in ast.walk(arvore)
              if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}
    return {n: l for n, l in usados.items() if n not in definidos}


# Nomes que o `import *` do tbr real exporta além das funções e constantes.
_IMPORTADOS_PELO_TBR = {"Color", "Button", "Stop", "Motor", "ColorSensor", "DriveBase",
                        "PrimeHub", "wait", "StopWatch", "sin", "cos", "atan2", "sqrt",
                        "pi", "config", "calibracao"}


def teste_missoes_so_usam_a_linguagem():
    disponiveis = set(REAL_F) | REAL_N | _IMPORTADOS_PELO_TBR
    soltos = _nomes_soltos(HUB / "missoes.py", disponiveis)
    assert not soltos, "nomes desconhecidos em missoes.py: %s" % soltos


def teste_saidas_so_usam_a_linguagem_e_missoes():
    missoes_f, _ = _api(HUB / "missoes.py")
    disponiveis = set(REAL_F) | REAL_N | _IMPORTADOS_PELO_TBR | set(missoes_f)
    soltos = _nomes_soltos(HUB / "saidas.py", disponiveis)
    assert not soltos, "nomes desconhecidos em saidas.py: %s" % soltos
