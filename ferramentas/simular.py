"""Roda as saídas de hub/saidas.py no PC, com o tbr falso.

Mostra cada passo com a posição estimada e o tempo de cada saída contra os
120 s da partida. Não substitui a mesa: serve para pegar erro de nome, de
digitação ou de lógica e ter uma noção de tempo.
"""

import importlib
import sys

from ferramentas import HUB
from ferramentas import tbr_falso
from ferramentas.hubconfig import constantes

# Tempo estimado na base entre duas saídas (trocar anexo, reposicionar), em s.
TROCA_NA_BASE_S = 5.0


def carregar_saidas():
    """Importa hub/saidas.py com o tbr falso no lugar do real."""
    sys.modules["tbr"] = tbr_falso
    caminho = str(HUB)
    if caminho not in sys.path:
        sys.path.insert(0, caminho)
    for nome in ("missoes", "saidas"):
        if nome in sys.modules:
            importlib.reload(sys.modules[nome])
    import saidas
    return saidas.SAIDAS


def simular_saida(nome, funcao):
    """Executa uma saída. → (tempo_s, passos, erro ou None)."""
    tbr_falso.reiniciar()
    try:
        funcao()
        erro = None
    except Exception as e:          # o objetivo é justamente mostrar o erro
        erro = "%s: %s" % (type(e).__name__, e)
    return tbr_falso.tempo(), list(tbr_falso.passos), erro


def main(indices=None, detalhado=True):
    """Simula todas as saídas (ou só as de `indices`, contando de 1). → código de saída."""
    saidas = carregar_saidas()
    partida_s = constantes()["PARTIDA_S"]
    total = 0.0
    falhou = False
    escolhidas = [i for i in range(1, len(saidas) + 1) if not indices or i in indices]
    for i in escolhidas:
        nome, funcao = saidas[i - 1]
        t, passos, erro = simular_saida(nome, funcao)
        print("\n=== Saída %d — %s ===" % (i, nome))
        if detalhado:
            if not passos:
                print("   (vazia)")
            for tp, x, y, r, desc in passos:
                print("   %6.1f s  x=%6.1f y=%6.1f rumo=%6.1f  %s" % (tp, x, y, r, desc))
        if erro:
            falhou = True
            print("   ERRO: %s" % erro)
        print("   tempo estimado: %.1f s" % t)
        total += t
    if len(escolhidas) > 1:
        trocas = TROCA_NA_BASE_S * (len(escolhidas) - 1)
        print("\nSoma das saídas: %.1f s + trocas na base ~%.0f s = %.1f s (partida: %d s)"
              % (total, trocas, total + trocas, partida_s))
        if total + trocas > partida_s:
            print("AVISO: passa dos %d s." % partida_s)
    return 1 if falhou else 0
