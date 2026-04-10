"""Model management endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.dependencies import get_llm_router
from backend.services.llm_router import LLMRouter
from config.settings import get_settings

router = APIRouter(tags=["models"])


class ModelSwitchRequest(BaseModel):
    backend: str  # "openai" | "anthropic" | "local"


class ModelInfo(BaseModel):
    active_backend: str
    available_backends: list[str]
    openai_model: str
    anthropic_model: str
    local_model_path: str
    has_openai_key: bool
    has_anthropic_key: bool


@router.get("/models")
async def get_models(
    llm: LLMRouter = Depends(get_llm_router),
) -> ModelInfo:
    settings = get_settings()
    return ModelInfo(
        active_backend=llm.active_backend_name,
        available_backends=["openai", "anthropic", "local"],
        openai_model=settings.openai_model,
        anthropic_model=settings.anthropic_model,
        local_model_path=settings.local_model_path,
        has_openai_key=bool(settings.openai_api_key),
        has_anthropic_key=bool(settings.anthropic_api_key),
    )


@router.post("/models/switch")
async def switch_model(
    req: ModelSwitchRequest,
    llm: LLMRouter = Depends(get_llm_router),
):
    llm.switch(req.backend)
    return {"status": "switched", "active_backend": req.backend}
