"""Test script to visualize PDF positioning"""
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from pypdf import PdfWriter, PdfReader
from pathlib import Path
import io

# Create overlay with grid and test text
packet = io.BytesIO()
can = canvas.Canvas(packet, pagesize=letter)
width, height = letter

# Draw bold grid lines every 0.5 inch with labels
can.setStrokeColorRGB(0, 0, 1)  # Blue
can.setLineWidth(2)
can.setFont("Helvetica-Bold", 10)

# Vertical lines
for i in range(0, int(width/inch) + 1):
    x = i * inch
    can.line(x, 0, x, height)
    # Label at top
    can.setFillColorRGB(0, 0, 1)
    can.drawString(x + 5, height - 30, f"{i}\" →")

# Horizontal lines (from top)
for i in range(0, int(height/inch) + 1):
    y = height - (i * inch)
    can.line(0, y, width, y)
    # Label at left
    can.drawString(10, y + 5, f"↓ {i}\"")

# Test positioning
can.setStrokeColorRGB(1, 0, 0)
can.setFont("Helvetica", 12)

# Date position
can.setFillColorRGB(1, 0, 0)
can.drawString(0.75 * inch, height - 1.95 * inch, "DATE: 01/19/2026")

# Name position  
can.drawString(0.75 * inch, height - 2.25 * inch, "Bill To: John Smith")

# Address position
can.drawString(0.75 * inch, height - 2.48 * inch, "123 Main Street, Denver CO")

# Description area
can.drawString(0.75 * inch, height - 4.2 * inch, "Description test text that should fit in left box")

# Amount area
can.drawRightString(7.5 * inch, height - 4.2 * inch, "$1,500.00")

can.save()
packet.seek(0)

# Merge with template
template_path = Path(__file__).parent / "app" / "templates" / "mph-invoice-pg1.pdf"
output_path = Path(__file__).parent / "test_output.pdf"

if template_path.exists():
    overlay_pdf = PdfReader(packet)
    output = PdfWriter(clone_from=template_path)
    output.pages[0].merge_page(overlay_pdf.pages[0])
    with open(output_path, "wb") as output_file:
        output.write(output_file)
    print(f"Test PDF created: {output_path}")
    print("Open it to see grid lines and test positioning")
else:
    print(f"Template not found: {template_path}")
