"""Executa o hub/ REAL no PC com o Pybricks falso preso a um Mundo.

    robo = novo_robo(Parametros().sortear(rng), semente=1)
    robo.tbr.zerar_rumo()
    robo.tbr.girar(90)
    robo.mundo.theta        # rumo verdadeiro

Os módulos falsos só ficam em sys.modules enquanto os arquivos do hub
executam; depois tudo volta como estava (o `pybricks` da .venv nunca é
importado, e o `tbr` falso do simular.py não é afetado). Cada robô tem as suas
próprias cópias de config, calibracao e tbr: dá para ter vários ao mesmo tempo.
"""

import sys
import types

from ferramentas import HUB
from . import pybricks_falso
from .mundo import Mundo, Parametros

_CODIGO = {}


def _compilar(nome):
    if nome not in _CODIGO:
        caminho = HUB / (nome + ".py")
        _CODIGO[nome] = compile(caminho.read_text(encoding="utf-8"), str(caminho), "exec")
    return _CODIGO[nome]


def _executar(nome, extras=None):
    mod = types.ModuleType(nome)
    mod.__file__ = str(HUB / (nome + ".py"))
    if extras:
        mod.__dict__.update(extras)
    exec(_compilar(nome), mod.__dict__)
    return mod


class Robo:
    def __init__(self, mundo, config, tbr, modulos):
        self.mundo = mundo
        self.config = config
        self.tbr = tbr
        self._modulos = modulos

    def carregar(self, nome):
        """Executa outro arquivo do hub (ex.: rotinas_cal) contra este robô."""
        salvo = _instalar(self._modulos)
        try:
            return _executar(nome, {"print": self.mundo.print})
        finally:
            _restaurar(salvo)


def _instalar(modulos):
    salvo = {k: sys.modules.get(k) for k in modulos}
    sys.modules.update(modulos)
    return salvo


def _restaurar(salvo):
    for k, v in salvo.items():
        if v is None:
            sys.modules.pop(k, None)
        else:
            sys.modules[k] = v


def novo_robo(p=None, semente=None, config=None, mundo=None):
    """Um robô novo, já ligado (boot do tbr.py executado).

    config: dict de constantes de hub/config.py a sobrescrever.
    """
    mundo = mundo or Mundo(p or Parametros(), semente)
    falsos = pybricks_falso.fabricar(mundo)
    modulos = dict(falsos)
    salvo = _instalar(modulos)
    try:
        cfg = _executar("config")
        for k, v in (config or {}).items():
            if not hasattr(cfg, k):
                raise KeyError("config.%s não existe" % k)
            setattr(cfg, k, v)
        modulos["config"] = cfg
        sys.modules["config"] = cfg
        cal = _executar("calibracao")
        modulos["calibracao"] = cal
        sys.modules["calibracao"] = cal
        tbr = _executar("tbr", {"print": mundo.print})
        modulos["tbr"] = tbr
    finally:
        _restaurar(salvo)
    for s, lado in ((tbr._cor_dir, "dir"), (tbr._cor_esq, "esq")):
        s.lado = lado
    return Robo(mundo, cfg, tbr, modulos)
