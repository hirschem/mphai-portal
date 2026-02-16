from app.middleware.error_handlers import error_response
from fastapi import APIRouter, Depends
from app.storage.file_manager import FileManager
from app.models.schemas import ProposalListResponse, ProposalSummary
from app.auth import require_admin
from pathlib import Path
import json
from datetime import datetime

from fastapi import Depends
from app.auth import require_admin
from fastapi import Depends
from app.auth import require_auth
router = APIRouter(
    dependencies=[Depends(require_auth)]
)
file_manager = FileManager()


from fastapi import Depends
from app.auth import require_admin
from fastapi import Depends
from app.auth import require_admin
@router.get("/list", response_model=ProposalListResponse, dependencies=[Depends(require_admin)])
async def list_proposals(auth_level: str = Depends(require_admin)):
    """Get list of all proposals"""
    
    proposals = []
    sessions_dir = file_manager.sessions_dir
    
    if not sessions_dir.exists():
        return ProposalListResponse(proposals=[], total=0)
    
    for session_dir in sorted(sessions_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
        if not session_dir.is_dir():
            continue
        
        proposal_file = session_dir / "proposal.json"
        if not proposal_file.exists():
            continue
        
        try:
            with open(proposal_file, 'r') as f:
                data = json.load(f)
            
            # Get creation time
            created_at = datetime.fromtimestamp(session_dir.stat().st_mtime)
            
            # Check if PDF exists
            pdf_file = session_dir / "proposal.pdf"
            has_pdf = pdf_file.exists()
            
            # Get original image
            image_files = list(session_dir.glob("original_*"))
            image_path = str(image_files[0].relative_to(file_manager.sessions_dir)) if image_files else None
            
            proposals.append(ProposalSummary(
                session_id=session_dir.name,
                client_name=data.get('client_name'),
                project_address=data.get('project_address'),
                total=data.get('total'),
                created_at=created_at.isoformat(),
                has_pdf=has_pdf,
                image_path=image_path
            ))
        except Exception as e:
            # Skip invalid proposals
            continue
    
    return ProposalListResponse(proposals=proposals, total=len(proposals))


@router.get("/{session_id}", dependencies=[Depends(require_admin)])
async def get_proposal(session_id: str, auth_level: str = Depends(require_admin)):
    """Get full proposal data by session ID"""
    
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
    
    return {
        "session_id": session_id,
        "proposal_data": proposal_data
    }


@router.delete("/{session_id}", dependencies=[Depends(require_admin)])
async def delete_proposal(session_id: str, auth_level: str = Depends(require_admin)):
    """Delete a proposal"""
    
    session_dir = file_manager.sessions_dir / session_id
    
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
    if not session_dir.exists():
        return error_response("not_found", "Proposal not found", request_id, 404)
    
    # Delete the entire session directory
    import shutil
    shutil.rmtree(session_dir)
    
    return {"message": "Proposal deleted successfully"}
