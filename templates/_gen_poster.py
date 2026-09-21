# -*- coding: utf-8 -*-
"""
Cartaz A4 (300 DPI) do portal de chamados — identidade AtivoFix.

Gera em templates/static/divulgacao/:
  cartaz-abrir-chamado-A4.png     impressao (2480x3508, 300 dpi)
  cartaz-abrir-chamado-A4.pdf     versao pdf p/ grafica
  cartaz-digital-1080x1350.png    quadrado 4:5 p/ WhatsApp/Instagram

Regenere:  .venv/Scripts/python.exe _gen_poster.py
"""
import os

import qrcode
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
STATIC = os.path.join(HERE, "static")
OUT = os.path.join(STATIC, "divulgacao")
os.makedirs(OUT, exist_ok=True)

URL = "https://ativofix.com.br/abrir-chamado"

DPI = 300
A4_W, A4_H = 2480, 3508  # 210x297mm @ 300dpi

CHARCOAL = (20, 24, 28)        # fundo #14181c
SURFACE = (27, 33, 38)         # #1b2126
BORDER = (42, 50, 58)          # #2a323a
TEXT = (233, 237, 240)         # #e9edf0
MUTED = (143, 154, 164)        # #8f9aa4
BLUE = (56, 189, 248)          # #38bdf8 — azul da marca
BLUE_DEEP = (2, 132, 199)      # #0284c7

FONTS = r"C:\Windows\Fonts"
F_REG = os.path.join(FONTS, "segoeui.ttf")
F_BOLD = os.path.join(FONTS, "segoeuib.ttf")
F_SEMI = os.path.join(FONTS, "segoeuisl.ttf")


def font(path, size):
    return ImageFont.truetype(path, size)


def center_text(d, xy, text, fnt, fill):
    w = d.textlength(text, font=fnt)
    d.text((xy[0] - w / 2, xy[1]), text, font=fnt, fill=fill)


def make_qr(size_px, dark, light):
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=12, border=2)
    qr.add_data(URL)
    qr.make(fit=True)
    img = qr.make_image(fill_color=dark, back_color=light).convert("RGB")
    return img.resize((size_px, size_px), Image.NEAREST)


def rounded(draw, box, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def build_poster():
    img = Image.new("RGB", (A4_W, A4_H), CHARCOAL)
    d = ImageDraw.Draw(img)

    # ---- moldura sutil
    m = 90
    rounded(d, (m, m, A4_W - m, A4_H - m), 60, None, outline=BORDER, width=3)

    # ---- marca d'agua gigante (chip fantasma no canto inferior)
    chip = Image.open(os.path.join(STATIC, "logo-icon.png")).convert("RGBA")
    wm_size = 1900
    wm = chip.resize((wm_size, wm_size), Image.LANCZOS)
    wm_alpha = wm.split()[3].point(lambda a: int(a * 0.05))
    wm.putalpha(wm_alpha)
    img.paste(wm, (A4_W - wm_size + 260, A4_H - wm_size + 300), wm)

    # ---- cabecalho: logo
    logo = Image.open(os.path.join(STATIC, "logo.png")).convert("RGBA")
    lw = 880
    lh = int(logo.height * lw / logo.width)
    logo = logo.resize((lw, lh), Image.LANCZOS)
    img.paste(logo, ((A4_W - lw) // 2, 260), logo)

    center_text(d, (A4_W / 2, 260 + lh + 60), "TECNOLOGIA EM MOVIMENTO", font(F_REG, 46), MUTED)

    # ---- titulo
    ty = 760
    center_text(d, (A4_W / 2, ty), "Precisa de ajuda", font(F_BOLD, 190), TEXT)
    center_text(d, (A4_W / 2, ty + 250), "da TI?", font(F_BOLD, 190), BLUE)

    # ---- subtitulo
    center_text(d, (A4_W / 2, ty + 560), "Abra um chamado em segundos:", font(F_SEMI, 68), TEXT)
    center_text(d, (A4_W / 2, ty + 660), "sem instalar nada, direto do navegador.", font(F_SEMI, 68), MUTED)

    # ---- QR code (grande, com moldura branca p/ leitura)
    qy = ty + 820
    qr_size = 1180
    pad = 46
    frame = qr_size + pad * 2
    qx = (A4_W - frame) // 2
    rounded(d, (qx, qy, qx + frame, qy + frame), 44, (255, 255, 255))
    qr = make_qr(qr_size, (16, 22, 28), (255, 255, 255))
    img.paste(qr, (qx + pad, qy + pad))

    # ---- chamada pra acao sob o QR
    ay = qy + frame + 90
    center_text(d, (A4_W / 2, ay), "Aponte a camera", font(F_BOLD, 110), TEXT)
    center_text(d, (A4_W / 2, ay + 150), "e abra seu chamado", font(F_BOLD, 110), BLUE)

    # ---- URL legivel
    uy = ay + 340
    rounded(d, (A4_W / 2 - 700, uy, A4_W / 2 + 700, uy + 120), 60, SURFACE, outline=BORDER, width=3)
    center_text(d, (A4_W / 2, uy + 26), "ativofix.com.br/abrir-chamado", font(F_BOLD, 64), TEXT)

    # ---- rodape
    fy = A4_H - 300
    d.line((m + 120, fy - 60, A4_W - m - 120, fy - 60), fill=BORDER, width=3)
    center_text(d, (A4_W / 2, fy), "AtivoFix  ·  Chamados organizados por unidade  ·  Relatorios para a diretoria", font(F_SEMI, 44), MUTED)

    out_png = os.path.join(OUT, "cartaz-abrir-chamado-A4.png")
    img.save(out_png, dpi=(DPI, DPI))
    img.save(os.path.join(OUT, "cartaz-abrir-chamado-A4.pdf"), "PDF", resolution=DPI)
    print("A4:", out_png)


def build_social():
    """Versao 4:5 (1080x1350) para WhatsApp/Instagram."""
    W, H = 1080, 1350
    img = Image.new("RGB", (W, H), CHARCOAL)
    d = ImageDraw.Draw(img)

    chip = Image.open(os.path.join(STATIC, "logo-icon.png")).convert("RGBA")
    wm = chip.resize((760, 760), Image.LANCZOS)
    wm.putalpha(wm.split()[3].point(lambda a: int(a * 0.05)))
    img.paste(wm, (W - 620, H - 620), wm)

    logo = Image.open(os.path.join(STATIC, "logo.png")).convert("RGBA")
    lw = 340
    lh = int(logo.height * lw / logo.width)
    logo = logo.resize((lw, lh), Image.LANCZOS)
    img.paste(logo, ((W - lw) // 2, 70), logo)

    center_text(d, (W / 2, 210 + lh), "Precisa de ajuda da TI?", font(F_BOLD, 72), TEXT)

    qs = 460
    pad = 22
    frame = qs + pad * 2
    qx = (W - frame) // 2
    qy = 420
    rounded(d, (qx, qy, qx + frame, qy + frame), 26, (255, 255, 255))
    qr = make_qr(qs, (16, 22, 28), (255, 255, 255))
    img.paste(qr, (qx + pad, qy + pad))

    center_text(d, (W / 2, qy + frame + 60), "Aponte a camera", font(F_BOLD, 58), TEXT)
    center_text(d, (W / 2, qy + frame + 150), "e abra seu chamado", font(F_BOLD, 58), BLUE)

    uy = qy + frame + 280
    rounded(d, (W / 2 - 340, uy, W / 2 + 340, uy + 74), 37, SURFACE, outline=BORDER, width=2)
    center_text(d, (W / 2, uy + 16), "ativofix.com.br/abrir-chamado", font(F_BOLD, 34), TEXT)

    out = os.path.join(OUT, "cartaz-digital-1080x1350.png")
    img.save(out, dpi=(150, 150))
    print("social:", out)


if __name__ == "__main__":
    build_poster()
    build_social()
