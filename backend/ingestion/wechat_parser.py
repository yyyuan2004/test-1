"""WeChat chat export parser.

Supports common WeChat export formats:
  - "Name:\n  message text" (plain text export)
  - "2024-01-01 12:00:00 Name\n  message text" (timestamped)
  - HTML exports from WeChat backup tools
"""

from __future__ import annotations

import re
from typing import Optional

from backend.ingestion.base_parser import BaseParser, ChatMessage


class WeChatParser(BaseParser):
    # Pattern: "2024-01-01 12:00  SpeakerName"
    TIMESTAMP_PATTERN = re.compile(
        r"^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}(?::\d{2})?)\s+(.+)$"
    )
    # Pattern: "SpeakerName:" at the start of a line
    SIMPLE_PATTERN = re.compile(r"^([^:\n]{1,30}):\s*$", re.MULTILINE)
    # HTML pattern from WeChat export tools
    HTML_MSG_PATTERN = re.compile(
        r'<div[^>]*class="message"[^>]*>.*?'
        r'<span[^>]*class="nickname"[^>]*>([^<]+)</span>.*?'
        r'<span[^>]*class="content"[^>]*>([^<]+)</span>',
        re.DOTALL,
    )

    @staticmethod
    def detect(content: str) -> bool:
        # Check for WeChat-style patterns
        if re.search(r"\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}", content):
            return True
        if '<div' in content and 'nickname' in content:
            return True
        return False

    def parse(self, content: str, target_speaker: str = "") -> list[ChatMessage]:
        # Try HTML first
        if "<div" in content and "nickname" in content:
            return self._parse_html(content, target_speaker)

        return self._parse_text(content, target_speaker)

    def _parse_html(self, content: str, target_speaker: str) -> list[ChatMessage]:
        messages = []
        for match in self.HTML_MSG_PATTERN.finditer(content):
            speaker = match.group(1).strip()
            text = match.group(2).strip()
            if target_speaker and speaker != target_speaker:
                continue
            if text:
                messages.append(ChatMessage(speaker=speaker, text=text, source="wechat"))
        return messages

    def _parse_text(self, content: str, target_speaker: str) -> list[ChatMessage]:
        messages = []
        lines = content.split("\n")
        current_speaker = ""
        current_timestamp = ""
        current_text_lines: list[str] = []

        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue

            # Try timestamp pattern
            ts_match = self.TIMESTAMP_PATTERN.match(line_stripped)
            if ts_match:
                # Save previous message
                if current_speaker and current_text_lines:
                    text = "\n".join(current_text_lines).strip()
                    if text and (not target_speaker or current_speaker == target_speaker):
                        messages.append(
                            ChatMessage(
                                speaker=current_speaker,
                                text=text,
                                timestamp=current_timestamp,
                                source="wechat",
                            )
                        )
                current_timestamp = ts_match.group(1)
                current_speaker = ts_match.group(2).strip()
                current_text_lines = []
                continue

            # Try simple "Name:" pattern
            simple_match = re.match(r"^([^:\n]{1,30}):\s*$", line_stripped)
            if simple_match and not line.startswith((" ", "\t")):
                if current_speaker and current_text_lines:
                    text = "\n".join(current_text_lines).strip()
                    if text and (not target_speaker or current_speaker == target_speaker):
                        messages.append(
                            ChatMessage(
                                speaker=current_speaker,
                                text=text,
                                source="wechat",
                            )
                        )
                current_speaker = simple_match.group(1).strip()
                current_text_lines = []
                continue

            # Content line
            if current_speaker:
                current_text_lines.append(line_stripped)

        # Don't forget last message
        if current_speaker and current_text_lines:
            text = "\n".join(current_text_lines).strip()
            if text and (not target_speaker or current_speaker == target_speaker):
                messages.append(
                    ChatMessage(
                        speaker=current_speaker,
                        text=text,
                        timestamp=current_timestamp,
                        source="wechat",
                    )
                )

        return messages
