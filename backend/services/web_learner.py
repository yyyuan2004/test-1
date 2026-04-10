"""Web learning module — fetch, extract, chunk, embed, and store web content."""

from __future__ import annotations

import httpx
from bs4 import BeautifulSoup

from backend.services.embeddings import EmbeddingService
from backend.services.rag import RAGService
from backend.services.vector_store import VectorStore


class WebLearner:
    def __init__(
        self,
        vector_store: VectorStore,
        embedding_service: EmbeddingService,
        rag_service: RAGService,
    ) -> None:
        self._vs = vector_store
        self._emb = embedding_service
        self._rag = rag_service

    async def learn_from_url(
        self, url: str, persona_id: str = "", chunk_size: int = 500
    ) -> dict:
        """Fetch a URL, extract text, chunk, embed, and store.

        Returns a summary dict with stats.
        """
        # Fetch
        async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
            resp = await client.get(url)
            resp.raise_for_status()

        # Extract text
        soup = BeautifulSoup(resp.text, "html.parser")
        # Remove script and style elements
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)

        if not text.strip():
            return {"url": url, "chunks": 0, "status": "no_content"}

        # Chunk
        chunks = self._rag.chunk_text(text, chunk_size=chunk_size)
        if not chunks:
            return {"url": url, "chunks": 0, "status": "no_content"}

        # Embed
        vectors = self._emb.encode(chunks)

        # Store with metadata
        metadatas = [
            {
                "text": chunk,
                "source": url,
                "source_type": "web",
                "persona_id": persona_id,
                "chunk_index": i,
            }
            for i, chunk in enumerate(chunks)
        ]
        self._vs.add(vectors, metadatas)
        self._vs.save()

        return {"url": url, "chunks": len(chunks), "status": "success"}
