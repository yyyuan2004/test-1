"""FAISS-based vector store with metadata sidecar."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np


class VectorStore:
    def __init__(self, dimension: int, index_dir: Path) -> None:
        self._dimension = dimension
        self._index_dir = index_dir
        self._index = None
        self._metadata: list[dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        import faiss

        index_path = self._index_dir / "index.faiss"
        meta_path = self._index_dir / "metadata.json"

        if index_path.exists() and meta_path.exists():
            self._index = faiss.read_index(str(index_path))
            self._metadata = json.loads(meta_path.read_text(encoding="utf-8"))
        else:
            self._index = faiss.IndexFlatIP(self._dimension)
            self._metadata = []

    def save(self) -> None:
        import faiss

        self._index_dir.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self._index, str(self._index_dir / "index.faiss"))
        (self._index_dir / "metadata.json").write_text(
            json.dumps(self._metadata, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @property
    def count(self) -> int:
        return self._index.ntotal if self._index else 0

    def add(self, vectors: np.ndarray, metadatas: list[dict]) -> None:
        assert len(vectors) == len(metadatas)
        self._index.add(vectors)
        self._metadata.extend(metadatas)

    def search(
        self,
        query_vector: np.ndarray,
        k: int = 5,
        filter_fn: Any = None,
    ) -> list[dict]:
        """Search for nearest neighbours. Returns list of metadata dicts with score."""
        if self._index.ntotal == 0:
            return []

        # Search more than k to allow for filtering
        search_k = min(k * 3, self._index.ntotal)
        query = query_vector.reshape(1, -1)
        scores, indices = self._index.search(query, search_k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            meta = self._metadata[idx].copy()
            meta["_score"] = float(score)
            if filter_fn and not filter_fn(meta):
                continue
            results.append(meta)
            if len(results) >= k:
                break

        return results

    def clear(self) -> None:
        import faiss

        self._index = faiss.IndexFlatIP(self._dimension)
        self._metadata = []
