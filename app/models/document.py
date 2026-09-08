"""
Pydantic models for Document and Page entities.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class DocumentPage(BaseModel):
    page_id: str
    document_id: str
    page_number: int  # 1-indexed PDF page
    text: str
    char_count: int
    word_count: int


class DocumentMetadata(BaseModel):
    document_id: str
    filename: str
    file_path: str
    document_type: Optional[str] = "unknown"
    page_count: int
    file_size_bytes: int
    file_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "uploaded"  # uploaded, parsed, extracted, failed
    error_message: Optional[str] = None


class DocumentDetail(DocumentMetadata):
    pages: List[DocumentPage] = []
    facts_count: int = 0
