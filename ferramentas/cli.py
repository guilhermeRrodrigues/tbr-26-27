"""`tbr` — linha de comando do CoopBot.

    tbr verificar           confere o código do hub (sintaxe + dialeto MicroPython)
    tbr gravar [--usb]      verifica e grava o menu no hub (não roda)
    tbr rodar  [--usb]      verifica, grava, roda e mostra os print() do hub
    tbr simular [N ...]     roda as saídas no PC com o tbr falso

Para escolher o hub por nome: `tbr gravar --nome "Pybricks Hub"`.
"""

import argparse
import ast
import asyncio
import subprocess
import sys

from ferramentas import HUB

PROGRAMA = HUB / "main.py"


# --- verificar ---------------------------------------------------------------------
def _dialeto(caminho, arvore):
    """Problemas de dialeto do hub que o mpy-cross deixa passar."""
    problemas = []
    for no in ast.walk(arvore):
        if isinstance(no, ast.JoinedStr):
            problemas.append((no.lineno, "f-string: use formatação com %"))
        elif isinstance(no, ast.arg) and no.annotation is not None:
            problemas.append((no.lineno, "anotação de tipo em parâmetro"))
        elif isinstance(no, (ast.FunctionDef, ast.AsyncFunctionDef)) and no.returns is not None:
            problemas.append((no.lineno, "anotação de tipo no retorno"))
        elif isinstance(no, ast.AnnAssign):
            problemas.append((no.lineno, "anotação de tipo em variável"))
        elif isinstance(no, (ast.Import, ast.ImportFrom)):
            nomes = [a.name for a in no.names] if isinstance(no, ast.Import) else [no.module]
            for nome in nomes:
                if nome in ("struct", "math", "time", "os", "sys", "asyncio"):
                    problemas.append((no.lineno, "módulo '%s' não existe no hub "
                                      "(use u%s / pybricks.tools)" % (nome, nome)))
    return problemas


def verificar(silencioso=False):
    """Compila cada arquivo do hub com mpy-cross e confere o dialeto. → True se ok."""
    from pybricksdev.compile import compile_multi_file, mpy_cross_v6

    ok = True
    for caminho in sorted(HUB.glob("*.py")):
        texto = caminho.read_text(encoding="utf-8")
        proc, _ = mpy_cross_v6.mpy_cross_compile(caminho.name, texto)
        if proc.returncode != 0:
            ok = False
            msg = proc.stderr.decode("utf-8", "replace").strip().splitlines()
            print("ERRO %s: %s" % (caminho.name, " | ".join(msg[-2:])))
            continue
        for linha, msg in _dialeto(caminho, ast.parse(texto)):
            ok = False
            print("ERRO %s:%d: %s" % (caminho.name, linha, msg))
    if not ok:
        return False
    blob = asyncio.run(compile_multi_file(str(PROGRAMA), (6, 1)))
    if not silencioso:
        print("OK: hub/ compila; programa empacotado com %d bytes." % len(blob))
    return True


# --- gravar / rodar ----------------------------------------------------------------
def _pybricksdev(args, rodar):
    conexao = "usb" if args.usb else "ble"
    cmd = [sys.executable, "-m", "pybricksdev", "run", conexao]
    if args.nome:
        cmd += ["--name", args.nome]
    cmd += ["--start", "--wait"] if rodar else ["--no-start"]
    cmd.append(str(PROGRAMA))
    print("$ " + " ".join(cmd))
    return subprocess.call(cmd)


def gravar(args):
    if not verificar():
        return 1
    codigo = _pybricksdev(args, rodar=False)
    if codigo == 0:
        print("Gravado. No hub: botão central para iniciar o programa.")
    return codigo


def rodar(args):
    if not verificar():
        return 1
    return _pybricksdev(args, rodar=True)


# --- main ----------------------------------------------------------------------------
def main(argv=None):
    p = argparse.ArgumentParser(prog="tbr", description="Ferramentas do CoopBot (TBR 2026)")
    sub = p.add_subparsers(dest="comando", required=True)

    sub.add_parser("verificar", help="confere o código do hub")
    for nome, ajuda in (("gravar", "grava o menu no hub"),
                        ("rodar", "grava, roda e mostra a saída do hub")):
        sp = sub.add_parser(nome, help=ajuda)
        sp.add_argument("--usb", action="store_true", help="usa o cabo USB em vez de BLE")
        sp.add_argument("--nome", help="nome Bluetooth do hub (ou porta serial com --usb)")
    sp = sub.add_parser("simular", help="roda as saídas no PC")
    sp.add_argument("saidas", nargs="*", type=int, help="números das saídas (padrão: todas)")
    sp.add_argument("--resumo", action="store_true", help="só os tempos, sem os passos")

    args = p.parse_args(argv)
    if args.comando == "verificar":
        return 0 if verificar() else 1
    if args.comando == "gravar":
        return gravar(args)
    if args.comando == "rodar":
        return rodar(args)
    if args.comando == "simular":
        from ferramentas import simular
        return simular.main(args.saidas, detalhado=not args.resumo)
    return 2


if __name__ == "__main__":
    sys.exit(main())
