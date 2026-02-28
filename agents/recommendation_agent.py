from typing import List, Dict, Any
import re
from database import db

class RecommendationAgent:
    async def get_recommendations(self, user_message: str, user_context: Dict[str, Any]) -> str:
        """Generate personalized product recommendations"""
        
        # Parse user intent from message
        intent = self._parse_intent(user_message)
        
        # Get relevant products
        products = db.search_products(
            category=intent.get("category"),
            occasion=intent.get("occasion"),
            min_price=intent.get("min_price"),
            max_price=intent.get("max_price")
        )
        
        # Filter to top 3 recommendations
        recommendations = products[:3]
        
        if not recommendations:
            return "I couldn't find any products matching your criteria. Could you tell me more about what you're looking for?"
        
        # Format response
        response = "Based on what you're looking for, here are my recommendations:\n\n"
        
        for i, product in enumerate(recommendations, 1):
            response += f"{i}. **{product['product_name']}**\n"
            response += f"   - Price: ${product['price']}\n"
            response += f"   - Category: {product['dress_category']}\n"
            response += f"   - Occasion: {product['occasion']}\n"
            response += f"   - Available in: {product['colors']}\n"
            if product['stock'] > 0:
                response += f"   - ✅ In stock ({product['stock']} available)\n"
            else:
                response += f"   - ⚠️ Currently out of stock\n"
            response += "\n"
        
        response += "Would you like me to:\n"
        response += "1. Show more details about any of these?\n"
        response += "2. Check availability in your size?\n"
        response += "3. See complementary accessories?\n"
        
        return response
    
    def _parse_intent(self, message: str) -> Dict[str, Any]:
        """Parse user intent from message"""
        message_lower = message.lower()
        intent = {}

        # Check for categories
        categories = ["evening", "summer", "office", "casual", "formal", "wedding", "party"]
        for category in categories:
            if category in message_lower:
                intent["category"] = category.capitalize()
                break

        # Check for occasions
        occasions = ["wedding", "party", "business", "date", "formal", "casual", "vacation"]
        for occasion in occasions:
            if occasion in message_lower:
                intent["occasion"] = occasion.capitalize()
                break

        budget_match = re.search(r"(?:under|below|less than|upto|up to)\s*\$?(\d+(?:\.\d+)?)", message_lower)
        if budget_match:
            intent["max_price"] = float(budget_match.group(1))

        range_match = re.search(r"\$?(\d+(?:\.\d+)?)\s*(?:to|\-|–)\s*\$?(\d+(?:\.\d+)?)", message_lower)
        if range_match:
            low = float(range_match.group(1))
            high = float(range_match.group(2))
            intent["min_price"] = min(low, high)
            intent["max_price"] = max(low, high)

        return intent
