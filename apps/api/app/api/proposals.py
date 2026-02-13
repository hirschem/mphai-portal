from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from app.auth import require_auth
from app.services.formatting_service import FormattingService
from app.services.export_service import ExportService
from app.models.schemas import ProposalRequest, ProposalResponse
from app.storage.file_manager import FileManager

router = APIRouter()
formatting_service = FormattingService()
export_service = ExportService()
file_manager = FileManager()


@router.post("/generate", response_model=ProposalResponse)
async def generate_proposal(request: ProposalRequest, auth_level: str = Depends(require_auth)):
    """Convert transcribed text to professional proposal"""
    
    # Rewrite as professional construction proposal
    professional_text = await formatting_service.rewrite_professional(request.raw_text)
    
    # Generate structured proposal
    proposal_data = await formatting_service.structure_proposal(professional_text)
    
    # Save to session
    await file_manager.save_proposal(request.session_id, proposal_data)
    
    # Automatically generate PDF with professional text
    await export_service.export_document(request.session_id, proposal_data, professional_text, "pdf")
    
    return ProposalResponse(
        session_id=request.session_id,
        professional_text=professional_text,
        proposal_data=proposal_data,
        status="generated"
    )


@router.post("/export/{session_id}")
async def export_proposal(session_id: str, format: str = "pdf", auth_level: str = Depends(require_auth)):
    """Export proposal to PDF or Word document"""
    
    # Load proposal data
    proposal_data = await file_manager.load_proposal(session_id)
    
    if not proposal_data:
        raise HTTPException(status_code=404, detail="Proposal not found")
    
    # Generate document
    file_path = await export_service.export_document(session_id, proposal_data, format)
    
    return {
        "session_id": session_id,
        "format": format,
        "file_path": str(file_path)
    }


@router.get("/download/{session_id}")
async def download_proposal(session_id: str, auth_level: str = Depends(require_auth)):
    """Download the PDF proposal"""
    
    # Check if PDF exists
    pdf_path = file_manager.sessions_dir / session_id / "proposal.pdf"
    
    if not pdf_path.exists():
        # Try to generate it
        proposal_data = await file_manager.load_proposal(session_id)
        if not proposal_data:
            raise HTTPException(status_code=404, detail="Proposal not found")
        
        await export_service.export_document(session_id, proposal_data, "pdf")
    
    # Serve the file
    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=f"MPH_Proposal_{session_id[:8]}.pdf"
    )
