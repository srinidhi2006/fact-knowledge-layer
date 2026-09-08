"""
PyMuPDF-based page-aware PDF parser.
Extracts text page-by-page, preserving document-page-chunk relationships.
"""

import hashlib
import uuid
from pathlib import Path
from typing import Tuple, List, Optional
import pymupdf

from app.core.logging import logger
from app.core.exceptions import DocumentParsingError
from app.models.document import DocumentMetadata, DocumentPage
from app.services.text_cleaner import TextCleaner


class PDFParser:
    @staticmethod
    def compute_file_hash(file_path: Path) -> str:
        """Calculate SHA256 hash of the file."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    @staticmethod
    def infer_document_type(filename: str, first_pages_text: str) -> str:
        """Infer document type based on filename and header text."""
        name_lower = filename.lower()
        text_lower = first_pages_text.lower()

        if "prospectus" in name_lower or "prospectus" in text_lower:
            return "prospectus"
        elif "annual-report" in name_lower or "annual report" in text_lower:
            return "annual_report"
        elif "earnings" in name_lower or "presentation" in name_lower or "investor presentation" in text_lower:
            return "earnings_presentation"
        elif "economic-survey" in name_lower or "economic survey" in text_lower:
            return "economic_survey"
        elif "rbi" in name_lower:
            return "central_bank_report"
        elif "imf" in name_lower or "article iv" in text_lower:
            return "multilateral_report"
        return "corporate_report"

    @classmethod
    def parse_pdf(cls, file_path: str, document_id: Optional[str] = None) -> Tuple[DocumentMetadata, List[DocumentPage]]:
        """
        Parse PDF file page by page.
        Returns document metadata and list of extracted page records.
        """
        path = Path(file_path)
        if not path.exists():
            raise DocumentParsingError(f"PDF file not found at: {file_path}")

        doc_id = document_id or f"doc_{uuid.uuid4().hex[:10]}"
        file_hash = cls.compute_file_hash(path)
        file_size = path.stat().st_size

        try:
            doc = pymupdf.open(str(path))
        except Exception as e:
            logger.error(f"Failed to open PDF {file_path}: {e}")
            raise DocumentParsingError(f"Failed to open PDF: {e}")

        pages: List[DocumentPage] = []
        sampled_text = ""

        try:
            for page_idx in range(len(doc)):
                page_number = page_idx + 1  # 1-indexed
                page = doc[page_idx]
                raw_text = page.get_text() or ""
                cleaned_text = TextCleaner.clean(raw_text)

                if page_idx < 3:
                    sampled_text += " " + cleaned_text[:300]

                page_id = f"{doc_id}_p{page_number}"
                pages.append(
                    DocumentPage(
                        page_id=page_id,
                        document_id=doc_id,
                        page_number=page_number,
                        text=cleaned_text,
                        char_count=len(cleaned_text),
                        word_count=len(cleaned_text.split())
                    )
                )
        except Exception as e:
            logger.error(f"Error reading pages from {file_path}: {e}")
            raise DocumentParsingError(f"Failed during page extraction: {e}")
        finally:
            doc.close()

        doc_type = cls.infer_document_type(path.name, sampled_text)

        metadata = DocumentMetadata(
            document_id=doc_id,
            filename=path.name,
            file_path=str(path.resolve()),
            document_type=doc_type,
            page_count=len(pages),
            file_size_bytes=file_size,
            file_hash=file_hash,
            status="parsed"
        )

        logger.info(f"Parsed {path.name}: {len(pages)} pages extracted (doc_id={doc_id})")
        return metadata, pages
