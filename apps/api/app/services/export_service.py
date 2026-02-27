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
    @staticmethod
    def format_money(value) -> str:
        """
        Return money formatted with commas and 2 decimals, prefixed with '$'.
        Accepts: int/float/Decimal/str (like "1234.5" or "$1234.50").
        Returns: "$1,234.50". If value is None or empty, returns ''.
        """
        if value is None or value == "":
            return ""
        from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
        s = str(value).replace("$", "").replace(",", "").strip()
        try:
            num = Decimal(s)
        except (InvalidOperation, ValueError):
            return str(value)
        # Clamp to max allowed value for rendering
        max_amt = Decimal("999999.99")
        if abs(num) > max_amt:
            num = max_amt.copy_sign(num)
        num = num.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return f"${num:,.2f}"
    DESC_PAD_R = 36  # pts, right padding for description column (was 32, +4 for earlier wrap)
    AMT_PAD_R = 12  # pts, right padding for amount column
    DESC_AMT_GAP = 16  # pts, gap between description and amount text when amount exists (was 12, +4 for earlier wrap)
    def __init__(self):
        # No static template file; will generate dynamically
        pass
    
    async def export_document(self, session_id: str, proposal_data: ProposalData, professional_text: str = "", format: str = "pdf", document_type: str = "proposal") -> Path:
        """Export proposal/invoice to PDF using MPH template"""

        # --- STRESS TEST SESSION LOGIC ---
        import os
        if session_id.startswith("stress_test_"):
            # Inject deterministic edge-case line items for validation
            proposal_data = ProposalData(
                client_name="Stress Test Client",
                project_address="Stress Test Address",
                line_items=[
                    # A) Long description + normal amount
                    {"description": "Interior wall painting for all rooms, including ceilings, closets, and trim surfaces.", "amount": 12345.67},
                    # B) Long description + NO amount
                    {"description": "Description with no amount present to test divider-based wrap boundary behavior.", "amount": None},
                    # C) Very large (but valid) line item amount
                    {"description": "Large amount formatting test for comma insertion and width stability.", "amount": 99999.99},
                    # D) Short description + small amount
                    {"description": "Touch-up", "amount": 150.00},
                ],
                total=12345.67 + 99999.99 + 150.00,  # sum for realism
                invoice_number="INV-STRESS-TEST",
                due_date="02/28/2026",
                date=None
            )
        # --- END STRESS TEST SESSION LOGIC ---

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
        import logging
        logger = logging.getLogger("mphai")
        logger.info("PDF DEBUG line_items: %s", data.line_items)
        logger.info("PDF DEBUG total: %s", data.total)
        logger.info("PDF DEBUG professional_text: %s", professional_text)
        def wrap_text_to_width(text, font_name, font_size, max_width):
            from reportlab.pdfbase import pdfmetrics
            safe_width = max_width - 2  # internal buffer to prevent borderline overflow
            words = text.split()
            lines = []
            current_line = ""
            for word in words:
                test_line = (current_line + " " + word).strip() if current_line else word
                if pdfmetrics.stringWidth(test_line, font_name, font_size) <= safe_width:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    # If the word itself is too long, hard-split it
                    while pdfmetrics.stringWidth(word, font_name, font_size) > safe_width:
                        for i in range(1, len(word)+1):
                            if pdfmetrics.stringWidth(word[:i], font_name, font_size) > safe_width:
                                lines.append(word[:i-1])
                                word = word[i-1:]
                                break
                        else:
                            break
                    current_line = word
            if current_line:
                lines.append(current_line)
            # Post-pass: guarantee all lines <= safe_width
            i = 0
            while i < len(lines):
                line = lines[i]
                while pdfmetrics.stringWidth(line, font_name, font_size) > safe_width and ' ' in line:
                    words = line.split()
                    if len(words) == 1:
                        break
                    last_word = words.pop()
                    lines[i] = ' '.join(words)
                    if i+1 < len(lines):
                        lines[i+1] = last_word + ' ' + lines[i+1]
                    else:
                        lines.append(last_word)
                    line = lines[i]
                i += 1
            return [l for l in lines if l.strip()]
        import os
        debug = os.environ.get("STRESS_TEST_DEBUG", "0") == "1"
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
        pg1_pos = compute_pg1_layout_positions()  # SINGLE CALL
        # Single-source all anchors and paddings
        date_value_x = pg1_pos["date_value_x"]
        date_value_y = pg1_pos["date_value_y"]
        billto_value_x = pg1_pos["billto_value_x"]
        billto_value_y = pg1_pos["billto_value_y"]
        divider_x = pg1_pos["amount_divider_x"]
        amount_right_x = pg1_pos.get("amount_right_x") or pg1_pos.get("amount_value_x")
        items_start_y = pg1_pos.get("body_top_y") or pg1_pos.get("items_start_y") or pg1_pos.get("table_body_top_y")
        if debug:
            print(f"[DEBUG] Anchors: divider_x={divider_x:.2f} amount_right_x={amount_right_x:.2f} items_start_y={items_start_y:.2f}")

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
        # Use template anchor for line item start Y
        y_position = items_start_y
        if y_position is None:
            # Fallback to PAGE1_BODY_TOP_Y if not present in pg1_pos
            from app.templates.generate_invoice_templates import PAGE1_BODY_TOP_Y
            y_position = PAGE1_BODY_TOP_Y
        bottom_margin = 1.5 * inch
        # Line Items (with true wrapping)
        if getattr(data, "line_items", None) and len(data.line_items) > 0:
            line_y = y_position - 18  # increased visual offset for spacing below header
            font_name = "Helvetica"
            font_size = 11
            can.setFont(font_name, font_size)
            desc_left_x = left_margin
            line_leading = 0.20 * inch
            # --- Amount column max width logic ---
            MAX_LINE_ITEM_AMOUNT_STR = "$99,999.99"
            MAX_TOTAL_AMOUNT_STR = "$999,999.99"  # for totals if needed
            from reportlab.pdfbase import pdfmetrics
            max_line_amt_width = pdfmetrics.stringWidth(MAX_LINE_ITEM_AMOUNT_STR, font_name, font_size)
            amount_left_x_fixed = amount_right_x - max_line_amt_width
            for idx, item in enumerate(data.line_items):
                desc = item.get("description") if isinstance(item, dict) else getattr(item, "description", None)
                amount = item.get("amount") if isinstance(item, dict) else getattr(item, "amount", None)
                if desc:
                    desc_text = str(desc)
                    # --- Unified wrap boundary logic with fixed max amount width ---
                    if amount is not None:
                        # Clamp and warn if needed
                        from decimal import Decimal, InvalidOperation
                        try:
                            amt_val = Decimal(str(amount).replace("$", "").replace(",", "").strip())
                        except (InvalidOperation, ValueError):
                            amt_val = None
                        max_amt = Decimal("999999.99")
                        if amt_val is not None and abs(amt_val) > max_amt:
                            if debug:
                                print(f"[DEBUG][WARN] [row {idx}] amount {amt_val} exceeds max; clamped to {max_amt}")
                        amount_str = self.format_money(amount)
                        wrap_limit_x = amount_left_x_fixed - self.DESC_AMT_GAP  # second purple line
                        wrap_rule = "amount_rule"
                    else:
                        amount_str = ""
                        wrap_limit_x = divider_x - self.DESC_PAD_R
                        wrap_rule = "divider_rule"
                    desc_max_width = wrap_limit_x - desc_left_x
                    # Debug: draw magenta guide and print wrap info
                    if debug:
                        can.saveState()
                        # Draw amount_right_x (header/amount right edge)
                        can.setStrokeColorRGB(0.5, 0, 1)  # purple
                        can.setLineWidth(1)
                        can.line(amount_right_x, line_y + 20, amount_right_x, line_y - 80)
                        # Draw amount_left_x_fixed (first purple line)
                        can.setStrokeColorRGB(0.3, 0, 0.7)
                        can.setLineWidth(1)
                        can.line(amount_left_x_fixed, line_y + 20, amount_left_x_fixed, line_y - 80)
                        # Draw desc_wrap_limit_x (second purple line)
                        can.setStrokeColorRGB(1, 0, 1)  # magenta
                        can.setLineWidth(1)
                        can.line(wrap_limit_x, line_y + 20, wrap_limit_x, line_y - 80)
                        can.restoreState()
                        print(f"[DEBUG] [row {idx}] divider_x={divider_x:.2f} amount_right_x={amount_right_x:.2f} amount_left_x_fixed={amount_left_x_fixed:.2f} wrap_limit_x={wrap_limit_x:.2f} rule={wrap_rule} desc_left_x={desc_left_x:.2f} desc_max_width={desc_max_width:.2f}")
                    wrapped_lines = wrap_text_to_width(desc_text, font_name, font_size, desc_max_width)
                    for i, line in enumerate(wrapped_lines):
                        if line_y < bottom_margin + line_leading:
                            can.showPage()
                            can.setFont(font_name, font_size)
                            line_y = y_position  # reset to body start, not header
                        can.setFont(font_name, font_size)
                        can.drawString(desc_left_x, line_y, line)
                        if debug and i == 0:
                            line_width = pdfmetrics.stringWidth(line, font_name, font_size)
                            print(f"[DEBUG] [row {idx}] first_line_width={line_width:.2f}")
                        if i == 0 and amount_str:
                            can.drawRightString(amount_right_x, line_y, amount_str)
                        line_y -= line_leading
                else:
                    # Still decrement line_y for empty description
                    line_y -= line_leading
        # Reset for content area
        y_position = height - 3.5 * inch if not (getattr(data, "line_items", None) and len(data.line_items) > 0) else line_y - 0.3 * inch
        can.setFont("Helvetica", 12)
        if professional_text:
            import re
            paragraphs = professional_text.strip().split('\n\n')
            money_cents_re = re.compile(r'(\$?\d{1,3}(?:,\d{3})*\.\d{2})')
            money_whole_re = re.compile(r'(\$?\d{1,3}(?:,\d{3})*)\b(?!\.)')
            amount_only_re = re.compile(r'^\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?$')
            for paragraph in paragraphs:
                if not paragraph.strip():
                    continue
                if y_position < bottom_margin + 30:
                    can.showPage()
                    y_position = height - 1.5 * inch
                    can.setFont("Helvetica", 12)
                lines = paragraph.strip().split('\n')
                # Build cleaned_lines for index tracking
                cleaned_lines = []
                for line in lines:
                    raw = line
                    line = line.strip()
                    lower = line.lower()
                    if line.startswith("Session:") or lower.startswith("session:"):
                        continue
                    if line.startswith("PROPOSAL (FALLBACK)"):
                        continue
                    if any(s in lower for s in ["here is the transcribed", "transcribed handwritten", "from the image", "```"]):
                        continue
                    if line.startswith("---"):
                        continue
                    import re
                    if re.match(r"^page\s*\d*$", line, re.I):
                        continue
                    if line.lower() == "invoice":
                        continue
                    line = line.replace("**", "").replace("`", "")
                    line = line.replace("\\", "")
                    if line.startswith("* "):
                        line = "• " + line[2:].strip()
                    line = ' '.join(line.split())
                    line = line.strip()
                    if not line:
                        continue
                    # Suppress standalone 1–2 digit lines (no $)
                    if re.fullmatch(r"\d{1,2}", line) and "$" not in line:
                        continue
                    if re.match(r"^\d{1,3}$", line):
                        continue
                    cleaned_lines.append(line)
                in_orphan_amount_block = False
                for idx, line in enumerate(cleaned_lines):
                    raw = line
                    raw_has_dollar = ("$" in raw)
                    lower = line.lower()
                    if line.lower() == "amount":
                        in_orphan_amount_block = True
                        continue
                    if in_orphan_amount_block:
                        if amount_only_re.match(line):
                            continue
                        elif line:
                            in_orphan_amount_block = False
                    # Universal money detection: accept if line contains $ or matches regex
                    money_accept_re = re.compile(r"\b\d{3,6}(?:,\d{3})?(?:\.\d{2})?\b")
                    phone_re = re.compile(r"\b\d{3}[- ]?\d{3}[- ]?\d{4}\b")
                    zip_re = re.compile(r"\b\d{5}(?:-\d{4})?\b")
                    street_re = re.compile(r"\d{1,5} [A-Za-z]+( St| Ave| Rd| Blvd| Dr| Ln| Ct| Pl| Way| Pkwy| Cir)\b")
                    # Standalone 1–2 digits
                    if re.fullmatch(r"\d{1,2}", line):
                        pass  # reject
                    # Phone pattern
                    elif phone_re.search(line):
                        pass  # reject
                    # Zip pattern
                    elif zip_re.search(line):
                        pass  # reject
                    # Street pattern
                    elif street_re.search(line):
                        pass  # reject
                    # Accept money if $ or money_accept_re
                    elif ("$" in line or money_accept_re.search(line)):
                        money_match = money_cents_re.search(line)
                        money_is_whole = False
                        if not money_match:
                            has_letters = any(ch.isalpha() for ch in line)
                            if has_letters:
                                money_match = money_whole_re.search(line)
                                money_is_whole = bool(money_match)
                        if money_match:
                            amount_text = money_match.group(1)
                            label_text = line[:money_match.start()].rstrip(" :\t")
                            if not amount_text.startswith("$"):
                                amount_text = "$" + amount_text
                            if money_is_whole and "." not in amount_text:
                                amount_text = amount_text + ".00"
                            # If this is the last cleaned line and amount-only, label as Total
                            if amount_only_re.match(line) and idx == len(cleaned_lines) - 1:
                                label_text = "Total"
                            prof_font_name = "Helvetica"
                            prof_font_size = 12
                            desc_max_width = divider_x - left_margin - self.DESC_PAD_R
                            wrapped_label_lines = wrap_text_to_width(label_text, prof_font_name, prof_font_size, desc_max_width)
                            first_line = True
                            for wrapped_line in wrapped_label_lines or [""]:
                                if y_position < bottom_margin + 30:
                                    can.showPage()
                                    y_position = height - 1.5 * inch
                                    can.setFont(prof_font_name, prof_font_size)
                                can.drawString(left_margin, y_position, wrapped_line)
                                if first_line:
                                    can.drawRightString(amount_right_x - self.AMT_PAD_R, y_position, amount_text)
                                    first_line = False
                                y_position -= 15
                            continue
                    # Bullets for real lists
                    if line.startswith('-') or line.startswith('•'):
                        line = '• ' + line.lstrip('-•').strip()
                    prof_font_name = "Helvetica"
                    prof_font_size = 12
                    prof_max_width = divider_x - left_margin - self.DESC_PAD_R
                    wrapped_prof_lines = wrap_text_to_width(line, prof_font_name, prof_font_size, prof_max_width)
                    for wrapped_line in wrapped_prof_lines:
                        if y_position < bottom_margin + 30:
                            can.showPage()
                            y_position = height - 1.5 * inch
                            can.setFont(prof_font_name, prof_font_size)
                        can.drawString(left_margin, y_position, wrapped_line)
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
        import re
        range_re = re.compile(r"\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?\s*[-–]\s*\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?")
        money_cents_re = re.compile(r"\$?\d{1,3}(?:,\d{3})*\.\d{2}")
        money_whole_re = re.compile(r"\$?\d{1,3}(?:,\d{3})*\b(?!\.)")
        money_label_re = re.compile(r"\b(cost|subtotal|total|grand total|overhead|profit)\b", re.I)
        min_total = 0.0
        max_total = 0.0
        found_range = False
        found_money = False
        total_amount = getattr(data, "total", 0) or 0
        line_items = getattr(data, "line_items", None)
        if line_items and len(line_items) > 0:
            total_display = f"${total_amount:,.2f}"
        else:
            if professional_text:
                paragraphs = professional_text.strip().split('\n\n')
                for paragraph in paragraphs:
                    lines = paragraph.strip().split('\n')
                    for line in lines:
                        line = line.strip()
                        if not line:
                            continue
                        is_moneyish = ("$" in line) or money_label_re.search(line.lower()) or ("—" in line)
                        # Range detection
                        range_match = range_re.search(line)
                        if range_match and is_moneyish:
                            found_range = True
                            found_money = True
                            amounts = []
                            cents_tokens = money_cents_re.findall(line)
                            if len(cents_tokens) >= 2:
                                amounts = cents_tokens
                            else:
                                whole_tokens = money_whole_re.findall(line)
                                if len(whole_tokens) >= 2:
                                    amounts = whole_tokens
                            if len(amounts) >= 2:
                                amt1 = float(amounts[0].replace('$','').replace(',',''))
                                amt2 = float(amounts[1].replace('$','').replace(',',''))
                                min_total += amt1
                                max_total += amt2
                            continue
                        # Single money line
                        money_match = money_cents_re.search(line)
                        if not money_match and is_moneyish:
                            money_match = money_whole_re.search(line)
                        if money_match and is_moneyish:
                            found_money = True
                            amt = float(money_match.group(0).replace('$','').replace(',',''))
                            min_total += amt
                            max_total += amt
            if not found_money:
                total_display = "TO BE DETERMINED"
            elif found_range:
                total_display = f"${min_total:,.2f} – ${max_total:,.2f}"
            else:
                total_display = f"${min_total:,.2f}"
        can.setFont("Helvetica-Bold", 14)
        can.drawString(5.5 * inch, 1 * inch, "Total:")
        can.drawRightString(amount_right_x - self.AMT_PAD_R, 1 * inch, total_display)
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
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_template_pg1:
            with open(generate_invoice_templates.PAGE1_PATH, "rb") as fsrc:
                tmp_template_pg1.write(fsrc.read())
            tmp_template_pg1.flush()
            tmp_template_path_pg1 = tmp_template_pg1.name
        # Try to create PAGE2_PATH, fallback to PAGE1_PATH if missing
        import os
        if os.path.exists(generate_invoice_templates.PAGE2_PATH):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_template_pg2:
                with open(generate_invoice_templates.PAGE2_PATH, "rb") as fsrc:
                    tmp_template_pg2.write(fsrc.read())
                tmp_template_pg2.flush()
                tmp_template_path_pg2 = tmp_template_pg2.name
        else:
            tmp_template_path_pg2 = tmp_template_path_pg1
        overlay_pdf = PdfReader(packet)
        output = None
        if len(overlay_pdf.pages) > 0:
            output = PdfWriter(clone_from=tmp_template_path_pg1)
            page = output.pages[0]
            page.merge_page(overlay_pdf.pages[0])
        for i in range(1, len(overlay_pdf.pages)):
            if output is None:
                output = PdfWriter(clone_from=tmp_template_path_pg1)
            else:
                extra_writer = PdfWriter(clone_from=tmp_template_path_pg2)
                output.add_page(extra_writer.pages[0])
            page = output.pages[-1]
            page.merge_page(overlay_pdf.pages[i])
        if output is not None:
            with open(output_path, "wb") as output_file:
                output.write(output_file)
                # INFO log for PDF written
                import logging, os
                logger = logging.getLogger("mphai")
                logger.info(
                    "proposal_pdf_written",
                    extra={
                        "session_id": session_id,
                        "pdf_path": str(output_path),
                        "size_bytes": os.path.getsize(output_path)
                    }
                )
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
                # INFO log for PDF written
                import logging, os
                logger = logging.getLogger("mphai")
                logger.info(
                    "proposal_pdf_written",
                    extra={
                        "session_id": session_id,
                        "pdf_path": str(output_path),
                        "size_bytes": os.path.getsize(output_path)
                    }
                )
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
