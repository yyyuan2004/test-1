"""Auto-detect chat log format and return the appropriate parser."""

from __future__ import annotations

from backend.ingestion.base_parser import BaseParser
from backend.ingestion.wechat_parser import WeChatParser
from backend.ingestion.whatsapp_parser import WhatsAppParser
from backend.ingestion.plaintext_parser import PlainTextParser

# Order matters — more specific parsers first, plaintext last (fallback)
_PARSERS: list[type[BaseParser]] = [
    WhatsAppParser,
    WeChatParser,
    PlainTextParser,
]


def detect_parser(content: str) -> BaseParser:
    """Detect the format of chat content and return a parser instance."""
    for parser_cls in _PARSERS:
        if parser_cls.detect(content):
            return parser_cls()
    return PlainTextParser()
