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
async def transcribe_image(file: UploadFile = File(...), auth_level: str = Depends(require_auth)):
    """Upload handwritten image and get transcription"""
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
    if not file.content_type or not file.content_type.startswith("image/"):
        return error_response("invalid_file", "File must be an image", request_id, 400)
    # Generate session ID
    session_id = str(uuid.uuid4())
    
    # Save uploaded file
    image_path = await file_manager.save_upload(session_id, file)
    
    # Transcribe handwriting
    raw_text = await get_ocr_service().transcribe_image(image_path)
    
    # Save raw transcription
    await file_manager.save_transcription(session_id, raw_text)
    
    return TranscriptionResponse(
        session_id=session_id,
        raw_text=raw_text,
        status="transcribed"
    )
