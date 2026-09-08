"""
Pydantic models for Fact Comparison and Cross-Document Relationship Classification.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from app.models.evidence import Evidence
from app.models.fact import Fact


class RelationshipType(str, Enum):
    CORROBORATED = "CORROBORATED"
    CONTRADICTION = "CONTRADICTION"
    CONTEXTUAL = "CONTEXTUAL"
    UNKNOWN = "UNKNOWN"


class FactComparison(BaseModel):
    comparison_id: str
    fact_a_id: str
    fact_b_id: str
    relationship: RelationshipType
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)
    reason: str = Field(description="Human-understandable explanation of the relationship")
    differences: List[str] = Field(default_factory=list, description="Specific identified points of divergence")
    evidence_a: Evidence
    evidence_b: Evidence
    fact_a: Optional[Fact] = None
    fact_b: Optional[Fact] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ComparisonSummary(BaseModel):
    total_comparisons: int
    corroborated_count: int
    contradiction_count: int
    contextual_count: int
    unknown_count: int
    high_confidence_count: int
