"""
Configurable embedding service supporting TF-IDF (instant local) and sentence-transformers.
Generates normalized semantic representations for facts.
"""

from typing import List, Optional
import numpy as np

from app.core.config import settings
from app.core.logging import logger
from app.models.fact import Fact


class EmbeddingService:
    _instance = None
    _st_model = None
    _tfidf_vectorizer = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.provider = settings.embedding_provider
        self.model_name = settings.embedding_model

    def _load_sentence_transformer(self):
        if self._st_model is None:
            try:
                # Check local cache first without long network hang
                from sentence_transformers import SentenceTransformer
                self._st_model = SentenceTransformer(self.model_name, local_files_only=True)
                logger.info("SentenceTransformer model loaded from local cache.")
            except Exception:
                try:
                    from sentence_transformers import SentenceTransformer
                    self._st_model = SentenceTransformer(self.model_name)
                except Exception as e:
                    logger.warning(f"SentenceTransformer offline/failed ({e}). Using robust TF-IDF embedding.")
                    self.provider = "tfidf"

    def embed_text(self, text: str) -> List[float]:
        """Generate embedding vector for a single text."""
        return self.embed_batch([text])[0]

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate normalized embedding vectors for a batch of strings."""
        if not texts:
            return []

        if self.provider == "sentence-transformers":
            self._load_sentence_transformer()
            if self._st_model is not None:
                try:
                    embeddings = self._st_model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
                    return [emb.tolist() for emb in embeddings]
                except Exception as e:
                    logger.warning(f"Sentence-transformer encoding failed: {e}. Falling back to TF-IDF.")
                    self.provider = "tfidf"

        # TF-IDF Fallback (deterministic, fast, zero network dependency)
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.preprocessing import normalize

        vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1, token_pattern=r"(?u)\b[\w-]+\b")
        try:
            vectors = vectorizer.fit_transform(texts).toarray()
            norm_vectors = normalize(vectors, norm="l2")
            return [v.tolist() for v in norm_vectors]
        except Exception:
            # Simple fallback if empty text
            return [[1.0] + [0.0] * 31 for _ in texts]

    def compute_similarity(self, vec_a: List[float], vec_b: List[float]) -> float:
        """Compute cosine similarity between two unit-normalized embedding vectors."""
        min_len = min(len(vec_a), len(vec_b))
        if min_len == 0:
            return 0.0
        a = np.array(vec_a[:min_len], dtype=np.float32)
        b = np.array(vec_b[:min_len], dtype=np.float32)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))
