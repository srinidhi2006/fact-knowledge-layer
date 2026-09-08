"""
API Routes for Fact Retrieval, Filtering, and Evidence Inspection.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from app.models.fact import Fact, FactFilter, FactCreate
from app.models.evidence import Evidence
from app.db.repositories import FactRepository
from app.services.evidence_service import EvidenceService

router = APIRouter(prefix="/facts", tags=["Facts"])


@router.get("", response_model=List[Fact])
def list_facts(
    document_id: Optional[str] = Query(None, description="Filter by source document ID"),
    subject: Optional[str] = Query(None, description="Filter by subject"),
    predicate: Optional[str] = Query(None, description="Filter by metric / predicate"),
    period: Optional[str] = Query(None, description="Filter by time period"),
    min_confidence: Optional[float] = Query(None, description="Minimum confidence threshold")
):
    """Retrieve facts matching optional filter criteria."""
    filters = FactFilter(
        document_id=document_id,
        subject=subject,
        predicate=predicate,
        period=period,
        min_confidence=min_confidence
    )
    return FactRepository.list_facts(filters)


@router.get("/{fact_id}", response_model=Fact)
def get_fact(fact_id: str):
    """Retrieve a single fact by ID."""
    fact = FactRepository.get_fact(fact_id)
    if not fact:
        raise HTTPException(status_code=404, detail="Fact not found")
    return fact


@router.get("/{fact_id}/evidence", response_model=Evidence)
def get_fact_evidence(fact_id: str):
    """Retrieve grounded evidence with surrounding context for a fact."""
    fact = FactRepository.get_fact(fact_id)
    if not fact:
        raise HTTPException(status_code=404, detail="Fact not found")
    return EvidenceService.get_evidence_for_fact(fact)


@router.post("", response_model=Fact)
def create_fact(fact_in: FactCreate):
    """Create a new fact (used for controlled evaluation benchmarks or manual ground truth)."""
    import uuid
    fact = Fact(
        fact_id=f"fact_{uuid.uuid4().hex[:12]}",
        **fact_in.model_dump()
    )
    FactRepository.save_facts([fact])
    return fact
