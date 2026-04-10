"""Health check and status endpoints — connection testing, error reporting."""

from __future__ import annotations

import platform
import sys

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.dependencies import get_llm_router, get_vector_store, get_embedding_service
from backend.services.llm_router import LLMRouter
from backend.services.vector_store import VectorStore
from backend.services.embeddings import EmbeddingService
from config.settings import get_settings

router = APIRouter(tags=["status"])


class BackendStatus(BaseModel):
    name: str
    display_name: str
    has_key: bool
    connected: bool
    error: str = ""
    model: str = ""


class SystemStatus(BaseModel):
    server_ok: bool = True
    embedding_ok: bool = False
    vector_store_count: int = 0
    python_version: str = ""
    platform: str = ""
    backends: list[BackendStatus] = []
    active_backend: str = ""
    pii_masking: bool = False
    humanizer: bool = False


@router.get("/status")
async def get_status(
    llm: LLMRouter = Depends(get_llm_router),
    vs: VectorStore = Depends(get_vector_store),
    emb: EmbeddingService = Depends(get_embedding_service),
) -> SystemStatus:
    settings = get_settings()

    # Check embedding
    embedding_ok = False
    try:
        _ = emb.dimension
        embedding_ok = True
    except Exception:
        pass

    # Backend statuses
    backend_configs = [
        ("openai", "OpenAI", settings.openai_api_key, settings.openai_model),
        ("anthropic", "Anthropic Claude", settings.anthropic_api_key, settings.anthropic_model),
        ("deepseek", "DeepSeek", settings.deepseek_api_key, settings.deepseek_model),
        ("qwen", "通义千问 Qwen", settings.qwen_api_key, settings.qwen_model),
        ("zhipu", "智谱清言 GLM", settings.zhipu_api_key, settings.zhipu_model),
        ("local", "本地模型", "local", settings.local_model_path),
    ]

    backends = []
    for name, display, key, model in backend_configs:
        has_key = bool(key) if name != "local" else True
        backends.append(BackendStatus(
            name=name,
            display_name=display,
            has_key=has_key,
            connected=False,  # Lightweight check only; full test via /status/test
            model=model,
        ))

    return SystemStatus(
        server_ok=True,
        embedding_ok=embedding_ok,
        vector_store_count=vs.count,
        python_version=sys.version.split()[0],
        platform=platform.system(),
        backends=backends,
        active_backend=llm.active_backend_name,
        pii_masking=settings.pii_masking_enabled,
        humanizer=settings.humanize_enabled,
    )


@router.post("/status/test/{backend_name}")
async def test_backend(
    backend_name: str,
    llm: LLMRouter = Depends(get_llm_router),
) -> BackendStatus:
    """Test a specific backend's connectivity and API key validity."""
    settings = get_settings()

    name_map = {
        "openai": ("OpenAI", settings.openai_api_key),
        "anthropic": ("Anthropic Claude", settings.anthropic_api_key),
        "deepseek": ("DeepSeek", settings.deepseek_api_key),
        "qwen": ("通义千问 Qwen", settings.qwen_api_key),
        "zhipu": ("智谱清言 GLM", settings.zhipu_api_key),
        "local": ("本地模型", "local"),
    }

    if backend_name not in name_map:
        return BackendStatus(
            name=backend_name,
            display_name=backend_name,
            has_key=False,
            connected=False,
            error=f"未知的后端: {backend_name}",
        )

    display_name, api_key = name_map[backend_name]
    has_key = bool(api_key)

    if not has_key:
        return BackendStatus(
            name=backend_name,
            display_name=display_name,
            has_key=False,
            connected=False,
            error="未配置 API Key",
        )

    # Try a minimal generation
    try:
        tokens = []
        async for t in llm.generate(
            [{"role": "user", "content": "hi"}],
            temperature=0.1,
            backend=backend_name,
        ):
            tokens.append(t)
            if len(tokens) > 5:
                break

        return BackendStatus(
            name=backend_name,
            display_name=display_name,
            has_key=has_key,
            connected=True,
            model=getattr(settings, f"{backend_name}_model", ""),
        )
    except Exception as e:
        return BackendStatus(
            name=backend_name,
            display_name=display_name,
            has_key=has_key,
            connected=False,
            error=str(e)[:200],
        )


@router.get("/status/trends")
async def get_available_trend_sources():
    """List available trend scraping sources."""
    from backend.services.trend_scraper import TrendScraper
    return {
        "sources": list(TrendScraper.SOURCES.keys()),
        "descriptions": {
            "weibo_hot": "微博热搜",
            "zhihu_hot": "知乎热榜",
            "baidu_hot": "百度热搜",
        },
    }
