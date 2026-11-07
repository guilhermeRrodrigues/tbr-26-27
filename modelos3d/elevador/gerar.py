# Gera os STL de todas as peças (já na orientação de impressão) e fatia os
# pratos para a A1 mini com PLA Lite (versão 2).
#
#   P1  elevador_p1_hastes.3mf       fuso (2 segmentos) + haste quadrada (2) + pinhão
#   P2  elevador_p2_carro_garra.3mf  carro + barra da garra + pino do batente
#   P2b elevador_p2b_barra.3mf       só a barra da garra (troca sem reimprimir o carro)
#   P2r elevador_p2_reservas.3mf     P2 + reservas: 2ª barra, mais 2 pinos e 1 pinhão
#   P3  elevador_p3_dedo_fixo.3mf    dedo fixo (na diagonal)
#   P4  elevador_p4_dedo_movel.3mf   dedo móvel (na diagonal)
#   P5  elevador_p5_torre.3mf        2 colunas + portal
# A placa de teste (teste_mancal.py) é o prato P0, gerado à parte.
#
# Uso: python gerar.py [pasta_png] [filtro_de_prato]
# Rode antes o montagem.py: ele confere interferência, altura e batente.

import sys

import parametros as p
import batente
import carro
import dedos
import eixo_fuso
import eixo_garra
import garra
import pinhao
import torre
from fatiar import fatiar
from rosca import exportar

# Rosca, engrenagens, soquetes e túnel em 0,20. Dedos e torre em 0,28 (−16 e
# −30 min): seus furos verticais não dependem da camada, e os furos de pino
# deitados são medidos na placa de teste, que também sai em 0,28.
PADRAO = "0.20mm Standard @BBL A1M"
RAPIDO = "0.28mm Extra Draft @BBL A1M"
PRATOS = [
    ("elevador_p1_hastes.3mf", ["fuso_baixo", "fuso_cima", "garra_baixo", "garra_cima",
                                "pinhao"], PADRAO),
    ("elevador_p2_carro_garra.3mf", ["carro", "garra", "batente"], PADRAO),
    ("elevador_p2b_barra.3mf", ["garra"], PADRAO),
    ("elevador_p2_reservas.3mf", ["carro", "garra", "garra", "batente", "batente", "batente",
                                  "pinhao"], PADRAO),
    # Cada dedo ocupa a diagonal do prato: um por prato.
    ("elevador_p3_dedo_fixo.3mf", ["dedo_fixo"], RAPIDO),
    ("elevador_p4_dedo_movel.3mf", ["dedo_movel"], RAPIDO),
    ("elevador_p5_torre.3mf", ["coluna_esq", "coluna_dir", "portal"], RAPIDO),
]


def pecas_de_impressao():
    s = {}
    s.update(eixo_fuso.impressao())
    s.update(eixo_garra.impressao())
    s.update(dedos.impressao())
    s.update(torre.impressao())
    s["pinhao"] = pinhao.impressao()
    s["carro"] = carro.impressao()
    s["garra"] = garra.impressao()
    s["batente"] = batente.impressao()
    return s


def main(pasta_png=None, so=None):
    stl = {}
    for nome, peca in pecas_de_impressao().items():
        # is_valid é propriedade no build123d 0.13 e método nas versões antigas.
        valida = peca.is_valid() if callable(peca.is_valid) else peca.is_valid
        if not valida:
            raise SystemExit("peça inválida: " + nome)
        bb = peca.bounding_box()
        maior = max(bb.size.X, bb.size.Y, bb.size.Z)
        if maior > p.VOLUME_IMPRESSAO:
            raise SystemExit("%s não cabe na impressora: %.1f mm" % (nome, maior))
        stl[nome] = exportar(peca, nome)
        print("%-11s %6.1f cm³  %5.1f × %5.1f × %5.1f mm"
              % (nome, peca.volume / 1000, bb.size.X, bb.size.Y, bb.size.Z))
    total = 0.0
    gramas = 0.0
    for arquivo, nomes, processo in PRATOS:
        if so and so not in arquivo:
            continue
        r = fatiar([stl[n] for n in nomes], arquivo, pasta_png=pasta_png, processo=processo)
        if r["minutos"] is None:
            raise SystemExit("falhou ao fatiar %s: %s" % (arquivo, r["erro"]))
        total += r["minutos"]
        gramas += r["gramas"] or 0.0
        print("%-30s %5.0f min  %5.1f g  camada %.2f  %s"
              % (arquivo, r["minutos"], r["gramas"] or 0.0, r["camada"] or 0.0, r["erro"]))
        for aviso in r["avisos"]:
            if "ZFiller" not in aviso:   # mensagem interna do fatiador, sem efeito no G-code
                print("   aviso:", aviso)
    print("total: %.0f min (%.1f h), %.0f g de PLA Lite" % (total, total / 60, gramas))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None, sys.argv[2] if len(sys.argv) > 2 else None)
