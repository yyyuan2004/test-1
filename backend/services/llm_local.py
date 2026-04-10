"""Local LLM backend via llama-cpp-python."""

from __future__ import annotations

import asyncio
from typing import AsyncIterator

from config.settings import Settings


class LocalBackend:
    def __init__(self, settings: Settings) -> None:
        self._model_path = settings.local_model_path
        self._n_ctx = settings.local_model_context_length
        self._n_gpu_layers = settings.local_model_gpu_layers
        self._model = None

    def _ensure_model(self):
        if self._model is None:
            try:
                from llama_cpp import Llama
            except ImportError:
                raise RuntimeError(
                    "llama-cpp-python is not installed. "
                    "Install it with: pip install llama-cpp-python"
                )
            self._model = Llama(
                model_path=self._model_path,
                n_ctx=self._n_ctx,
                n_gpu_layers=self._n_gpu_layers,
                verbose=False,
            )

    async def generate(
        self, messages: list[dict], *, temperature: float = 0.7
    ) -> AsyncIterator[str]:
        self._ensure_model()

        # Run blocking llama-cpp in a thread
        def _stream():
            return self._model.create_chat_completion(
                messages=messages,
                temperature=temperature,
                stream=True,
            )

        loop = asyncio.get_event_loop()
        stream = await loop.run_in_executor(None, _stream)

        for chunk in stream:
            delta = chunk["choices"][0].get("delta", {})
            content = delta.get("content", "")
            if content:
                yield content
