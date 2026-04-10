"""Persona request/response schemas."""

from pydantic import BaseModel, Field


class PersonaUpdate(BaseModel):
    name: str | None = None
    tone: str | None = None
    formality_level: str | None = None
    humor_style: str | None = None
    style_description: str | None = None
    topics_of_interest: list[str] | None = None


class PersonaInfo(BaseModel):
    id: str
    name: str
    tone: str = ""
    formality_level: str = ""
    humor_style: str = ""
    style_description: str = ""
    topics_of_interest: list[str] = []
    common_phrases: list[str] = []
    emoji_usage: list[str] = []
    avg_message_length: float = 0.0
    total_messages_analyzed: int = 0
    created_at: str = ""
    updated_at: str = ""
