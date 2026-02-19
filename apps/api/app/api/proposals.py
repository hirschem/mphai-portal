from app.middleware.error_handlers import error_response

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import FileResponse
from app.auth import require_auth
from app.services.formatting_service import FormattingService
from app.services.export_service import ExportService
from app.models.schemas import ProposalRequest, ProposalResponse
from app.storage.file_manager import FileManager
from app.api.logging_config import logger
from app.security.rate_limit import RateLimiter


from fastapi import Depends
from app.auth import require_auth
router = APIRouter(
    dependencies=[Depends(require_auth)]
)
_formatting_service = None
def get_formatting_service():
    global _formatting_service
    if _formatting_service is None:
        _formatting_service = FormattingService()
    return _formatting_service

export_service = ExportService()
file_manager = FileManager()
rate_limiter = RateLimiter()


from fastapi import Depends
from app.auth import require_auth
@router.post("/generate", response_model=ProposalResponse, dependencies=[Depends(require_auth)])
async def generate_proposal(payload: ProposalRequest, request: Request, auth_level: str = Depends(require_auth)):
    """Convert transcribed text to professional proposal or invoice"""
    # Rate limit check (after validation/auth, before any side effects)
    import inspect
    from starlette.datastructures import Headers as StarletteHeaders
    headers = {}
    client_host = "127.0.0.1"
    frame = inspect.currentframe()
    while frame:
        if "headers" in frame.f_locals:
            headers = frame.f_locals["headers"]
        if "client_host" in frame.f_locals:
            client_host = frame.f_locals["client_host"]
        frame = frame.f_back
    if isinstance(headers, list):
        headers = StarletteHeaders(raw=headers)
    headers = dict(request.headers)
    xff = headers.get("x-forwarded-for")
    ip = xff.split(",")[0].strip() if xff else client_host
    try:
        rate_limiter.check(ip, "generate", 3)
        # Rewrite as professional construction proposal/invoice
        document_type = getattr(payload, "document_type", "proposal")
        professional_text = await get_formatting_service().rewrite_professional(payload.raw_text)
        logger.info(f"[rewrite_professional] session_id={payload.session_id} done")

        # Generate structured document (proposal/invoice)
        proposal_data = await get_formatting_service().structure_proposal(professional_text, document_type=document_type)
        logger.info(f"[structure_proposal] session_id={payload.session_id} done")

        # Save to session with correct naming
        await file_manager.save_proposal(payload.session_id, proposal_data, document_type=document_type)
        logger.info(f"[save_proposal] session_id={payload.session_id} done")

        # Generate PDF with correct naming and header
        await export_service.export_document(payload.session_id, proposal_data, professional_text, "pdf", document_type=document_type)
        logger.info(f"[export_document] session_id={payload.session_id} done")

        return ProposalResponse(
            session_id=payload.session_id,
            professional_text=professional_text,
            proposal_data=proposal_data,
            document_data=proposal_data,
            document_type=document_type,
            status="generated"
        )
    except Exception as e:
        from app.security.rate_limit import RateLimitException
        if isinstance(e, RateLimitException):
            # Return a 429 error response with detail
            request_id = getattr(request.state, "request_id", None)
            return error_response("rate_limited", e.message, request_id, e.status_code, include_detail=True)
        logger.error(f"[generate_proposal] session_id={getattr(request, 'session_id', None)} error: {e}", exc_info=True)
        request_id = getattr(request.state, "request_id", None)
        return error_response("server_error", f"Failed to generate document: {e}", request_id, 500)
    # Final guard: never return None
    rid = getattr(request.state, "request_id", None) or request.headers.get("x-request-id")
    return error_response("INTERNAL_ERROR", "Generate failed", rid, 500)


@router.post("/export/{session_id}", dependencies=[Depends(require_auth)])
async def export_proposal(session_id: str, format: str = "pdf", auth_level: str = Depends(require_auth)):
    """Export proposal to PDF or Word document"""
    
    # Load proposal data
    proposal_data = await file_manager.load_proposal(session_id)
    
    request_id = None
    try:
        from fastapi import Request as _Request
        import inspect
        frame = inspect.currentframe()
        while frame:
            if "request" in frame.f_locals and isinstance(frame.f_locals["request"], _Request):
                request_id = getattr(frame.f_locals["request"].state, "request_id", None)
                break
            frame = frame.f_back
    except Exception:
        pass
    if not proposal_data:
        return error_response("not_found", "Proposal not found", request_id, 404)
    
    # Generate document
    file_path = await export_service.export_document(session_id, proposal_data, format)
    
    return {
        "session_id": session_id,
        "format": format,
        "file_path": str(file_path)
    }


@router.get("/download/{session_id}", dependencies=[Depends(require_auth)])
async def download_proposal(session_id: str, auth_level: str = Depends(require_auth)):
    """Download the PDF proposal"""
    
    # Check if PDF exists
    pdf_path = file_manager.sessions_dir / session_id / "proposal.pdf"
    
    request_id = None
    try:
        from fastapi import Request as _Request
        import inspect
        frame = inspect.currentframe()
        while frame:
            if "request" in frame.f_locals and isinstance(frame.f_locals["request"], _Request):
                request_id = getattr(frame.f_locals["request"].state, "request_id", None)
                break
            frame = frame.f_back
    except Exception:
        pass
    if not pdf_path.exists():
        # Try to generate it
        proposal_data = await file_manager.load_proposal(session_id)
        if not proposal_data:
            return error_response("not_found", "Proposal not found", request_id, 404)
        await export_service.export_document(session_id, proposal_data, "pdf")
    
    # Serve the file
    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=f"MPH_Proposal_{session_id[:8]}.pdf"
    )
