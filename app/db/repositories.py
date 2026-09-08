"""
Data access repositories for Documents, Pages, Facts, and Comparisons.
"""

import json
from datetime import datetime
from typing import List, Optional, Tuple
from app.db.database import get_db
from app.models.document import DocumentMetadata, DocumentPage
from app.models.fact import Fact, FactFilter
from app.models.evidence import Evidence
from app.models.comparison import FactComparison, ComparisonSummary, RelationshipType


class DocumentRepository:
    @staticmethod
    def save_document(doc: DocumentMetadata) -> None:
        with get_db() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO documents 
                (document_id, filename, file_path, document_type, page_count, file_size_bytes, file_hash, status, error_message, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    doc.document_id, doc.filename, doc.file_path, doc.document_type,
                    doc.page_count, doc.file_size_bytes, doc.file_hash, doc.status,
                    doc.error_message, doc.created_at.isoformat()
                )
            )

    @staticmethod
    def save_pages(pages: List[DocumentPage]) -> None:
        with get_db() as conn:
            conn.executemany(
                """
                INSERT OR REPLACE INTO pages (page_id, document_id, page_number, text, char_count, word_count)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (p.page_id, p.document_id, p.page_number, p.text, p.char_count, p.word_count)
                    for p in pages
                ]
            )

    @staticmethod
    def get_document(doc_id: str) -> Optional[DocumentMetadata]:
        with get_db() as conn:
            row = conn.execute("SELECT * FROM documents WHERE document_id = ?", (doc_id,)).fetchone()
            if not row:
                return None
            return DocumentMetadata(
                document_id=row["document_id"],
                filename=row["filename"],
                file_path=row["file_path"],
                document_type=row["document_type"],
                page_count=row["page_count"],
                file_size_bytes=row["file_size_bytes"],
                file_hash=row["file_hash"],
                status=row["status"],
                error_message=row["error_message"],
                created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.utcnow()
            )

    @staticmethod
    def get_document_by_hash(file_hash: str) -> Optional[DocumentMetadata]:
        with get_db() as conn:
            row = conn.execute("SELECT * FROM documents WHERE file_hash = ?", (file_hash,)).fetchone()
            if not row:
                return None
            return DocumentMetadata(
                document_id=row["document_id"],
                filename=row["filename"],
                file_path=row["file_path"],
                document_type=row["document_type"],
                page_count=row["page_count"],
                file_size_bytes=row["file_size_bytes"],
                file_hash=row["file_hash"],
                status=row["status"],
                error_message=row["error_message"],
                created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.utcnow()
            )

    @staticmethod
    def list_documents() -> List[DocumentMetadata]:
        with get_db() as conn:
            rows = conn.execute("SELECT * FROM documents ORDER BY created_at DESC").fetchall()
            return [
                DocumentMetadata(
                    document_id=r["document_id"],
                    filename=r["filename"],
                    file_path=r["file_path"],
                    document_type=r["document_type"],
                    page_count=r["page_count"],
                    file_size_bytes=r["file_size_bytes"],
                    file_hash=r["file_hash"],
                    status=r["status"],
                    error_message=r["error_message"],
                    created_at=datetime.fromisoformat(r["created_at"]) if r["created_at"] else datetime.utcnow()
                )
                for r in rows
            ]

    @staticmethod
    def get_pages(doc_id: str) -> List[DocumentPage]:
        with get_db() as conn:
            rows = conn.execute(
                "SELECT * FROM pages WHERE document_id = ? ORDER BY page_number ASC", (doc_id,)
            ).fetchall()
            return [
                DocumentPage(
                    page_id=r["page_id"],
                    document_id=r["document_id"],
                    page_number=r["page_number"],
                    text=r["text"],
                    char_count=r["char_count"],
                    word_count=r["word_count"]
                )
                for r in rows
            ]

    @staticmethod
    def get_page(doc_id: str, page_number: int) -> Optional[DocumentPage]:
        with get_db() as conn:
            row = conn.execute(
                "SELECT * FROM pages WHERE document_id = ? AND page_number = ?", (doc_id, page_number)
            ).fetchone()
            if not row:
                return None
            return DocumentPage(
                page_id=row["page_id"],
                document_id=row["document_id"],
                page_number=row["page_number"],
                text=row["text"],
                char_count=row["char_count"],
                word_count=row["word_count"]
            )

    @staticmethod
    def update_status(doc_id: str, status: str, error: Optional[str] = None) -> None:
        with get_db() as conn:
            conn.execute(
                "UPDATE documents SET status = ?, error_message = ? WHERE document_id = ?",
                (status, error, doc_id)
            )

    @staticmethod
    def delete_document(doc_id: str) -> None:
        with get_db() as conn:
            conn.execute("DELETE FROM documents WHERE document_id = ?", (doc_id,))


class FactRepository:
    @staticmethod
    def save_facts(facts: List[Fact]) -> None:
        with get_db() as conn:
            conn.executemany(
                """
                INSERT OR REPLACE INTO facts 
                (fact_id, source_document_id, source_document_name, page_number, subject, predicate,
                 raw_value, raw_unit, period, scope, original_value, normalized_value, original_unit,
                 normalized_unit, is_numerical, evidence_text, confidence, extraction_method, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        f.fact_id, f.source_document_id, f.source_document_name, f.page_number,
                        f.subject, f.predicate, str(f.value), f.unit, f.period, f.scope,
                        str(f.original_value) if f.original_value is not None else str(f.value),
                        f.normalized_value, f.original_unit or f.unit, f.normalized_unit,
                        1 if f.is_numerical else 0, f.evidence_text, f.confidence,
                        f.extraction_method, f.created_at.isoformat()
                    )
                    for f in facts
                ]
            )

    @staticmethod
    def get_fact(fact_id: str) -> Optional[Fact]:
        with get_db() as conn:
            r = conn.execute("SELECT * FROM facts WHERE fact_id = ?", (fact_id,)).fetchone()
            if not r:
                return None
            return Fact(
                fact_id=r["fact_id"],
                source_document_id=r["source_document_id"],
                source_document_name=r["source_document_name"],
                page_number=r["page_number"],
                subject=r["subject"],
                predicate=r["predicate"],
                value=r["raw_value"],
                unit=r["raw_unit"],
                period=r["period"],
                scope=r["scope"],
                original_value=r["original_value"],
                normalized_value=r["normalized_value"],
                original_unit=r["original_unit"],
                normalized_unit=r["normalized_unit"],
                is_numerical=bool(r["is_numerical"]),
                evidence_text=r["evidence_text"],
                confidence=r["confidence"],
                extraction_method=r["extraction_method"],
                created_at=datetime.fromisoformat(r["created_at"]) if r["created_at"] else datetime.utcnow()
            )

    @staticmethod
    def list_facts(filter_params: Optional[FactFilter] = None) -> List[Fact]:
        query = "SELECT * FROM facts WHERE 1=1"
        args = []
        if filter_params:
            if filter_params.document_id:
                query += " AND source_document_id = ?"
                args.append(filter_params.document_id)
            if filter_params.subject:
                query += " AND subject LIKE ?"
                args.append(f"%{filter_params.subject}%")
            if filter_params.predicate:
                query += " AND predicate LIKE ?"
                args.append(f"%{filter_params.predicate}%")
            if filter_params.period:
                query += " AND period LIKE ?"
                args.append(f"%{filter_params.period}%")
            if filter_params.min_confidence is not None:
                query += " AND confidence >= ?"
                args.append(filter_params.min_confidence)

        query += " ORDER BY page_number ASC"
        with get_db() as conn:
            rows = conn.execute(query, tuple(args)).fetchall()
            return [
                Fact(
                    fact_id=r["fact_id"],
                    source_document_id=r["source_document_id"],
                    source_document_name=r["source_document_name"],
                    page_number=r["page_number"],
                    subject=r["subject"],
                    predicate=r["predicate"],
                    value=r["raw_value"],
                    unit=r["raw_unit"],
                    period=r["period"],
                    scope=r["scope"],
                    original_value=r["original_value"],
                    normalized_value=r["normalized_value"],
                    original_unit=r["original_unit"],
                    normalized_unit=r["normalized_unit"],
                    is_numerical=bool(r["is_numerical"]),
                    evidence_text=r["evidence_text"],
                    confidence=r["confidence"],
                    extraction_method=r["extraction_method"],
                    created_at=datetime.fromisoformat(r["created_at"]) if r["created_at"] else datetime.utcnow()
                )
                for r in rows
            ]

    @staticmethod
    def count_facts() -> int:
        with get_db() as conn:
            res = conn.execute("SELECT COUNT(*) as cnt FROM facts").fetchone()
            return res["cnt"] if res else 0

    @staticmethod
    def delete_facts_by_document(doc_id: str) -> None:
        with get_db() as conn:
            conn.execute("DELETE FROM facts WHERE source_document_id = ?", (doc_id,))

    @staticmethod
    def update_embedding(fact_id: str, embedding: List[float]) -> None:
        with get_db() as conn:
            conn.execute(
                "UPDATE facts SET embedding_json = ? WHERE fact_id = ?",
                (json.dumps(embedding), fact_id)
            )

    @staticmethod
    def get_facts_with_embeddings() -> List[Tuple[Fact, Optional[List[float]]]]:
        with get_db() as conn:
            rows = conn.execute("SELECT * FROM facts").fetchall()
            result = []
            for r in rows:
                fact = Fact(
                    fact_id=r["fact_id"],
                    source_document_id=r["source_document_id"],
                    source_document_name=r["source_document_name"],
                    page_number=r["page_number"],
                    subject=r["subject"],
                    predicate=r["predicate"],
                    value=r["raw_value"],
                    unit=r["raw_unit"],
                    period=r["period"],
                    scope=r["scope"],
                    original_value=r["original_value"],
                    normalized_value=r["normalized_value"],
                    original_unit=r["original_unit"],
                    normalized_unit=r["normalized_unit"],
                    is_numerical=bool(r["is_numerical"]),
                    evidence_text=r["evidence_text"],
                    confidence=r["confidence"],
                    extraction_method=r["extraction_method"],
                    created_at=datetime.fromisoformat(r["created_at"]) if r["created_at"] else datetime.utcnow()
                )
                emb = json.loads(r["embedding_json"]) if r["embedding_json"] else None
                result.append((fact, emb))
            return result


class ComparisonRepository:
    @staticmethod
    def save_comparisons(comparisons: List[FactComparison]) -> None:
        with get_db() as conn:
            conn.executemany(
                """
                INSERT OR REPLACE INTO fact_comparisons
                (comparison_id, fact_a_id, fact_b_id, relationship, confidence, reason,
                 differences_json, evidence_a_json, evidence_b_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        c.comparison_id, c.fact_a_id, c.fact_b_id, c.relationship.value,
                        c.confidence, c.reason, json.dumps(c.differences),
                        c.evidence_a.model_dump_json(), c.evidence_b.model_dump_json(),
                        c.created_at.isoformat()
                    )
                    for c in comparisons
                ]
            )

    @staticmethod
    def list_comparisons(relationship: Optional[str] = None) -> List[FactComparison]:
        query = "SELECT * FROM fact_comparisons WHERE 1=1"
        args = []
        if relationship:
            query += " AND relationship = ?"
            args.append(relationship.upper())
        query += " ORDER BY confidence DESC, created_at DESC"

        with get_db() as conn:
            rows = conn.execute(query, tuple(args)).fetchall()
            comparisons = []
            for r in rows:
                ev_a = Evidence.model_validate_json(r["evidence_a_json"])
                ev_b = Evidence.model_validate_json(r["evidence_b_json"])
                diffs = json.loads(r["differences_json"]) if r["differences_json"] else []
                
                # Fetch full fact details
                fact_a = FactRepository.get_fact(r["fact_a_id"])
                fact_b = FactRepository.get_fact(r["fact_b_id"])

                comparisons.append(
                    FactComparison(
                        comparison_id=r["comparison_id"],
                        fact_a_id=r["fact_a_id"],
                        fact_b_id=r["fact_b_id"],
                        relationship=RelationshipType(r["relationship"]),
                        confidence=r["confidence"],
                        reason=r["reason"],
                        differences=diffs,
                        evidence_a=ev_a,
                        evidence_b=ev_b,
                        fact_a=fact_a,
                        fact_b=fact_b,
                        created_at=datetime.fromisoformat(r["created_at"]) if r["created_at"] else datetime.utcnow()
                    )
                )
            return comparisons

    @staticmethod
    def get_comparison(comparison_id: str) -> Optional[FactComparison]:
        with get_db() as conn:
            r = conn.execute(
                "SELECT * FROM fact_comparisons WHERE comparison_id = ?", (comparison_id,)
            ).fetchone()
            if not r:
                return None
            ev_a = Evidence.model_validate_json(r["evidence_a_json"])
            ev_b = Evidence.model_validate_json(r["evidence_b_json"])
            diffs = json.loads(r["differences_json"]) if r["differences_json"] else []
            fact_a = FactRepository.get_fact(r["fact_a_id"])
            fact_b = FactRepository.get_fact(r["fact_b_id"])

            return FactComparison(
                comparison_id=r["comparison_id"],
                fact_a_id=r["fact_a_id"],
                fact_b_id=r["fact_b_id"],
                relationship=RelationshipType(r["relationship"]),
                confidence=r["confidence"],
                reason=r["reason"],
                differences=diffs,
                evidence_a=ev_a,
                evidence_b=ev_b,
                fact_a=fact_a,
                fact_b=fact_b,
                created_at=datetime.fromisoformat(r["created_at"]) if r["created_at"] else datetime.utcnow()
            )

    @staticmethod
    def get_summary() -> ComparisonSummary:
        with get_db() as conn:
            total = conn.execute("SELECT COUNT(*) as c FROM fact_comparisons").fetchone()["c"]
            corroborated = conn.execute(
                "SELECT COUNT(*) as c FROM fact_comparisons WHERE relationship = 'CORROBORATED'"
            ).fetchone()["c"]
            contradiction = conn.execute(
                "SELECT COUNT(*) as c FROM fact_comparisons WHERE relationship = 'CONTRADICTION'"
            ).fetchone()["c"]
            contextual = conn.execute(
                "SELECT COUNT(*) as c FROM fact_comparisons WHERE relationship = 'CONTEXTUAL'"
            ).fetchone()["c"]
            unknown = conn.execute(
                "SELECT COUNT(*) as c FROM fact_comparisons WHERE relationship = 'UNKNOWN'"
            ).fetchone()["c"]
            high_conf = conn.execute(
                "SELECT COUNT(*) as c FROM fact_comparisons WHERE confidence >= 0.85"
            ).fetchone()["c"]

            return ComparisonSummary(
                total_comparisons=total,
                corroborated_count=corroborated,
                contradiction_count=contradiction,
                contextual_count=contextual,
                unknown_count=unknown,
                high_confidence_count=high_conf
            )

    @staticmethod
    def clear_comparisons() -> None:
        with get_db() as conn:
            conn.execute("DELETE FROM fact_comparisons")
