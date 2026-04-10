"""Unified LLM router — delegates to OpenAI / Anthropic / local backend."""

from __future__ import annotations

from typing import AsyncIterator, Protocol, runtime_checkable

from config.settings import Settings


@runtime_checkable
class LLMBackend(Protocol):
    """Every backend must implement this interface."""

    async def generate(
        self, messages: list[dict], *, temperature: float = 0.7
    ) -> AsyncIterator[str]:
        """Yield tokens as they arrive."""
        ...  # pragma: no cover


class LLMRouter:
    """Selects and delegates to the active backend."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._backends: dict[str, LLMBackend] = {}
        self._active: str = settings.default_llm_backend

    def _get_backend(self, name: str) -> LLMBackend:
        if name not in self._backends:
            if name == "openai":
                from backend.services.llm_openai import OpenAIBackend

                self._backends[name] = OpenAIBackend(self._settings)
            elif name == "anthropic":
                from backend.services.llm_claude import ClaudeBackend

                self._backends[name] = ClaudeBackend(self._settings)
            elif name == "local":
                from backend.services.llm_local import LocalBackend

                self._backends[name] = LocalBackend(self._settings)
            else:
                raise ValueError(f"Unknown backend: {name}")
        return self._backends[name]

    @property
    def active_backend_name(self) -> str:
        return self._active

    def switch(self, name: str) -> None:
        if name not in ("openai", "anthropic", "local"):
            raise ValueError(f"Unknown backend: {name}")
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
