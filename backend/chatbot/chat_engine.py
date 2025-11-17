from typing import Any, Dict, Optional
from uuid import uuid4

from langchain import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate

from backend.config.settings import settings
from backend.utils.chat_context import ChatContextManager
from backend.utils.intent_classifier import IntentClassifier
from backend.utils.rule_checker import ComplianceRuleChecker


class ChatEngine:
    """LLM-based conversational engine for banking operations."""

    def __init__(self):
        self.model = ChatOpenAI(
            model_name="gpt-3.5-turbo",
            temperature=0.2,
            openai_api_key=settings.openai_api_key,
        )
        self.memory = ConversationBufferMemory(
            memory_key="chat_history", return_messages=True
        )
        self.intent_classifier = IntentClassifier()
        self.context_manager = ChatContextManager()
        self.rule_checker = ComplianceRuleChecker()

        self.template = PromptTemplate(
            input_variables=["chat_history", "user_input"],
            template=(
                "You are a financial assistant chatbot.\n"
                "Chat History:\n{chat_history}\n"
                "User: {user_input}\n"
                "Follow compliance rules, enforce sanctions and limits, "
                "and generate a concise, polite response."
            ),
        )
        self.chain = LLMChain(llm=self.model, prompt=self.template, memory=self.memory)

    async def chat(self, user_input: str, user_id: str) -> Dict[str, Any]:
        """Process user query and route to the appropriate backend logic."""
        intent = self.intent_classifier.detect_intent(user_input)
        session_id = str(uuid4())

        if intent == "check_balance":
            balance_data = await self.context_manager.fetch_balance(user_id)
            return {
                "response": f"Your current balance is {balance_data['balance']} BHD.",
                "intent": intent,
                "session_id": session_id,
            }

        elif intent == "add_beneficiary":
            result = await self.context_manager.add_beneficiary(user_id, user_input)
            return {
                "response": result["message"],
                "intent": intent,
                "session_id": session_id,
            }

        elif intent == "transfer_funds":
            compliance_ok, msg = await self.rule_checker.verify_transaction(
                user_id, user_input
            )
            if not compliance_ok:
                return {
                    "response": f"Transfer blocked – {msg}",
                    "intent": intent,
                    "session_id": session_id,
                }

            result = await self.context_manager.execute_transfer(user_id, user_input)
            return {
                "response": result["message"],
                "intent": intent,
                "session_id": session_id,
            }

        else:
            reply = self.chain.run(user_input=user_input)
            return {
                "response": reply,
                "intent": "general",
                "session_id": session_id,
            }
