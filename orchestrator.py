from typing import Dict, Any, Optional, List
import json
from datetime import datetime
from agents.sales_agent import SalesAgent
from agents.recommendation_agent import RecommendationAgent
from agents.inventory_agent import InventoryAgent
from agents.payment_agent import PaymentAgent
from agents.fulfillment_agent import FulfillmentAgent
from agents.loyalty_agent import LoyaltyAgent
from agents.support_agent import SupportAgent
from mongo_database import db
from schemas import SalesRequest, SalesResponse, Channel

class Orchestrator:
    def __init__(self):
        self.sales_agent = SalesAgent()
        self.recommendation_agent = RecommendationAgent()
        self.inventory_agent = InventoryAgent()
        self.payment_agent = PaymentAgent()
        self.fulfillment_agent = FulfillmentAgent()
        self.loyalty_agent = LoyaltyAgent()
        self.support_agent = SupportAgent()
        
        # Agent registry
        self.agents = {
            "sales": self.sales_agent,
            "recommendation": self.recommendation_agent,
            "inventory": self.inventory_agent,
            "payment": self.payment_agent,
            "fulfillment": self.fulfillment_agent,
            "loyalty": self.loyalty_agent,
            "support": self.support_agent
        }
    
    async def process_message(self, request: SalesRequest) -> SalesResponse:
        """Main entry point for processing sales conversations"""
        
        # Get or create session
        session_id = request.session_id
        if not session_id and request.user_id:
            session_id = db.create_chat_session(request.user_id, request.channel)
        
        # Add user message to history
        if session_id:
            db.add_chat_message(session_id, "user", request.message)
        
        # Get user context
        user_context = {}
        if request.user_id:
            user = db.get_user(request.user_id)
            if user:
                user_context = {
                    "name": f"{user['first_name']} {user['last_name']}",
                    "loyalty_score": user['loyalty_score'],
                    "past_orders": self._get_user_orders(request.user_id)
                }
        
        # Get chat history
        chat_history = []
        if session_id:
            messages = db.get_chat_history(session_id, limit=10)
            chat_history = [
                {"role": msg["message_type"], "content": msg["content"]}
                for msg in messages
            ]
        
        # Determine which agent should handle this
        agent_type = self._route_to_agent(request.message, user_context)
        
        # Process with appropriate agent
        if agent_type == "sales":
            response_text = self.sales_agent.process(
                user_message=request.message,
                history=chat_history,
                user_context=user_context,
                channel=request.channel
            )
        else:
            # Delegate to specialized agent
            response_text = await self._delegate_to_agent(
                agent_type, request.message, user_context
            )
        
        # Add assistant response to history
        if session_id:
            db.add_chat_message(session_id, "assistant", response_text, agent_type)
        
        # Check if action is required
        requires_action, action_type, action_data = self._extract_action(
            response_text, user_context
        )
        
        return SalesResponse(
            reply=response_text,
            session_id=session_id,
            requires_action=requires_action,
            action_type=action_type,
            action_data=action_data
        )
    
    def _route_to_agent(self, message: str, user_context: Dict[str, Any]) -> str:
        """Route message to appropriate agent"""
        message_lower = message.lower()
        
        # Check for specific intents
        if any(word in message_lower for word in ["recommend", "suggest", "find", "looking for", "need help finding"]):
            return "recommendation"
        elif any(word in message_lower for word in ["stock", "available", "in stock", "out of stock", "inventory"]):
            return "inventory"
        elif any(word in message_lower for word in ["pay", "payment", "checkout", "buy", "purchase", "order"]):
            return "payment"
        elif any(word in message_lower for word in ["delivery", "ship", "pickup", "fulfillment", "when will it arrive"]):
            return "fulfillment"
        elif any(word in message_lower for word in ["discount", "coupon", "promo", "loyalty", "points", "offer"]):
            return "loyalty"
        elif any(word in message_lower for word in ["return", "exchange", "support", "help", "issue", "problem"]):
            return "support"
        else:
            return "sales"
    
    async def _delegate_to_agent(self, agent_type: str, message: str, 
                                user_context: Dict[str, Any]) -> str:
        """Delegate task to specialized agent"""
        agent = self.agents.get(agent_type)
        if not agent:
            return "I'll connect you with the right specialist. Please wait a moment."
        
        try:
            if agent_type == "recommendation":
                return await agent.get_recommendations(message, user_context)
            elif agent_type == "inventory":
                return await agent.check_inventory(message, user_context)
            elif agent_type == "payment":
                return await agent.process_payment(message, user_context)
            elif agent_type == "fulfillment":
                return await agent.arrange_fulfillment(message, user_context)
            elif agent_type == "loyalty":
                return await agent.apply_offers(message, user_context)
            elif agent_type == "support":
                return await agent.handle_support(message, user_context)
        except Exception as e:
            return f"I encountered an issue. Let me connect you with our sales agent instead. Error: {str(e)}"
    
    def _extract_action(self, response: str, user_context: Dict[str, Any]) -> tuple:
        """Extract required actions from agent response"""
        # This is simplified - in production, use proper intent recognition
        if "add to cart" in response.lower():
            return True, "add_to_cart", {"product_id": 1, "quantity": 1}  # Example
        elif "checkout" in response.lower():
            return True, "checkout", {"user_id": user_context.get("user_id")}
        return False, None, None
    
    def _get_user_orders(self, user_id: int) -> List[Dict]:
        """Get user's past orders"""
        return db.get_user_orders(user_id)