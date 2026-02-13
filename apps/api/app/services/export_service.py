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
        self.template_pg1_path = Path(__file__).parent.parent / "templates" / "mph-invoice-pg1.pdf"
        self.template_pg2_path = Path(__file__).parent.parent / "templates" / "mph-invoice-pg2.pdf"
    
    async def export_document(self, session_id: str, proposal_data: ProposalData, professional_text: str = "", format: str = "pdf", document_type: str = "proposal") -> Path:
        """Export proposal/invoice to PDF using MPH template"""
        output_path = file_manager.sessions_dir / session_id / f"{document_type}.{format}"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if format == "pdf":
            self._generate_pdf(session_id, proposal_data, professional_text, output_path, document_type=document_type)
        else:
            self._generate_text(proposal_data, output_path)
        return output_path
    
    def _generate_pdf(self, session_id: str, data: ProposalData, professional_text: str, output_path: Path, document_type: str = "proposal"):
        """Generate PDF by overlaying data onto MPH template, with header for proposal/invoice"""
        # Create overlay with proposal/invoice data
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)
        width, height = letter
        can.setFont("Helvetica-Bold", 18)
        # Header: INVOICE or PROPOSAL / ESTIMATE
        if document_type == "invoice":
            can.drawString(1.0 * inch, height - 1.0 * inch, "INVOICE")
        else:
            can.drawString(1.0 * inch, height - 1.0 * inch, "PROPOSAL / ESTIMATE")
        can.setFont("Helvetica", 12)
        # Date - right after "Date:" label
        can.drawString(1.5 * inch, height - 2.0 * inch, datetime.now().strftime('%m/%d/%Y'))
        # Bill To: Name
        if getattr(data, "client_name", None):
            can.drawString(1.5 * inch, height - 2.3 * inch, data.client_name)
        # Bill To: Address
        if getattr(data, "project_address", None):
            can.drawString(1.5 * inch, height - 2.5 * inch, data.project_address)
        # Invoice-specific fields
        if document_type == "invoice":
            if getattr(data, "invoice_number", None):
                can.drawString(5.5 * inch, height - 2.0 * inch, f"Invoice #: {data.invoice_number}")
            if getattr(data, "due_date", None):
                can.drawString(5.5 * inch, height - 2.3 * inch, f"Due: {data.due_date}")
        # Start position for content below headers
        left_margin = 1.0 * inch
        amount_column_x = 7.5 * inch
        y_position = height - 4.0 * inch
        bottom_margin = 1.5 * inch
        # Line Items
        if getattr(data, "line_items", None) and len(data.line_items) > 0:
            line_y = y_position
            can.setFont("Helvetica", 11)
            for idx, item in enumerate(data.line_items):
                if getattr(item, "description", None):
                    desc_text = item.description[:80]
                    can.drawString(left_margin, line_y, desc_text)
                if getattr(item, "amount", None):
                    can.drawRightString(amount_column_x, line_y, f"${item.amount:.2f}")
                line_y -= 0.25 * inch
                if idx > 15:
                    break
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
        if self.template_pg1_path.exists() and self.template_pg2_path.exists():
            overlay_pdf = PdfReader(packet)
            output = None
            if len(overlay_pdf.pages) > 0:
                output = PdfWriter(clone_from=self.template_pg1_path)
                page = output.pages[0]
                page.merge_page(overlay_pdf.pages[0])
            for i in range(1, len(overlay_pdf.pages)):
                if output is None:
                    output = PdfWriter(clone_from=self.template_pg2_path)
                else:
                    # For additional pages, clone template_pg2 and add
                    extra_writer = PdfWriter(clone_from=self.template_pg2_path)
                    output.add_page(extra_writer.pages[0])
                page = output.pages[-1]
                page.merge_page(overlay_pdf.pages[i])
            if output is not None:
                with open(output_path, "wb") as output_file:
                    output.write(output_file)
        else:
            with open(output_path, "wb") as output_file:
                output_file.write(packet.getvalue())
    
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
