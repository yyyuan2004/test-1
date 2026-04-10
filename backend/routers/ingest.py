"""Chat log ingestion endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, UploadFile

from backend.dependencies import (
    get_embedding_service,
    get_llm_router,
    get_rag_service,
    get_vector_store,
)
from backend.ingestion.registry import detect_parser
from backend.schemas.ingest import IngestResponse
from backend.services.embeddings import EmbeddingService
from backend.services.llm_router import LLMRouter
from backend.services.persona_extractor import PersonaExtractor
from backend.services.rag import RAGService
from backend.services.vector_store import VectorStore
from backend.models.persona_profile import PersonaProfile
from config.settings import get_settings

router = APIRouter(tags=["ingest"])


@router.post("/ingest", response_model=IngestResponse)
async def ingest_chat_log(
    file: UploadFile = File(...),
    persona_name: str = Form(""),
    target_speaker: str = Form(""),
    persona_id: str = Form(""),
    emb_svc: EmbeddingService = Depends(get_embedding_service),
    vs: VectorStore = Depends(get_vector_store),
    rag: RAGService = Depends(get_rag_service),
    llm: LLMRouter = Depends(get_llm_router),
):
    """Upload and process a chat log file."""
    settings = get_settings()

    # Read file content
    raw = await file.read()
    # Try utf-8, then gbk (common for Chinese files)
    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError:
        content = raw.decode("gbk", errors="replace")

    # Detect format and parse
    parser = detect_parser(content)
    messages = parser.parse(content, target_speaker=target_speaker)

    if not messages:
        return IngestResponse(
            persona_id="",
            persona_name=persona_name or "Unknown",
            messages_parsed=0,
            chunks_stored=0,
            status="no_messages_found",
        )

    # Create or load persona
    if persona_id:
        path = settings.personas_dir / f"{persona_id}.json"
        if path.exists():
            profile = PersonaProfile.load(path)
        else:
            profile = PersonaProfile(name=persona_name or target_speaker or "Unknown")
            persona_id = profile.id
    else:
        profile = PersonaProfile(name=persona_name or target_speaker or "Unknown")
        persona_id = profile.id

    # Phase 1: Statistical extraction
    profile = PersonaExtractor.extract_statistical(messages, profile.name)
    profile.id = persona_id
    profile.source_files.append(file.filename or "unknown")

    # Phase 2: LLM-assisted analysis (try, don't fail if LLM unavailable)
    try:
        analysis_prompt = PersonaExtractor.build_analysis_prompt(messages, profile.name)
        response_parts = []
        async for token in llm.generate(analysis_prompt, temperature=0.3):
            response_parts.append(token)
        response_text = "".join(response_parts)
        profile = PersonaExtractor.parse_analysis_response(response_text, profile)
    except Exception:
        # LLM analysis is optional — statistical profile is sufficient
        pass

    profile.save(settings.personas_dir)

    # PII masking before indexing
    if settings.pii_masking_enabled:
        from backend.services.pii_masker import mask_pii_batch
        for m in messages:
            m.text = mask_pii_batch([m.text])[0]

    # Chunk and embed messages for RAG
    texts = [m.text for m in messages]
    # Group short messages
    chunks = []
    current_chunk = []
    current_len = 0
    for t in texts:
        current_chunk.append(t)
        current_len += len(t)
        if current_len >= settings.rag_chunk_size:
            chunks.append("\n".join(current_chunk))
            current_chunk = []
            current_len = 0
    if current_chunk:
        chunks.append("\n".join(current_chunk))

    if chunks:
        vectors = emb_svc.encode(chunks)
        metadatas = [
            {
                "text": chunk,
                "speaker": target_speaker or persona_name,
                "persona_id": persona_id,
                "source": file.filename or "uploaded",
                "source_type": "chat_log",
                "chunk_index": i,
            }
            for i, chunk in enumerate(chunks)
        ]
        vs.add(vectors, metadatas)
        vs.save()

    return IngestResponse(
        persona_id=persona_id,
        persona_name=profile.name,
        messages_parsed=len(messages),
        chunks_stored=len(chunks),
        status="success",
    )
