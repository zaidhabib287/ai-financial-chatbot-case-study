# backend/api/chatbot.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.auth.dependencies import get_current_active_user

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
    # If you have a real chat manager, call it here; otherwise return a stub.
    text = body.content.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Empty message.")
    return ChatResponse(reply=f"(stub) You said: {text}")
