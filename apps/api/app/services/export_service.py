from pathlib import Path
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from pypdf import PdfWriter, PdfReader
import io
from app.models.schemas import ProposalData
from app.storage.file_manager import FileManager

file_manager = FileManager()


class ExportService:
    def __init__(self):
        # No static template file; will generate dynamically
        pass
    
    async def export_document(self, session_id: str, proposal_data: ProposalData, professional_text: str = "", format: str = "pdf", document_type: str = "proposal") -> Path:
        """Export proposal/invoice to PDF using MPH template"""

        # --- TEMP STRESS TEST DATA ---
        import os
        is_stress = session_id.startswith("stress_test_") or os.environ.get("STRESS_TEST_DEBUG", "0") == "1"
        if is_stress:
            proposal_data = ProposalData(
                client_name="Jonathan A. Richardson III",
                project_address="12345 South Evergreen Terrace, Unit 204B",
                line_items=[
                    {"description": "Interior wall painting for all rooms, including ceilings, closets, and all trim surfaces. This description is intentionally long to test truncation at 80 characters.", "amount": 12345.67},
                    {"description": "Exterior deck staining", "amount": 850.00},
                    {"description": "Garage floor epoxy coating", "amount": 2250.00},
                    {"description": "Window caulking and sealing", "amount": 350.00},
                ],
                total=18950.75,
                invoice_number="INV-2026-001",
                due_date="02/28/2026",
                date=None  # forces fallback to today
            )
        # --- END TEMP STRESS TEST DATA ---

        output_path = file_manager.sessions_dir / session_id / f"{document_type}.{format}"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if format == "pdf":
            self._generate_pdf(session_id, proposal_data, professional_text, output_path, document_type=document_type)
        else:
            self._generate_text(proposal_data, output_path)
        return output_path
    
    def _generate_pdf(self, session_id: str, data: ProposalData, professional_text: str, output_path: Path, document_type: str = "proposal"):
        """Generate PDF by overlaying data onto MPH template, with header for proposal/invoice
        If STRESS_TEST_DEBUG=1 and session_id=="STRESS_TEST", also write overlay-only and template-only PDFs for inspection.
        """
        def wrap_text_to_width(text, font_name, font_size, max_width):
            from reportlab.pdfbase import pdfmetrics
            words = text.split()
            lines = []
            current_line = ""
            for word in words:
                test_line = (current_line + " " + word).strip() if current_line else word
                if pdfmetrics.stringWidth(test_line, font_name, font_size) <= max_width:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    # If the word itself is too long, hard-split it
                    while pdfmetrics.stringWidth(word, font_name, font_size) > max_width:
                        for i in range(1, len(word)+1):
                            if pdfmetrics.stringWidth(word[:i], font_name, font_size) > max_width:
                                lines.append(word[:i-1])
                                word = word[i-1:]
                                break
                        else:
                            break
                    current_line = word
            if current_line:
                lines.append(current_line)
            return lines
        import os
        debug = session_id.startswith("stress_test_") or os.environ.get("STRESS_TEST_DEBUG", "0") == "1"
        # Create overlay with proposal/invoice data
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)
        width, height = letter
        # (Header already present in template; do not draw again)
        # Optional overlay marker for debug
        if debug:
            can.setFont("Helvetica-Bold", 10)
            can.setFillColorRGB(1, 0, 0)
            can.drawString(60, height - 30, "OVERLAY TEST")
            can.setFillColorRGB(0, 0, 0)

        # --- Overlay dynamic values next to static labels ---
        label_font = "Helvetica"
        label_size = 11
        can.setFont(label_font, label_size)
        # Use template-derived coordinates for Date/Bill To values
        from app.templates.generate_invoice_templates import compute_pg1_layout_positions
        pg1_pos = compute_pg1_layout_positions()
        date_value_x = pg1_pos["date_value_x"]
        date_value_y = pg1_pos["date_value_y"]
        billto_value_x = pg1_pos["billto_value_x"]
        billto_value_y = pg1_pos["billto_value_y"]
        if debug:
            print(f"[DEBUG] Overlay X: date_value_x={date_value_x:.2f} billto_value_x={billto_value_x:.2f}")

        # Date value (from data or fallback to today)
        date_val = getattr(data, "date", None)
        if not date_val:
            date_val = datetime.now().strftime('%m/%d/%Y')
        can.drawString(date_value_x, date_value_y, str(date_val))

        # Bill To: Name (required) and Address (multi-line, match template spacing)
        from app.templates.generate_invoice_templates import PG1_BILLTO_LINE_HEIGHT
        billto_lines = []
        client_name = getattr(data, "client_name", None)
        if client_name:
            billto_lines.append(client_name)
        else:
            billto_lines.append("[Missing client name]")
        project_address = getattr(data, "project_address", None)
        if project_address:
            billto_lines.append(project_address)
        else:
            billto_lines.append("[Missing address]")
        if debug:
            print(f"[DEBUG] BillTo Overlay: date=({date_value_x:.2f},{date_value_y:.2f}) billto=({billto_value_x:.2f},{billto_value_y:.2f}) line_spacing={PG1_BILLTO_LINE_HEIGHT} n_lines={len(billto_lines)} lines={[repr(l) for l in billto_lines[:2]]}")
        for i, line in enumerate(billto_lines):
            y = billto_value_y - i * PG1_BILLTO_LINE_HEIGHT
            if "[Missing" in line:
                can.setFillColorRGB(0.7, 0.1, 0.1)
            can.drawString(billto_value_x, y, line)
            if debug and i == 0:
                can.setFont("Helvetica", 7)
                can.setFillColorRGB(0.2, 0.2, 0.8)
                can.drawString(billto_value_x + 180, y + 2, f"BILLTO y={y:.2f}")
                can.setFont(label_font, label_size)
                can.setFillColorRGB(0, 0, 0)
            elif "[Missing" in line:
                can.setFillColorRGB(0, 0, 0)

        # Invoice-specific fields (right side, unchanged)
        if document_type == "invoice":
            if getattr(data, "invoice_number", None):
                can.drawString(5.5 * inch, height - 2.0 * inch, f"Invoice #: {data.invoice_number}")
            if getattr(data, "due_date", None):
                can.drawString(5.5 * inch, height - 2.3 * inch, f"Due: {data.due_date}")
        # Start position for content below headers
        left_margin = 1.0 * inch
        amount_column_x = 7.5 * inch
        # Use template anchor for divider X
        from app.templates.generate_invoice_templates import compute_pg1_layout_positions
        pg1_pos = compute_pg1_layout_positions()
        divider_x = pg1_pos.get("amount_divider_x", amount_column_x - 8)  # fallback for legacy
        gutter = 6  # pts, minimal gutter before divider
        y_position = height - 4.0 * inch
        bottom_margin = 1.5 * inch
        # Line Items (with true wrapping)
        if getattr(data, "line_items", None) and len(data.line_items) > 0:
            line_y = y_position
            font_name = "Helvetica"
            font_size = 11
            can.setFont(font_name, font_size)
            desc_left_x = left_margin
            desc_max_width = divider_x - gutter - desc_left_x
            line_leading = 0.20 * inch
            for idx, item in enumerate(data.line_items):
                desc = item.get("description") if isinstance(item, dict) else getattr(item, "description", None)
                amount = item.get("amount") if isinstance(item, dict) else getattr(item, "amount", None)
                if desc:
                    desc_text = str(desc)
                    wrapped_lines = wrap_text_to_width(desc_text, font_name, font_size, desc_max_width)
                    for i, line in enumerate(wrapped_lines):
                        if line_y < bottom_margin + line_leading:
                            can.showPage()
                            can.setFont(font_name, font_size)
                            line_y = y_position  # reset to body start, not header
                        can.drawString(desc_left_x, line_y, line)
                        if i == 0 and amount is not None:
                            can.drawRightString(amount_column_x, line_y, f"${amount:.2f}")
                        line_y -= line_leading
                else:
                    # Still decrement line_y for empty description
                    line_y -= line_leading
                # Remove idx > 15 break; rely on page breaks
        # Reset for content area
        y_position = height - 3.5 * inch if not (getattr(data, "line_items", None) and len(data.line_items) > 0) else line_y - 0.3 * inch
        can.setFont("Helvetica", 12)
        if professional_text:
            paragraphs = professional_text.strip().split('\n\n')
            for paragraph in paragraphs:
                if not paragraph.strip():
                    continue
                if y_position < bottom_margin + 30:
                    can.showPage()
                    y_position = height - 1.5 * inch
                    can.setFont("Helvetica", 12)
                lines = paragraph.strip().split('\n')
                for line in lines:
                    text = line.strip()
                    if not text:
                        continue
                    if text.startswith('-') or text.startswith('•'):
                        text = '• ' + text.lstrip('-•').strip()
                    elif len(lines) > 1 and not text.endswith(':'):
                        text = '• ' + text
                    if len(text) > 75:
                        words = text.split()
                        current_line = ""
                        for word in words:
                            if len(current_line + word) < 75:
                                current_line += word + " "
                            else:
                                if y_position < bottom_margin + 30:
                                    can.showPage()
                                    y_position = height - 1.5 * inch
                                    can.setFont("Helvetica", 12)
                                can.drawString(left_margin, y_position, current_line.strip())
                                y_position -= 15
                                current_line = "  " + word + " "
                        if current_line.strip():
                            if y_position < bottom_margin + 30:
                                can.showPage()
                                y_position = height - 1.5 * inch
                                can.setFont("Helvetica", 12)
                            can.drawString(left_margin, y_position, current_line.strip())
                            y_position -= 15
                    else:
                        can.drawString(left_margin, y_position, text)
                        y_position -= 15
                y_position -= 5
        # Timeline (proposal only)
        if document_type == "proposal" and getattr(data, "timeline", None):
            y_position -= 10
            if y_position < bottom_margin + 30:
                can.showPage()
                y_position = height - 1.5 * inch
            can.setFont("Helvetica-Bold", 12)
            can.drawString(left_margin, y_position, "Timeline:")
            y_position -= 18
            can.setFont("Helvetica", 12)
            words = data.timeline.split()
            line = ""
            for word in words:
                if len(line + word) < 75:
                    line += word + " "
                else:
                    if y_position < bottom_margin + 30:
                        can.showPage()
                        y_position = height - 1.5 * inch
                        can.setFont("Helvetica", 12)
                    can.drawString(left_margin, y_position, line.strip())
                    y_position -= 15
                    line = word + " "
            if line.strip():
                can.drawString(left_margin, y_position, line.strip())
                y_position -= 15
            y_position -= 10
        # Notes
        if getattr(data, "notes", None):
            y_position -= 10
            if y_position < bottom_margin + 50:
                can.showPage()
                y_position = height - 1.5 * inch
            can.setFont("Helvetica", 12)
            notes_lines = data.notes.split('\n')
            for note_line in notes_lines:
                if not note_line.strip():
                    continue
                if y_position < bottom_margin + 30:
                    can.showPage()
                    y_position = height - 1.5 * inch
                    can.setFont("Helvetica", 12)
                words = note_line.split()
                current_line = ""
                for word in words:
                    if len(current_line + word) < 75:
                        current_line += word + " "
                    else:
                        can.drawString(left_margin, y_position, current_line.strip())
                        y_position -= 15
                        current_line = word + " "
                        if y_position < bottom_margin + 30:
                            can.showPage()
                            y_position = height - 1.5 * inch
                            can.setFont("Helvetica", 12)
                if current_line.strip():
                    can.drawString(left_margin, y_position, current_line.strip())
                    y_position -= 15
        # Add Total at the bottom
        total_amount = getattr(data, "total", 0) or 0
        can.setFont("Helvetica-Bold", 14)
        can.drawString(5.5 * inch, 1 * inch, "Total:")
        can.drawRightString(amount_column_x, 1 * inch, f"${total_amount:.2f}")
        can.save()
        packet.seek(0)
        # Merge with template if it exists
        from app.templates import generate_invoice_templates
        import tempfile
        import os
        # Debug: print generator module path
        if debug:
            print("TEMPLATE GENERATOR MODULE:", generate_invoice_templates.__file__)
        # Dynamically generate the finalized template PDF (Page 1)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_template:
            generate_invoice_templates.generate_pg1()
            # Copy the freshly generated template to the temp file
            with open(generate_invoice_templates.PAGE1_PATH, "rb") as fsrc:
                tmp_template.write(fsrc.read())
            tmp_template.flush()
            tmp_template_path = tmp_template.name
        overlay_pdf = PdfReader(packet)
        output = None
        if len(overlay_pdf.pages) > 0:
            output = PdfWriter(clone_from=tmp_template_path)
            page = output.pages[0]
            page.merge_page(overlay_pdf.pages[0])
        for i in range(1, len(overlay_pdf.pages)):
            if output is None:
                output = PdfWriter(clone_from=tmp_template_path)
            else:
                extra_writer = PdfWriter(clone_from=tmp_template_path)
                output.add_page(extra_writer.pages[0])
            page = output.pages[-1]
            page.merge_page(overlay_pdf.pages[i])
        if output is not None:
            with open(output_path, "wb") as output_file:
                output.write(output_file)
            if debug:
                session_dir = output_path.parent
                overlay_path = session_dir / "invoice_overlay.pdf"
                template_path = session_dir / "invoice_template.pdf"
                # Write overlay-only
                with open(overlay_path, "wb") as f:
                    f.write(packet.getvalue())
                # Copy freshly generated template
                with open(tmp_template_path, "rb") as fsrc, open(template_path, "wb") as fdst:
                    fdst.write(fsrc.read())
                for p in [template_path, overlay_path, output_path]:
                    print(f"PDF: {os.path.abspath(p)} | Size: {os.path.getsize(p)} bytes")
        else:
            with open(output_path, "wb") as output_file:
                output_file.write(packet.getvalue())
            if debug:
                session_dir = output_path.parent
                overlay_path = session_dir / "invoice_overlay.pdf"
                template_path = session_dir / "invoice_template.pdf"
                with open(overlay_path, "wb") as f:
                    f.write(packet.getvalue())
                # Copy freshly generated template
                with open(tmp_template_path, "rb") as fsrc, open(template_path, "wb") as fdst:
                    fdst.write(fsrc.read())
                for p in [template_path, overlay_path, output_path]:
                    print(f"PDF: {os.path.abspath(p)} | Size: {os.path.getsize(p)} bytes")
    
    def _generate_text(self, data: ProposalData, output_path: Path):
        """Fallback text format"""
        with open(output_path, "w") as f:
            f.write(f"CONSTRUCTION PROPOSAL\n\n")
            f.write(f"Client: {data.client_name or 'N/A'}\n")
            f.write(f"Project Address: {data.project_address or 'N/A'}\n\n")
            f.write(f"SCOPE OF WORK:\n")
            for item in data.scope_of_work or []:
                f.write(f"- {item}\n")
            f.write(f"\nTOTAL: ${data.total or 0:.2f}\n")
