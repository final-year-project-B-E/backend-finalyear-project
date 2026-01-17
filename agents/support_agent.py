from typing import Dict, Any

class SupportAgent:
    async def handle_support(self, user_message: str, user_context: Dict[str, Any]) -> str:
        """Handle customer support requests like returns, exchanges, complaints"""

        message_lower = user_message.lower()

        # Check for return/exchange requests
        if any(word in message_lower for word in ["return", "exchange", "refund"]):
            return self._handle_return_request(user_message, user_context)

        # Check for order issues
        elif any(word in message_lower for word in ["wrong item", "damaged", "defective", "quality issue"]):
            return self._handle_order_issue(user_message, user_context)

        # Check for account issues
        elif any(word in message_lower for word in ["account", "login", "password", "profile"]):
            return self._handle_account_issue(user_message, user_context)

        # Check for general complaints
        elif any(word in message_lower for word in ["complaint", "unhappy", "disappointed", "problem"]):
            return self._handle_complaint(user_message, user_context)

        # Default support response
        else:
            return """I'm here to help with any issues you might have. Could you please tell me more about what you need assistance with?

**Common Support Topics:**
- Returns and exchanges
- Order issues (wrong/damaged items)
- Account and login problems
- Product questions
- Billing and payment issues

Please describe your concern, and I'll connect you with the right specialist or provide immediate assistance."""

    def _handle_return_request(self, message: str, user_context: Dict[str, Any]) -> str:
        """Handle return/exchange requests"""
        return """I understand you'd like to return or exchange an item. Let me help you with that.

**Return Policy:**
- Items can be returned within 30 days of delivery
- Must be in original condition with tags attached
- Free return shipping for defective items
- Exchanges processed within 3-5 business days

To process your return:
1. Please provide your order number (ORD-XXXXX)
2. Tell me which item(s) you'd like to return
3. Reason for return (fit, style, defect, etc.)

Would you like me to look up your recent orders, or do you have your order number ready?"""

    def _handle_order_issue(self, message: str, user_context: Dict[str, Any]) -> str:
        """Handle order-related issues"""
        return """I'm sorry to hear you're experiencing an issue with your order. Let me help resolve this.

**Common Order Issues:**
- Wrong item received
- Damaged/defective product
- Missing items
- Late delivery

Could you please provide:
- Your order number
- A description of the issue
- Photos if applicable (for damage/defects)

I'll investigate immediately and arrange for a replacement, refund, or other resolution. For urgent issues, I can escalate this to our priority support team."""

    def _handle_account_issue(self, message: str, user_context: Dict[str, Any]) -> str:
        """Handle account-related issues"""
        return """I'd be happy to help with your account concerns.

**Account Support Options:**
- Password reset assistance
- Profile information updates
- Order history access
- Loyalty program questions
- Communication preferences

Please let me know specifically what you'd like to update or what issue you're experiencing, and I'll guide you through the process or make the changes for you."""

    def _handle_complaint(self, message: str, user_context: Dict[str, Any]) -> str:
        """Handle general complaints"""
        return """I apologize for any negative experience you've had. Your satisfaction is our top priority.

To better assist you, could you please share:
- What specifically went wrong
- When this occurred
- Any order numbers involved
- How you'd like us to make this right

I'll personally ensure this is addressed promptly. For serious concerns, I can connect you directly with our customer experience manager."""