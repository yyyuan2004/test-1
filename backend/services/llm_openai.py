"""OpenAI-compatible backend (works with any OpenAI-API-compatible provider)."""

from __future__ import annotations

from typing import AsyncIterator

from config.settings import Settings


class OpenAIBackend:
    def __init__(self, settings: Settings) -> None:
        self._model = settings.openai_model
        self._client = None
        self._api_key = settings.openai_api_key
        self._base_url = settings.openai_base_url or None

    def _ensure_client(self):
        if self._client is None:
            from openai import AsyncOpenAI

            kwargs: dict = {"api_key": self._api_key}
            if self._base_url:
                kwargs["base_url"] = self._base_url
            self._client = AsyncOpenAI(**kwargs)

    async def generate(
        self, messages: list[dict], *, temperature: float = 0.7
    ) -> AsyncIterator[str]:
        self._ensure_client()
        stream = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=temperature,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content
