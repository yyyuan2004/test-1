"""Humanization engine — make AI responses feel more natural and less 'AI-like'.

Features:
- Filler words injection (语气词: 哈、嘛、呢、吧、啊、嗯)
- Imperfect punctuation and sentence breaks
- Context-appropriate typo simulation
- Remove typical AI patterns (perfect parallel structure, over-formality)
- Slang / emoji dictionary mapping
"""

from __future__ import annotations

import random
import re

from backend.services.slang_dict import SlangDict


class Humanizer:
    """Post-processes AI output to reduce 'AI-flavor'."""

    # Common Chinese filler words
    FILLERS = ["哈", "嘛", "呢", "吧", "啊", "嗯", "emmm", "hh", "hhh", "~"]
    SENTENCE_ENDERS = ["。", "！", "？", ".", "!", "?"]
    # Patterns that scream "AI-generated"
    AI_PATTERNS = [
        # Remove numbered lists with "首先...其次...最后"
        (re.compile(r"首先[，,]"), ""),
        (re.compile(r"其次[，,]"), ""),
        (re.compile(r"最后[，,]"), ""),
        (re.compile(r"总之[，,]"), ""),
        (re.compile(r"综上所述[，,]"), ""),
        # Remove over-polite openings
        (re.compile(r"^(好的[，,]\s*|当然[，,]\s*|没问题[，,]\s*)?我来"), "我来"),
        # Remove "as an AI" disclaimers
        (re.compile(r"作为一个AI[，,]?\s*"), ""),
        (re.compile(r"作为人工智能[，,]?\s*"), ""),
    ]

    def __init__(
        self,
        enabled: bool = True,
        filler_rate: float = 0.15,
        typo_rate: float = 0.02,
        slang_dict: SlangDict | None = None,
    ) -> None:
        self._enabled = enabled
        self._filler_rate = filler_rate
        self._typo_rate = typo_rate
        self._slang = slang_dict or SlangDict()

    def process(self, text: str, persona_style: str = "") -> str:
        """Apply humanization pipeline to text."""
        if not self._enabled or not text.strip():
            return text

        text = self._remove_ai_patterns(text)
        text = self._apply_slang_mapping(text)
        text = self._inject_fillers(text)
        text = self._add_imperfections(text)
        return text

    def _remove_ai_patterns(self, text: str) -> str:
        for pattern, replacement in self.AI_PATTERNS:
            text = pattern.sub(replacement, text)
        return text

    def _apply_slang_mapping(self, text: str) -> str:
        return self._slang.apply(text)

    def _inject_fillers(self, text: str) -> str:
        """Add filler words at natural breakpoints."""
        if random.random() > self._filler_rate * 3:
            return text

        sentences = re.split(r"([。！？!?])", text)
        result = []
        for i, part in enumerate(sentences):
            result.append(part)
            # After a sentence-ending punctuation, maybe add a filler
            if part in self.SENTENCE_ENDERS and random.random() < self._filler_rate:
                continue  # just don't add filler after every sentence
            # Before sentence-ending punctuation in the content
            if len(part) > 5 and random.random() < self._filler_rate:
                # Insert a filler near the end of the sentence
                filler = random.choice(self.FILLERS[:6])  # prefer natural ones
                # Add filler before the last character
                if part and part[-1] not in self.SENTENCE_ENDERS:
                    result[-1] = part + filler

        return "".join(result)

    def _add_imperfections(self, text: str) -> str:
        """Add subtle imperfections: random '~', ellipsis breaks, etc."""
        # Occasionally replace 。 with ~ or ...
        if random.random() < self._typo_rate * 5:
            text = text.replace("。", "~", 1)

        # Occasionally add trailing particles
        if random.random() < self._typo_rate * 3 and len(text) > 10:
            endings = ["~", "...", "hh", ""]
            text = text.rstrip("。.!！?？") + random.choice(endings)

        return text
