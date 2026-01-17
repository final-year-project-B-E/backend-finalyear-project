from typing import List, Dict, Any
import random
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
        
        # Check for price mentions
        if "under" in message_lower or "less than" in message_lower:
            # Simple price extraction - in production use proper NLP
            intent["max_price"] = 100  # Default
        
        return intent