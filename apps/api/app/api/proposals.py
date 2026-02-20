from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import FileResponse
from app.middleware.error_handlers import error_response
from app.auth import require_auth
from app.services.formatting_service import FormattingService
from app.services.export_service import ExportService
from app.models.schemas import ProposalRequest, ProposalResponse
from app.storage.file_manager import FileManager
from app.api.logging_config import logger
from app.security.rate_limit import RateLimiter

router = APIRouter(
    dependencies=[Depends(require_auth)]
)

@router.get("/download/{session_id}")
async def download_proposal(session_id: str, request: Request):
    request_id = getattr(request.state, "request_id", None) or request.headers.get("x-request-id")

    # Try expected PDF locations (proposal first, then invoice)
    pdf_path = file_manager.sessions_dir / session_id / "proposal.pdf"
    if not pdf_path.exists():
        alt = file_manager.sessions_dir / session_id / "invoice.pdf"
        pdf_path = alt if alt.exists() else pdf_path

    if not pdf_path.exists():
        return error_response(
            error_code="NOT_FOUND",
            message="Document not found.",
            request_id=request_id,
            status_code=404,
        )

    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=f"MPH_Document_{session_id[:8]}.pdf",
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



@router.post("/generate", response_model=ProposalResponse, dependencies=[Depends(require_auth)])
async def generate_proposal(payload: ProposalRequest, request: Request, auth_level: str = Depends(require_auth)):
    """Convert transcribed text to professional proposal or invoice"""
    import os
    request_id = getattr(request.state, "request_id", None) or request.headers.get("x-request-id")

    from fastapi import HTTPException
    try:
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
        except Exception:
            return error_response(
                error_code="RATE_LIMITED",
                message="Rate limit exceeded.",
                request_id=request_id,
                status_code=429,
            )
        # Rewrite as professional construction proposal/invoice
        document_type = getattr(payload, "document_type", "proposal")

        # Stub mode when OPENAI_API_KEY is missing (local/dev)
        if not os.environ.get("OPENAI_API_KEY"):
            professional_text = (
                f"{document_type.upper()} (STUB)\n\n"
                f"Session: {payload.session_id}\n\n"
                f"{payload.raw_text}".strip()
            )
            proposal_data = {
                "document_type": document_type,
                "session_id": payload.session_id,
                "sections": [{"title": "Scope", "items": [payload.raw_text]}],
            }
            logger.info(f"[stub_generate] session_id={payload.session_id} done")
        else:
            professional_text = await get_formatting_service().rewrite_professional(payload.raw_text)
            logger.info(f"[rewrite_professional] session_id={payload.session_id} done")

            # Generate structured document (proposal/invoice)
            proposal_data = await get_formatting_service().structure_proposal(
                professional_text, document_type=document_type
            )
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
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[generate_proposal] session_id={getattr(request, 'session_id', None)} error: {e}")
        return error_response(
            error_code="INTERNAL_ERROR",
            message="Proposal generation failed.",
            request_id=request_id,
            status_code=500,
        )
    # Final guard: never return None
    return error_response(
        error_code="INTERNAL_ERROR",
        message="Generate failed",
        request_id=request_id,
        status_code=500,
    )



@router.post("/export/{session_id}", dependencies=[Depends(require_auth)])
async def export_proposal(session_id: str, format: str = "pdf", request: Request = None, auth_level: str = Depends(require_auth)):
    """Export proposal to PDF or Word document"""
    request_id = None
    try:
        request_id = getattr(request.state, "request_id", None) if request else None
    except Exception:
        request_id = None

    try:
        proposal_data = await file_manager.load_proposal(session_id)
        if not proposal_data:
            return error_response(
                error_code="NOT_FOUND",
                message="Proposal not found.",
                request_id=request_id,
                status_code=404,
            )

        professional_text = ""
        try:
            professional_text = await file_manager.load_professional_text(session_id)
        except Exception:
            pass

        output_path = await export_service.export_document(
            session_id,
            proposal_data,
            professional_text,
            format,
            document_type=getattr(proposal_data, "document_type", "proposal"),
        )

        return {
            "session_id": session_id,
            "format": format,
            "file_path": str(output_path),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[export_proposal] session_id={session_id} error: {e}")
        return error_response(
            error_code="EXPORT_FAILED",
            message="Export failed.",
            request_id=request_id,
            status_code=500,
        )