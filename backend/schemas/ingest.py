"""Ingestion request/response schemas."""

from pydantic import BaseModel, Field


class IngestResponse(BaseModel):
    persona_id: str
    persona_name: str
    messages_parsed: int
    chunks_stored: int
    status: str = "success"
