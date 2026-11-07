# Confere se uma peça (já na orientação de impressão) imprime sem suporte e sem soltar
# da mesa na A1 mini, que move a mesa em y (peça alta e de base estreita balança e
# solta). Lê o STL gravado (a malha que vai para o Bambu):
#   - primeira camada: área de contato com a mesa;
#   - esbeltez: altura dividida pelo lado menor da base (o retângulo que envolve a
#     primeira camada);
#   - balanço: faces viradas para baixo, fora da mesa, mais deitadas que BALANCO_MAX
#     graus da vertical (precisariam de suporte). Faixas com menos de LARGURA_MIN de
#     largura (o alto de furos deitados, os degraus rasos do logo) não contam; pontes
#     curtas dão um pouco de área, por isso o limite é em mm². Nem contam os tetos até
#     Z_RASO da mesa (rebaixos na face de baixo: o fatiador faz ponte sobre eles).
#
# Uso: python imprimivel.py stl/rampa.stl [...]

import struct
import sys

import numpy as np

BALANCO_MAX = 50.0            # graus da vertical (o Bambu imprime bem até ~50–55)
BALANCO_AREA_MAX = 60.0       # mm² de balanço tolerados (furos deitados, pontes curtas)
LARGURA_MIN = 1.0             # mm: balanço mais estreito que isto não conta
Z_RASO = 1.0                  # mm: tetos de rebaixos da face de baixo não contam
BASE_AREA_MIN = 400.0         # mm² na primeira camada
ESBELTEZ_MAX = 2.5            # altura / lado menor da base


def ler_stl(caminho):
    with open(caminho, "rb") as f:
        dados = f.read()
    n = struct.unpack("<I", dados[80:84])[0]
    if len(dados) == 84 + 50 * n:
        reg = np.frombuffer(dados, dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("a", "<u2")]),
                            count=n, offset=84)
        return reg["v"].reshape(-1, 3, 3).astype(float)
    tri, atual = [], []
    for linha in dados.decode("ascii", "replace").splitlines():
        partes = linha.split()
        if partes and partes[0] == "vertex":
            atual.append([float(c) for c in partes[1:4]])
            if len(atual) == 3:
                tri.append(atual)
                atual = []
    return np.array(tri)


def conferir(caminho):
    t = ler_stl(caminho)
    t = t - [0, 0, t[:, :, 2].min()]
    cruz = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
    area = np.linalg.norm(cruz, axis=1) / 2
    ok = area > 1e-9
    normal = np.zeros_like(cruz)
    normal[ok] = cruz[ok] / (2 * area[ok])[:, None]
    zmax = t[:, :, 2].max(axis=1)
    na_mesa = ok & (zmax < 0.05) & (normal[:, 2] < -0.99)
    base = area[na_mesa].sum()
    pts = t[na_mesa].reshape(-1, 3)
    if len(pts):
        lado = min(np.ptp(pts[:, 0]), np.ptp(pts[:, 1]))
    else:
        lado = 0.0
    altura = t[:, :, 2].max()
    limite = -np.sin(np.radians(BALANCO_MAX))
    # Largura da face vista de cima: 2 × área / maior lado (no plano xy).
    xy = t[:, :, :2]
    d1, d2 = xy[:, 1] - xy[:, 0], xy[:, 2] - xy[:, 0]
    a_xy = np.abs(d1[:, 0] * d2[:, 1] - d1[:, 1] * d2[:, 0]) / 2
    lado_max = np.max([np.linalg.norm(xy[:, i] - xy[:, (i + 1) % 3], axis=1)
                       for i in range(3)], axis=0)
    largura = 2 * a_xy / np.maximum(lado_max, 1e-9)
    balanco = (ok & ~na_mesa & (normal[:, 2] < limite) & (largura >= LARGURA_MIN)
               & (zmax > Z_RASO))
    a_bal = area[balanco].sum()
    problemas = []
    if base < BASE_AREA_MIN:
        problemas.append("primeira camada de %.0f mm² (mínimo %.0f)" % (base, BASE_AREA_MIN))
    esb = altura / lado if lado > 0 else float("inf")
    if esb > ESBELTEZ_MAX:
        problemas.append("alta demais para a base: %.0f mm de altura sobre %.0f mm (%.1f×)"
                         % (altura, lado, esb))
    if a_bal > BALANCO_AREA_MAX:
        zs = t[balanco][:, :, 2]
        problemas.append("%.0f mm² em balanço além de %.0f° (z de %.1f a %.1f)"
                         % (a_bal, BALANCO_MAX, zs.min(), zs.max()))
    resumo = ("primeira camada %.0f mm², altura %.1f, lado menor da base %.1f, "
              "balanço %.0f mm²" % (base, altura, lado, a_bal))
    return resumo, problemas


if __name__ == "__main__":
    ruim = False
    for caminho in sys.argv[1:]:
        resumo, problemas = conferir(caminho)
        print("%s: %s" % (caminho, resumo))
        for linha in problemas:
            print("   PROBLEMA:", linha)
        ruim = ruim or bool(problemas)
    sys.exit(1 if ruim else 0)
