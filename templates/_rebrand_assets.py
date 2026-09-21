# -*- coding: utf-8 -*-
"""
Rebrand AtivoFix — processa as logos novas (fundo preto -> alfa) e regenera:
  static/logo-icon.png   icone do chip azul (quadrado)
  static/logo.png        lockup completo (chip + ativofix + tagline)
  static/logo-dark.png   lockup em tinta UNICA escura (p/ impressao/etiqueta)
  static/favicon.ico / favicon-32.png / apple-touch-icon.png

Fontes em static/brand-src/ (imagens originais com fundo preto).
"""
import os

from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
STATIC = os.path.join(HERE, "static")
SRC = os.path.join(STATIC, "brand-src")

CHARCOAL = (27, 33, 38, 255)  # #1b2126 — superficie da marca (brand.css)


def knock_out_black(src, scale=1.15):
    """Remove fundo preto -> alfa, sem encoler os raios de brilho.

    Luz acumula: a imagem e 'preto + luz aditiva'. Entao o alfa deriva do
    brilho maximo (max canais), e a cor e preservada (pre-multiplicacao
    invertida). scale > 1 deixa o glow respirar um pouco alem do recorte duro.
    """
    im = src.convert("RGB")
    maxc = im.split()  # r, g, b
    # brilho = max(r,g,b) por pixel -> luminosity como alfa
    gray = Image.merge("RGB", maxc).convert("L")
    # pontos quentes saturam mais rapido (glow vira solido)
    lut = [min(255, int(v * scale)) for v in range(256)]
    alpha = gray.point(lut)
    alpha = alpha.filter(ImageFilter.GaussianBlur(0.4))
    out = im.copy()
    out.putalpha(alpha)
    return out


def crop_alpha(im, pad_ratio=0.02):
    bb = im.split()[3].getbbox()
    if not bb:
        return im
    pad = int(max(im.size) * pad_ratio)
    box = (
        max(0, bb[0] - pad),
        max(0, bb[1] - pad),
        min(im.width, bb[2] + pad),
        min(im.height, bb[3] + pad),
    )
    return im.crop(box)


def monochrome_dark(src_rgba, ink=(30, 41, 59, 255)):
    """Versao tinta unica (para etiqueta impressa em fundo branco)."""
    gray = src_rgba.convert("L")
    lut = []
    for v in range(256):
        # luz -> tinta: mais brilho = mais opacidade
        lut.append(min(255, int(v * 1.05)))
    alpha = gray.point(lut)
    out = Image.new("RGBA", src_rgba.size, ink)
    out.putalpha(alpha)
    return out


def print_lockup(src_rgba, ink=(30, 41, 59, 255)):
    """Lockup para fundo CLARO (PDF): tinta branca -> ardósia; azuis preservados.

    Na arte, 'ativo' e a tagline sao brancos (para fundo escuro). Em papel
    branco sumiriam — aqui viram cinza-ardosia escuro; o azul da marca fica.
    """
    from PIL import ImageChops

    im = src_rgba.convert("RGBA")
    alpha = im.split()[3]
    hsv = im.convert("RGB").convert("HSV")
    s, v = hsv.split()[1], hsv.split()[2]
    low_sat = s.point(lambda x: 255 if x < 70 else 0)   # branco/cinza
    bright = v.point(lambda x: 255 if x > 130 else 0)   # claro
    white_mask = ImageChops.multiply(low_sat, bright)
    out = im.copy()
    dark = Image.new("RGBA", im.size, ink)
    out.paste(dark, (0, 0), white_mask)
    out.putalpha(alpha)
    return out


def main():
    icon = crop_alpha(knock_out_black(Image.open(os.path.join(SRC, "icon-src.png"))))
    lockup = crop_alpha(knock_out_black(Image.open(os.path.join(SRC, "lockup-src.png"))))

    # 1) icone quadrado (base para favicons e brand-icon das paginas)
    side = max(icon.size)
    sq = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    sq.alpha_composite(icon, ((side - icon.width) // 2, (side - icon.height) // 2))
    sq = sq.resize((512, 512), Image.LANCZOS)
    sq.save(os.path.join(STATIC, "logo-icon.png"))

    # 2) lockup completo (chip + nome + tagline)
    target_w = 1100
    lockup = lockup.resize((target_w, int(lockup.height * target_w / lockup.width)), Image.LANCZOS)
    lockup.save(os.path.join(STATIC, "logo.png"))
    print("logo.png:", lockup.size)

    # 2b) versao para fundo claro (cabecalho dos PDFs)
    print_lockup(lockup).save(os.path.join(STATIC, "logo-print.png"))

    # 3) versao impressa (tinta unica escura, fundo transparente)
    dark = monochrome_dark(lockup, ink=(28, 36, 43, 255))
    dark.save(os.path.join(STATIC, "logo-dark.png"))

    # 4) kit de favicons a partir do icone azul (sem tile — a arte ja tem fundo)
    #    a) .ico multi-tamanho, fundo solido carvao arredondado p/ contraste na aba
    SIDE, CORNER = 512, int(512 * 0.22)
    ink = crop_alpha(sq)
    ink_side = int(SIDE * 0.70)
    ink_r = ink.resize((ink_side, ink_side), Image.LANCZOS)
    tile = Image.new("RGBA", (SIDE, SIDE), (0, 0, 0, 0))
    d = ImageDraw.Draw(tile)
    d.rounded_rectangle([0, 0, SIDE - 1, SIDE - 1], radius=CORNER, fill=CHARCOAL)
    tile.alpha_composite(ink_r, ((SIDE - ink_side) // 2, (SIDE - ink_side) // 2))
    tile.save(
        os.path.join(STATIC, "favicon.ico"),
        sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )

    #    b) 32px nitido
    tile.resize((32, 32), Image.LANCZOS).save(os.path.join(STATIC, "favicon-32.png"))

    #    c) apple touch 180x180 fundo solido (sem cantos transparentes)
    flat = Image.new("RGBA", (SIDE, SIDE), CHARCOAL)
    flat.alpha_composite(ink_r, ((SIDE - ink_side) // 2, (SIDE - ink_side) // 2))
    flat.resize((180, 180), Image.LANCZOS).save(os.path.join(STATIC, "apple-touch-icon.png"))

    # 5) icone do agente Windows (mesmo tile do favicon, multi-tamanho)
    tile.save(
        os.path.join(HERE, "agent.ico"),
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )
    print("agent.ico:", os.path.getsize(os.path.join(HERE, "agent.ico")), "bytes")

    for f in ("logo-icon.png", "logo.png", "logo-dark.png", "favicon.ico", "favicon-32.png", "apple-touch-icon.png"):
        p = os.path.join(STATIC, f)
        im = Image.open(p)
        print(f"{f}: {im.size} {os.path.getsize(p)} bytes")


if __name__ == "__main__":
    main()
