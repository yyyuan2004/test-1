"""Web learning request/response schemas."""

from pydantic import BaseModel


class WebLearnRequest(BaseModel):
    url: str
    persona_id: str = ""


class WebLearnResponse(BaseModel):
    url: str
    chunks: int = 0
    status: str = "success"
