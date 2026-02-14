from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import os

TEMPLATES_DIR = os.path.dirname(__file__)
ASSETS_DIR = os.path.join(TEMPLATES_DIR, "assets")
LOGO_PATH = os.path.join(ASSETS_DIR, "mph_logo.png")
PAGE1_PATH = os.path.join(TEMPLATES_DIR, "mph_invoice_pg1.pdf")
PAGE2_PATH = os.path.join(TEMPLATES_DIR, "mph_invoice_pg2.pdf")

# Layout constants
PAGE_WIDTH, PAGE_HEIGHT = letter
PAGE1_LOGO_WIDTH = 2.0 * inch
PAGE2_LOGO_WIDTH = 1.85 * inch
PAGE1_HEADER_TOP = 10.65 * inch  # 731.8 pts
PAGE2_HEADER_TOP = 10.30 * inch  # 741.6 pts
PAGE1_BODY_TOP_Y = 9.05 * inch  # 651.6 pts
PAGE2_BODY_TOP_Y = 9.65 * inch  # 694.8 pts

COMPANY_NAME = "MPH Construction & Painting"
COMPANY_INFO = "[Address/Contact Here]"


def draw_logo(c, x, y, target_width):
    logo = ImageReader(LOGO_PATH)
    iw, ih = logo.getSize()
    aspect = ih / iw
    target_height = target_width * aspect
    c.drawImage(logo, x, y - target_height, width=target_width, height=target_height, mask='auto', preserveAspectRatio=True)
    return target_height

def generate_pg1():
    c = canvas.Canvas(PAGE1_PATH, pagesize=letter)
    # Logo left, top
    logo_h = draw_logo(c, 1 * inch, PAGE1_HEADER_TOP, PAGE1_LOGO_WIDTH)
    # Company info right aligned, tight vertical spacing
    right_x = PAGE_WIDTH - 1 * inch
    y = PAGE1_HEADER_TOP - 0.05 * inch  # 10.60 in
    c.setFont('Helvetica-Bold', 16)
    c.drawRightString(right_x, y, COMPANY_NAME)
    # (If you want a second line, add here)
    # Divider line: BODY_TOP_Y + 0.15 in (9.20 in)
    divider_y = PAGE1_BODY_TOP_Y + 0.15 * inch
    c.setLineWidth(1)
    c.line(1 * inch, divider_y, PAGE_WIDTH - 1 * inch, divider_y)
    # BODY_TOP_Y constant visual (not rendered, just for dev reference)
    # c.setStrokeColorRGB(1,0,0); c.line(0, PAGE1_BODY_TOP_Y, PAGE_WIDTH, PAGE1_BODY_TOP_Y)
    c.save()
    print(f"✓ Saved: {os.path.abspath(PAGE1_PATH)}")

def generate_pg2():
    c = canvas.Canvas(PAGE2_PATH, pagesize=letter)
    # Logo left, top (slightly larger)
    logo_h = draw_logo(c, 1 * inch, PAGE2_HEADER_TOP, PAGE2_LOGO_WIDTH)
    # Company name right-aligned, compact
    right_x = PAGE_WIDTH - 1 * inch
    y = PAGE2_HEADER_TOP - 0.03 * inch  # 10.27 in
    c.setFont('Helvetica-Bold', 13)
    c.drawRightString(right_x, y, COMPANY_NAME)
    # Divider line: BODY_TOP_Y + 0.10 in (9.75 in)
    divider_y = PAGE2_BODY_TOP_Y + 0.10 * inch
    c.setLineWidth(1)
    c.line(1 * inch, divider_y, PAGE_WIDTH - 1 * inch, divider_y)
    c.setLineWidth(1)
    c.line(1 * inch, header_bottom, PAGE_WIDTH - 1 * inch, header_bottom)
    # BODY_TOP_Y constant visual (not rendered, just for dev reference)
    # c.setStrokeColorRGB(0,0,1); c.line(0, PAGE2_BODY_TOP_Y, PAGE_WIDTH, PAGE2_BODY_TOP_Y)
    c.save()
    print(f"✓ Saved: {os.path.abspath(PAGE2_PATH)}")

def main():
    os.makedirs(ASSETS_DIR, exist_ok=True)
    generate_pg1()
    generate_pg2()

if __name__ == "__main__":
    main()
