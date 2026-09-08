"""
API Routes for Document Upload, Parsing, and Management.
"""

import shutil
import uuid
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel

from app.core.config import settings
from app.core.logging import logger
from app.models.document import DocumentMetadata, DocumentPage
from app.db.repositories import DocumentRepository, FactRepository
from app.services.pdf_parser import PDFParser
from app.services.fact_extractor import FactExtractor

router = APIRouter(prefix="/documents", tags=["Documents"])


class ProcessRequest(BaseModel):
    document_ids: Optional[List[str]] = None
    subject_hint: str = "Delhivery"


@router.post("/upload", response_model=List[DocumentMetadata])
async def upload_documents(files: List[UploadFile] = File(...)):
    """Upload one or multiple PDF documents and store initial metadata."""
    uploaded_docs: List[DocumentMetadata] = []

    for file in files:
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail=f"File '{file.filename}' is not a PDF")

        doc_id = f"doc_{uuid.uuid4().hex[:10]}"
        dest_path = settings.uploads_dir / f"{doc_id}_{file.filename}"

        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        try:
            metadata, pages = PDFParser.parse_pdf(str(dest_path), document_id=doc_id)
            metadata.filename = file.filename
            DocumentRepository.save_document(metadata)
            DocumentRepository.save_pages(pages)
            uploaded_docs.append(metadata)
        except Exception as e:
            logger.error(f"Error processing uploaded PDF {file.filename}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to process {file.filename}: {str(e)}")

    return uploaded_docs


@router.post("/process")
def process_documents(req: ProcessRequest):
    """
    Process uploaded documents: parse pages (if not already parsed) and extract facts.
    """
    docs_to_process = []
    if req.document_ids:
        for d_id in req.document_ids:
            doc = DocumentRepository.get_document(d_id)
            if doc:
                docs_to_process.append(doc)
    else:
        docs_to_process = DocumentRepository.list_documents()

    total_facts_extracted = 0
    results = []

    for doc in docs_to_process:
        pages = DocumentRepository.get_pages(doc.document_id)
        if not pages:
            # Try parsing if not yet parsed
            try:
                meta, pages = PDFParser.parse_pdf(doc.file_path, document_id=doc.document_id)
                DocumentRepository.save_pages(pages)
            except Exception as e:
                DocumentRepository.update_status(doc.document_id, "failed", str(e))
                continue

        doc_facts = []
        for page in pages:
            extracted = FactExtractor.extract_facts_from_page(
                page=page,
                document_name=doc.filename,
                subject_hint=req.subject_hint
            )
            doc_facts.extend(extracted)

        FactRepository.save_facts(doc_facts)
        DocumentRepository.update_status(doc.document_id, "extracted")
        total_facts_extracted += len(doc_facts)
        results.append({
            "document_id": doc.document_id,
            "filename": doc.filename,
            "pages_count": len(pages),
            "facts_extracted": len(doc_facts)
        })

    return {
        "status": "success",
        "processed_documents": len(results),
        "total_facts_extracted": total_facts_extracted,
        "details": results
    }


@router.get("", response_model=List[DocumentMetadata])
def list_documents():
    """List all registered documents."""
    return DocumentRepository.list_documents()


@router.get("/{document_id}", response_model=DocumentMetadata)
def get_document(document_id: str):
    """Get metadata for a specific document."""
    doc = DocumentRepository.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.get("/{document_id}/pages", response_model=List[DocumentPage])
def get_document_pages(document_id: str):
    """Retrieve all extracted pages for a document."""
    pages = DocumentRepository.get_pages(document_id)
    if not pages:
        raise HTTPException(status_code=404, detail="No pages found for document")
    return pages


@router.delete("/{document_id}")
def delete_document(document_id: str):
    """Delete a document, its extracted pages, and its associated facts."""
    doc = DocumentRepository.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    FactRepository.delete_facts_by_document(document_id)
    DocumentRepository.delete_document(document_id)

    # Delete physical file if in uploads dir
    p = Path(doc.file_path)
    if p.exists() and settings.uploads_dir in p.parents:
        try:
            p.unlink()
        except Exception:
            pass

    return {"status": "deleted", "document_id": document_id}
