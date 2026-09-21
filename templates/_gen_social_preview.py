# -*- coding: utf-8 -*-
"""Social preview do repo (1280x640) — identidade AtivoFix.

Sobe via PATCH /repos/{owner}/{repo}/social-preview (multipart form).
"""
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
STATIC = os.path.join(HERE, "static")
OUT = os.path.join(STATIC, "social-preview.png")

W, H = 1280, 640
CHARCOAL = (18, 22, 26)
CHARCOAL2 = (23, 29, 35)
BLUE = (56, 189, 248)
MUTED = (148, 163, 184)
WHITE = (244, 246, 248)

img = Image.new("RGB", (W, H), CHARCOAL)

# gradiente sutil
top = Image.new("RGB", (W, H), CHARCOAL)
td = ImageDraw.Draw(top)
for y in range(H):
    t = y / H
    c = tuple(int(CHARCOAL[i] + (CHARCOAL2[i] - CHARCOAL[i]) * t) for i in range(3))
    td.line([(0, y), (W, y)], fill=c)
img.paste(top)

# grade de fundo sutil
d = ImageDraw.Draw(img, "RGBA")
for x in range(0, W, 56):
    d.line([(x, 0), (x, H)], fill=(255, 255, 255, 6), width=1)
for y in range(0, H, 56):
    d.line([(0, y), (W, y)], fill=(255, 255, 255, 6), width=1)

# chip gigante em marca d'agua a direita
chip = Image.open(os.path.join(STATIC, "logo-icon.png")).convert("RGBA")
chip = chip.resize((640, 640), Image.LANCZOS)
chip = chip.filter(ImageFilter.GaussianBlur(0.5))
mask = chip.split()[3].point(lambda a: int(a * 0.13))
img.paste(chip, (W - 620, 10), mask)

# vinheta esquerda pra texto respirar
vig = Image.new("L", (W, H), 0)
vd = ImageDraw.Draw(vig)
vd.rectangle([0, 0, 760, H], fill=210)
vig = vig.filter(ImageFilter.GaussianBlur(120))
dark = Image.new("RGB", (W, H), CHARCOAL)
img = Image.composite(dark, img, vig)
d = ImageDraw.Draw(img, "RGBA")

# fontes
def font(size, bold=True):
    names = (["segoeuib.ttf", "arialbd.ttf"] if bold else ["segoeui.ttf", "arial.ttf"])
    for n in names:
        try:
            return ImageFont.truetype(n, size)
        except OSError:
            continue
    return ImageFont.load_default()

F_TITLE = font(74)
F_SUB = font(34, bold=False)
F_TAG = font(26, bold=False)
F_URL = font(30)

# logo lockup no topo esquerdo
lockup = Image.open(os.path.join(STATIC, "logo.png")).convert("RGBA")
lw = 360
lh = int(lockup.height * lw / lockup.width)
lockup = lockup.resize((lw, lh), Image.LANCZOS)
img.paste(lockup, (80, 70), lockup)

# titulo
ty = 320
d.text((80, ty), "Todo o parque de TI", font=F_TITLE, fill=WHITE)
d.text((80, ty + 96), "da sua empresa,", font=F_TITLE, fill=WHITE)
d.text((80, ty + 192), "em um só painel.", font=F_TITLE, fill=BLUE)

# subtitulo
d.text((82, ty + 316), "Inventário automático · Chamados por unidade · Relatórios PDF",
       font=F_SUB, fill=MUTED)

# rodape
d.text((82, H - 84), "ativofix.com.br", font=F_URL, fill=WHITE)
d.text((330, H - 78), "Tecnologia em Movimento", font=F_TAG, fill=MUTED)

img.save(OUT, "PNG", optimize=True)
print("gerado:", OUT, img.size)
