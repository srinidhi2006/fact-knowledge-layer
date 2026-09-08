"""
Unit tests for PDF Parser and Text Extraction.
"""

from pathlib import Path
import pytest

from app.services.pdf_parser import PDFParser
from app.services.text_cleaner import TextCleaner


def test_pdf_parsing_delhivery_presentation():
    pdf_path = Path("delhivery/03-delhivery-q4-fy24-earnings-presentation.pdf")
    if not pdf_path.exists():
        pytest.skip("Delhivery presentation PDF not found in workspace")

    meta, pages = PDFParser.parse_pdf(str(pdf_path))

    assert meta.page_count == 27
    assert len(pages) == 27
    assert meta.document_type == "earnings_presentation"
    assert len(meta.file_hash) == 64  # SHA256 hex string

    # Verify Page 6 contents
    page_6 = next((p for p in pages if p.page_number == 6), None)
    assert page_6 is not None
    assert "8,142" in page_6.text or "8142" in page_6.text
    assert "740" in page_6.text


def test_text_cleaner():
    raw_text = "  Revenue from services   amounted to  \n\n\n  ₹8,142 crore  "
    cleaned = TextCleaner.clean(raw_text)
    assert "₹8,142 crore" in cleaned
    assert "\n\n\n" not in cleaned

    # Broken line wrapping
    wrapped = "The com-\n pany reported higher volume"
    cleaned_wrapped = TextCleaner.clean(wrapped)
    assert "company" in cleaned_wrapped


def test_cleaner_extract_context_window():
    full_text = "The financial review states that Revenue from services reached ₹81,415Mn in FY24 due to scale efficiencies."
    snippet = "Revenue from services reached ₹81,415Mn"
    ctx = TextCleaner.extract_context_window(full_text, snippet, window_chars=20)
    assert "Revenue from services reached ₹81,415Mn" in ctx
    assert len(ctx) > len(snippet)
