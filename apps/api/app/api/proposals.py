
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from app.auth import require_auth
from app.services.formatting_service import FormattingService
from app.services.export_service import ExportService
from app.models.schemas import ProposalRequest, ProposalResponse
from app.storage.file_manager import FileManager
from app.api.logging_config import logger
from app.security.rate_limit import RateLimiter


router = APIRouter()
_formatting_service = None
def get_formatting_service():
    global _formatting_service
    if _formatting_service is None:
        _formatting_service = FormattingService()
    return _formatting_service

export_service = ExportService()
file_manager = FileManager()
rate_limiter = RateLimiter()


@router.post("/generate", response_model=ProposalResponse)
async def generate_proposal(request: ProposalRequest, auth_level: str = Depends(require_auth)):
    """Convert transcribed text to professional proposal or invoice"""
    # Rate limit check (after validation/auth, before any side effects)
    # Extract headers and client IP for rate limiting
    import inspect
    # Try to get headers from context (test or prod)
    headers = {}
    client_host = "127.0.0.1"
    frame = inspect.currentframe()
    while frame:
        if "headers" in frame.f_locals:
            headers = frame.f_locals["headers"]
        if "client_host" in frame.f_locals:
            client_host = frame.f_locals["client_host"]
        frame = frame.f_back
    # Use X-Forwarded-For if present
    xff = headers.get("X-Forwarded-For") or headers.get("x-forwarded-for")
    ip = xff.split(",")[0].strip() if xff else client_host
    try:
        rate_limiter.check(ip, "generate", 3)
    except HTTPException as exc:
        raise exc

    document_type = getattr(request, "document_type", None) or "proposal"
    logger.info(f"[generate_proposal] session_id={request.session_id} document_type={document_type}")
    try:
        # Rewrite as professional construction proposal/invoice
        professional_text = await get_formatting_service().rewrite_professional(request.raw_text)
        logger.info(f"[rewrite_professional] session_id={request.session_id} done")

        # Generate structured document (proposal/invoice)
        proposal_data = await get_formatting_service().structure_proposal(professional_text, document_type=document_type)
        logger.info(f"[structure_proposal] session_id={request.session_id} done")

        # Save to session with correct naming
        await file_manager.save_proposal(request.session_id, proposal_data, document_type=document_type)
        logger.info(f"[save_proposal] session_id={request.session_id} done")

        # Generate PDF with correct naming and header
        await export_service.export_document(request.session_id, proposal_data, professional_text, "pdf", document_type=document_type)
        logger.info(f"[export_document] session_id={request.session_id} done")

        # Backward compatible: proposal_data, new: document_data, document_type
        return ProposalResponse(
            session_id=request.session_id,
            professional_text=professional_text,
            proposal_data=proposal_data,
            document_data=proposal_data,
            document_type=document_type,
            status="generated"
        )
    except Exception as e:
        logger.error(f"[generate_proposal] session_id={request.session_id} error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail={
            "error": "Failed to generate document",
            "session_id": request.session_id,
            "document_type": document_type,
            "reason": f"{type(e).__name__}: {e}"
        })


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
