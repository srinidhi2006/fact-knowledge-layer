"""
API Routes for Cross-Document Fact Comparison and Reconciliation.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.models.comparison import FactComparison, ComparisonSummary, RelationshipType
from app.db.repositories import FactRepository, ComparisonRepository
from app.services.fact_matcher import FactMatcher
from app.services.comparison_engine import ComparisonEngine

router = APIRouter(prefix="/comparisons", tags=["Comparisons"])


class RunComparisonRequest(BaseModel):
    document_ids: Optional[List[str]] = None
    similarity_threshold: Optional[float] = None
    numeric_tolerance: Optional[float] = None


@router.post("/run", response_model=List[FactComparison])
def run_comparisons(req: Optional[RunComparisonRequest] = None):
    """
    Run candidate pair matching and comparison engine across all facts.
    Identifies Corroborations, Contradictions, Contextual differences, and Unknown relationships.
    """
    facts = FactRepository.list_facts()
    if req and req.document_ids:
        facts = [f for f in facts if f.source_document_id in req.document_ids]

    if len(facts) < 2:
        return []

    threshold = req.similarity_threshold if req and req.similarity_threshold else None
    matcher = FactMatcher(threshold=threshold) if threshold else FactMatcher()
    candidate_pairs = matcher.generate_candidate_pairs(facts)

    tol = req.numeric_tolerance if req and req.numeric_tolerance else None
    engine = ComparisonEngine(numeric_tolerance=tol) if tol else ComparisonEngine()

    comparisons: List[FactComparison] = []
    for fact_a, fact_b, score in candidate_pairs:
        comparison = engine.compare_fact_pair(fact_a, fact_b)
        comparisons.append(comparison)

    ComparisonRepository.clear_comparisons()
    ComparisonRepository.save_comparisons(comparisons)
    return comparisons


@router.get("", response_model=List[FactComparison])
def list_comparisons(
    relationship: Optional[str] = Query(None, description="Filter by: CORROBORATED, CONTRADICTION, CONTEXTUAL, UNKNOWN")
):
    """Retrieve comparisons with optional relationship filtering."""
    return ComparisonRepository.list_comparisons(relationship)


@router.get("/summary", response_model=ComparisonSummary)
def get_comparison_summary():
    """Retrieve summary counts for Dashboard cards."""
    return ComparisonRepository.get_summary()


@router.get("/{comparison_id}", response_model=FactComparison)
def get_comparison(comparison_id: str):
    """Retrieve details of a single comparison."""
    comp = ComparisonRepository.get_comparison(comparison_id)
    if not comp:
        raise HTTPException(status_code=404, detail="Comparison not found")
    return comp


@router.delete("")
def clear_all_comparisons():
    """Clear all stored comparisons."""
    ComparisonRepository.clear_comparisons()
    return {"status": "cleared"}
