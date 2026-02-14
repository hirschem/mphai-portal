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
    header_baseline_y = divider_y + 14

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

    # Date/Bill To labels under logo, not computed from divider_y
    date_label_y = PAGE1_HEADER_TOP - 1.60 * inch
    billto_label_y = date_label_y - 18
    c.setFont("Helvetica", 11)
    c.drawString(MARGIN_L, date_label_y, "Date:")
    c.drawString(MARGIN_L, billto_label_y, "Bill To:")

    # Header labels
    c.setFont("Helvetica", 12)
    c.drawString(left_x, header_baseline_y, "Description")
    c.drawRightString(right_x, header_baseline_y, "Amount")

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

    c.save()
    print(f"✓ Saved: {os.path.abspath(PAGE1_PATH)}")

    c = canvas.Canvas(PAGE1_PATH, pagesize=letter)

    left_x = MARGIN_L
    right_x = MARGIN_R
    extension = PAGE_WIDTH * 0.05

    divider_y = PAGE1_BODY_TOP_Y
    header_baseline_y = divider_y + 14

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

    # Date/Bill To labels above header text, below logo
    date_label_y = header_baseline_y + 42
    billto_label_y = header_baseline_y + 22
    c.setFont("Helvetica", 11)
    c.drawString(left_x, date_label_y, "Date:")
    c.drawString(left_x, billto_label_y, "Bill To:")

    # Header labels
    c.setFont("Helvetica", 12)
    c.drawString(left_x, header_baseline_y, "Description")
    c.drawRightString(right_x, header_baseline_y, "Amount")

    # Single horizontal divider line
    c.setLineWidth(1)
    c.setStrokeColorRGB(0, 0, 0)
    c.line(left_x - extension, divider_y, right_x + extension, divider_y)

    # Vertical divider for Amount column
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
    c.saveState()
    c.setStrokeColorRGB(1, 0, 1)
    c.setLineWidth(3)
    margin_w = MARGIN_R - MARGIN_L
    margin_h = MARGIN_T - MARGIN_B
    c.rect(MARGIN_L, MARGIN_B, margin_w, margin_h)
    c.restoreState()

    c.save()
    print(f"✓ Saved: {os.path.abspath(PAGE1_PATH)}")

    c = canvas.Canvas(PAGE1_PATH, pagesize=letter)
    # --- Stable header anchors (single source of truth) ---
    left_x = 1 * inch
    right_x = PAGE_WIDTH - 1 * inch
    extension = PAGE_WIDTH * 0.05

    divider_y = PAGE1_BODY_TOP_Y                 # horizontal line Y
    header_baseline_y = divider_y + 14           # "Description"/"Amount" baseline

    # Date/Bill To labels above header text (no PAGE_HEIGHT math)
    date_label_y = header_baseline_y + 42
    billto_label_y = header_baseline_y + 22

    # Draw logo first (behind text)
    LEFT_PAD = -20
    TOP_PAD = -40
    logo_w = PAGE1_LOGO_WIDTH * 1.7
    logo = ImageReader(LOGO_PATH)
    iw, ih = logo.getSize()
    aspect = ih / iw
    logo_h = logo_w * aspect * 0.9  # reduce logo height by 10%
    logo_x = LEFT_PAD
    logo_y = PAGE_HEIGHT - TOP_PAD - logo_h
    c.drawImage(logo, logo_x, logo_y, width=logo_w, height=logo_h, mask='auto', preserveAspectRatio=True)

    # Draw Date / Bill To
    c.setFont("Helvetica", 11)
    c.drawString(MARGIN_L, date_label_y, "Date:")
    c.drawString(MARGIN_L, billto_label_y, "Bill To:")

    # Header labels
    c.setFont("Helvetica", 12)
    c.drawString(left_x, header_baseline_y, "Description")
    c.drawRightString(right_x, header_baseline_y, "Amount")

    # Single horizontal divider line
    c.setLineWidth(1)
    c.setStrokeColorRGB(0, 0, 0)
    c.line(left_x - extension, divider_y, right_x + extension, divider_y)

    # Vertical divider for Amount column (starts exactly at divider line)
    amount_divider_x = right_x - 70
    c.line(amount_divider_x, divider_y, amount_divider_x, 1 * inch)

    # =========================
    # FORCE-VISIBLE DEBUG GUIDES (TEMP)
    # =========================
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
    # Logo: top-left corner, anchored at debug label position
    LEFT_PAD = -20
    TOP_PAD = -40
    logo_w = PAGE1_LOGO_WIDTH * 1.7
    logo = ImageReader(LOGO_PATH)
    iw, ih = logo.getSize()
    aspect = ih / iw
    logo_h = logo_w * aspect * 0.9  # reduce logo height by 10%
    logo_x = LEFT_PAD
    logo_y = PAGE_HEIGHT - TOP_PAD - logo_h
    c.drawImage(logo, logo_x, logo_y, width=logo_w, height=logo_h, mask='auto', preserveAspectRatio=True)

    # (Removed earlier header label block; only the divider_y-derived block below remains)

    # Vertical divider line for Amount column
    table_nudge = 70  # move table block up by 70 pts
    logo_bottom = logo_y
    billto_y_for_divider = logo_bottom - 6 - 18
    divider_y = billto_y_for_divider - 0.55 * inch + table_nudge

    # Header layout using BODY_TOP_Y as anchor
    extension = PAGE_WIDTH * 0.05
    divider_y = PAGE1_BODY_TOP_Y
    header_baseline_y = divider_y + 14
    amount_line_top = divider_y
    amount_line_bottom = 1 * inch

    # Vertical line for Amount column
    c.setLineWidth(1)
    c.setStrokeColorRGB(0, 0, 0)
    c.line(right_x - 70, amount_line_top, right_x - 70, amount_line_bottom)

    # Header labels
    c.setFont("Helvetica", 12)
    c.drawString(left_x, header_baseline_y, "Description")
    c.drawRightString(right_x, header_baseline_y, "Amount")

    # Single horizontal divider line
    c.line(left_x - extension, divider_y, right_x + extension, divider_y)
    # BODY_TOP_Y line + label
    # Crosshair helper (no debug text labels at real label positions)
    def crosshair(cx, cy):
        c.setStrokeColorRGB(0.8, 0.1, 0.1)
        c.setLineWidth(0.7)
        c.line(cx-4, cy, cx+4, cy)
        c.line(cx, cy-4, cx, cy+4)
    # Logo anchor (removed: logo_top_y undefined in this logic)
    # crosshair(logo_x, logo_top_y)
    # Date label anchor (no text label)
    # crosshair(date_x, date_y)
    # Bill To label anchor (no text label)
    # crosshair(billto_x, billto_y)
    # Print computed values (points)
    print(f"logo_x={logo_x:.2f}  logo_w={logo_w:.2f}  logo_h={logo_h:.2f}")
    print(f"divider_y={divider_y:.2f}")
    print(f"BODY_TOP_Y={PAGE1_BODY_TOP_Y:.2f}")
    # Company contact block, all right-aligned
    right_x = PAGE_WIDTH - 1 * inch
    y = PAGE1_HEADER_TOP - 10  # Move text block down by 10 pts
    c.setFont('Helvetica-Bold', 14)
    c.drawRightString(right_x, y, "MPH Construction & Painting")
    c.setFont('Helvetica', 11)
    leading = 12  # pts, tighter line spacing (was 14)
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

    # (removed duplicate Date/Bill To label block)

    # (removed unnecessary top horizontal line under header/logo area)
    # BODY_TOP_Y constant visual (not rendered, just for dev reference)
    # c.setStrokeColorRGB(1,0,0); c.line(0, PAGE1_BODY_TOP_Y, PAGE_WIDTH, PAGE1_BODY_TOP_Y)

    c.save()

    print(f"✓ Saved: {os.path.abspath(PAGE1_PATH)}")

def generate_pg2():
    right_x = PAGE_WIDTH - 1 * inch
    c = canvas.Canvas(PAGE2_PATH, pagesize=letter)

    # =========================
    # FORCE-VISIBLE DEBUG GUIDES (TEMP)
    # =========================
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
