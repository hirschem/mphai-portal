# Amount column x constant for table alignment

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
DEBUG_GUIDES = False


# Layout constants
PAGE_WIDTH, PAGE_HEIGHT = letter
PAGE1_LOGO_WIDTH = 2.3 * inch
PAGE2_LOGO_WIDTH = 1.85 * inch
PAGE1_HEADER_TOP = 10.65 * inch  # 731.8 pts
PAGE2_HEADER_TOP = 10.30 * inch  # 741.6 pts
PAGE1_BODY_TOP_Y = 9.05 * inch  # 651.6 pts
PAGE2_BODY_TOP_Y = 9.65 * inch  # 694.8 pts

# Margin constants for debug overlay
MARGIN_L = 1.0 * inch
MARGIN_R = PAGE_WIDTH - 1.0 * inch
MARGIN_T = PAGE_HEIGHT - 1.0 * inch
MARGIN_B = 1.0 * inch

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

    left_x = MARGIN_L
    right_x = MARGIN_R
    extension = PAGE_WIDTH * 0.05

    divider_y = PAGE1_BODY_TOP_Y
    header_baseline_y = divider_y + 7

    # Draw logo first (behind text)
    LEFT_PAD = -20
    TOP_PAD = -40
    logo_w = PAGE1_LOGO_WIDTH * 1.7
    logo = ImageReader(LOGO_PATH)
    iw, ih = logo.getSize()
    aspect = ih / iw
    logo_h = logo_w * aspect * 0.9
    logo_x = LEFT_PAD
    logo_y = PAGE_HEIGHT - TOP_PAD - logo_h
    c.drawImage(logo, logo_x, logo_y, width=logo_w, height=logo_h, mask='auto', preserveAspectRatio=True)

    # Date/Bill To labels derived from header_baseline_y
    date_label_y = header_baseline_y + 48
    billto_label_y = header_baseline_y + 28
    c.setFont("Helvetica", 11)
    c.drawString(left_x, date_label_y, "Date:")
    c.drawString(left_x, billto_label_y, "Bill To:")


    # Vertical divider for Amount column (starts exactly at divider line)
    amount_divider_x = right_x - 70

    # Header labels
    c.setFont("Helvetica", 12)
    c.drawString(left_x + 6, header_baseline_y, "Description")
    c.drawString(amount_divider_x + 8, header_baseline_y, "Amount")

    # Single horizontal divider line (table header line)
    c.setLineWidth(1)
    c.setStrokeColorRGB(0, 0, 0)
    c.line(left_x - extension, divider_y, right_x + extension, divider_y)

    # Vertical divider for Amount column (starts exactly at divider line)
    amount_divider_x = right_x - 70
    c.line(amount_divider_x, divider_y, amount_divider_x, MARGIN_B)

    # Company contact block, all right-aligned
    y = PAGE1_HEADER_TOP - 10
    c.setFont('Helvetica-Bold', 14)
    c.drawRightString(right_x, y, COMPANY_NAME)
    c.setFont('Helvetica', 11)
    leading = 12
    contact_lines = [
        "9426 Troon Village Way",
        "Lone Tree, CO 80124",
        "(303) 249-4563",
        "(720) 883-5097",
        "mhirsch60@hotmail.com",
    ]
    for line in contact_lines:
        y -= leading
        c.drawRightString(right_x, y, line)

    # Optional: Debug margin box
    if DEBUG_GUIDES:
        c.saveState()
        c.setStrokeColorRGB(1, 0, 1)
        c.setLineWidth(3)
        margin_w = MARGIN_R - MARGIN_L
        margin_h = MARGIN_T - MARGIN_B
        c.rect(MARGIN_L, MARGIN_B, margin_w, margin_h)
        c.restoreState()

    c.save()
    print(f"✓ Saved: {os.path.abspath(PAGE1_PATH)}")

def generate_pg2():
    right_x = PAGE_WIDTH - 1 * inch
    c = canvas.Canvas(PAGE2_PATH, pagesize=letter)


    # Optional: Debug guides
    if DEBUG_GUIDES:
        c.saveState()
        c.setStrokeColorRGB(1, 0, 1)  # bright magenta
        c.setLineWidth(3)

        # page border
        c.rect(0.5, 0.5, PAGE_WIDTH - 1, PAGE_HEIGHT - 1)

        # 1-inch margin box
        c.rect(1 * inch, 1 * inch, PAGE_WIDTH - 2 * inch, PAGE_HEIGHT - 2 * inch)

        # vertical center
        c.line(PAGE_WIDTH / 2, 0, PAGE_WIDTH / 2, PAGE_HEIGHT)

        # top guide (0.5 inch from top)
        c.line(0, PAGE_HEIGHT - 0.5 * inch, PAGE_WIDTH, PAGE_HEIGHT - 0.5 * inch)

        # amount column guide
        amount_col_x = PAGE_WIDTH - 2.5 * inch
        c.line(amount_col_x, 0, amount_col_x, PAGE_HEIGHT)
        c.restoreState()

    # Logo left, top (slightly larger)
    logo_h = draw_logo(c, 1 * inch, PAGE2_HEADER_TOP, PAGE2_LOGO_WIDTH)
    # Company name right-aligned, compact
    y = PAGE2_HEADER_TOP - 0.03 * inch  # 10.27 in
    c.setFont('Helvetica-Bold', 13)
    c.drawRightString(right_x, y, COMPANY_NAME)
    # Divider line: BODY_TOP_Y + 0.10 in (9.75 in)
    divider_y = PAGE2_BODY_TOP_Y + 0.10 * inch
    c.setLineWidth(1)
    c.line(1 * inch, divider_y, PAGE_WIDTH - 1 * inch, divider_y)
    # BODY_TOP_Y constant visual (not rendered, just for dev reference)
    # c.setStrokeColorRGB(0,0,1); c.line(0, PAGE2_BODY_TOP_Y, PAGE_WIDTH, PAGE2_BODY_TOP_Y)
    c.save()
    print(f"\u2713 Saved: {os.path.abspath(PAGE2_PATH)}")

def main():
    os.makedirs(ASSETS_DIR, exist_ok=True)
    generate_pg1()
    generate_pg2()

if __name__ == "__main__":
    main()
