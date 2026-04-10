"""Sentence-transformers embedding service."""

from __future__ import annotations

import numpy as np


class EmbeddingService:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        self._model_name = model_name
        self._model = None

    def _ensure_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self._model_name)

    @property
    def dimension(self) -> int:
        """Return embedding dimension (384 for MiniLM)."""
        self._ensure_model()
        return self._model.get_sentence_embedding_dimension()

    def encode(self, texts: list[str]) -> np.ndarray:
        """Encode texts into normalized vectors."""
        self._ensure_model()
        embeddings = self._model.encode(texts, normalize_embeddings=True)
        return np.array(embeddings, dtype=np.float32)

    def encode_query(self, text: str) -> np.ndarray:
        return self.encode([text])[0]
