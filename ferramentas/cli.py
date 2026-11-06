"""`tbr` — linha de comando do CoopBot.

    tbr verificar           confere o código do hub (sintaxe + dialeto MicroPython)
    tbr gravar [--usb]      verifica e grava o menu no hub (não roda)
    tbr rodar  [--usb]      verifica, grava, roda e mostra os print() do hub
    tbr rodar  --maker      os dois hubs: maker.py no Maker e o menu no robô, console junto
    tbr gravar --so-maker   só o 2º hub (Dispositivo Maker), com hub/maker.py
    tbr simular [N ...]     roda as saídas no PC com o tbr falso

Por BLE o hub é escolhido sozinho: o Maker é o hub NOME_MAKER e o robô é
qualquer outro hub Pybricks. Para forçar um: `tbr gravar --nome "Pybricks Hub"`.
"""

import argparse
import ast
import asyncio
import os
import subprocess
import sys

from ferramentas import HUB

PROGRAMA = HUB / "main.py"
PROGRAMA_MAKER = HUB / "maker.py"     # 2º hub: Dispositivo Maker (M8)


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
    # Nome errado (ex.: `espera` em vez de `esperar`) compila, mas quebra o
    # programa no meio da saída. Rodar as saídas no simulador pega isso no PC.
    import contextlib
    import io

    from ferramentas import simular
    for i, (nome, funcao) in enumerate(simular.carregar_saidas(), 1):
        with contextlib.redirect_stdout(io.StringIO()):     # cala os print() das missões
            _, _, erro = simular.simular_saida(nome, funcao)
        if erro:
            ok = False
            print("ERRO na saída %d (%s): %s" % (i, nome, erro))
    if not ok:
        print("Dica: `tbr simular N` mostra os passos até o erro.")
        return False
    blob = asyncio.run(compile_multi_file(str(PROGRAMA), (6, 1)))
    blob_maker = asyncio.run(compile_multi_file(str(PROGRAMA_MAKER), (6, 1)))
    if not silencioso:
        print("OK: hub/ compila; programa empacotado com %d bytes (maker: %d)."
              % (len(blob), len(blob_maker)))
    return True


# --- gravar / rodar ----------------------------------------------------------------
# Nome Bluetooth do 2º hub (Dispositivo Maker). O robô é qualquer outro hub
# Pybricks: com os dois ligados, o pybricksdev sozinho pegaria o primeiro que
# aparecesse.
NOME_MAKER = "overclockm8"
ROTULO = {"robo": "robô", "maker": "maker"}


def _achar_hubs(quais, timeout=10.0):
    """{"robo"/"maker": endereço BLE} dos hubs pedidos, numa varredura só."""
    from bleak import BleakScanner
    from pybricksdev.ble.pybricks import PYBRICKS_SERVICE_UUID

    async def varrer():
        achados = {}
        pronto = asyncio.Event()

        def visto(dispositivo, adv):
            if PYBRICKS_SERVICE_UUID not in adv.service_uuids or adv.local_name is None:
                return
            papel = "maker" if adv.local_name.lower() == NOME_MAKER.lower() else "robo"
            if papel in quais and papel not in achados:
                achados[papel] = dispositivo.address
                print("Hub do %s: %s (%s)" % (ROTULO[papel], adv.local_name,
                                              dispositivo.address), flush=True)
                if all(q in achados for q in quais):
                    pronto.set()

        async with BleakScanner(detection_callback=visto):
            try:
                await asyncio.wait_for(pronto.wait(), timeout)
            except asyncio.TimeoutError:
                pass
        return achados

    achados = asyncio.run(varrer())
    for q in quais:
        if q not in achados:
            print("ERRO: hub do %s não encontrado%s. Está ligado?"
                  % (ROTULO[q], " (%s)" % NOME_MAKER if q == "maker"
                     else " (qualquer hub Pybricks que não seja o %s)" % NOME_MAKER))
    return achados if len(achados) == len(quais) else None


def _cmd(programa, rodar, nome=None, usb=False):
    cmd = [sys.executable, "-m", "pybricksdev", "run", "usb" if usb else "ble"]
    if nome:
        cmd += ["--name", nome]
    cmd += ["--start", "--wait"] if rodar else ["--no-start"]
    cmd.append(str(programa))
    print("$ " + " ".join(cmd), flush=True)
    return cmd


# Sem buffer: com `| tee arquivo` o console do hub aparece na hora, e não só
# quando o programa termina.
_ENV = dict(os.environ, PYTHONUNBUFFERED="1")


def _um_hub(args, rodar):
    """Um hub só: o robô (padrão) ou, com --so-maker, o do Maker."""
    papel = "maker" if args.so_maker else "robo"
    nome = args.nome
    if nome is None and not args.usb:
        achados = _achar_hubs([papel])
        if achados is None:
            return 1
        nome = achados[papel]
    programa = PROGRAMA_MAKER if args.so_maker else PROGRAMA
    return subprocess.call(_cmd(programa, rodar, nome, args.usb), env=_ENV)


def _repassar(papel, proc, maker_pronto):
    """Copia a saída de um pybricksdev para o terminal com o nome do hub na frente."""
    for linha in proc.stdout:
        linha = linha.rstrip()
        if not linha or "%|" in linha:          # barras de progresso do envio
            continue
        print("[%s] %s" % (ROTULO[papel], linha), flush=True)
        if papel == "maker" and "MAKER esperando" in linha:
            maker_pronto.set()
    if papel == "maker":
        maker_pronto.set()                      # terminou (ou falhou): não segura o robô


def _dois_hubs(args, rodar):
    """--maker: maker.py no hub do Maker e o menu no robô, no mesmo comando."""
    import threading

    if args.usb or args.nome:
        print("ERRO: --maker usa os dois hubs por Bluetooth; para um hub só por "
              "cabo ou por nome, use --so-maker ou tire o --maker.")
        return 1
    achados = _achar_hubs(["maker", "robo"])
    if achados is None:
        return 1
    if not rodar:
        codigo = subprocess.call(_cmd(PROGRAMA_MAKER, False, achados["maker"]), env=_ENV)
        if codigo != 0:
            return codigo
        return subprocess.call(_cmd(PROGRAMA, False, achados["robo"]), env=_ENV)

    # O Maker primeiro: o robô só começa quando o Maker já está ouvindo, senão
    # um aviso logo no início poderia passar sem ninguém ouvir.
    maker_pronto = threading.Event()
    procs, fios = {}, []
    try:
        for papel, programa in (("maker", PROGRAMA_MAKER), ("robo", PROGRAMA)):
            if papel == "robo" and not maker_pronto.wait(60):
                print("AVISO: o Maker não disse que está ouvindo em 60 s; seguindo com o robô.")
            procs[papel] = subprocess.Popen(
                _cmd(programa, True, achados[papel]), env=_ENV, text=True,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1)
            fio = threading.Thread(target=_repassar, args=(papel, procs[papel], maker_pronto),
                                   daemon=True)
            fio.start()
            fios.append(fio)
        codigos = [proc.wait() for proc in procs.values()]
    except KeyboardInterrupt:
        for proc in procs.values():
            proc.terminate()
        codigos = [proc.wait() for proc in procs.values()]
    for fio in fios:
        fio.join(1)
    return max(codigos)


def _pybricksdev(args, rodar):
    return _dois_hubs(args, rodar) if args.maker else _um_hub(args, rodar)


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
    # Linha a linha também com `| tee`: senão as mensagens do PC saem fora de
    # ordem com o console do hub.
    sys.stdout.reconfigure(line_buffering=True)
    p = argparse.ArgumentParser(prog="tbr", description="Ferramentas do CoopBot (TBR 2026)")
    sub = p.add_subparsers(dest="comando", required=True)

    sub.add_parser("verificar", help="confere o código do hub")
    for nome, ajuda in (("gravar", "grava o menu no hub"),
                        ("rodar", "grava, roda e mostra a saída do hub")):
        sp = sub.add_parser(nome, help=ajuda)
        sp.add_argument("--usb", action="store_true", help="usa o cabo USB em vez de BLE")
        sp.add_argument("--nome", help="nome Bluetooth do hub (ou porta serial com --usb)")
        sp.add_argument("--maker", action="store_true",
                        help="os DOIS hubs: maker.py no %s e o menu no robô" % NOME_MAKER)
        sp.add_argument("--so-maker", action="store_true",
                        help="só o hub do Maker (%s), com maker.py" % NOME_MAKER)
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
