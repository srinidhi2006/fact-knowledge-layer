"""
CLI Script to Ingest Datasets into Fact Knowledge Layer.
Parses PDFs, extracts grounded facts, generates embeddings, and executes reconciliation.
"""

import argparse
import sys
from pathlib import Path

# UTF-8 stdout support on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from app.core.config import settings
from app.core.logging import logger
from app.db.database import init_db
from app.db.repositories import DocumentRepository, FactRepository, ComparisonRepository
from app.services.pdf_parser import PDFParser
from app.services.fact_extractor import FactExtractor
from app.services.fact_matcher import FactMatcher
from app.services.comparison_engine import ComparisonEngine


def ingest_folder(folder_path: Path, subject_hint: str):
    init_db()
    pdf_files = sorted(list(folder_path.glob("*.pdf")))
    if not pdf_files:
        print(f"No PDF files found in: {folder_path}")
        return

    print(f"\n=======================================================")
    print(f"INGESTING DATASET FROM: {folder_path.name}")
    print(f"Found {len(pdf_files)} PDF documents to process")
    print(f"=======================================================")

    total_facts = 0
    for idx, pdf in enumerate(pdf_files, 1):
        print(f"\n[{idx}/{len(pdf_files)}] Parsing: {pdf.name}...")
        meta, pages = PDFParser.parse_pdf(str(pdf))
        DocumentRepository.save_document(meta)
        DocumentRepository.save_pages(pages)
        print(f"  Extracted {len(pages)} pages.")

        facts = []
        for p in pages:
            ext = FactExtractor.extract_facts_from_page(
                page=p,
                document_name=pdf.name,
                subject_hint=subject_hint
            )
            facts.extend(ext)

        FactRepository.save_facts(facts)
        DocumentRepository.update_status(meta.document_id, "extracted")
        total_facts += len(facts)
        print(f"  Extracted {len(facts)} grounded facts.")

    print(f"\nTotal facts extracted across dataset: {total_facts}")
    print("Running cross-document semantic matching and comparison...")

    all_facts = FactRepository.list_facts()
    matcher = FactMatcher()
    candidate_pairs = matcher.generate_candidate_pairs(all_facts)
    print(f"Generated {len(candidate_pairs)} candidate comparison pairs.")

    engine = ComparisonEngine()
    comparisons = [engine.compare_fact_pair(fa, fb) for fa, fb, _ in candidate_pairs]

    ComparisonRepository.clear_comparisons()
    ComparisonRepository.save_comparisons(comparisons)

    summary = ComparisonRepository.get_summary()
    print("\n" + "=" * 55)
    print("RECONCILIATION SUMMARY")
    print("=" * 55)
    print(f"Total Comparisons Reconciled : {summary.total_comparisons}")
    print(f"  🟢 Corroborated Relationships : {summary.corroborated_count}")
    print(f"  🔴 Contradictions Detected    : {summary.contradiction_count}")
    print(f"  🟡 Contextual Differences     : {summary.contextual_count}")
    print(f"  ⚪ Unknown / Uncertain Cases   : {summary.unknown_count}")
    print("=" * 55 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Ingest PDF dataset into Fact Knowledge Layer")
    parser.add_argument(
        "--dataset",
        choices=["delhivery", "india-macroeconomy"],
        default="delhivery",
        help="Predefined dataset to ingest"
    )
    parser.add_argument(
        "--path",
        type=str,
        default=None,
        help="Custom folder path containing PDF files"
    )
    parser.add_argument(
        "--subject",
        type=str,
        default=None,
        help="Subject hint (e.g. 'Delhivery' or 'India Economy')"
    )

    args = parser.parse_args()

    if args.path:
        target_path = Path(args.path)
        subject = args.subject or "Entity"
    else:
        target_path = root_dir / args.dataset
        subject = "Delhivery" if args.dataset == "delhivery" else "India Economy"

    ingest_folder(target_path, subject)


if __name__ == "__main__":
    main()
