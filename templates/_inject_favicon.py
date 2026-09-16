# -*- coding: utf-8 -*-
"""Aponta todas as paginas para o kit de favicon profissional (ico + 32px + apple)."""
import glob
import io
import os

OLD = '<link rel="icon" href="/static/favicon.png" />'
NEW = (
    '<link rel="icon" type="image/png" sizes="32x32" href="/static/favicon-32.png" />\n'
    '  <link rel="icon" href="/static/favicon.ico" sizes="any" />\n'
    '  <link rel="apple-touch-icon" href="/static/apple-touch-icon.png" />'
)

os.chdir(os.path.dirname(os.path.abspath(__file__)))

changed = missing = 0
for fp in sorted(glob.glob("*.html")):
    s = io.open(fp, encoding="utf-8", newline="").read()
    if OLD in s:
        s = s.replace(OLD, NEW)
        io.open(fp, "w", encoding="utf-8", newline="").write(s)
        changed += 1
    else:
        missing += 1
        print("SEM ANCORA PADRAO:", fp)

print("OK alteradas:", changed, "| sem anchor:", missing)
