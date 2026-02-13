from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from app.auth import require_auth
from app.services.ocr_service import OCRService
from app.models.schemas import TranscriptionResponse
from app.storage.file_manager import FileManager
import uuid


router = APIRouter()
_ocr_service = None
def get_ocr_service():
    global _ocr_service
    if _ocr_service is None:
        _ocr_service = OCRService()
    return _ocr_service
file_manager = FileManager()


@router.post("/upload", response_model=TranscriptionResponse)
async def transcribe_image(file: UploadFile = File(...), auth_level: str = Depends(require_auth)):
    """Upload handwritten image and get transcription"""
    
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
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
