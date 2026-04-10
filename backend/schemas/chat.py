"""Chat request/response schemas."""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str
    conversation_id: str = ""
    persona_id: str = ""


class ConversationInfo(BaseModel):
    id: str
    persona_id: str = ""
    title: str = "New Chat"
    created_at: str = ""
    updated_at: str = ""


class MessageInfo(BaseModel):
    role: str
    content: str
    created_at: str = ""
