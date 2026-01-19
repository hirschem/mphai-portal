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
        self.template_path = Path(__file__).parent.parent / "templates" / "mph-invoice.pdf"
    
    async def export_document(self, session_id: str, proposal_data: ProposalData, format: str = "pdf") -> Path:
        """Export proposal to PDF using MPH invoice template"""
        
        output_path = file_manager.sessions_dir / session_id / f"proposal.{format}"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format == "pdf":
            self._generate_pdf(session_id, proposal_data, output_path)
        else:
            # Fallback to text format
            self._generate_text(proposal_data, output_path)
        
        return output_path
    
    def _generate_pdf(self, session_id: str, data: ProposalData, output_path: Path):
        """Generate PDF by overlaying data onto MPH template"""
        
        # Create overlay with proposal data
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)
        width, height = letter
        
        # Set font
        can.setFont("Helvetica", 10)
        
        # Position data on template (adjust these positions based on your template)
        y_position = height - 2.5 * inch  # Start below header
        bottom_margin = 1 * inch  # Stop before bottom of page
        
        # Client Information
        if data.client_name:
            can.setFont("Helvetica-Bold", 11)
            can.drawString(1 * inch, y_position, "BILL TO:")
            can.setFont("Helvetica", 10)
            can.drawString(1 * inch, y_position - 15, data.client_name)
            y_position -= 30
        
        if data.project_address:
            can.drawString(1 * inch, y_position, data.project_address)
            y_position -= 30
        
        # Date and Invoice Number
        can.setFont("Helvetica", 9)
        can.drawRightString(width - 1 * inch, height - 2.5 * inch, f"Date: {datetime.now().strftime('%B %d, %Y')}")
        can.drawRightString(width - 1 * inch, height - 2.7 * inch, f"Invoice #: {session_id[:8].upper()}")
        
        y_position -= 20
        
        # Scope of Work
        if data.scope_of_work:
            can.setFont("Helvetica-Bold", 11)
            can.drawString(1 * inch, y_position, "SCOPE OF WORK")
            y_position -= 20
            
            can.setFont("Helvetica", 10)
            for item in data.scope_of_work:
                # Check if we need a new page
                if y_position < bottom_margin + 30:
                    can.showPage()
                    y_position = height - 1 * inch
                    can.setFont("Helvetica", 10)
                
                # Wrap long text
                if len(item) > 80:
                    words = item.split()
                    line = ""
                    for word in words:
                        if len(line + word) < 80:
                            line += word + " "
                        else:
                            if y_position < bottom_margin + 30:
                                can.showPage()
                                y_position = height - 1 * inch
                                can.setFont("Helvetica", 10)
                            can.drawString(1.2 * inch, y_position, "• " + line.strip())
                            y_position -= 15
                            line = word + " "
                    if line:
                        if y_position < bottom_margin + 30:
                            can.showPage()
                            y_position = height - 1 * inch
                            can.setFont("Helvetica", 10)
                        can.drawString(1.2 * inch, y_position, "• " + line.strip())
                        y_position -= 15
                else:
                    can.drawString(1.2 * inch, y_position, "• " + item)
                    y_position -= 15
            
            y_position -= 10
        
        # Line Items Table
        if data.line_items:
            # Check if we need a new page
            if y_position < bottom_margin + 100:
                can.showPage()
                y_position = height - 1 * inch
            
            y_position -= 20
            can.setFont("Helvetica-Bold", 10)
            can.drawString(1 * inch, y_position, "Description")
            can.drawString(4.5 * inch, y_position, "Qty")
            can.drawString(5.2 * inch, y_position, "Rate")
            can.drawString(6.2 * inch, y_position, "Amount")
            y_position -= 5
            
            # Draw line
            can.line(1 * inch, y_position, width - 1 * inch, y_position)
            y_position -= 15
            
            can.setFont("Helvetica", 9)
            for item in data.line_items:
                # Check if we need a new page
                if y_position < bottom_margin + 30:
                    can.showPage()
                    y_position = height - 1 * inch
                    can.setFont("Helvetica", 9)
                
                can.drawString(1 * inch, y_position, item.description or "")
                if item.quantity:
                    can.drawString(4.5 * inch, y_position, str(item.quantity))
                if item.rate:
                    can.drawString(5.2 * inch, y_position, f"${item.rate:.2f}")
                if item.amount:
                    can.drawRightString(width - 1 * inch, y_position, f"${item.amount:.2f}")
                y_position -= 15
        
        # Totals
        y_position -= 20
        can.setFont("Helvetica-Bold", 10)
        
        if data.subtotal:
            can.drawString(5.5 * inch, y_position, "Subtotal:")
            can.drawRightString(width - 1 * inch, y_position, f"${data.subtotal:.2f}")
            y_position -= 15
        
        if data.tax:
            can.drawString(5.5 * inch, y_position, "Tax:")
            can.drawRightString(width - 1 * inch, y_position, f"${data.tax:.2f}")
            y_position -= 15
        
        if data.total:
            can.setFont("Helvetica-Bold", 12)
            can.drawString(5.5 * inch, y_position, "TOTAL:")
            can.drawRightString(width - 1 * inch, y_position, f"${data.total:.2f}")
            y_position -= 30
        
        # Payment Terms
        if data.payment_terms:
            can.setFont("Helvetica-Bold", 10)
            can.drawString(1 * inch, y_position, "Payment Terms:")
            y_position -= 15
            can.setFont("Helvetica", 9)
            can.drawString(1 * inch, y_position, data.payment_terms)
            y_position -= 20
        
        # Timeline
        if data.timeline:
            can.setFont("Helvetica-Bold", 10)
            can.drawString(1 * inch, y_position, "Timeline:")
            y_position -= 15
            can.setFont("Helvetica", 9)
            can.drawString(1 * inch, y_position, data.timeline)
            y_position -= 20
        
        # Notes
        if data.notes:
            # Check if we need a new page
            if y_position < bottom_margin + 50:
                can.showPage()
                y_position = height - 1 * inch
            
            can.setFont("Helvetica-Bold", 10)
            can.drawString(1 * inch, y_position, "Notes:")
            y_position -= 15
            can.setFont("Helvetica", 9)
            # Wrap notes text
            notes_lines = data.notes.split('\n')
            for line in notes_lines:
                if y_position < bottom_margin + 30:
                    can.showPage()
                    y_position = height - 1 * inch
                    can.setFont("Helvetica", 9)
                
                if len(line) > 90:
                    words = line.split()
                    current_line = ""
                    for word in words:
                        if len(current_line + word) < 90:
                            current_line += word + " "
                        else:
                            if y_position < bottom_margin + 30:
                                can.showPage()
                                y_position = height - 1 * inch
                                can.setFont("Helvetica", 9)
                            can.drawString(1 * inch, y_position, current_line.strip())
                            y_position -= 12
                            current_line = word + " "
                    if current_line:
                        if y_position < bottom_margin + 30:
                            can.showPage()
                            y_position = height - 1 * inch
                            can.setFont("Helvetica", 9)
                        can.drawString(1 * inch, y_position, current_line.strip())
                        y_position -= 12
                else:
                    can.drawString(1 * inch, y_position, line)
                    y_position -= 12
        
        can.save()
        packet.seek(0)
        
        # Merge with template if it exists
        if self.template_path.exists():
            overlay_pdf = PdfReader(packet)
            template_pdf = PdfReader(self.template_path)
            output = PdfWriter()
            
            # First page: merge with template
            if len(overlay_pdf.pages) > 0:
                page = template_pdf.pages[0]
                page.merge_page(overlay_pdf.pages[0])
                output.add_page(page)
            
            # Additional pages: add as plain white pages (no template)
            for i in range(1, len(overlay_pdf.pages)):
                output.add_page(overlay_pdf.pages[i])
            
            # Write output
            with open(output_path, "wb") as output_file:
                output.write(output_file)
        else:
            # No template, just save overlay
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
