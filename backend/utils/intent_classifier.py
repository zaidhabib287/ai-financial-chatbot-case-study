import re

from backend.config.constants import CHAT_INTENTS


class IntentClassifier:
    """Simple rule-based intent classifier."""

    def detect_intent(self, text: str) -> str:
        text_lower = text.lower()
        for intent, keywords in CHAT_INTENTS.items():
            if any(re.search(rf"\\b{kw}\\b", text_lower) for kw in keywords):
                return intent
        return "general"
