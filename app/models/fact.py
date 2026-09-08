"""
Pydantic models for structured, evidence-grounded facts.
"""

from datetime import datetime
from typing import Optional, Union, Any, List
from pydantic import BaseModel, Field


class FactBase(BaseModel):
    subject: str = Field(description="Entity or subject of the fact (e.g. 'Delhivery')")
    predicate: str = Field(description="Normalized attribute or metric (e.g. 'revenue_from_services')")
    value: Union[float, int, str] = Field(description="Raw extracted value")
    unit: Optional[str] = Field(default=None, description="Raw extracted unit (e.g. '₹ crore')")
    period: Optional[str] = Field(default=None, description="Time period or reporting date (e.g. 'FY24', 'Q4 FY24')")
    scope: Optional[str] = Field(default=None, description="Scope or segment qualifier (e.g. 'pro forma', 'since inception')")
    
    # Normalized fields (deterministic grounding)
    original_value: Optional[Union[float, int, str]] = None
    normalized_value: Optional[float] = Field(default=None, description="Canonical numerical value")
    original_unit: Optional[str] = None
    normalized_unit: Optional[str] = Field(default=None, description="Canonical unit representation (e.g. 'INR million')")
    
    is_numerical: bool = True
    page_number: int
    evidence_text: str = Field(description="Exact snippet extracted from source document")
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)
    extraction_method: str = Field(default="deterministic", description="'llm' or 'deterministic'")


class FactCreate(FactBase):
    source_document_id: str
    source_document_name: str


class Fact(FactBase):
    fact_id: str
    source_document_id: str
    source_document_name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def to_embedding_text(self) -> str:
        """Standardized string representation for semantic embedding generation."""
        val_str = f"{self.normalized_value}" if self.normalized_value is not None else str(self.value)
        unit_str = self.normalized_unit or self.unit or ""
        period_str = self.period or ""
        scope_str = f" [{self.scope}]" if self.scope else ""
        return f"{self.subject} | {self.predicate} | {period_str} | {unit_str} | {val_str}{scope_str}"


class FactFilter(BaseModel):
    document_id: Optional[str] = None
    subject: Optional[str] = None
    predicate: Optional[str] = None
    period: Optional[str] = None
    min_confidence: Optional[float] = None
