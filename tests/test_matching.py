"""
Unit tests for Semantic Fact Matching and Candidate Pair Generation.
"""

import pytest
from app.models.fact import Fact
from app.services.fact_matcher import FactMatcher


def test_fact_matching_cross_document_filtering():
    # Two facts from the SAME document should NOT be paired
    fact_a1 = Fact(
        fact_id="f1",
        source_document_id="doc_1",
        source_document_name="doc1.pdf",
        page_number=1,
        subject="Delhivery",
        predicate="revenue_from_services",
        value=81415,
        unit="INR million",
        period="FY24",
        normalized_value=81415.0,
        normalized_unit="INR million",
        evidence_text="Evidence 1"
    )
    fact_a2 = Fact(
        fact_id="f2",
        source_document_id="doc_1",
        source_document_name="doc1.pdf",
        page_number=2,
        subject="Delhivery",
        predicate="revenue_from_services",
        value=81420,
        unit="INR million",
        period="FY24",
        normalized_value=81420.0,
        normalized_unit="INR million",
        evidence_text="Evidence 2"
    )

    matcher = FactMatcher()
    pairs = matcher.generate_candidate_pairs([fact_a1, fact_a2])
    assert len(pairs) == 0  # Ignored because both are from doc_1


def test_fact_matching_cross_document_success():
    # Two facts from DIFFERENT documents with same predicate
    fact_a = Fact(
        fact_id="fa",
        source_document_id="doc_1",
        source_document_name="doc1.pdf",
        page_number=1,
        subject="Delhivery",
        predicate="revenue_from_services",
        value=81415,
        unit="INR million",
        period="FY24",
        normalized_value=81415.0,
        normalized_unit="INR million",
        evidence_text="Evidence A"
    )
    fact_b = Fact(
        fact_id="fb",
        source_document_id="doc_2",
        source_document_name="doc2.pdf",
        page_number=5,
        subject="Delhivery",
        predicate="revenue_from_services",
        value=8142,
        unit="INR crore",
        period="FY24",
        normalized_value=81420.0,
        normalized_unit="INR million",
        evidence_text="Evidence B"
    )

    matcher = FactMatcher()
    pairs = matcher.generate_candidate_pairs([fact_a, fact_b])
    assert len(pairs) == 1
    assert pairs[0][0].fact_id == "fa"
    assert pairs[0][1].fact_id == "fb"
    assert pairs[0][2] >= 0.6  # Similarity score
