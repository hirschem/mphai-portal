from pydantic import BaseModel
from typing import Optional, List


class TranscriptionResponse(BaseModel):
    session_id: str
    raw_text: str
    status: str


class ProposalRequest(BaseModel):
    session_id: str
    raw_text: str


class LineItem(BaseModel):
    description: str
    quantity: Optional[float] = None
    rate: Optional[float] = None
    amount: Optional[float] = None


class ProposalData(BaseModel):
    client_name: Optional[str] = None
    project_address: Optional[str] = None
    scope_of_work: Optional[List[str]] = None
    line_items: Optional[List[LineItem]] = None
    subtotal: Optional[float] = None
    tax: Optional[float] = None
    total: Optional[float] = None
    payment_terms: Optional[str] = None
    timeline: Optional[str] = None
    notes: Optional[str] = None


class ProposalResponse(BaseModel):
    session_id: str
    professional_text: str
    proposal_data: ProposalData
    status: str


class ProposalSummary(BaseModel):
    session_id: str
    client_name: Optional[str] = None
    project_address: Optional[str] = None
    total: Optional[float] = None
    created_at: str
    has_pdf: bool = False
    image_path: Optional[str] = None


class ProposalListResponse(BaseModel):
    proposals: List[ProposalSummary]
    total: int


# Book/Chapter schemas
class ChapterUploadResponse(BaseModel):
    chapter_id: str
    chapter_name: str
    transcribed_text: str
    page_count: int
    status: str


class ChapterData(BaseModel):
    chapter_id: str
    chapter_name: str
    transcribed_text: str
    page_count: int
    created_at: str
    has_docx: bool = False


class ChapterListResponse(BaseModel):
    chapters: List[ChapterData]
    total: int
