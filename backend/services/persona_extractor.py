"""Extract persona profile from parsed chat messages."""

from __future__ import annotations

import re
from collections import Counter
from typing import AsyncIterator

from backend.ingestion.base_parser import ChatMessage
from backend.models.persona_profile import PersonaProfile


class PersonaExtractor:
    """Two-phase persona extraction: statistical + LLM-assisted."""

    @staticmethod
    def extract_statistical(
        messages: list[ChatMessage], name: str
    ) -> PersonaProfile:
        """Phase 1: Extract statistical features from messages."""
        profile = PersonaProfile(name=name)
        profile.total_messages_analyzed = len(messages)

        if not messages:
            return profile

        texts = [m.text for m in messages]

        # Average message length
        lengths = [len(t) for t in texts]
        profile.avg_message_length = sum(lengths) / len(lengths)

        # Common phrases (2-grams and 3-grams)
        all_words = []
        for t in texts:
            words = t.split()
            all_words.extend(words)
            # bigrams
            for i in range(len(words) - 1):
                all_words.append(f"{words[i]} {words[i+1]}")

        freq = Counter(all_words)
        # Filter short/common words
        profile.common_phrases = [
            phrase for phrase, count in freq.most_common(50)
            if count >= 3 and len(phrase) > 3
        ][:20]

        # Vocabulary richness
        unique_words = set(w.lower() for t in texts for w in t.split())
        total_words = sum(len(t.split()) for t in texts)
        if total_words > 0:
            profile.vocabulary_richness = len(unique_words) / total_words

        # Emoji usage
        emoji_pattern = re.compile(
            r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF"
            r"\U0001F680-\U0001F6FF\U0001F900-\U0001F9FF"
            r"\U00002702-\U000027B0\U0001FA00-\U0001FA6F"
            r"\U0001FA70-\U0001FAFF]+"
        )
        emojis = Counter()
        for t in texts:
            for match in emoji_pattern.finditer(t):
                emojis[match.group()] += 1
        profile.emoji_usage = [e for e, _ in emojis.most_common(20)]

        # Greeting / farewell patterns
        greetings = ["你好", "嗨", "hi", "hello", "hey", "早", "晚上好", "哈喽", "在吗"]
        farewells = ["再见", "拜拜", "bye", "晚安", "好的", "886", "88", "see you"]

        greeting_found = []
        farewell_found = []
        for t in texts:
            t_lower = t.lower().strip()
            for g in greetings:
                if t_lower.startswith(g):
                    greeting_found.append(t_lower[:30])
                    break
            for f in farewells:
                if f in t_lower:
                    farewell_found.append(t_lower[:30])
                    break

        profile.greeting_patterns = list(set(greeting_found))[:10]
        profile.farewell_patterns = list(set(farewell_found))[:10]

        return profile

    @staticmethod
    def build_analysis_prompt(messages: list[ChatMessage], name: str) -> list[dict]:
        """Build prompt for LLM-assisted persona analysis (Phase 2)."""
        # Sample messages for analysis (up to 100)
        sample = messages[:100] if len(messages) > 100 else messages
        sample_text = "\n".join(f"- {m.text}" for m in sample)

        return [
            {
                "role": "system",
                "content": "You are a linguistic analyst. Analyze the following messages and produce a detailed persona description.",
            },
            {
                "role": "user",
                "content": f"""Analyze the following messages from "{name}" and describe their communication style.

Messages:
{sample_text}

Please provide analysis in this exact format:
TONE: (e.g., warm, sarcastic, formal, casual, enthusiastic)
FORMALITY: (e.g., very casual, casual, neutral, formal, very formal)
HUMOR: (e.g., frequent jokes, dry wit, playful, rarely humorous)
TOPICS: (comma-separated list of main topics they discuss)
STYLE_DESCRIPTION: (2-3 sentences describing how this person communicates, their unique patterns, word choices, sentence structures, and any distinctive habits)""",
            },
        ]

    @staticmethod
    def parse_analysis_response(response: str, profile: PersonaProfile) -> PersonaProfile:
        """Parse LLM analysis response and update the profile."""
        lines = response.strip().split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith("TONE:"):
                profile.tone = line[5:].strip()
            elif line.startswith("FORMALITY:"):
                profile.formality_level = line[10:].strip()
            elif line.startswith("HUMOR:"):
                profile.humor_style = line[6:].strip()
            elif line.startswith("TOPICS:"):
                topics = line[7:].strip()
                profile.topics_of_interest = [t.strip() for t in topics.split(",") if t.strip()]
            elif line.startswith("STYLE_DESCRIPTION:"):
                profile.style_description = line[18:].strip()

        # If style_description spans multiple lines after the label
        if not profile.style_description:
            in_desc = False
            desc_lines = []
            for line in lines:
                if line.strip().startswith("STYLE_DESCRIPTION:"):
                    in_desc = True
                    rest = line.strip()[18:].strip()
                    if rest:
                        desc_lines.append(rest)
                elif in_desc and line.strip():
                    desc_lines.append(line.strip())
            profile.style_description = " ".join(desc_lines)

        return profile
