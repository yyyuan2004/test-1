"""Tiered memory system — short-term, mid-term (summaries), long-term (RAG)."""

from __future__ import annotations

from backend.models.conversation import ConversationStore
from backend.services.llm_router import LLMRouter


class MemoryManager:
    """Manages three-tier memory for conversations.

    - Short-term: recent N raw messages (kept in full)
    - Mid-term: periodic summaries of older messages (compressed)
    - Long-term: RAG vector retrieval (handled externally)
    """

    def __init__(
        self,
        conversations: ConversationStore,
        short_term_limit: int = 10,
        summary_threshold: int = 20,
        max_summaries: int = 5,
    ) -> None:
        self._conv = conversations
        self._short_term_limit = short_term_limit
        self._summary_threshold = summary_threshold
        self._max_summaries = max_summaries

    async def get_context_messages(self, conversation_id: str) -> tuple[list[dict], str]:
        """Return (recent_messages, summary_context).

        recent_messages: last N messages as-is for the LLM context.
        summary_context: compressed summaries of earlier conversation.
        """
        all_messages = await self._conv.get_messages(conversation_id, limit=200)
        summaries = await self._conv.get_summaries(conversation_id)

        # Recent messages (short-term)
        recent = all_messages[-self._short_term_limit:]

        # Build summary context (mid-term)
        summary_text = ""
        if summaries:
            summary_parts = [s["content"] for s in summaries[-self._max_summaries:]]
            summary_text = "\n---\n".join(summary_parts)

        return recent, summary_text

    async def maybe_summarize(
        self, conversation_id: str, llm: LLMRouter
    ) -> bool:
        """Check if the conversation needs summarization, and do it if so.

        Returns True if a summary was generated.
        """
        msg_count = await self._conv.get_message_count(conversation_id)
        last_summary_at = await self._conv.get_last_summary_position(conversation_id)

        unsummarized = msg_count - last_summary_at
        if unsummarized < self._summary_threshold:
            return False

        # Get the messages that need summarizing
        messages = await self._conv.get_messages(conversation_id, limit=200)
        to_summarize = messages[last_summary_at : last_summary_at + self._summary_threshold]

        if not to_summarize:
            return False

        # Build summarization prompt
        convo_text = "\n".join(
            f"{m['role']}: {m['content']}" for m in to_summarize
        )
        summary_prompt = [
            {
                "role": "system",
                "content": (
                    "你是一个对话摘要助手。请将以下对话内容压缩为简洁的摘要，"
                    "保留关键信息、话题要点和重要细节。用中文回答。"
                ),
            },
            {
                "role": "user",
                "content": f"请总结以下对话：\n\n{convo_text}",
            },
        ]

        try:
            parts = []
            async for token in llm.generate(summary_prompt, temperature=0.3):
                parts.append(token)
            summary = "".join(parts)

            if summary.strip():
                await self._conv.add_summary(
                    conversation_id,
                    summary.strip(),
                    last_summary_at + len(to_summarize),
                )
                return True
        except Exception:
            pass

        return False
