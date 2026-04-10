"""Web learning endpoints."""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends

from backend.dependencies import get_embedding_service, get_rag_service, get_vector_store
from backend.schemas.web_learn import WebLearnRequest, WebLearnResponse
from backend.services.embeddings import EmbeddingService
from backend.services.rag import RAGService
from backend.services.vector_store import VectorStore
from backend.services.web_learner import WebLearner

router = APIRouter(tags=["web_learn"])


@router.post("/web-learn", response_model=WebLearnResponse)
async def learn_from_web(
    req: WebLearnRequest,
    vs: VectorStore = Depends(get_vector_store),
    emb: EmbeddingService = Depends(get_embedding_service),
    rag: RAGService = Depends(get_rag_service),
):
    """Fetch a URL, extract text, and add to the knowledge base."""
    learner = WebLearner(vs, emb, rag)
    result = await learner.learn_from_url(
        url=req.url,
        persona_id=req.persona_id,
    )
    return WebLearnResponse(**result)
