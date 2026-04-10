"""Anthropic Claude backend."""

from __future__ import annotations

from typing import AsyncIterator

from config.settings import Settings


class ClaudeBackend:
    def __init__(self, settings: Settings) -> None:
        self._model = settings.anthropic_model
        self._client = None
        self._api_key = settings.anthropic_api_key

    def _ensure_client(self):
        if self._client is None:
            from anthropic import AsyncAnthropic

            self._client = AsyncAnthropic(api_key=self._api_key)

    async def generate(
        self, messages: list[dict], *, temperature: float = 0.7
    ) -> AsyncIterator[str]:
        self._ensure_client()

        # Separate system message from conversation
        system_text = ""
        conv_messages = []
        for m in messages:
            if m["role"] == "system":
                system_text += m["content"] + "\n"
            else:
                conv_messages.append(m)

        # Ensure messages alternate user/assistant
        if not conv_messages or conv_messages[0]["role"] != "user":
            conv_messages.insert(0, {"role": "user", "content": "Hello"})

        async with self._client.messages.stream(
            model=self._model,
            max_tokens=4096,
            temperature=temperature,
            system=system_text.strip() or "You are a helpful assistant.",
            messages=conv_messages,
        ) as stream:
            async for text in stream.text_stream:
                yield text
