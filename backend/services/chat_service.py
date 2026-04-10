"""Chat orchestration — ties persona, RAG, and LLM together."""

from __future__ import annotations

from pathlib import Path
from typing import AsyncIterator

from backend.models.conversation import ConversationStore
from backend.models.persona_profile import PersonaProfile
from backend.services.llm_router import LLMRouter
from backend.services.rag import RAGService


class ChatService:
    def __init__(
        self,
        llm: LLMRouter,
        rag: RAGService,
        conversations: ConversationStore,
        personas_dir: Path,
    ) -> None:
        self._llm = llm
        self._rag = rag
        self._conv = conversations
        self._personas_dir = personas_dir

    def _load_persona(self, persona_id: str) -> PersonaProfile | None:
        if not persona_id:
            return None
        path = self._personas_dir / f"{persona_id}.json"
        if path.exists():
            return PersonaProfile.load(path)
        return None

    def _build_system_prompt(self, persona: PersonaProfile | None) -> str:
        if not persona:
            return "You are a helpful AI assistant. Respond naturally and helpfully."

        parts = [
            f'You are now roleplaying as "{persona.name}". You must replicate their speaking style exactly.',
            f"Do NOT break character. Respond as {persona.name} would.",
        ]

        if persona.tone:
            parts.append(f"Tone: {persona.tone}")
        if persona.formality_level:
            parts.append(f"Formality: {persona.formality_level}")
        if persona.humor_style:
            parts.append(f"Humor style: {persona.humor_style}")
        if persona.style_description:
            parts.append(f"Communication style: {persona.style_description}")
        if persona.common_phrases:
            phrases = ", ".join(persona.common_phrases[:10])
            parts.append(f"Frequently used phrases/words: {phrases}")
        if persona.emoji_usage:
            emojis = " ".join(persona.emoji_usage[:10])
            parts.append(f"Often uses emojis: {emojis}")
        if persona.topics_of_interest:
            topics = ", ".join(persona.topics_of_interest)
            parts.append(f"Topics they often discuss: {topics}")
        if persona.avg_message_length > 0:
            parts.append(
                f"Average message length: ~{int(persona.avg_message_length)} characters. "
                f"Try to match this length."
            )

        return "\n".join(parts)

    async def chat(
        self,
        conversation_id: str,
        user_message: str,
        persona_id: str = "",
    ) -> AsyncIterator[str]:
        """Process a chat message and stream the response."""
        # Load persona
        persona = self._load_persona(persona_id)

        # Get conversation history
        history = await self._conv.get_messages(conversation_id, limit=20)

        # Build system prompt
        system_prompt = self._build_system_prompt(persona)

        # Retrieve relevant context via RAG
        rag_results = self._rag.retrieve(
            user_message, persona_id=persona_id
        )
        rag_context = self._rag.build_context(rag_results)

        if rag_context:
            system_prompt += (
                f"\n\nHere are examples of how {persona.name if persona else 'this person'} "
                f"speaks (use these as reference for style and content):\n{rag_context}"
            )

        # Build message list
        messages = [{"role": "system", "content": system_prompt}]
        for h in history:
            messages.append({"role": h["role"], "content": h["content"]})
        messages.append({"role": "user", "content": user_message})

        # Save user message
        await self._conv.add_message(conversation_id, "user", user_message)

        # Stream response
        full_response = []
        async for token in self._llm.generate(messages):
            full_response.append(token)
            yield token

        # Save assistant response
        assistant_text = "".join(full_response)
        await self._conv.add_message(conversation_id, "assistant", assistant_text)

        # Auto-generate title for new conversations
        if len(history) == 0 and len(user_message) > 0:
            title = user_message[:50] + ("..." if len(user_message) > 50 else "")
            await self._conv.update_title(conversation_id, title)
