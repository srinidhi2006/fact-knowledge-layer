"""
Integration tests for FastAPI endpoints.
"""

from datetime import datetime
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.database import init_db
from app.db.repositories import DocumentRepository, FactRepository, ComparisonRepository
from app.models.document import DocumentMetadata


@pytest.fixture(scope="module")
def client():
    init_db()
    
    # Pre-register test documents so foreign key constraints are satisfied
    doc1 = DocumentMetadata(
        document_id="test_doc_1",
        filename="test_doc1.pdf",
        file_path="data/uploads/test_doc1.pdf",
        document_type="annual_report",
        page_count=5,
        file_size_bytes=1024,
        file_hash="hash_test_1",
        status="parsed"
    )
    doc2 = DocumentMetadata(
        document_id="test_doc_2",
        filename="test_doc2.pdf",
        file_path="data/uploads/test_doc2.pdf",
        document_type="earnings_presentation",
        page_count=5,
        file_size_bytes=1024,
        file_hash="hash_test_2",
        status="parsed"
    )
    DocumentRepository.save_document(doc1)
    DocumentRepository.save_document(doc2)

    with TestClient(app) as c:
        yield c


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "statistics" in data
    assert "app_name" in data


def test_fact_creation_and_retrieval(client):
    fact_payload = {
        "source_document_id": "test_doc_1",
        "source_document_name": "test_doc1.pdf",
        "page_number": 1,
        "subject": "TestCompany",
        "predicate": "revenue_from_services",
        "value": "1000",
        "unit": "INR crore",
        "period": "FY24",
        "normalized_value": 10000.0,
        "normalized_unit": "INR million",
        "is_numerical": True,
        "evidence_text": "TestCompany revenue was 1000 crore in FY24",
        "confidence": 0.95
    }

    create_resp = client.post("/facts", json=fact_payload)
    assert create_resp.status_code == 200
    created = create_resp.json()
    fact_id = created["fact_id"]
    assert fact_id is not None

    get_resp = client.get(f"/facts/{fact_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["predicate"] == "revenue_from_services"

    list_resp = client.get("/facts?subject=TestCompany")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1


def test_comparisons_endpoints(client):
    # Add second fact from test_doc_2
    fact_payload_2 = {
        "source_document_id": "test_doc_2",
        "source_document_name": "test_doc2.pdf",
        "page_number": 3,
        "subject": "TestCompany",
        "predicate": "revenue_from_services",
        "value": "10000",
        "unit": "INR million",
        "period": "FY24",
        "normalized_value": 10000.0,
        "normalized_unit": "INR million",
        "is_numerical": True,
        "evidence_text": "TestCompany revenue reached 10,000 million in FY24",
        "confidence": 0.95
    }
    client.post("/facts", json=fact_payload_2)

    # Run comparisons
    run_resp = client.post("/comparisons/run", json={})
    assert run_resp.status_code == 200

    # Get summary
    summary_resp = client.get("/comparisons/summary")
    assert summary_resp.status_code == 200
    summary = summary_resp.json()
    assert summary["total_comparisons"] >= 1
    assert summary["corroborated_count"] >= 1
