# -*- coding: utf-8 -*-
"""Injeta static/brand.css como ÚLTIMO stylesheet de cada página AtivoFix."""
import glob
import io
import os

SNIP = '<link rel="stylesheet" href="/static/brand.css" />'
os.chdir(os.path.dirname(os.path.abspath(__file__)))

changed = skipped = 0
for fp in sorted(glob.glob("*.html")):
    s = io.open(fp, encoding="utf-8", newline="").read()
    if "brand.css" in s or "/static/" not in s:
        skipped += 1
        continue
    last = s.rfind('/static/')
    i = s.find(">", last)
    if last < 0 or i < 0:
        print("SEM ANCORA:", fp)
        continue
    s = s[: i + 1] + "\n  " + SNIP + s[i + 1 :]
    io.open(fp, "w", encoding="utf-8", newline="").write(s)
    changed += 1

print("OK alteradas:", changed, "| puladas:", skipped)
