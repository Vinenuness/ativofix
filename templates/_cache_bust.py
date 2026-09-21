# -*- coding: utf-8 -*-
"""Cache-busting: adiciona ?v=YYYYMMDD nas refs de /static em todos os .html.

Idempotente: refs que ja tem ?v= ficam intocadas.
Rode novamente (mudando VERSAO) quando trocar um asset.
"""
import glob
import io
import os
import re

VERSAO = "20260921a"
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# (nome_do_arquivo_estatico) -> sera versionado
ALVO = re.compile(
    r'(/static/(?:brand\.css|logo\.png|logo-icon\.png|logo-dark\.png|'
    r'favicon\.ico|favicon-32\.png|apple-touch-icon\.png))'
    r'(?![?a-z0-9])'  # ainda sem query string
)

total_arqs = 0
total_subs = 0
for path in glob.glob("*.html"):
    s = io.open(path, encoding="utf-8").read()
    nova, n = ALVO.subn(r"\1?v=" + VERSAO, s)
    if n:
        io.open(path, "w", encoding="utf-8", newline="").write(nova)
        total_arqs += 1
        total_subs += n
        print(f"{path}: {n} refs versionadas")

print(f"\nTotal: {total_subs} refs em {total_arqs} arquivos (v={VERSAO})")
