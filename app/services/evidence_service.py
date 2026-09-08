"""
Evidence service for linking, expanding, and retrieving contextual evidence for facts.
"""

from typing import Optional
from app.db.repositories import DocumentRepository, FactRepository
from app.models.evidence import Evidence
from app.models.fact import Fact
from app.services.text_cleaner import TextCleaner


class EvidenceService:
    @staticmethod
    def get_evidence_for_fact(fact: Fact) -> Evidence:
        """
        Build an Evidence object for a fact with surrounding context extracted
        directly from the stored database page text.
        """
        page = DocumentRepository.get_page(fact.source_document_id, fact.page_number)
        surrounding_context = None
        char_start = None
        char_end = None

        if page and page.text:
            idx = page.text.find(fact.evidence_text)
            if idx != -1:
                char_start = idx
                char_end = idx + len(fact.evidence_text)
            surrounding_context = TextCleaner.extract_context_window(
                page.text, fact.evidence_text, window_chars=200
            )

        return Evidence(
            document_id=fact.source_document_id,
            document_name=fact.source_document_name,
            page_number=fact.page_number,
            evidence_text=fact.evidence_text,
            surrounding_context=surrounding_context,
            char_start=char_start,
            char_end=char_end
        )
