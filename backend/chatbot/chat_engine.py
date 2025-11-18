# backend/chatbot/chat_engine.py
import logging
from typing import Dict, List, Optional

import httpx

from backend.config.settings import settings
from backend.rag.rag_manager import rag_manager

logger = logging.getLogger(__name__)


class ConversationMemory:
    """
    Very simple in-memory conversation store keyed by user_id.

    This is sufficient for the case study:
    - Survives within a single process lifetime
    - Keeps the last N turns per user
    """

    def __init__(self, max_turns: int = 6):
        self.max_turns = max_turns
        self._store: Dict[str, List[Dict[str, str]]] = {}

    def get_history(self, user_id: str) -> List[Dict[str, str]]:
        return self._store.get(user_id, [])

    def add_turn(self, user_id: str, user_message: str, assistant_reply: str) -> None:
        history = self._store.get(user_id, [])
        history.append({"role": "user", "content": user_message})
        history.append({"role": "assistant", "content": assistant_reply})

        # Keep only the last N turns
        if len(history) > self.max_turns * 2:
            history = history[-self.max_turns * 2 :]
        self._store[user_id] = history


memory = ConversationMemory(max_turns=6)


class ChatEngine:
    """
    Main orchestrator for the chatbot:
    - Builds prompt with system instructions
    - Pulls contextual snippets from the RAG vector store
    - Uses Ollama to generate a reply
    - Stores short-term conversation history
    """

    def __init__(self) -> None:
        self.ollama_base_url = settings.ollama_base_url.rstrip("/")
        self.model_name = settings.ollama_model

    async def _get_rag_context(self, query: str, k: int = 3) -> str:
        """
        Query the vector store for relevant chunks.

        Assumes rag_manager.vector_store exposes a `search(query, k)`-like API
        that returns a list of dicts with `content` and optional `metadata`.
        If your actual API is slightly different, adjust here.
        """
        vs = getattr(rag_manager, "vector_store", None)
        if vs is None:
            return ""

        try:
            # Most simple search signature; tweak if needed
            results = vs.search(query, k=k)  # type: ignore[attr-defined]
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("RAG search failed: %s", exc)
            return ""

        snippets: List[str] = []
        for r in results or []:
            content = r.get("content") or r.get("text") or ""
            if not content:
                continue

            meta = r.get("metadata", {})
            src: Optional[str] = None
            if isinstance(meta, dict):
                src = meta.get("source")

            if src:
                snippets.append(f"[Source: {src}]\n{content}")
            else:
                snippets.append(content)

        return "\n\n".join(snippets[:k])

    async def _call_ollama(self, messages: List[Dict[str, str]]) -> str:
        """
        Call Ollama /api/chat endpoint with the composed messages.
        """

        url = f"{self.ollama_base_url}/api/chat"
        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
        }

        async with httpx.AsyncClient(timeout=60) as client:
            try:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
                # Ollama chat format: {"message": {"role": "...", "content": "..."}, ...}
                message = data.get("message") or {}
                content = message.get("content")
                if not content:
                    raise ValueError("No 'content' in Ollama response")
                return content.strip()
            except Exception as exc:  # pragma: no cover - defensive
                logger.exception("Error calling Ollama: %s", exc)
                # Fallback stub so the endpoint never completely breaks
                return "(fallback) LLM is currently unavailable. You said: " + messages[-1]["content"]

    async def chat(
        self,
        user_id: str,
        user_role: str,
        message: str,
    ) -> str:
        """
        High-level chat method used by the FastAPI endpoint.

        - Builds system prompt with capabilities + safety
        - Adds short-term history
        - Adds RAG context for compliance / sanctions / limits
        - Calls Ollama
        - Updates memory
        """
        message = message.strip()
        if not message:
            return "Please enter a non-empty message."

        # 1) System prompt
        system_prompt = (
            "You are an AI-powered financial assistant for a digital bank.\n"
            "- You help users with balances, beneficiaries, and fund transfers.\n"
            "- You must respect the bank's compliance and sanctions policies.\n"
            "- When context from compliance documents is provided, treat it as source-of-truth.\n"
            "- If a transfer violates a rule (limits or sanctions), clearly explain why.\n"
            "- If you are unsure, say that you are unsure instead of inventing facts.\n\n"
            f"The current user role is: {user_role}. "
            "If they appear to be a normal customer, explain things in simple language.\n"
        )

        # 2) Short-term conversation history
        history = memory.get_history(user_id)

        # 3) RAG context (rules, sanctions, etc.)
        rag_context = await self._get_rag_context(message)
        if rag_context:
            user_content = (
                f"User question: {message}\n\n"
                "Here are some relevant compliance / sanctions / rules snippets:\n"
                f"{rag_context}\n\n"
                "Please answer using these rules, and mention when a rule or sanction applies."
            )
        else:
            user_content = message

        # 4) Compose messages for Ollama
        messages: List[Dict[str, str]] = [
            {"role": "system", "content": system_prompt},
            *history,
            {"role": "user", "content": user_content},
        ]

        # 5) Call Ollama
        reply = await self._call_ollama(messages)

        # 6) Persist short-term memory
        memory.add_turn(user_id=user_id, user_message=message, assistant_reply=reply)

        return reply


# Singleton engine used by the API route
chat_engine = ChatEngine()
