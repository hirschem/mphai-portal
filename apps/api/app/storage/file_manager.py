from pathlib import Path
from fastapi import UploadFile
from typing import Optional
import json
import aiofiles
from app.models.schemas import ProposalData

BASE_DIR = Path(__file__).parent.parent.parent.parent


class FileManager:
    def __init__(self):
        self.data_dir = BASE_DIR / "data"
        self.uploads_dir = self.data_dir / "raw_uploads"
        self.sessions_dir = self.data_dir / "sessions"
        self.ground_truth_dir = self.data_dir / "ground_truth"
        self.books_dir = self.data_dir / "books"
        
        # Create directories
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.ground_truth_dir.mkdir(parents=True, exist_ok=True)
        self.books_dir.mkdir(parents=True, exist_ok=True)
    
    async def save_upload(self, session_id: str, file: UploadFile) -> Path:
        """Save uploaded image to raw_uploads and session directory"""
        
        session_dir = self.sessions_dir / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = session_dir / f"original_{file.filename}"
        
        async with aiofiles.open(file_path, "wb") as f:
            content = await file.read()
            await f.write(content)
        
        return file_path
    
    async def save_transcription(self, session_id: str, text: str):
        """Save raw transcription to session directory"""
        
        session_dir = self.sessions_dir / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        
        async with aiofiles.open(session_dir / "transcription.txt", "w", encoding="utf-8") as f:
            await f.write(text)
    
    async def save_proposal(self, session_id: str, proposal_data, document_type: str = "proposal"):
        """Save structured proposal/invoice data to session directory. Accepts Pydantic model or dict."""
        session_dir = self.sessions_dir / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{document_type}.json"
        if hasattr(proposal_data, "model_dump_json"):
            json_str = proposal_data.model_dump_json(indent=2)
        else:
            import json
            json_str = json.dumps(proposal_data, indent=2, ensure_ascii=False)
        async with aiofiles.open(session_dir / filename, "w", encoding="utf-8") as f:
            await f.write(json_str)
    
    async def load_proposal(self, session_id: str, document_type: str = "proposal") -> Optional[ProposalData]:
        """Load proposal/invoice data from session directory"""
        session_dir = self.sessions_dir / session_id
        filename = f"{document_type}.json"
        proposal_path = session_dir / filename
        if not proposal_path.exists():
            # fallback for legacy: try proposal.json
            if document_type != "proposal":
                proposal_path = session_dir / "proposal.json"
                if not proposal_path.exists():
                    return None
            else:
                return None
        async with aiofiles.open(proposal_path, "r") as f:
            content = await f.read()
            data = json.loads(content)
            return ProposalData(**data)
    
    async def save_chapter_pages(self, chapter_id: str, files: list) -> list[Path]:
        """Save multiple uploaded pages for a chapter"""
        
        chapter_dir = self.books_dir / chapter_id
        chapter_dir.mkdir(parents=True, exist_ok=True)
        
        saved_paths = []
        for i, file in enumerate(files, 1):
            file_path = chapter_dir / f"page_{i:03d}_{file.filename}"
            
            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
            
            saved_paths.append(file_path)
        
        return saved_paths
    
    async def save_chapter_data(self, chapter_id: str, chapter_name: str, transcribed_text: str, page_count: int):
        """Save chapter metadata and transcription"""
        
        chapter_dir = self.books_dir / chapter_id
        chapter_dir.mkdir(parents=True, exist_ok=True)
        
        data = {
            "chapter_id": chapter_id,
            "chapter_name": chapter_name,
            "transcribed_text": transcribed_text,
            "page_count": page_count
        }
        
        async with aiofiles.open(chapter_dir / "chapter.json", "w") as f:
            await f.write(json.dumps(data, indent=2))
