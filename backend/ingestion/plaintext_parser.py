"""Plain text / generic chat log parser.

Supports formats like:
  Speaker: message text
  Speaker> message text
  [Speaker] message text

Also supports raw text (no speaker labels) — all treated as one speaker.
"""

from __future__ import annotations

import re

from backend.ingestion.base_parser import BaseParser, ChatMessage


class PlainTextParser(BaseParser):
    # Common chat patterns
    PATTERNS = [
        re.compile(r"^([^:\[\]>]{1,30}):\s*(.+)"),     # Name: text
        re.compile(r"^([^:\[\]>]{1,30})>\s*(.+)"),      # Name> text
        re.compile(r"^\[([^\]]{1,30})\]\s*(.+)"),       # [Name] text
    ]

    @staticmethod
    def detect(content: str) -> bool:
        # Fallback parser — always returns True
        return True

    def parse(self, content: str, target_speaker: str = "") -> list[ChatMessage]:
        messages = []
        lines = content.split("\n")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            matched = False
            for pattern in self.PATTERNS:
                m = pattern.match(line)
                if m:
                    speaker = m.group(1).strip()
                    text = m.group(2).strip()
                    if text and (not target_speaker or speaker == target_speaker):
                        messages.append(
                            ChatMessage(speaker=speaker, text=text, source="plaintext")
                        )
                    matched = True
                    break

            if not matched:
                # No speaker label — use "unknown" or target_speaker
                speaker = target_speaker or "unknown"
                messages.append(
                    ChatMessage(speaker=speaker, text=line, source="plaintext")
                )

        return messages
