# -*- coding: utf-8 -*-
"""Patch: logo AtivoFix no cabecalho e rodape dos relatorios PDF.

- Adiciona get_brand_pdf() (helpers compartilhados de marca)
- Inventario (/api/export/pdf): classe PDF usa header/footer com logo
- Chamados (/api/tickets/report/pdf): PDF vira classe com header/footer
"""
import io
import sys

FP = "server.py"
s = io.open(FP, encoding="utf-8", newline="").read()
orig = s
NL = "\r\n" if "\r\n" in s[:4000] else "\n"


def rep(old, new, count=1):
    global s
    old = old.replace("\n", NL)
    new = new.replace("\n", NL)
    n = s.count(old)
    if n != count:
        print(f"ANCHOR FAIL ({n}/{count}): {old[:70]!r}")
        sys.exit(1)
    s = s.replace(old, new, count)


# ---------- 1) Helpers de marca (antes de ALLOWED_ATT_EXT) ----------
rep(
    'ALLOWED_ATT_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".pdf", ".txt", ".zip", ".docx", ".xlsx", ".csv", ".mp4", ".mov"}',
    '''ALLOWED_ATT_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".pdf", ".txt", ".zip", ".docx", ".xlsx", ".csv", ".mp4", ".mov"}

# ---------- Marca para relatorios PDF (logo azul + rodape padrao) ----------
LOGO_PRINT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "logo-print.png")
BRAND_BLUE = (2, 132, 199)   # azul escuro da marca (legivel em papel)
BRAND_SLATE = (71, 85, 105)


def get_brand_pdf():
    """Retorna (logo_bytes, logo_size) p/ embutir nos PDFs; (None, 0) se faltar."""
    try:
        with open(LOGO_PRINT_PATH, "rb") as f:
            data = f.read()
        from PIL import Image as _Img
        import io as _io
        w, h = _Img.open(_io.BytesIO(data)).size
        return data, (w, h)
    except Exception:
        return None, (0, 0)


def brand_pdf_header(pdf, title):
    """Cabecalho padrao: logo a esquerda + titulo a direita + linha azul."""
    logo, (lw, lh) = get_brand_pdf()
    top = pdf.t_margin
    if logo:
        # lockup com proporcao original ~2.74:1 (largura 58mm)
        w_mm, h_mm = 58.0, 58.0 * lh / lw
        try:
            pdf.image(io.BytesIO(logo), x=pdf.l_margin, y=top + 2, w=w_mm, h=h_mm)
        except Exception:
            logo = None
    if logo:
        pdf.set_y(top + 2)
    else:
        pdf.set_y(top + 2)
        pdf.set_font("Helvetica", "B", 15)
        pdf.set_text_color(*BRAND_SLATE)
        pdf.cell(0, 9, "AtivoFix", 0, 2, "L")
    # titulo alinhado a direita, na mesma faixa da logo
    pdf.set_xy(pdf.l_margin, top + 4)
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 8, title, 0, 2, "R")
    pdf.set_xy(pdf.l_margin, top + 12)
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(*BRAND_SLATE)
    pdf.cell(0, 5, "Relatorio gerado pelo AtivoFix - gestao de inventario e chamados de TI", 0, 2, "R")
    y_end = top + max(16.0, (58.0 * lh / lw if logo else 16.0)) + 2.0
    pdf.set_y(y_end)
    pdf.set_draw_color(*BRAND_BLUE)
    pdf.set_line_width(0.5)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(4)
    pdf.set_text_color(0, 0, 0)


def brand_pdf_footer(pdf):
    """Rodape padrao: linha + marca e pagina (Fpdf2 exige {{nb}} sem f-string)."""
    pdf.set_y(-14)
    pdf.set_draw_color(203, 213, 225)
    pdf.set_line_width(0.3)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.set_y(-12)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(*BRAND_SLATE)
    pdf.cell(0, 6, "AtivoFix - Tecnologia em Movimento", 0, 0, "L")
    pdf.cell(0, 6, "Pagina " + str(pdf.page_no()) + "/{{nb}}", 0, 0, "R")''',
    count=1,
)

# ---------- 2) Inventario: classe PDF usa a marca ----------
rep(
    '''    class PDF(FPDF):
        def header(self):
            self.set_font("Helvetica", "B", 14)
            self.cell(0, 10, "Relatorio de Inventario por Unidade", 0, 1, "C")
            self.ln(5)
        
        def footer(self):
            self.set_y(-15)
            self.set_font("Helvetica", "I", 8)
            self.cell(0, 10, f"Pagina {self.page_no()}/{{nb}}", 0, 0, "C")''',
    '''    class PDF(FPDF):
        def header(self):
            brand_pdf_header(self, "Relatorio de Inventario por Unidade")
        
        def footer(self):
            brand_pdf_footer(self)''',
    count=1,
)

# ---------- 3) Chamados: FPDF puro -> classe com marca ----------
rep(
    '''    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 15, "AtivoFix - Relatorio de Chamados", 0, 1, "C")
    pdf.set_font("Helvetica", "", 12)
    tname = tenant["name"] if tenant else "N/A"''',
    '''    class PDF(FPDF):
        def header(self):
            brand_pdf_header(self, "Relatorio de Chamados")
        
        def footer(self):
            brand_pdf_footer(self)
    
    pdf = PDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_font("Helvetica", "", 12)
    tname = tenant["name"] if tenant else "N/A"''',
    count=1,
)

# Saltos de pagina do relatorio de chamados devem disparar header/footer
rep(
    '''    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Resumo por Status", 0, 1)''',
    '''    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 10, "Resumo por Status", 0, 1)''',
    count=1,
)

if s == orig:
    print("NOTHING CHANGED")
    sys.exit(1)
io.open(FP, "w", encoding="utf-8", newline="").write(s)
print("PATCH OK")
