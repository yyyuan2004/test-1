"""Chat orchestration — ties persona, RAG, memory, humanizer, and LLM together."""

from __future__ import annotations

from pathlib import Path
from typing import AsyncIterator

from backend.models.conversation import ConversationStore
from backend.models.persona_profile import PersonaProfile
from backend.services.llm_router import LLMRouter
from backend.services.rag import RAGService
from backend.services.memory import MemoryManager
from backend.services.humanizer import Humanizer
from backend.services.slang_dict import SlangDict


class ChatService:
    def __init__(
        self,
        llm: LLMRouter,
        rag: RAGService,
        conversations: ConversationStore,
        personas_dir: Path,
        memory: MemoryManager,
        humanizer: Humanizer,
    ) -> None:
        self._llm = llm
        self._rag = rag
        self._conv = conversations
        self._personas_dir = personas_dir
        self._memory = memory
        self._humanizer = humanizer

    def _load_persona(self, persona_id: str) -> PersonaProfile | None:
        if not persona_id:
            return None
        path = self._personas_dir / f"{persona_id}.json"
        if path.exists():
            return PersonaProfile.load(path)
        return None

    def _build_system_prompt(
        self, persona: PersonaProfile | None, summary_context: str = ""
    ) -> str:
        if not persona:
            return "你是一个有帮助的AI助手。请自然、有帮助地回答。"

        parts = []

        if persona.persona_type == "group":
            parts.append(
                f'你现在正在模仿"{persona.name}"这个群体的社交氛围和说话方式。'
                f"你需要完美复刻这个群的交流风格、互动逻辑和整体氛围。"
            )
            if persona.group_vibe:
                parts.append(f"群体氛围: {persona.group_vibe}")
            if persona.interaction_patterns:
                parts.append(f"互动模式: {persona.interaction_patterns}")
            if persona.group_members:
                parts.append(f"群成员: {', '.join(persona.group_members)}")
        else:
            parts.append(
                f'你现在正在扮演"{persona.name}"。你必须完美复刻他/她的说话方式。'
            )
            parts.append(f"绝对不要跳出角色。按照 {persona.name} 的方式回复。")

        if persona.tone:
            parts.append(f"语气: {persona.tone}")
        if persona.formality_level:
            parts.append(f"正式程度: {persona.formality_level}")
        if persona.humor_style:
            parts.append(f"幽默风格: {persona.humor_style}")
        if persona.style_description:
            parts.append(f"说话风格: {persona.style_description}")
        if persona.common_phrases:
            phrases = "、".join(persona.common_phrases[:10])
            parts.append(f"常用词句: {phrases}")
        if persona.emoji_usage:
            emojis = " ".join(persona.emoji_usage[:10])
            parts.append(f"常用表情: {emojis}")
        if persona.topics_of_interest:
            topics = "、".join(persona.topics_of_interest)
            parts.append(f"常聊话题: {topics}")
        if persona.filler_words:
            fillers = "、".join(persona.filler_words[:10])
            parts.append(f"口头禅/语气词: {fillers}")
        if persona.avg_message_length > 0:
            parts.append(f"平均消息长度: ~{int(persona.avg_message_length)} 个字。尽量匹配这个长度。")

        # Anti-AI instructions
        parts.append(
            "\n重要指令（去AI味）："
            "\n- 不要使用"首先、其次、最后"这类列举结构"
            "\n- 不要使用过度完美的语法和排比句"
            "\n- 适当加入语气词（哈、嘛、呢、吧、啊、嗯等）"
            "\n- 可以偶尔打错字或用缩写"
            "\n- 像真人聊天一样自然，不要像教科书"
            "\n- 不要说\"作为AI\"或任何暴露AI身份的话"
        )

        # Summary context (mid-term memory)
        if summary_context:
            parts.append(f"\n之前的对话摘要:\n{summary_context}")

        return "\n".join(parts)

    async def chat(
        self,
        conversation_id: str,
        user_message: str,
        persona_id: str = "",
    ) -> AsyncIterator[str]:
        """Process a chat message and stream the response."""
        persona = self._load_persona(persona_id)

        # Get tiered memory context
        recent_messages, summary_context = await self._memory.get_context_messages(
            conversation_id
        )

        # Build system prompt with summary context
        system_prompt = self._build_system_prompt(persona, summary_context)

        # Retrieve relevant context via RAG (long-term memory)
        rag_results = self._rag.retrieve(user_message, persona_id=persona_id)
        rag_context = self._rag.build_context(rag_results)

        if rag_context:
            name = persona.name if persona else "该人物"
            system_prompt += f"\n\n以下是{name}的说话示例（作为风格和内容的参考）:\n{rag_context}"

        # Emoji context for cultural mapping
        slang = SlangDict()
        emoji_ctx = slang.get_all_emoji_context()
        if emoji_ctx and persona:
            system_prompt += (
                f"\n\n表情/符号语义映射（在此文化语境中的真实含义）:\n{emoji_ctx}"
            )

        # Build message list: system + recent history (short-term) + new message
        messages = [{"role": "system", "content": system_prompt}]
        for h in recent_messages:
            messages.append({"role": h["role"], "content": h["content"]})
        messages.append({"role": "user", "content": user_message})

        # Save user message
        await self._conv.add_message(conversation_id, "user", user_message)

        # Stream response
        full_response = []
        async for token in self._llm.generate(messages):
            full_response.append(token)
            yield token

        # Post-process with humanizer
        assistant_text = "".join(full_response)
        if persona:
            assistant_text = self._humanizer.process(
                assistant_text, persona.style_description
            )

        # Save assistant response
        await self._conv.add_message(conversation_id, "assistant", assistant_text)

        # Auto-generate title for new conversations
        if len(recent_messages) == 0 and len(user_message) > 0:
            title = user_message[:50] + ("..." if len(user_message) > 50 else "")
            await self._conv.update_title(conversation_id, title)

        # Check if we need to generate a mid-term summary
        await self._memory.maybe_summarize(conversation_id, self._llm)
