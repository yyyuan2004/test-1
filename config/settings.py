"""Application settings via pydantic-settings."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- LLM ---
    default_llm_backend: Literal["openai", "anthropic", "local"] = "openai"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str = ""
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-20250514"
    local_model_path: str = str(PROJECT_ROOT / "data" / "models" / "model.gguf")
    local_model_context_length: int = 4096
    local_model_gpu_layers: int = 0

    # --- Embedding ---
    embedding_model: str = "all-MiniLM-L6-v2"

    # --- Server ---
    host: str = "127.0.0.1"
    port: int = 8765

    # --- RAG ---
    rag_top_k: int = 5
    rag_chunk_size: int = 500
    rag_chunk_overlap: int = 50

    # --- Paths ---
    data_dir: str = str(PROJECT_ROOT / "data")

    @property
    def faiss_index_dir(self) -> Path:
        return Path(self.data_dir) / "faiss_index"

    @property
    def personas_dir(self) -> Path:
        return Path(self.data_dir) / "personas"

    @property
    def db_path(self) -> Path:
        return Path(self.data_dir) / "conversations.db"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
