from fastapi import APIRouter, HTTPException, Depends, Request, Response
from fastapi.responses import FileResponse
from app.middleware.error_handlers import error_response
from app.auth import require_auth
from app.services.formatting_service import FormattingService
from app.services.export_service import ExportService
from app.models.schemas import ProposalRequest, ProposalResponse, ProposalData

from app.services.openai_guard import OpenAIFailure
from app.errors import StandardizedAIError
from pydantic import ValidationError
from app.storage.file_manager import FileManager
from app.api.logging_config import logger
from app.security.rate_limit import RateLimiter

export_service = ExportService()
file_manager = FileManager()
rate_limiter = RateLimiter()

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

    size_bytes = None
    try:
        size_bytes = pdf_path.stat().st_size
    except Exception:
        pass

    logger.info(
        "proposal_pdf_served",
        extra={
            "request_id": request_id,
            "session_id": session_id,
            "pdf_path": str(pdf_path),
            "size_bytes": size_bytes,
        },
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




@router.post("/generate", response_model=ProposalResponse)
async def generate_proposal(payload: ProposalRequest, request: Request, response: Response):
    """Convert transcribed text to professional proposal or invoice"""
    import os
    aidoc_strict = os.environ.get("AIDOC_STRICT", "0") == "1"
    request_id = getattr(request.state, "request_id", None) or request.headers.get("x-request-id")

    structuring_ok = False
    used_aidoc_fallback = False
    try:
        # Rate limit check (after validation/auth, before any side effects)
        xff = request.headers.get("x-forwarded-for")
        ip = xff.split(",")[0].strip() if xff else (request.client.host if request.client else "127.0.0.1")
        try:
            rate_limiter.check(ip, "generate", 3)
        except Exception:
            return error_response(
                error_code="RATE_LIMITED",
                message="Rate limit exceeded.",
                request_id=request_id,
                status_code=429,
            )



        document_type = getattr(payload, "document_type", "proposal")
        client_name = (getattr(payload, "client_name", None) or "").strip() or None
        address = (getattr(payload, "address", None) or "").strip() or None
        # Log raw text and payload client info before any OpenAI calls
        if globals().get("DEBUG", False):
            logger.info(f"RAW_TEXT_PREVIEW_TOP: {repr(payload.raw_text[:500])}")
            logger.info(f"PAYLOAD client_name={repr(client_name)} address={repr(address)}")

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
            if client_name:
                proposal_data["client_name"] = client_name
            if address:
                proposal_data["project_address"] = address
            logger.info(f"[stub_generate] session_id={payload.session_id} done")
        else:
            try:
                professional_text = await get_formatting_service().rewrite_professional(payload.raw_text)
                logger.info(f"[rewrite_professional] session_id={payload.session_id} done")
                # TEMP LOG: professional_text type and first 800 chars
                logger.info(f"professional_text type: {type(professional_text)}")
                logger.info(f"professional_text preview: {repr(professional_text[:800])}")

                proposal_data = await get_formatting_service().structure_proposal(
                    professional_text, document_type=document_type
                )
                structuring_ok = True
                # TEMP LOG: client_name, project_address, keys
                logger.info(f"proposal_data client_name: {proposal_data.get('client_name')}")
                logger.info(f"proposal_data project_address: {proposal_data.get('project_address')}")
                logger.info(f"proposal_data keys: {list(proposal_data.keys())}")

                if client_name:
                    proposal_data["client_name"] = client_name
                if address:
                    proposal_data["project_address"] = address
                logger.info(f"[structure_proposal] session_id={payload.session_id} done")
            except StandardizedAIError as e:
                # Fallback for AiDocV1/schema validation failure
                if aidoc_strict:
                    return error_response(
                        error_code=getattr(e, "code", "AI_SCHEMA_VALIDATION_FAILED"),
                        message=str(e),
                        request_id=request_id,
                        status_code=503,
                    )
                # Non-strict: fallback ProposalData, set header
                used_aidoc_fallback = True
                logger.info(
                    "aidoc_fallback",
                    extra={
                        "request_id": request_id,
                        "session_id": payload.session_id,
                    },
                )
                professional_text = professional_text if 'professional_text' in locals() else (
                    f"{document_type.upper()} (FALLBACK)\n\n"
                    f"Session: {payload.session_id}\n\n"
                    f"{payload.raw_text}".strip()
                )
                proposal_data = {
                    "document_type": document_type,
                    "session_id": payload.session_id,
                    "sections": [{"title": "Scope", "items": [payload.raw_text]}],
                }
                # Deterministic header parse for client_name and address from raw_text
                if not client_name or not address:
                    import re
                    lines = [ln.strip() for ln in payload.raw_text.splitlines() if ln.strip()]
                    # Remove leading page markers (e.g. --- Page ...)
                    i = 0
                    while i < len(lines):
                        if re.match(r"^---\s*Page\b", lines[i], re.IGNORECASE):
                            del lines[i]
                            # Remove following blank if present
                            if i < len(lines) and not lines[i]:
                                del lines[i]
                        else:
                            break
                    head = lines[:20]
                    name_candidate = None
                    addr_candidate = None
                    # Find name_candidate
                    for idx, line in enumerate(head):
                        if len(line) > 60:
                            continue
                        if not re.search(r"[a-zA-Z]", line):
                            continue
                        if re.search(r"invoice|proposal", line, re.IGNORECASE):
                            continue
                        if line.lstrip().startswith('-'):
                            continue
                        name_candidate = line
                        # Find addr_candidate as next line after name_candidate
                        for j in range(idx+1, len(head)):
                            addr_line = head[j]
                            # Must not be digits-only
                            if re.fullmatch(r"\d+", addr_line):
                                continue
                            # Must contain digit and letter OR street suffix
                            street_re = re.compile(r"\b(Pl|Place|St|Street|Ave|Avenue|Rd|Road|Dr|Drive|Way|Ln|Lane|Blvd|Boulevard|Ct|Court|Cir|Circle)\b", re.IGNORECASE)
                            if ((re.search(r"[a-zA-Z]", addr_line) and re.search(r"\d", addr_line)) or street_re.search(addr_line)):
                                addr_candidate = addr_line
                                break
                        break
                    if not client_name and name_candidate:
                        proposal_data["client_name"] = name_candidate
                    if not address and addr_candidate:
                        proposal_data["project_address"] = addr_candidate
                if client_name:
                    proposal_data["client_name"] = client_name
                if address:
                    proposal_data["project_address"] = address
                proposal_data_obj = ProposalData.model_validate(proposal_data)
                await file_manager.save_proposal(payload.session_id, proposal_data_obj, document_type=document_type)
                await export_service.export_document(payload.session_id, proposal_data_obj, professional_text, "pdf", document_type=document_type)
                response.headers["X-AI-DOC"] = "fallback"
                return ProposalResponse(
                    session_id=payload.session_id,
                    professional_text=professional_text,
                    proposal_data=proposal_data_obj,
                    document_data=proposal_data_obj,
                    document_type=document_type,
                    status="generated"
                )
            except OpenAIFailure as e:
                # Map OpenAI upstream failures to HTTP 503 with deterministic error contract
                return error_response(
                    error_code=getattr(e, "code", "AI_UPSTREAM_UNAVAILABLE"),
                    message="Proposal generation is temporarily unavailable. Please retry.",
                    request_id=request_id,
                    status_code=503,
                )

        # Validate ProposalData before returning ProposalResponse
        try:
            proposal_data_obj = ProposalData.model_validate(proposal_data)
        except ValidationError:
            return error_response(
                error_code="PROPOSAL_SCHEMA_INVALID",
                message="Generated proposal data was invalid. Please retry.",
                request_id=request_id,
                status_code=500,
            )

        # Save to session with correct naming
        await file_manager.save_proposal(payload.session_id, proposal_data_obj, document_type=document_type)
        logger.info(f"[save_proposal] session_id={payload.session_id} done")

        # Temporary debug logging before PDF rendering
        if globals().get("DEBUG", False):
            logger.info(f"structuring_ok={structuring_ok}")
            logger.info(f"used_aidoc_fallback={used_aidoc_fallback}")
            logger.info(f"ProposalData fields: client_name={getattr(proposal_data_obj, 'client_name', None)}, project_address={getattr(proposal_data_obj, 'project_address', None)}, line_items={len(getattr(proposal_data_obj, 'line_items', []) or [])}, total={getattr(proposal_data_obj, 'total', None)}")
            logger.info("PDF DEBUG line_items: %s", proposal_data_obj.line_items)
            logger.info("PDF DEBUG total: %s", proposal_data_obj.total)
            logger.info("PDF DEBUG professional_text: %s", professional_text)

        # Generate PDF with correct naming and header
        format = "pdf"
        output_path = await export_service.export_document(payload.session_id, proposal_data_obj, professional_text, format, document_type=document_type)
        size_bytes = None
        try:
            size_bytes = output_path.stat().st_size
        except Exception:
            pass

        logger.info(
            "proposal_pdf_written",
            extra={
                "request_id": request_id,
                "session_id": payload.session_id,
                "document_type": document_type,
                "format": format,
                "pdf_path": str(output_path),
                "size_bytes": size_bytes,
            },
        )
        logger.info(f"[export_document] session_id={payload.session_id} done")

        return ProposalResponse(
            session_id=payload.session_id,
            professional_text=professional_text,
            proposal_data=proposal_data_obj,
            document_data=proposal_data_obj,
            document_type=document_type,
            status="generated"
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception(
            "proposal_generate_unhandled_error",
            extra={"request_id": getattr(request.state, "request_id", None)},
        )
        return error_response(
            error_code="INTERNAL_ERROR",
            message="Proposal generation failed.",
            request_id=getattr(request.state, "request_id", None),
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