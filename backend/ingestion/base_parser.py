"""Base parser interface and shared data model for chat log ingestion."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ChatMessage:
    speaker: str
    text: str
    timestamp: str = ""
    source: str = ""


class BaseParser(ABC):
    """Abstract base for all chat log parsers."""

    @abstractmethod
    def parse(self, content: str, target_speaker: str = "") -> list[ChatMessage]:
        """Parse raw text content into a list of ChatMessage objects.

        Args:
            content: Raw file content.
            target_speaker: If provided, only return messages from this speaker.
        """
        ...

    @staticmethod
    def detect(content: str) -> bool:
        """Return True if this parser can handle the given content."""
        return False
