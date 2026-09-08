"""
Semantic Fact Matcher for candidate pair generation across distinct documents.
"""

from typing import List, Tuple, Set
from app.core.config import settings
from app.core.logging import logger
from app.models.fact import Fact
from app.services.embedding_service import EmbeddingService


class FactMatcher:
    def __init__(self, threshold: float = settings.similarity_threshold):
        self.threshold = threshold
        self.embedding_service = EmbeddingService.get_instance()

    def generate_candidate_pairs(self, facts: List[Fact]) -> List[Tuple[Fact, Fact, float]]:
        """
        Generate candidate pairs of facts across different documents.
        Filters by:
        - Cross-document requirement (doc_a != doc_b)
        - Predicate compatibility or high semantic similarity
        - Deduplication of (A, B) and (B, A)
        """
        if len(facts) < 2:
            return []

        # Prepare embedding representations
        texts = [f.to_embedding_text() for f in facts]
        embeddings = self.embedding_service.embed_batch(texts)

        candidates: List[Tuple[Fact, Fact, float]] = []
        seen_pairs: Set[Tuple[str, str]] = set()

        n = len(facts)
        for i in range(n):
            fact_a = facts[i]
            emb_a = embeddings[i]

            for j in range(i + 1, n):
                fact_b = facts[j]
                emb_b = embeddings[j]

                # Rule 1: Must be from different documents
                if fact_a.source_document_id == fact_b.source_document_id:
                    continue

                pair_key = (min(fact_a.fact_id, fact_b.fact_id), max(fact_a.fact_id, fact_b.fact_id))
                if pair_key in seen_pairs:
                    continue

                sim_score = self.embedding_service.compute_similarity(emb_a, emb_b)

                # Matching logic:
                # Direct predicate match (highest confidence candidate)
                is_direct_predicate_match = (
                    fact_a.predicate == fact_b.predicate and 
                    fact_a.subject.lower() == fact_b.subject.lower()
                )

                # High semantic similarity above threshold
                is_semantic_match = sim_score >= self.threshold

                if is_direct_predicate_match or is_semantic_match:
                    score = max(sim_score, 0.90 if is_direct_predicate_match else sim_score)
                    candidates.append((fact_a, fact_b, float(score)))
                    seen_pairs.add(pair_key)

        logger.info(f"Generated {len(candidates)} candidate cross-document pairs from {len(facts)} facts")
        return candidates
