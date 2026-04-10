"""WhatsApp chat export parser.

Supports the standard WhatsApp export format:
  [DD/MM/YYYY, HH:MM:SS] Speaker: message text
  MM/DD/YY, HH:MM - Speaker: message text
"""

from __future__ import annotations

import re

from backend.ingestion.base_parser import BaseParser, ChatMessage


class WhatsAppParser(BaseParser):
    # Pattern variants for WhatsApp exports
    PATTERNS = [
        # [DD/MM/YYYY, HH:MM:SS] Name: text
        re.compile(
            r"^\[(\d{1,2}/\d{1,2}/\d{2,4},\s*\d{1,2}:\d{2}(?::\d{2})?)\]\s+([^:]+):\s*(.+)"
        ),
        # MM/DD/YY, HH:MM - Name: text
        re.compile(
            r"^(\d{1,2}/\d{1,2}/\d{2,4},\s*\d{1,2}:\d{2}(?:\s*[APap][Mm])?)\s*-\s*([^:]+):\s*(.+)"
        ),
    ]

    @staticmethod
    def detect(content: str) -> bool:
        first_lines = content[:500]
        if re.search(r"\[\d{1,2}/\d{1,2}/\d{2,4},\s*\d{1,2}:\d{2}", first_lines):
            return True
        if re.search(r"\d{1,2}/\d{1,2}/\d{2,4},\s*\d{1,2}:\d{2}\s*-", first_lines):
            return True
        return False

    def parse(self, content: str, target_speaker: str = "") -> list[ChatMessage]:
        messages = []
        lines = content.split("\n")
        current_speaker = ""
        current_timestamp = ""
        current_text_lines: list[str] = []

        for line in lines:
            matched = False
            for pattern in self.PATTERNS:
                m = pattern.match(line)
                if m:
                    # Save previous
                    if current_speaker and current_text_lines:
                        text = "\n".join(current_text_lines).strip()
                        if text and (not target_speaker or current_speaker == target_speaker):
                            messages.append(
                                ChatMessage(
                                    speaker=current_speaker,
                                    text=text,
                                    timestamp=current_timestamp,
                                    source="whatsapp",
                                )
                            )
                    current_timestamp = m.group(1)
                    current_speaker = m.group(2).strip()
                    current_text_lines = [m.group(3)]
                    matched = True
                    break

            if not matched and current_speaker:
                # Continuation line
                current_text_lines.append(line)

        # Last message
        if current_speaker and current_text_lines:
            text = "\n".join(current_text_lines).strip()
            if text and (not target_speaker or current_speaker == target_speaker):
                messages.append(
                    ChatMessage(
                        speaker=current_speaker,
                        text=text,
                        timestamp=current_timestamp,
                        source="whatsapp",
                    )
                )

        return messages
