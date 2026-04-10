"""RAG (Retrieval-Augmented Generation) service."""

from __future__ import annotations

from backend.services.embeddings import EmbeddingService
from backend.services.vector_store import VectorStore


class RAGService:
    def __init__(
        self,
        vector_store: VectorStore,
        embedding_service: EmbeddingService,
        top_k: int = 5,
    ) -> None:
        self._vs = vector_store
        self._emb = embedding_service
        self._top_k = top_k

    def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        persona_id: str = "",
    ) -> list[dict]:
        """Retrieve relevant chunks for a query."""
        if self._vs.count == 0:
            return []

        query_vec = self._emb.encode_query(query)
        k = top_k or self._top_k

        filter_fn = None
        if persona_id:
            filter_fn = lambda m: m.get("persona_id") == persona_id

        return self._vs.search(query_vec, k=k, filter_fn=filter_fn)

    def build_context(self, results: list[dict]) -> str:
        """Format retrieved results into context text."""
        if not results:
            return ""

        lines = []
        for r in results:
            speaker = r.get("speaker", "")
            text = r.get("text", "")
            if speaker:
                lines.append(f"[{speaker}]: {text}")
            else:
                lines.append(text)

        return "\n".join(lines)

    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
        """Split text into overlapping chunks."""
        if len(text) <= chunk_size:
            return [text] if text.strip() else []

        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            start = end - overlap

        return chunks
