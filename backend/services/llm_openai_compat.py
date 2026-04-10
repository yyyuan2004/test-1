"""Generic OpenAI-compatible backend for DeepSeek, Qwen, Zhipu, etc."""

from __future__ import annotations

from typing import AsyncIterator


class OpenAICompatBackend:
    """Works with any provider that exposes an OpenAI-compatible chat API."""

    def __init__(self, api_key: str, model: str, base_url: str) -> None:
        self._api_key = api_key
        self._model = model
        self._base_url = base_url
        self._client = None

    def _ensure_client(self):
        if self._client is None:
            from openai import AsyncOpenAI

            self._client = AsyncOpenAI(
                api_key=self._api_key,
                base_url=self._base_url,
            )

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
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def test_connection(self) -> dict:
        """Test if the API is reachable and key is valid."""
        self._ensure_client()
        try:
            resp = await self._client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=5,
            )
            return {"ok": True, "model": self._model}
        except Exception as e:
            return {"ok": False, "error": str(e)}
