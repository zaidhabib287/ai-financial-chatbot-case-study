# backend/api/chatbot.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.auth.dependencies import get_current_active_user
from backend.chatbot.chat_engine import chat_engine

router = APIRouter()


class ChatRequest(BaseModel):
    content: str


class ChatResponse(BaseModel):
    reply: str


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    body: ChatRequest,
    current_user=Depends(get_current_active_user),
):
    """
    Chat endpoint for the financial assistant.

    - Requires an authenticated user (JWT)
    - Delegates to ChatEngine (Ollama + RAG + memory)
    """
    text = body.content.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Empty message.")

    reply = await chat_engine.chat(
        user_id=str(current_user.id),
        user_role=str(current_user.role.value if hasattr(current_user.role, "value") else current_user.role),
        message=text,
    )
    return ChatResponse(reply=reply)
