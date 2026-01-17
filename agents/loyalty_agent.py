from typing import Dict, Any, List
import random
from datetime import datetime, timedelta
from database import db

class LoyaltyAgent:
    async def apply_offers(self, user_message: str, user_context: Dict[str, Any]) -> str:
        """Apply loyalty points, coupons, and offers"""
        
        user_id = user_context.get("user_id")
        if not user_id:
            return "I need to know who you are to check your offers. Please provide your account details."
        
        user = db.get_user(user_id)
        if not user:
            return "I couldn't find your account. Please sign in or create an account."
        
        loyalty_score = user.get("loyalty_score", 0)
        loyalty_tier = self._get_loyalty_tier(loyalty_score)
        
        # Check for specific intents
        message_lower = user_message.lower()
        
        if any(word in message_lower for word in ["point", "loyalty", "reward"]):
            return self._show_loyalty_status(user, loyalty_tier)
        elif any(word in message_lower for word in ["coupon", "promo", "discount", "offer", "code"]):
            return self._show_available_coupons(user_id, loyalty_tier)
        elif "apply" in message_lower and "coupon" in message_lower:
            return self._apply_coupon(user_message, user_id)
        elif "redeem" in message_lower and "point" in message_lower:
            return self._redeem_points(user_message, user_id, loyalty_score)
        else:
            return self._show_all_offers(user, loyalty_tier)
    
    def _show_loyalty_status(self, user: Dict, tier: str) -> str:
        """Show user's loyalty program status"""
        
        response = f"**✨ {user['first_name']}'s Loyalty Status**\n\n"
        response += f"**Current Tier:** {tier}\n"
        response += f"**Points Balance:** {user['loyalty_score']} points\n"
        response += f"**Member Since:** {user['created_at'][:10]}\n\n"
        
        # Show tier benefits
        response += f"**{tier} Tier Benefits:**\n"
        if tier == "Platinum":
            response += "✅ 20% off all purchases\n"
            response += "✅ Free express shipping\n"
            response += "✅ Early access to sales\n"
            response += "✅ Personal shopping assistant\n"
            response += "✅ Birthday bonus (500 points)\n"
        elif tier == "Gold":
            response += "✅ 15% off all purchases\n"
            response += "✅ Free standard shipping\n"
            response += "✅ 48-hour early access to sales\n"
            response += "✅ Birthday bonus (250 points)\n"
        elif tier == "Silver":
            response += "✅ 10% off all purchases\n"
            response += "✅ Free shipping over $75\n"
            response += "✅ Birthday bonus (100 points)\n"
        else:  # Bronze
            response += "✅ 5% off all purchases\n"
            response += "✅ Free shipping over $100\n"
            response += "✅ Earn 2x points on first purchase\n"
        
        # Points value
        points_value = user['loyalty_score'] * 0.01  # $0.01 per point
        response += f"\n**Points Value:** ${points_value:.2f}\n"
        response += f"**Next Tier:** {self._get_next_tier_info(user['loyalty_score'])}\n"
        
        return response
    
    def _show_available_coupons(self, user_id: int, tier: str) -> str:
        """Show available coupons and promotions"""
        
        coupons = self._get_available_coupons(user_id, tier)
        
        response = "**🎟️ Available Offers & Coupons**\n\n"
        
        for i, coupon in enumerate(coupons, 1):
            response += f"{i}. **{coupon['name']}**\n"
            response += f"   Code: `{coupon['code']}`\n"
            response += f"   Discount: {coupon['discount']}\n"
            response += f"   Valid: {coupon['valid_until']}\n"
            if coupon['min_purchase']:
                response += f"   Min. Purchase: ${coupon['min_purchase']}\n"
            response += "\n"
        
        response += "**How to use:**\n"
        response += "1. Add items to your cart\n"
        response += "2. At checkout, enter the coupon code\n"
        response += "3. Discount will be applied automatically\n\n"
        
        response += "Say 'apply coupon [CODE]' to use one now!"
        
        return response
    
    def _apply_coupon(self, message: str, user_id: int) -> str:
        """Apply a coupon code"""
        
        # Extract coupon code
        code = self._extract_coupon_code(message)
        if not code:
            return "Please provide a coupon code. Example: 'apply coupon SUMMER20'"
        
        # Validate coupon
        coupon = self._validate_coupon(code.upper(), user_id)
        if not coupon:
            return f"❌ Coupon code `{code}` is invalid or expired. Please check and try again."
        
        response = f"✅ **Coupon Applied Successfully!**\n\n"
        response += f"**{coupon['name']}**\n"
        response += f"Code: `{coupon['code']}`\n"
        response += f"Discount: {coupon['discount']}\n"
        
        if coupon['description']:
            response += f"Details: {coupon['description']}\n"
        
        if coupon['exclusions']:
            response += f"Exclusions: {coupon['exclusions']}\n"
        
        response += f"\nThe discount will be applied at checkout."
        
        return response
    
    def _redeem_points(self, message: str, user_id: int, points_balance: int) -> str:
        """Redeem loyalty points"""
        
        # Extract points amount
        points_to_redeem = self._extract_points_amount(message)
        if not points_to_redeem:
            return "How many points would you like to redeem? Example: 'redeem 500 points'"
        
        if points_to_redeem > points_balance:
            return f"❌ You only have {points_balance} points. Please enter a smaller amount."
        
        if points_to_redeem < 100:
            return "❌ Minimum redemption is 100 points."
        
        # Calculate discount
        discount_amount = points_to_redeem * 0.01  # $0.01 per point
        
        response = f"✅ **Points Redemption Ready**\n\n"
        response += f"Redeeming: **{points_to_redeem} points**\n"
        response += f"Discount Value: **${discount_amount:.2f}**\n"
        response += f"Remaining Balance: **{points_balance - points_to_redeem} points**\n\n"
        
        response += "Your points discount will be applied at checkout. Continue shopping?"
        
        return response
    
    def _show_all_offers(self, user: Dict, tier: str) -> str:
        """Show all available offers"""
        
        response = f"**🎁 Special Offers for {user['first_name']}**\n\n"
        
        # Current promotions
        response += "**🔥 Current Promotions:**\n"
        promotions = [
            "Spring Sale: Up to 40% off select dresses",
            "New Customer: 15% off first order",
            "Bundle & Save: Buy 2, get 10% off",
            "Weekend Special: Free shipping on all orders"
        ]
        for promo in promotions:
            response += f"• {promo}\n"
        
        response += "\n**🎟️ Your Coupons:**\n"
        coupons = self._get_available_coupons(user['id'], tier)
        for coupon in coupons[:3]:
            response += f"• {coupon['name']}: {coupon['discount']} (Code: {coupon['code']})\n"
        
        response += f"\n**✨ Loyalty Points:** {user['loyalty_score']} points available\n"
        response += f"**💎 Tier Status:** {tier} Member\n\n"
        
        response += "Would you like to:\n"
        response += "1. See all coupons\n"
        response += "2. Check loyalty points value\n"
        response += "3. Apply a specific coupon\n"
        response += "4. Redeem points\n"
        
        return response
    
    def _get_loyalty_tier(self, points: int) -> str:
        """Get loyalty tier based on points"""
        if points >= 500:
            return "Platinum"
        elif points >= 200:
            return "Gold"
        elif points >= 100:
            return "Silver"
        else:
            return "Bronze"
    
    def _get_next_tier_info(self, current_points: int) -> str:
        """Get information about next tier"""
        if current_points < 100:
            needed = 100 - current_points
            return f"Silver Tier in {needed} points"
        elif current_points < 200:
            needed = 200 - current_points
            return f"Gold Tier in {needed} points"
        elif current_points < 500:
            needed = 500 - current_points
            return f"Platinum Tier in {needed} points"
        else:
            return "You're at the highest tier!"
    
    def _get_available_coupons(self, user_id: int, tier: str) -> List[Dict]:
        """Get available coupons for user (simulated)"""
        
        base_coupons = [
            {
                "name": "Welcome Bonus",
                "code": "WELCOME15",
                "discount": "15% off first order",
                "valid_until": "2024-12-31",
                "min_purchase": None,
                "description": "For new customers only",
                "exclusions": "Sale items"
            },
            {
                "name": "Spring Sale",
                "code": "SPRING20",
                "discount": "20% off all dresses",
                "valid_until": "2024-04-30",
                "min_purchase": 50,
                "description": "Spring collection special",
                "exclusions": None
            }
        ]
        
        tier_coupons = {
            "Bronze": [
                {
                    "name": "Bronze Member Special",
                    "code": "BRONZE10",
                    "discount": "10% off",
                    "valid_until": "2024-12-31",
                    "min_purchase": 75,
                    "description": "Exclusive for Bronze members",
                    "exclusions": None
                }
            ],
            "Silver": [
                {
                    "name": "Silver Exclusive",
                    "code": "SILVER15",
                    "discount": "15% off",
                    "valid_until": "2024-12-31",
                    "min_purchase": None,
                    "description": "For Silver members and above",
                    "exclusions": "Already discounted items"
                }
            ],
            "Gold": [
                {
                    "name": "Gold VIP Offer",
                    "code": "GOLD20",
                    "discount": "20% off",
                    "valid_until": "2024-12-31",
                    "min_purchase": None,
                    "description": "VIP discount for Gold members",
                    "exclusions": None
                }
            ],
            "Platinum": [
                {
                    "name": "Platinum Elite",
                    "code": "PLATINUM25",
                    "discount": "25% off",
                    "valid_until": "2024-12-31",
                    "min_purchase": None,
                    "description": "Elite discount for Platinum members",
                    "exclusions": None
                }
            ]
        }
        
        return base_coupons + tier_coupons.get(tier, [])
    
    def _extract_coupon_code(self, message: str) -> str:
        """Extract coupon code from message"""
        words = message.upper().split()
        for word in words:
            if len(word) >= 6 and any(c.isalpha() for c in word) and any(c.isdigit() for c in word):
                return word
        return ""
    
    def _extract_points_amount(self, message: str) -> int:
        """Extract points amount from message"""
        words = message.split()
        for i, word in enumerate(words):
            if word.isdigit():
                return int(word)
        return 0
    
    def _validate_coupon(self, code: str, user_id: int) -> Dict:
        """Validate coupon code (simulated)"""
        # In production, this would check a database
        valid_coupons = {
            "WELCOME15": {
                "name": "Welcome Bonus",
                "code": "WELCOME15",
                "discount": "15% off",
                "valid_until": "2024-12-31",
                "min_purchase": None,
                "description": "For new customers",
                "exclusions": "Sale items"
            },
            "SPRING20": {
                "name": "Spring Sale",
                "code": "SPRING20",
                "discount": "20% off dresses",
                "valid_until": "2024-04-30",
                "min_purchase": 50,
                "description": "Spring collection",
                "exclusions": None
            }
        }
        
        return valid_coupons.get(code)