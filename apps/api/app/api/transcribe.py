from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from app.auth import require_auth
from app.middleware.error_handlers import error_response
from app.services.ocr_service import OCRService
from app.models.schemas import TranscriptionResponse
from app.storage.file_manager import FileManager
import uuid


from fastapi import Depends
from app.auth import require_auth
from fastapi import Depends
from app.auth import require_auth
router = APIRouter(
    dependencies=[Depends(require_auth)]
)
_ocr_service = None
def get_ocr_service():
    global _ocr_service
    if _ocr_service is None:
        _ocr_service = OCRService()
    return _ocr_service
file_manager = FileManager()


from fastapi import Depends
from app.auth import require_auth
@router.post("/upload", response_model=TranscriptionResponse, dependencies=[Depends(require_auth)])
async def transcribe_image(
    files: list[UploadFile] | None = File(None),
    file: UploadFile | None = File(None)
):
    """Upload handwritten image(s) and get transcription (multi-image supported)"""
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
    # Normalize input: accept both 'files' and 'file' fields
    if (not files or len(files) == 0) and file is not None:
        files = [file]
    if not files or len(files) == 0:
        return error_response(
            "VALIDATION_ERROR",
            "body.files: Field required",
            request_id,
            422,
        )
    settings = __import__("app.models.config", fromlist=["get_settings"]).get_settings()
    max_pages = getattr(settings, "MAX_UPLOAD_PAGES", 25)
    if len(files) > max_pages:
        return error_response(
            "VALIDATION_ERROR",
            f"Too many pages: {len(files)} exceeds MAX_UPLOAD_PAGES ({max_pages})",
            request_id,
            422,
        )
    if not all(f.content_type and f.content_type.startswith("image/") for f in files):
        return error_response("invalid_file", "File(s) must be image(s)", request_id, 400)
    session_id = str(uuid.uuid4())
    image_paths = []
    for file in files:
        image_path = await file_manager.save_upload(session_id, file)
        image_paths.append(image_path)
    # Deterministic aggregation
    ocr_results = []
    if len(image_paths) == 1:
        ocr_results = [await get_ocr_service().transcribe_image(image_paths[0])]
    else:
        ocr_results = await get_ocr_service().transcribe_pages([str(p) for p in image_paths])
        if not isinstance(ocr_results, list):
            ocr_results = [ocr_results]
    # Ensure all pages are marked
    raw_text_parts = []
    for i, img in enumerate(image_paths):
        page_text = ocr_results[i] if i < len(ocr_results) and ocr_results[i] else "(no text)"
        raw_text_parts.append(f"\n\n--- Page {i+1} ---\n\n" + page_text)
    raw_text = "".join(raw_text_parts)
    await file_manager.save_transcription(session_id, raw_text)
    return TranscriptionResponse(
        session_id=session_id,
        raw_text=raw_text,
        status="transcribed"
    )
