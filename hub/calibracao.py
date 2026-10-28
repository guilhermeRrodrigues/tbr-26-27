# CoopBot — calibração gravada na memória do hub
# ==============================================
# Guarda em hub.system.storage os valores medidos pelas rotinas do menu
# (rotinas_cal.py): diâmetro da roda, bitola e preto/branco de cada sensor.
# Mesmo esquema do Baymax: byte MAGIC + versão + campos com ustruct. Se o MAGIC
# ou a versão não baterem, a calibração é ignorada e valem os padrões do config.
#
# A escala do giroscópio (heading_correction) NÃO mora aqui: o Pybricks a grava
# sozinho pelo hub.imu.settings() e ela persiste por conta própria.

import ustruct as struct

import config

STORAGE_OFFSET = 0
MAGIC = 0xCB
VERSAO = 1
# magic, versao, roda_mm(f), bitola_mm(f), preto_dir, branco_dir, preto_esq, branco_esq
FORMATO = "<BBffhhhh"

CAMPOS = ("roda", "bitola", "preto_dir", "branco_dir", "preto_esq", "branco_esq")


def padrao():
    return {
        "roda": config.RODA_MM,
        "bitola": config.BITOLA_MM,
        "preto_dir": config.PRETO_PADRAO,
        "branco_dir": config.BRANCO_PADRAO,
        "preto_esq": config.PRETO_PADRAO,
        "branco_esq": config.BRANCO_PADRAO,
    }


def _valida(cal):
    if not (config.RODA_MIN <= cal["roda"] <= config.RODA_MAX):
        return False
    if not (config.BITOLA_MIN <= cal["bitola"] <= config.BITOLA_MAX):
        return False
    # Sensor precisa de contraste mínimo entre preto e branco.
    if cal["branco_dir"] - cal["preto_dir"] < 10:
        return False
    if cal["branco_esq"] - cal["preto_esq"] < 10:
        return False
    return True


def ler(hub):
    """Calibração gravada, ou None se não houver nada válido."""
    try:
        bruto = hub.system.storage(STORAGE_OFFSET, read=struct.calcsize(FORMATO))
        v = struct.unpack(FORMATO, bruto)
    except Exception:
        return None
    if v[0] != MAGIC or v[1] != VERSAO:
        return None
    cal = {}
    for i in range(len(CAMPOS)):
        cal[CAMPOS[i]] = v[i + 2]
    if not _valida(cal):
        return None
    return cal


def carregar(hub):
    """(calibração, veio_do_storage). Nunca falha: sem storage, usa o config."""
    cal = ler(hub)
    if cal is None:
        return padrao(), False
    return cal, True


def salvar(hub, **mudancas):
    """Atualiza só os campos passados e grava. Retorna True se releu igual.

    Ex.: salvar(hub, roda=55.4) mantém bitola e sensores como estavam.
    """
    cal, _ = carregar(hub)
    for nome in mudancas:
        if nome not in CAMPOS:
            raise ValueError("campo de calibracao desconhecido: %s" % nome)
        cal[nome] = mudancas[nome]
    if not _valida(cal):
        return False
    dados = struct.pack(FORMATO, MAGIC, VERSAO, cal["roda"], cal["bitola"],
                        int(cal["preto_dir"]), int(cal["branco_dir"]),
                        int(cal["preto_esq"]), int(cal["branco_esq"]))
    hub.system.storage(STORAGE_OFFSET, write=dados)
    return hub.system.storage(STORAGE_OFFSET, read=len(dados)) == dados
