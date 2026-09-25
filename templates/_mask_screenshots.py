# -*- coding: utf-8 -*-
"""Aplica mascaras opacas sobre dados sensiveis dos screenshots do README.

Uso: python _mask_screenshots.py   (a partir da raiz do repo)
Idempotente: na 1a execucao copia os originais para assets/screenshots/_orig/
e sempre reaplica as mascaras a partir dos originais.
"""
import os, shutil, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from PIL import Image, ImageDraw

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # raiz do repo
SHOTS = os.path.join(BASE, "assets", "screenshots")
ORIG = os.path.join(SHOTS, "_orig")

# Caixas (x, y, w, h) medidas por OCR (winsdk) sobre os ORIGINAIS.
# Pad de ~6px e aplicado automaticamente.
MASKS = {
    "detalhes-ativo.png": [
        (18, 60, 210, 17),    # hostname DESKTOP-IFM3R09
        (335, 98, 86, 9),     # TAG EVO-ME6KARXB
        (521, 98, 225, 9),    # Device UID (uuid)
        (463, 154, 85, 11),   # AnyDesk ID
        (491, 191, 57, 12),   # usuario Windows (Vinicius)
        (442, 230, 107, 11),  # IP
        (409, 268, 139, 11),  # MAC
    ],
    "inventario.png": [
        (24, 152, 175, 40),   # titulo do card: TAG badge + hostname (2 linhas OCR)
        (112, 197, 84, 14),   # IP na linha de status
        (68, 214, 54, 14),    # usuario (Vinicius)
        (23, 233, 175, 17),   # unidade "Escritorio TH" + local ADM
        (22, 248, 60, 17),    # "CLINICA)" (continuacao do local)
    ],
    "relatorio-por-unidade.png": [
        (30, 338, 88, 16),    # "Escritorio TH" na tabela
    ],
    "login.png": [],
    "abrir-chamado.png": [],
    "novo-usuario.png": [],
}

PAD = 6


def sample_bg(img, box):
    """Cor de fundo = media dos pixels da moldura ao redor da caixa."""
    x, y, w, h = box
    px = img.load()
    pts = []
    for dx in range(-PAD - 4, w + PAD + 4, 3):
        for dy in (-PAD - 4, h + PAD + 3):
            for sx, sy in ((x + dx, y + dy),):
                if 0 <= sx < img.width and 0 <= sy < img.height:
                    pts.append(px[sx, sy])
    for dy in range(-PAD - 4, h + PAD + 4, 3):
        for dx in (-PAD - 4, w + PAD + 3):
            sx, sy = x + dx, y + dy
            if 0 <= sx < img.width and 0 <= sy < img.height:
                pts.append(px[sx, sy])
    if not pts:
        return (20, 24, 28, 255)
    n = len(pts)
    return tuple(sum(p[i] for p in pts) // n for i in range(3)) + (255,)


def main():
    os.makedirs(ORIG, exist_ok=True)
    for name, boxes in MASKS.items():
        src = os.path.join(SHOTS, name)
        if not os.path.exists(src):
            print(f"skip (nao encontrado): {name}")
            continue
        orig_path = os.path.join(ORIG, name)
        if not os.path.exists(orig_path):
            shutil.copy2(src, orig_path)
            print(f"original guardado: _orig/{name}")
        img = Image.open(orig_path).convert("RGB")
        draw = ImageDraw.Draw(img)
        for (x, y, w, h) in boxes:
            bg = sample_bg(img, (x, y, w, h))
            draw.rounded_rectangle(
                [x - PAD, y - PAD, x + w + PAD, y + h + PAD],
                radius=6, fill=bg,
            )
        img.save(src)
        print(f"mascarado: {name} ({len(boxes)} caixas)")
    print("OK")


if __name__ == "__main__":
    main()
