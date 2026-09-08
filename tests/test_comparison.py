"""
Unit tests for Comparison Engine relationship classification.
Tests: CORROBORATED, CONTRADICTION, CONTEXTUAL, and UNKNOWN.
"""

import pytest
from app.models.fact import Fact
from app.models.comparison import RelationshipType
from app.services.comparison_engine import ComparisonEngine


@pytest.fixture
def comparison_engine():
    return ComparisonEngine(numeric_tolerance=0.015)


def test_corroboration_with_unit_conversion(comparison_engine):
    # Fact A: 81,415 INR million (Annual report)
    # Fact B: 8,142 INR crore -> 81,420 INR million (Presentation)
    fact_a = Fact(
        fact_id="fa",
        source_document_id="doc_ar",
        source_document_name="annual_report.pdf",
        page_number=4,
        subject="Delhivery",
        predicate="revenue_from_services",
        value=81415,
        unit="INR million",
        period="FY24",
        normalized_value=81415.0,
        normalized_unit="INR million",
        evidence_text="₹81,415Mn Revenue from services"
    )
    fact_b = Fact(
        fact_id="fb",
        source_document_id="doc_pr",
        source_document_name="presentation.pdf",
        page_number=6,
        subject="Delhivery",
        predicate="revenue_from_services",
        value=8142,
        unit="INR crore",
        period="FY24",
        normalized_value=81420.0,
        normalized_unit="INR million",
        evidence_text="₹8,142 Cr FY24 revenue from services"
    )

    result = comparison_engine.compare_fact_pair(fact_a, fact_b)
    assert result.relationship == RelationshipType.CORROBORATED
    assert result.confidence >= 0.90
    assert "rounding" in result.reason.lower() or "equivalent" in result.reason.lower()


def test_contradiction_detection(comparison_engine):
    # Same metric, same period, but materially different: 81,415 vs 65,000
    fact_a = Fact(
        fact_id="fa",
        source_document_id="doc_ar",
        source_document_name="annual_report.pdf",
        page_number=4,
        subject="Delhivery",
        predicate="revenue_from_services",
        value=81415,
        unit="INR million",
        period="FY24",
        normalized_value=81415.0,
        normalized_unit="INR million",
        evidence_text="₹81,415Mn Revenue from services"
    )
    fact_b = Fact(
        fact_id="fb",
        source_document_id="doc_syn",
        source_document_name="other.pdf",
        page_number=1,
        subject="Delhivery",
        predicate="revenue_from_services",
        value=65000,
        unit="INR million",
        period="FY24",
        normalized_value=65000.0,
        normalized_unit="INR million",
        evidence_text="₹65,000Mn Revenue from services"
    )

    result = comparison_engine.compare_fact_pair(fact_a, fact_b)
    assert result.relationship == RelationshipType.CONTRADICTION
    assert "discrepancy" in result.reason.lower() or "conflicting" in result.reason.lower()
    assert len(result.differences) > 0


def test_contextual_quarter_vs_full_year(comparison_engine):
    # Q4 FY24 (2,076 Cr = 20,760 Mn) vs Full Year FY24 (81,415 Mn)
    fact_q4 = Fact(
        fact_id="fq4",
        source_document_id="doc_pr",
        source_document_name="presentation.pdf",
        page_number=7,
        subject="Delhivery",
        predicate="revenue_from_services",
        value=2076,
        unit="INR crore",
        period="Q4 FY24",
        normalized_value=20760.0,
        normalized_unit="INR million",
        evidence_text="₹2,076 Cr Q4 FY24 revenue from services"
    )
    fact_fy = Fact(
        fact_id="ffy",
        source_document_id="doc_ar",
        source_document_name="annual_report.pdf",
        page_number=4,
        subject="Delhivery",
        predicate="revenue_from_services",
        value=81415,
        unit="INR million",
        period="FY24",
        normalized_value=81415.0,
        normalized_unit="INR million",
        evidence_text="₹81,415Mn Revenue from services"
    )

    result = comparison_engine.compare_fact_pair(fact_q4, fact_fy)
    assert result.relationship == RelationshipType.CONTEXTUAL
    assert "time windows" in result.reason.lower() or "period" in result.reason.lower()


def test_contextual_fiscal_year_difference(comparison_engine):
    # FY23 (72,236 Mn) vs FY24 (81,415 Mn)
    fact_fy23 = Fact(
        fact_id="f23",
        source_document_id="doc_ar",
        source_document_name="annual_report.pdf",
        page_number=6,
        subject="Delhivery",
        predicate="revenue_from_services",
        value=72236,
        unit="INR million",
        period="FY23",
        normalized_value=72236.0,
        normalized_unit="INR million",
        evidence_text="72,236 FY23"
    )
    fact_fy24 = Fact(
        fact_id="f24",
        source_document_id="doc_pr",
        source_document_name="presentation.pdf",
        page_number=6,
        subject="Delhivery",
        predicate="revenue_from_services",
        value=8142,
        unit="INR crore",
        period="FY24",
        normalized_value=81420.0,
        normalized_unit="INR million",
        evidence_text="₹8,142 Cr FY24"
    )

    result = comparison_engine.compare_fact_pair(fact_fy23, fact_fy24)
    assert result.relationship == RelationshipType.CONTEXTUAL


def test_contextual_inception_vs_annual_scope(comparison_engine):
    # Inception to date (>2.8Bn = 2,800 Mn) vs Annual FY24 (740 Mn)
    fact_inc = Fact(
        fact_id="f_inc",
        source_document_id="doc_ar",
        source_document_name="annual_report.pdf",
        page_number=2,
        subject="Delhivery",
        predicate="express_parcel_shipments",
        value="2.8",
        unit="Bn",
        period="Inception to Date",
        scope="since inception",
        normalized_value=2800.0,
        normalized_unit="million",
        evidence_text=">2.8Bn Express parcel shipments delivered since inception"
    )
    fact_fy24 = Fact(
        fact_id="f_fy24",
        source_document_id="doc_pr",
        source_document_name="presentation.pdf",
        page_number=6,
        subject="Delhivery",
        predicate="express_parcel_shipments",
        value="740",
        unit="Mn",
        period="FY24",
        normalized_value=740.0,
        normalized_unit="million",
        evidence_text="740 Mn Express parcel shipments in FY24"
    )

    result = comparison_engine.compare_fact_pair(fact_inc, fact_fy24)
    assert result.relationship == RelationshipType.CONTEXTUAL
    assert "scope" in result.reason.lower() or "cumulative" in result.reason.lower()


def test_unknown_incompatible_units(comparison_engine):
    # Cannot compare tonnes with INR million
    fact_tonnes = Fact(
        fact_id="ft",
        source_document_id="doc_1",
        source_document_name="doc1.pdf",
        page_number=1,
        subject="Delhivery",
        predicate="freight_volume",
        value=1429000,
        unit="tonnes",
        period="FY24",
        normalized_value=1429000.0,
        normalized_unit="tonnes",
        evidence_text="1,429K tonnes freight"
    )
    fact_inr = Fact(
        fact_id="fi",
        source_document_id="doc_2",
        source_document_name="doc2.pdf",
        page_number=1,
        subject="Delhivery",
        predicate="freight_volume",
        value=15174,
        unit="INR million",
        period="FY24",
        normalized_value=15174.0,
        normalized_unit="INR million",
        evidence_text="₹15,174Mn freight"
    )

    result = comparison_engine.compare_fact_pair(fact_tonnes, fact_inr)
    assert result.relationship == RelationshipType.UNKNOWN
