"""Gêmeo digital do giroscópio do CoopBot.

Roda o hub/tbr.py DE VERDADE no PC, com um Pybricks falso (pybricks_falso.py)
ligado a um modelo físico do robô e do giroscópio (mundo.py). Serve para
comparar estratégias de giro e de reta por Monte Carlo (cenarios.py) sem o
robô na mesa.

O pacote `pybricks` da .venv nunca é importado: o carregador (carregar.py)
injeta os módulos falsos em sys.modules só enquanto executa os arquivos do hub.

Não substitui a mesa. Os números do modelo vêm do código-fonte do Pybricks,
do datasheet do sensor e das medições do docs/diario.md (ver docs/giroscopio.md).
"""
