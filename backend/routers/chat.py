"""Chat API endpoints with SSE streaming."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from backend.dependencies import get_chat_service, get_conversation_store
from backend.schemas.chat import ChatRequest, ConversationInfo, MessageInfo
from backend.services.chat_service import ChatService
from backend.models.conversation import ConversationStore

router = APIRouter(tags=["chat"])


@router.post("/chat")
async def chat(
    req: ChatRequest,
    chat_svc: ChatService = Depends(get_chat_service),
    conv_store: ConversationStore = Depends(get_conversation_store),
):
    """Stream a chat response via SSE."""
    # Create conversation if needed
    conversation_id = req.conversation_id
    if not conversation_id:
        conversation_id = await conv_store.create_conversation(persona_id=req.persona_id)

    async def event_stream():
        # Send conversation_id first
        yield f"data: {json.dumps({'type': 'start', 'conversation_id': conversation_id})}\n\n"

        try:
            async for token in chat_svc.chat(
                conversation_id=conversation_id,
                user_message=req.message,
                persona_id=req.persona_id,
            ):
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/conversations")
async def list_conversations(
    conv_store: ConversationStore = Depends(get_conversation_store),
) -> list[ConversationInfo]:
    rows = await conv_store.list_conversations()
    return [ConversationInfo(**r) for r in rows]


@router.get("/conversations/{conversation_id}/messages")
async def get_messages(
    conversation_id: str,
    conv_store: ConversationStore = Depends(get_conversation_store),
) -> list[MessageInfo]:
    rows = await conv_store.get_messages(conversation_id)
    return [MessageInfo(**r) for r in rows]


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    conv_store: ConversationStore = Depends(get_conversation_store),
):
    await conv_store.delete_conversation(conversation_id)
    return {"status": "deleted"}
