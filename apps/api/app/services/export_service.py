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
        can.setFont("Helvetica", 12)
        
        # Position data on template based on red line markings
        left_margin = 0.75 * inch  # Left edge for text
        max_text_width = 5.75 * inch  # Max width for description box (left red box)
        amount_x = 7.0 * inch  # Right column for amounts
        
        # Date - first red line
        can.setFont("Helvetica", 12)
        can.drawString(left_margin, height - 1.95 * inch, datetime.now().strftime('%m/%d/%Y'))
        
        # Bill To: Client name - second red line
        if data.client_name:
            can.setFont("Helvetica", 12)
            can.drawString(left_margin, height - 2.25 * inch, data.client_name)
        
        # Bill To: Address - third red line
        if data.project_address:
            can.setFont("Helvetica", 12)
            can.drawString(left_margin, height - 2.48 * inch, data.project_address)
        
        # Start position for description text (below the Bill To section)
        y_position = height - 3.5 * inch
        bottom_margin = 1.5 * inch
        
        # Line Items - place in template table if present
        if data.line_items and len(data.line_items) > 0:
            # Starting position for line items in template
            line_y = height - 4.2 * inch
            can.setFont("Helvetica", 11)
            
            for idx, item in enumerate(data.line_items):
                # Description in left red box
                if item.description:
                    # Wrap description to fit within max_text_width
                    desc_text = item.description[:80]  # Limit length
                    can.drawString(left_margin, line_y, desc_text)
                
                # Amount in right red box (right-aligned)
                if item.amount:
                    can.drawRightString(amount_x + 0.5 * inch, line_y, f"${item.amount:.2f}")
                
                line_y -= 0.25 * inch  # Move to next line
                
                # Check if we need a new page (template has limited rows)
                if idx > 15:  # Assuming ~16 rows per page
                    break
        
        # Reset for content area - professionally rewritten proposal text
        # Start below line items section
        y_position = height - 3.5 * inch if not (data.line_items and len(data.line_items) > 0) else line_y - 0.3 * inch
        
        # Content area - professionally rewritten proposal text (fits in left red box)
        can.setFont("Helvetica", 12)
        
        # Scope of Work
        if data.scope_of_work:
            for item in data.scope_of_work:
                # Check if we need a new page
                if y_position < bottom_margin + 30:
                    can.showPage()
                    y_position = height - 1.5 * inch
                    can.setFont("Helvetica", 12)
                
                # Wrap long text to fit within left red box max width
                if len(item) > 70:  # Adjusted for max_text_width
                    words = item.split()
                    line = ""
                    for word in words:
                        if len(line + word) < 70:
                            line += word + " "
                        else:
                            if y_position < bottom_margin + 30:
                                can.showPage()
                                y_position = height - 1.5 * inch
                                can.setFont("Helvetica", 12)
                            can.drawString(left_margin, y_position, line.strip())
                            y_position -= 15
                            line = word + " "
                    if line:
                        if y_position < bottom_margin + 30:
                            can.showPage()
                            y_position = height - 1.5 * inch
                            can.setFont("Helvetica", 12)
                        can.drawString(left_margin, y_position, line.strip())
                        y_position -= 15
                else:
                    can.drawString(left_margin, y_position, item)
                    y_position -= 15
            
            y_position -= 10
        
        # Payment Terms
        if data.payment_terms:
            if y_position < bottom_margin + 50:
                can.showPage()
                y_position = height - 1.5 * inch
            
            can.setFont("Helvetica", 12)
            # Wrap payment terms text
            if len(data.payment_terms) > 90:
                words = data.payment_terms.split()
                line = ""
                for word in words:
                    if len(line + word) < 90:
                        line += word + " "
                    else:
                        if y_position < bottom_margin + 30:
                            can.showPage()
                            y_position = height - 1.5 * inch
                            can.setFont("Helvetica", 10)
                        can.drawString(1.2 * inch, y_position, line.strip())
                        y_position -= 15
                        line = word + " "
                if line:
                    can.drawString(1.2 * inch, y_position, line.strip())
                    y_position -= 15
            else:
                can.drawString(1.2 * inch, y_position, data.payment_terms)
                y_position -= 15
            y_position -= 10
        
        # Timeline
        if data.timeline:
            if y_position < bottom_margin + 50:
                can.showPage()
                y_position = height - 1.5 * inch
            
            can.setFont("Helvetica", 12)
            # Wrap timeline text
            if len(data.timeline) > 90:
                words = data.timeline.split()
                line = ""
                for word in words:
                    if len(line + word) < 90:
                        line += word + " "
                    else:
                        if y_position < bottom_margin + 30:
                            can.showPage()
                            y_position = height - 1.5 * inch
                            can.setFont("Helvetica", 10)
                        can.drawString(1.2 * inch, y_position, line.strip())
                        y_position -= 15
                        line = word + " "
                if line:
                    can.drawString(1.2 * inch, y_position, line.strip())
                    y_position -= 15
            else:
                can.drawString(1.2 * inch, y_position, data.timeline)
                y_position -= 15
            y_position -= 10
        
        # Notes
        if data.notes:
            # Check if we need a new page
            if y_position < bottom_margin + 50:
                can.showPage()
                y_position = height - 1.5 * inch
            
            can.setFont("Helvetica", 12)
            # Wrap notes text
            notes_lines = data.notes.split('\n')
            for line in notes_lines:
                if y_position < bottom_margin + 30:
                    can.showPage()
                    y_position = height - 1.5 * inch
                    can.setFont("Helvetica", 10)
                
                if len(line) > 90:
                    words = line.split()
                    current_line = ""
                    for word in words:
                        if len(current_line + word) < 90:
                            current_line += word + " "
                        else:
                            if y_position < bottom_margin + 30:
                                can.showPage()
                                y_position = height - 1.5 * inch
                                can.setFont("Helvetica", 10)
                            can.drawString(1.2 * inch, y_position, current_line.strip())
                            y_position -= 15
                            current_line = word + " "
                    if current_line:
                        if y_position < bottom_margin + 30:
                            can.showPage()
                            y_position = height - 1.5 * inch
                            can.setFont("Helvetica", 10)
                        can.drawString(1.2 * inch, y_position, current_line.strip())
                        y_position -= 15
                else:
                    can.drawString(1.2 * inch, y_position, line)
                    y_position -= 15
        
        # Add Total at the bottom of the last page
        # Calculate total from all line items
        total_amount = data.total if data.total else 0
        
        # Position at bottom of page (1 inch from bottom)
        can.setFont("Helvetica-Bold", 12)
        can.drawString(5.5 * inch, 1 * inch, "Total")
        can.drawRightString(width - 1 * inch, 1 * inch, f"${total_amount:.2f}")
        
        can.save()
        packet.seek(0)
        
        # Merge with template if it exists
        if self.template_pg1_path.exists() and self.template_pg2_path.exists():
            overlay_pdf = PdfReader(packet)
            template_pg1 = PdfReader(self.template_pg1_path)
            template_pg2 = PdfReader(self.template_pg2_path)
            output = PdfWriter()
            
            # First page: merge with page 1 template
            if len(overlay_pdf.pages) > 0:
                page = template_pg1.pages[0]
                page.merge_page(overlay_pdf.pages[0])
                output.add_page(page)
            
            # Additional pages: merge with page 2 template
            for i in range(1, len(overlay_pdf.pages)):
                page = template_pg2.pages[0]
                page.merge_page(overlay_pdf.pages[i])
                output.add_page(page)
            
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
