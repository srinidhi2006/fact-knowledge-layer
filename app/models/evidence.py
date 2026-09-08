"""
Pydantic models for Evidence grounding.
"""

from typing import Optional
from pydantic import BaseModel


class Evidence(BaseModel):
    document_id: str
    document_name: str
    page_number: int
    evidence_text: str
    surrounding_context: Optional[str] = None
    char_start: Optional[int] = None
    char_end: Optional[int] = None
