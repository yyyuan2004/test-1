"""Unified LLM router — delegates to OpenAI / Anthropic / DeepSeek / Qwen / Zhipu / local."""

from __future__ import annotations

from typing import AsyncIterator, Protocol, runtime_checkable

from config.settings import Settings, ALL_BACKENDS


@runtime_checkable
class LLMBackend(Protocol):
    """Every backend must implement this interface."""

    async def generate(
        self, messages: list[dict], *, temperature: float = 0.7
    ) -> AsyncIterator[str]:
        ...  # pragma: no cover


class LLMRouter:
    """Selects and delegates to the active backend."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._backends: dict[str, LLMBackend] = {}
        self._active: str = settings.default_llm_backend

    def _get_backend(self, name: str) -> LLMBackend:
        if name not in self._backends:
            s = self._settings
            if name == "openai":
                from backend.services.llm_openai import OpenAIBackend
                self._backends[name] = OpenAIBackend(s)
            elif name == "anthropic":
                from backend.services.llm_claude import ClaudeBackend
                self._backends[name] = ClaudeBackend(s)
            elif name == "local":
                from backend.services.llm_local import LocalBackend
                self._backends[name] = LocalBackend(s)
            elif name == "deepseek":
                from backend.services.llm_openai_compat import OpenAICompatBackend
                self._backends[name] = OpenAICompatBackend(
                    api_key=s.deepseek_api_key,
                    model=s.deepseek_model,
                    base_url=s.deepseek_base_url,
                )
            elif name == "qwen":
                from backend.services.llm_openai_compat import OpenAICompatBackend
                self._backends[name] = OpenAICompatBackend(
                    api_key=s.qwen_api_key,
                    model=s.qwen_model,
                    base_url=s.qwen_base_url,
                )
            elif name == "zhipu":
                from backend.services.llm_openai_compat import OpenAICompatBackend
                self._backends[name] = OpenAICompatBackend(
                    api_key=s.zhipu_api_key,
                    model=s.zhipu_model,
                    base_url=s.zhipu_base_url,
                )
            else:
                raise ValueError(f"未知的后端: {name}")
        return self._backends[name]

    @property
    def active_backend_name(self) -> str:
        return self._active

    def switch(self, name: str) -> None:
        if name not in ALL_BACKENDS:
            raise ValueError(f"未知的后端: {name}")
        self._active = name

    async def generate(
        self,
        messages: list[dict],
        *,
        temperature: float = 0.7,
        backend: str | None = None,
    ) -> AsyncIterator[str]:
        name = backend or self._active
        be = self._get_backend(name)
        async for token in be.generate(messages, temperature=temperature):
            yield token
