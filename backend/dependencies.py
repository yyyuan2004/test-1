"""Shared dependency injection — singletons initialised at startup."""

from __future__ import annotations

from backend.services.vector_store import VectorStore
from backend.services.embeddings import EmbeddingService
from backend.services.llm_router import LLMRouter
from backend.services.chat_service import ChatService
from backend.services.rag import RAGService
from backend.models.conversation import ConversationStore
from config.settings import get_settings

# ---- singletons (populated by startup()) ----
_embedding_service: EmbeddingService | None = None
_vector_store: VectorStore | None = None
_llm_router: LLMRouter | None = None
_rag_service: RAGService | None = None
_chat_service: ChatService | None = None
_conversation_store: ConversationStore | None = None


async def startup() -> None:
    global _embedding_service, _vector_store, _llm_router
    global _rag_service, _chat_service, _conversation_store

    settings = get_settings()

    _embedding_service = EmbeddingService(settings.embedding_model)
    _vector_store = VectorStore(
        dimension=_embedding_service.dimension,
        index_dir=settings.faiss_index_dir,
    )
    _llm_router = LLMRouter(settings)
    _rag_service = RAGService(
        vector_store=_vector_store,
        embedding_service=_embedding_service,
        top_k=settings.rag_top_k,
    )
    _conversation_store = ConversationStore(settings.db_path)
    await _conversation_store.init()

    _chat_service = ChatService(
        llm=_llm_router,
        rag=_rag_service,
        conversations=_conversation_store,
        personas_dir=settings.personas_dir,
    )


async def shutdown() -> None:
    if _vector_store:
        _vector_store.save()
    if _conversation_store:
        await _conversation_store.close()


# --- FastAPI Depends helpers ---
def get_embedding_service() -> EmbeddingService:
    assert _embedding_service is not None
    return _embedding_service


def get_vector_store() -> VectorStore:
    assert _vector_store is not None
    return _vector_store


def get_llm_router() -> LLMRouter:
    assert _llm_router is not None
    return _llm_router


def get_rag_service() -> RAGService:
    assert _rag_service is not None
    return _rag_service


def get_chat_service() -> ChatService:
    assert _chat_service is not None
    return _chat_service


def get_conversation_store() -> ConversationStore:
    assert _conversation_store is not None
    return _conversation_store
