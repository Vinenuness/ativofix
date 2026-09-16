# -*- coding: utf-8 -*-
"""
Gera o kit de favicon profissional do AtivoFix a partir da logo (static/logo-icon.png).

Saida em static/:
  favicon.ico            - multi-tamanho (16/32/48/64/128/256) p/ abas e atalhos
  favicon-32.png         - png nitido p/ navegadores modernos
  apple-touch-icon.png   - 180x180 fundo solido (iOS nao lida bem com transparencia)

Estilo: tile arredondado em carvao (cor da marca) + chip branco centralizado.
Regenere apos trocar a logo:  python _gen_favicon.py
"""
import os

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
STATIC = os.path.join(HERE, "static")

TILE = (27, 33, 38, 255)      # #1b2126 - carvao da marca (brand.css --af-surface)
INK = (242, 244, 245, 255)    # #f2f4f5 - branco da marca
SIDE = 512
CORNER = int(SIDE * 0.22)     # cantos arredondados modernos
INK_RATIO = 0.62              # chip ocupa 62% do tile


def build_tile(with_corners=True):
    """Tile quadrado (cantos transparentes se with_corners) + chip branco centralizado."""
    src = Image.open(os.path.join(STATIC, "logo-icon.png")).convert("RGBA")
    bb = src.split()[3].getbbox()
    src = src.crop(bb)

    out = Image.new("RGBA", (SIDE, SIDE), (0, 0, 0, 0))
    d = ImageDraw.Draw(out)
    if with_corners:
        d.rounded_rectangle([0, 0, SIDE - 1, SIDE - 1], radius=CORNER, fill=TILE)
    else:
        d.rectangle([0, 0, SIDE - 1, SIDE - 1], fill=TILE)

    ink_side = int(SIDE * INK_RATIO)
    ink = src.resize((ink_side, ink_side), Image.LANCZOS)

    # tinta da logo -> branco solido da marca (preserva alfa)
    alpha = ink.split()[3]
    solid = Image.new("RGBA", ink.size, INK)
    solid.putalpha(alpha)

    pos = ((SIDE - ink_side) // 2, (SIDE - ink_side) // 2)
    out.alpha_composite(solid, pos)
    return out


def main():
    tile = build_tile(with_corners=True)

    # 1) .ico multi-tamanho
    ico_path = os.path.join(STATIC, "favicon.ico")
    tile.save(ico_path, sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])

    # 2) png 32px nitido
    tile.resize((32, 32), Image.LANCZOS).save(os.path.join(STATIC, "favicon-32.png"))

    # 3) apple touch 180x180, fundo solido
    apple = build_tile(with_corners=False).resize((180, 180), Image.LANCZOS)
    apple.save(os.path.join(STATIC, "apple-touch-icon.png"))

    for f in ("favicon.ico", "favicon-32.png", "apple-touch-icon.png"):
        p = os.path.join(STATIC, f)
        print(f"{f}: {os.path.getsize(p)} bytes")


if __name__ == "__main__":
    main()
