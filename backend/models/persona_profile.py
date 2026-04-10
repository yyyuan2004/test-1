"""Persona profile data model and persistence — supports individual and group personas."""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field


class PersonaProfile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "未知"
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

    # Persona type: "individual" or "group"
    persona_type: str = "individual"

    # Statistical features
    avg_message_length: float = 0.0
    common_phrases: list[str] = Field(default_factory=list)
    vocabulary_richness: float = 0.0
    emoji_usage: list[str] = Field(default_factory=list)
    greeting_patterns: list[str] = Field(default_factory=list)
    farewell_patterns: list[str] = Field(default_factory=list)

    # LLM-generated description
    style_description: str = ""
    tone: str = ""
    formality_level: str = ""
    humor_style: str = ""
    topics_of_interest: list[str] = Field(default_factory=list)

    # Group persona fields
    group_members: list[str] = Field(default_factory=list)
    interaction_patterns: str = ""
    group_vibe: str = ""

    # Humanization settings
    filler_words: list[str] = Field(default_factory=list)
    typo_tendency: float = 0.0
    slang_preference: list[str] = Field(default_factory=list)

    # Raw data stats
    total_messages_analyzed: int = 0
    source_files: list[str] = Field(default_factory=list)

    def save(self, personas_dir: Path) -> None:
        personas_dir.mkdir(parents=True, exist_ok=True)
        path = personas_dir / f"{self.id}.json"
        self.updated_at = datetime.utcnow().isoformat()
        path.write_text(self.model_dump_json(indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> PersonaProfile:
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(**data)

    @classmethod
    def list_all(cls, personas_dir: Path) -> list[PersonaProfile]:
        if not personas_dir.exists():
            return []
        profiles = []
        for f in personas_dir.glob("*.json"):
            try:
                profiles.append(cls.load(f))
            except Exception:
                continue
        return sorted(profiles, key=lambda p: p.updated_at, reverse=True)
