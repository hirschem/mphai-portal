from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from fastapi.responses import FileResponse
from app.storage.file_manager import FileManager
from app.services.book_ocr_service import BookOCRService
from app.services.book_export_service import BookExportService
from app.models.schemas import ChapterUploadResponse, ChapterListResponse, ChapterData
from app.auth import require_admin
from datetime import datetime
from pathlib import Path
import uuid
import json

router = APIRouter()
file_manager = FileManager()
ocr_service = BookOCRService()
export_service = BookExportService()


@router.post("/upload", response_model=ChapterUploadResponse)
async def upload_chapter(
    chapter_name: str = Form(...),
    files: list[UploadFile] = File(...)
):
    """Upload and transcribe multiple pages of a book chapter"""
    
    chapter_id = str(uuid.uuid4())
    
    # Save all uploaded pages
    saved_paths = await file_manager.save_chapter_pages(chapter_id, files)
    
    # Transcribe all pages in order
    transcribed_text = await ocr_service.transcribe_pages([str(p) for p in saved_paths])
    
    # Save chapter data
    await file_manager.save_chapter_data(chapter_id, chapter_name, transcribed_text, len(files))
    
    # Generate Word document
    chapter_dir = file_manager.books_dir / chapter_id
    docx_path = chapter_dir / f"{chapter_name}.docx"
    export_service.export_chapter(chapter_name, transcribed_text, docx_path)
    
    return ChapterUploadResponse(
        chapter_id=chapter_id,
        chapter_name=chapter_name,
        transcribed_text=transcribed_text,
        page_count=len(files),
        status="success"
    )


@router.get("/list", response_model=ChapterListResponse)
async def list_chapters(auth_level: str = Depends(require_admin)):
    """Get list of all book chapters (admin only)"""
    
    chapters = []
    books_dir = file_manager.books_dir
    
    if not books_dir.exists():
        return ChapterListResponse(chapters=[], total=0)
    
    for chapter_dir in sorted(books_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
        if not chapter_dir.is_dir():
            continue
        
        chapter_file = chapter_dir / "chapter.json"
        if not chapter_file.exists():
            continue
        
        try:
            with open(chapter_file, 'r') as f:
                data = json.load(f)
            
            created_at = datetime.fromtimestamp(chapter_dir.stat().st_mtime)
            
            # Check if DOCX exists
            docx_files = list(chapter_dir.glob("*.docx"))
            has_docx = len(docx_files) > 0
            
            chapters.append(ChapterData(
                chapter_id=data['chapter_id'],
                chapter_name=data['chapter_name'],
                transcribed_text=data['transcribed_text'],
                page_count=data['page_count'],
                created_at=created_at.isoformat(),
                has_docx=has_docx
            ))
        except Exception as e:
            print(f"Error loading chapter {chapter_dir.name}: {e}")
            continue
    
    return ChapterListResponse(chapters=chapters, total=len(chapters))


@router.get("/download/{chapter_id}")
async def download_chapter(chapter_id: str):
    """Download chapter as Word document"""
    
    chapter_dir = file_manager.books_dir / chapter_id
    
    if not chapter_dir.exists():
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    # Find the docx file
    docx_files = list(chapter_dir.glob("*.docx"))
    
    if not docx_files:
        raise HTTPException(status_code=404, detail="Document not found")
    
    docx_path = docx_files[0]
    
    return FileResponse(
        docx_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=docx_path.name
    )


@router.delete("/{chapter_id}")
async def delete_chapter(chapter_id: str, auth_level: str = Depends(require_admin)):
    """Delete a chapter"""
    
    chapter_dir = file_manager.books_dir / chapter_id
    
    if not chapter_dir.exists():
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    # Delete directory and all contents
    import shutil
    shutil.rmtree(chapter_dir)
    
    return {"message": "Chapter deleted successfully"}
