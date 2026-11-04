"""python -m ferramentas.simgiro [giro|reta|largada|todos] [-n N] [-c CHAVE=VALOR ...]

-c sobrescreve constantes de hub/config.py (ex.: -c LARGADA_COMPENSADA=False).
-k passa argumentos ao cenário (ex.: -k gabarito=True -k ancorar=True).
"""

import argparse
import ast
import time

from .cenarios import CENARIOS, rodar, resumo


def _pares(lista):
    d = {}
    for item in lista or []:
        k, v = item.split("=", 1)
        try:
            d[k] = ast.literal_eval(v)
        except (ValueError, SyntaxError):
            d[k] = v
    return d


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m ferramentas.simgiro")
    ap.add_argument("cenario", nargs="?", default="todos")
    ap.add_argument("-n", type=int, default=200)
    ap.add_argument("-c", action="append", help="CONFIG=valor")
    ap.add_argument("-k", action="append", help="argumento do cenário")
    a = ap.parse_args(argv)
    config = _pares(a.c)
    kw = _pares(a.k)
    nomes = list(CENARIOS) if a.cenario == "todos" else [a.cenario]
    for nome in nomes:
        t0 = time.time()
        r = rodar(nome, a.n, config, **(kw if nome == a.cenario else {}))
        print("== %s (n=%d robôs, %.0f s) config=%s %s" % (nome, a.n, time.time() - t0, config, kw))
        print(resumo(r))


if __name__ == "__main__":
    main()
