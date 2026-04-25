from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from database import db

TIER_RANKS = {
    "Bronze": 0,
    "Silver": 1,
    "Gold": 2,
    "Platinum": 3,
}


class LoyaltyAgent:
    async def apply_offers(self, user_message: str, user_context: Dict[str, Any]) -> str:
        """Apply loyalty points, coupons, and offers."""

        user_id = user_context.get("user_id")
        if not user_id:
            return "I need to know who you are to check your offers. Please provide your account details."

        user = db.get_user_flexible(user_id)
        if not user:
            return "I couldn't find your account. Please sign in or create an account."

        loyalty_score = user.get("loyalty_score", 0)
        loyalty_tier = self._get_loyalty_tier(loyalty_score)
        message_lower = user_message.lower()

        if self._is_coupon_application_request(message_lower):
            return self._apply_coupon(user_message, user_id)
        if self._is_points_redemption_request(message_lower):
            return self._redeem_points(user_message, user_id, loyalty_score)
        if any(word in message_lower for word in ["point", "loyalty", "reward"]):
            return self._show_loyalty_status(user, loyalty_tier)
        if any(word in message_lower for word in ["coupon", "promo", "discount", "offer", "code"]):
            return self._show_available_coupons(user_id, loyalty_tier)
        return self._show_all_offers(user, loyalty_tier)

    def _show_loyalty_status(self, user: Dict[str, Any], tier: str) -> str:
        response = f"**✨ {user['first_name']}'s Loyalty Status**\n\n"
        response += f"**Current Tier:** {tier}\n"
        response += f"**Points Balance:** {user['loyalty_score']} points\n"
        response += f"**Member Since:** {str(user['created_at'])[:10]}\n\n"

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
        else:
            response += "✅ 5% off all purchases\n"
            response += "✅ Free shipping over $100\n"
            response += "✅ Earn 2x points on first purchase\n"

        points_value = user["loyalty_score"] * 0.01
        response += f"\n**Points Value:** ${points_value:.2f}\n"
        response += f"**Next Tier:** {self._get_next_tier_info(user['loyalty_score'])}\n"
        return response

    def _show_available_coupons(self, user_id: str, tier: str) -> str:
        coupons = self._get_available_coupons(user_id, tier)
        if not coupons:
            return (
                "**🎟️ Available Offers & Coupons**\n\n"
                "You do not have any active coupon codes right now, but your loyalty benefits still apply."
            )

        response = "**🎟️ Available Offers & Coupons**\n\n"
        for index, coupon in enumerate(coupons, 1):
            response += f"{index}. **{coupon['name']}**\n"
            response += f"   Code: `{coupon['code']}`\n"
            response += f"   Discount: {coupon['discount']}\n"
            response += f"   Valid Until: {coupon['valid_until']}\n"
            if coupon.get("min_purchase"):
                response += f"   Min. Purchase: ${coupon['min_purchase']}\n"
            response += "\n"

        response += "**How to use:**\n"
        response += "1. Add items to your cart\n"
        response += "2. At checkout, enter the coupon code\n"
        response += "3. Discount will be applied automatically\n\n"
        response += "Say 'apply coupon [CODE]' to use one now!"
        return response

    def _apply_coupon(self, message: str, user_id: str) -> str:
        code = self._extract_coupon_code(message)
        if not code:
            return "Please provide a coupon code. Example: 'apply coupon SUMMER20'"

        coupon = self._validate_coupon(code.upper(), user_id)
        if not coupon:
            return f"❌ Coupon code `{code}` is invalid, ineligible for your account, or expired."

        response = "✅ **Coupon Applied Successfully!**\n\n"
        response += f"**{coupon['name']}**\n"
        response += f"Code: `{coupon['code']}`\n"
        response += f"Discount: {coupon['discount']}\n"
        response += f"Valid Until: {coupon['valid_until']}\n"
        if coupon.get("description"):
            response += f"Details: {coupon['description']}\n"
        if coupon.get("exclusions"):
            response += f"Exclusions: {coupon['exclusions']}\n"
        response += "\nThe discount will be applied at checkout."
        return response

    def _redeem_points(self, message: str, user_id: str, points_balance: int) -> str:
        points_to_redeem = self._extract_points_amount(message)
        if not points_to_redeem:
            return "How many points would you like to redeem? Example: 'redeem 500 points'"

        if points_to_redeem > points_balance:
            return f"❌ You only have {points_balance} points. Please enter a smaller amount."
        if points_to_redeem < 100:
            return "❌ Minimum redemption is 100 points."

        discount_amount = points_to_redeem * 0.01
        response = "✅ **Points Redemption Ready**\n\n"
        response += f"Redeeming: **{points_to_redeem} points**\n"
        response += f"Discount Value: **${discount_amount:.2f}**\n"
        response += f"Remaining Balance: **{points_balance - points_to_redeem} points**\n\n"
        response += "Your points discount will be applied at checkout. Continue shopping?"
        return response

    def _show_all_offers(self, user: Dict[str, Any], tier: str) -> str:
        response = f"**🎁 Special Offers for {user['first_name']}**\n\n"
        response += "**🔥 Current Promotions:**\n"
        promotions = [
            "Seasonal Sale: Up to 40% off select dresses",
            "New Customer: 15% off first order",
            "Bundle & Save: Buy 2, get 10% off",
            "Weekend Special: Free shipping on all orders",
        ]
        for promo in promotions:
            response += f"• {promo}\n"

        response += "\n**🎟️ Your Coupons:**\n"
        coupons = self._get_available_coupons(str(user["id"]), tier)
        if coupons:
            for coupon in coupons[:3]:
                response += f"• {coupon['name']}: {coupon['discount']} (Code: {coupon['code']})\n"
        else:
            response += "• No active coupon codes at the moment\n"

        response += f"\n**✨ Loyalty Points:** {user['loyalty_score']} points available\n"
        response += f"**💎 Tier Status:** {tier} Member\n\n"
        response += "Would you like to:\n"
        response += "1. See all coupons\n"
        response += "2. Check loyalty points value\n"
        response += "3. Apply a specific coupon\n"
        response += "4. Redeem points\n"
        return response

    def _get_loyalty_tier(self, points: int) -> str:
        if points >= 500:
            return "Platinum"
        if points >= 200:
            return "Gold"
        if points >= 100:
            return "Silver"
        return "Bronze"

    def _get_next_tier_info(self, current_points: int) -> str:
        if current_points < 100:
            return f"Silver Tier in {100 - current_points} points"
        if current_points < 200:
            return f"Gold Tier in {200 - current_points} points"
        if current_points < 500:
            return f"Platinum Tier in {500 - current_points} points"
        return "You're at the highest tier!"

    def _get_available_coupons(self, user_id: str, tier: str) -> List[Dict[str, Any]]:
        order_count = len(db.get_user_orders(user_id))
        coupons = []
        for coupon in self._coupon_catalog():
            if self._coupon_is_eligible(coupon, tier, order_count):
                coupons.append(coupon)
        return coupons

    def _coupon_catalog(self) -> List[Dict[str, Any]]:
        return [
            self._build_coupon(
                name="Welcome Bonus",
                code="WELCOME15",
                discount="15% off first order",
                valid_days=90,
                description="For customers placing their first order",
                exclusions="Sale items",
                new_customer_only=True,
            ),
            self._build_coupon(
                name="Seasonal Style Sale",
                code="SPRING20",
                discount="20% off all dresses",
                valid_days=45,
                min_purchase=50,
                description="Limited-time seasonal collection offer",
            ),
            self._build_coupon(
                name="Bronze Member Special",
                code="BRONZE10",
                discount="10% off",
                valid_days=60,
                min_purchase=75,
                description="Exclusive for Bronze members",
                minimum_tier="Bronze",
            ),
            self._build_coupon(
                name="Silver Exclusive",
                code="SILVER15",
                discount="15% off",
                valid_days=60,
                description="For Silver members and above",
                exclusions="Already discounted items",
                minimum_tier="Silver",
            ),
            self._build_coupon(
                name="Gold VIP Offer",
                code="GOLD20",
                discount="20% off",
                valid_days=60,
                description="VIP discount for Gold members",
                minimum_tier="Gold",
            ),
            self._build_coupon(
                name="Platinum Elite",
                code="PLATINUM25",
                discount="25% off",
                valid_days=60,
                description="Elite discount for Platinum members",
                minimum_tier="Platinum",
            ),
        ]

    def _build_coupon(
        self,
        *,
        name: str,
        code: str,
        discount: str,
        valid_days: int,
        description: Optional[str] = None,
        exclusions: Optional[str] = None,
        min_purchase: Optional[int] = None,
        minimum_tier: str = "Bronze",
        new_customer_only: bool = False,
    ) -> Dict[str, Any]:
        valid_until = (
            datetime.now(timezone.utc).date() + timedelta(days=valid_days)
        ).isoformat()
        return {
            "name": name,
            "code": code,
            "discount": discount,
            "valid_until": valid_until,
            "min_purchase": min_purchase,
            "description": description,
            "exclusions": exclusions,
            "minimum_tier": minimum_tier,
            "new_customer_only": new_customer_only,
        }

    def _extract_coupon_code(self, message: str) -> str:
        for word in message.upper().split():
            normalized = word.strip(".,!?;:()[]{}")
            if len(normalized) >= 6 and any(char.isalpha() for char in normalized) and any(
                char.isdigit() for char in normalized
            ):
                return normalized
        return ""

    def _extract_points_amount(self, message: str) -> int:
        for word in message.split():
            normalized = word.strip(".,!?;:")
            if normalized.isdigit():
                return int(normalized)
        return 0

    def _validate_coupon(self, code: str, user_id: str) -> Optional[Dict[str, Any]]:
        user = db.get_user_flexible(user_id)
        if not user:
            return None

        tier = self._get_loyalty_tier(user.get("loyalty_score", 0))
        order_count = len(db.get_user_orders(user_id))
        coupon = next((item for item in self._coupon_catalog() if item["code"] == code), None)
        if not coupon:
            return None
        if not self._coupon_is_active(coupon):
            return None
        if not self._coupon_is_eligible(coupon, tier, order_count):
            return None
        return coupon

    def _coupon_is_active(self, coupon: Dict[str, Any]) -> bool:
        valid_until = datetime.fromisoformat(coupon["valid_until"]).date()
        return valid_until >= datetime.now(timezone.utc).date()

    def _coupon_is_eligible(self, coupon: Dict[str, Any], tier: str, order_count: int) -> bool:
        if not self._coupon_is_active(coupon):
            return False
        if TIER_RANKS.get(tier, 0) < TIER_RANKS.get(coupon.get("minimum_tier", "Bronze"), 0):
            return False
        if coupon.get("new_customer_only") and order_count > 0:
            return False
        return True

    def _is_coupon_application_request(self, message_lower: str) -> bool:
        return (
            ("apply" in message_lower and any(word in message_lower for word in ["coupon", "promo", "discount", "code"]))
            or ("use" in message_lower and any(word in message_lower for word in ["coupon", "promo", "code"]))
        )

    def _is_points_redemption_request(self, message_lower: str) -> bool:
        return "redeem" in message_lower and "point" in message_lower
