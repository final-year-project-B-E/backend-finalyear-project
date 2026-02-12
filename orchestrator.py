from typing import Dict, Any, List

from agents.sales_agent import SalesAgent
from agents.recommendation_agent import RecommendationAgent
from agents.inventory_agent import InventoryAgent
from agents.payment_agent import PaymentAgent
from agents.fulfillment_agent import FulfillmentAgent
from agents.loyalty_agent import LoyaltyAgent
from agents.support_agent import SupportAgent
from database import db
from schemas import SalesRequest, SalesResponse


class Orchestrator:
    def __init__(self):
        self.sales_agent = SalesAgent()
        self.recommendation_agent = RecommendationAgent()
        self.inventory_agent = InventoryAgent()
        self.payment_agent = PaymentAgent()
        self.fulfillment_agent = FulfillmentAgent()
        self.loyalty_agent = LoyaltyAgent()
        self.support_agent = SupportAgent()

        self.agents = {
            "sales": self.sales_agent,
            "recommendation": self.recommendation_agent,
            "inventory": self.inventory_agent,
            "payment": self.payment_agent,
            "fulfillment": self.fulfillment_agent,
            "loyalty": self.loyalty_agent,
            "support": self.support_agent,
        }

    async def process_message(self, request: SalesRequest) -> SalesResponse:
        """Main entry point for processing sales conversations."""
        session_id = request.session_id
        if not session_id and request.user_id:
            session_id = db.create_chat_session(request.user_id, request.channel)

        if session_id:
            db.add_chat_message(session_id, "user", request.message)

        user_context = self._build_user_context(request.user_id)

        chat_history: List[Dict[str, str]] = []
        if session_id:
            messages = db.get_chat_history(session_id, limit=12)
            chat_history = [
                {"role": msg["message_type"], "content": msg["content"]}
                for msg in messages
            ]

        intents = self._detect_intents(request.message)
        tool_outputs = await self._run_agentic_steps(intents, request.message, user_context)

        response_text = self.sales_agent.compose_response(
            user_message=request.message,
            history=chat_history,
            user_context=user_context,
            channel=request.channel,
            tool_outputs=tool_outputs,
        )

        if session_id:
            db.add_chat_message(session_id, "assistant", response_text, "sales")

        requires_action, action_type, action_data = self._extract_action(response_text, user_context)

        return SalesResponse(
            reply=response_text,
            session_id=session_id,
            requires_action=requires_action,
            action_type=action_type,
            action_data=action_data,
        )

    def _build_user_context(self, user_id: int | None) -> Dict[str, Any]:
        if not user_id:
            return {}

        user = db.get_user(user_id)
        if not user:
            return {"user_id": user_id}

        return {
            "name": f"{user['first_name']} {user['last_name']}",
            "loyalty_score": user.get("loyalty_score", 0),
            "past_orders": db.get_user_orders(user_id),
            "user_id": user_id,
        }

    def _detect_intents(self, message: str) -> List[str]:
        message_lower = message.lower()
        intents: List[str] = []

        intent_rules = {
            "recommendation": ["recommend", "suggest", "find", "looking for", "style"],
            "inventory": ["stock", "available", "in stock", "inventory", "size availability"],
            "payment": ["pay", "payment", "checkout", "buy", "purchase", "price total"],
            "fulfillment": ["delivery", "ship", "pickup", "arrive", "track", "shipping"],
            "loyalty": ["discount", "coupon", "promo", "loyalty", "points", "offer"],
            "support": ["return", "exchange", "refund", "issue", "problem", "damaged"],
        }

        for intent, triggers in intent_rules.items():
            if any(trigger in message_lower for trigger in triggers):
                intents.append(intent)

        if not intents:
            intents.append("sales")

        return intents[:3]

    async def _run_agentic_steps(
        self,
        intents: List[str],
        message: str,
        user_context: Dict[str, Any],
    ) -> List[Dict[str, str]]:
        outputs: List[Dict[str, str]] = []

        for intent in intents:
            if intent == "sales":
                continue

            response = await self._delegate_to_agent(intent, message, user_context)
            if response:
                outputs.append({"source": f"{intent}_agent", "content": response})

        return outputs

    async def _delegate_to_agent(self, agent_type: str, message: str, user_context: Dict[str, Any]) -> str:
        agent = self.agents.get(agent_type)
        if not agent:
            return ""

        try:
            if agent_type == "recommendation":
                return await agent.get_recommendations(message, user_context)
            if agent_type == "inventory":
                return await agent.check_inventory(message, user_context)
            if agent_type == "payment":
                return await agent.process_payment(message, user_context)
            if agent_type == "fulfillment":
                return await agent.arrange_fulfillment(message, user_context)
            if agent_type == "loyalty":
                return await agent.apply_offers(message, user_context)
            if agent_type == "support":
                return await agent.handle_support(message, user_context)
            return ""
        except Exception as error:
            return f"{agent_type} agent error: {str(error)}"

    def _extract_action(self, response: str, user_context: Dict[str, Any]) -> tuple:
        response_lower = response.lower()

        if "add to cart" in response_lower:
            return True, "add_to_cart", {"product_id": 1, "quantity": 1}
        if "checkout" in response_lower or "complete purchase" in response_lower:
            return True, "checkout", {"user_id": user_context.get("user_id")}

        return False, None, None
