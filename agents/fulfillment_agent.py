from datetime import timedelta
from typing import Any, Dict, List, Optional, Set

from commerce_service import ORDER_STATUS_LABELS, parse_dt, utc_now
from database import db

ACTIVE_FULFILLMENT_STATUSES: Set[str] = {
    "order_placed",
    "payment_confirmed",
    "processing",
    "shipped",
    "out_for_delivery",
}


class FulfillmentAgent:
    async def arrange_fulfillment(self, user_message: str, user_context: Dict[str, Any]) -> str:
        """Arrange delivery or in-store pickup."""

        user_id = user_context.get("user_id")
        if not user_id:
            return "I need to know who you are to arrange fulfillment. Please provide your account details."

        pending_orders = self._get_pending_orders(user_id)
        message_lower = user_message.lower()

        if "delivery" in message_lower or "ship" in message_lower:
            return self._handle_delivery(user_id, user_message)
        if "pickup" in message_lower or "store" in message_lower:
            return self._handle_store_pickup(user_id, user_message)
        if "when" in message_lower and "arrive" in message_lower:
            return self._check_delivery_status(user_id)
        return self._show_fulfillment_options(pending_orders)

    def _handle_delivery(self, user_id: str, message: str) -> str:
        """Handle home delivery arrangement."""

        address = self._extract_address(message) or "Your default shipping address"
        today = utc_now()
        standard_date = today + timedelta(days=3)
        express_date = today + timedelta(days=1)

        response = f"**Delivery Options to {address}:**\n\n"
        response += "**1. Standard Delivery (FREE)**\n"
        response += f"   - Estimated delivery: {standard_date.strftime('%A, %B %d')}\n"
        response += "   - 3-5 business days\n\n"

        response += "**2. Express Delivery ($12.99)**\n"
        response += f"   - Estimated delivery: {express_date.strftime('%A, %B %d')}\n"
        response += "   - 1-2 business days\n\n"

        response += "**3. Premium Same-Day ($24.99)**\n"
        response += "   - Estimated delivery: Today by 9 PM\n"
        response += "   - Order before 2 PM for same-day delivery\n\n"
        response += "Please select an option or say 'schedule for specific date'."
        return response

    def _handle_store_pickup(self, user_id: str, message: str) -> str:
        """Handle in-store pickup arrangement."""

        user_city = self._get_user_city(user_id)
        stores = self._get_nearby_stores(user_city)

        response = f"**In-Store Pickup Options near {user_city}:**\n\n"
        for index, store in enumerate(stores, 1):
            response += f"{index}. **{store['name']}**\n"
            response += f"   Address: {store['address']}\n"
            response += f"   Hours: {store['hours']}\n"
            response += f"   Ready in: {store['ready_time']}\n"
            response += f"   Parking: {store['parking']}\n"
            if store["has_fitting_rooms"]:
                response += "   ✅ Fitting rooms available\n"
            response += "\n"

        response += "**How it works:**\n"
        response += "1. Select a store and pickup time\n"
        response += "2. We'll prepare your order\n"
        response += "3. You'll receive a pickup QR code\n"
        response += "4. Show QR code at store for quick pickup\n\n"
        response += "Would you like to reserve a specific time slot?"
        return response

    def _check_delivery_status(self, user_id: str) -> str:
        """Check delivery status using the real order lifecycle."""

        active_orders = self._get_pending_orders(user_id)
        if not active_orders:
            return "You don't have any pending deliveries."

        response = "**Your Delivery Status:**\n\n"
        for order in active_orders[:3]:
            status = self._get_order_status(order)
            tracking_number = self._get_tracking_number(order)
            payment_status = str(order.get("payment_status") or "initiated").replace("_", " ").title()

            response += f"**Order {order['order_number']}**\n"
            response += f"- Status: {ORDER_STATUS_LABELS.get(status, status.replace('_', ' ').title())}\n"
            response += f"- Payment: {payment_status}\n"
            if tracking_number:
                response += f"- Tracking: {tracking_number}\n"

            eta = self._resolve_delivery_eta(order)
            if eta:
                response += f"- Estimated Delivery: {eta}\n"

            last_update = self._get_last_update(order)
            if last_update:
                response += f"- Last Update: {last_update}\n"

            next_step = self._get_next_step(status)
            if next_step:
                response += f"- Next Step: {next_step}\n"

            response += "\n"

        response += "Would you like to:\n"
        response += "1. Track a specific package\n"
        response += "2. Change delivery instructions\n"
        response += "3. Contact the carrier\n"
        return response

    def _show_fulfillment_options(self, pending_orders: List[Dict[str, Any]]) -> str:
        response = "**How would you like to receive your order?**\n\n"

        if pending_orders:
            response += "**Active Orders:**\n"
            for order in pending_orders[:3]:
                status = self._get_order_status(order)
                response += (
                    f"- {order['order_number']}: "
                    f"{ORDER_STATUS_LABELS.get(status, status.replace('_', ' ').title())}\n"
                )
            response += "\n"

        response += "**🏠 Home Delivery**\n"
        response += "- Free shipping on orders over $100\n"
        response += "- 2-3 business days\n"
        response += "- Package tracking included\n"
        response += "- Contactless delivery available\n\n"

        response += "**🏬 Store Pickup**\n"
        response += "- Ready in 2 hours\n"
        response += "- No shipping fees\n"
        response += "- Try before you buy\n"
        response += "- Easy returns\n\n"

        response += "**📦 Parcel Locker**\n"
        response += "- 24/7 access\n"
        response += "- Secure pickup\n"
        response += "- 3-day free storage\n"
        response += "- Locations near you\n\n"
        response += "Which option would you prefer?"
        return response

    def _extract_address(self, message: str) -> str:
        address_keywords = ["address", "street", "avenue", "road", "drive", "boulevard"]
        words = message.lower().split()

        for index, word in enumerate(words):
            if word in address_keywords and index < len(words) - 1:
                return " ".join(words[max(index - 1, 0):index + 3]).title()

        return ""

    def _get_user_city(self, user_id: str) -> str:
        user = db.get_user_flexible(user_id)
        return user.get("city", "New York") if user else "New York"

    def _get_nearby_stores(self, city: str) -> List[Dict[str, Any]]:
        stores_data = {
            "New York": [
                {
                    "name": "NYC Flagship Store",
                    "address": "123 Fifth Avenue, New York, NY 10001",
                    "hours": "10 AM - 9 PM Daily",
                    "ready_time": "2 hours",
                    "parking": "Valet available",
                    "has_fitting_rooms": True,
                },
                {
                    "name": "Soho Boutique",
                    "address": "456 Broadway, New York, NY 10013",
                    "hours": "11 AM - 8 PM Daily",
                    "ready_time": "1 hour",
                    "parking": "Street parking",
                    "has_fitting_rooms": True,
                },
            ],
            "Los Angeles": [
                {
                    "name": "Beverly Hills Boutique",
                    "address": "789 Rodeo Drive, Beverly Hills, CA 90210",
                    "hours": "10 AM - 8 PM Daily",
                    "ready_time": "3 hours",
                    "parking": "Valet parking",
                    "has_fitting_rooms": True,
                }
            ],
            "Chicago": [
                {
                    "name": "Magnificent Mile Store",
                    "address": "101 Michigan Avenue, Chicago, IL 60611",
                    "hours": "10 AM - 7 PM Daily",
                    "ready_time": "2.5 hours",
                    "parking": "Garage available",
                    "has_fitting_rooms": True,
                }
            ],
        }

        return stores_data.get(city, stores_data["New York"])

    def _get_pending_orders(self, user_id: str) -> List[Dict[str, Any]]:
        return [
            order
            for order in db.get_user_orders(user_id)
            if self._get_order_status(order) in ACTIVE_FULFILLMENT_STATUSES
        ]

    def _get_order_status(self, order: Dict[str, Any]) -> str:
        return str(order.get("order_status") or order.get("status") or "order_placed")

    def _get_tracking_number(self, order: Dict[str, Any]) -> Optional[str]:
        fulfillment = order.get("fulfillment") or {}
        return fulfillment.get("tracking_number") or order.get("tracking_number")

    def _resolve_delivery_eta(self, order: Dict[str, Any]) -> Optional[str]:
        fulfillment = order.get("fulfillment") or {}
        delivered_at = fulfillment.get("delivered_at")
        if delivered_at:
            return f"Delivered on {parse_dt(delivered_at).strftime('%A, %B %d')}"

        delivery_eta = fulfillment.get("delivery_eta")
        if delivery_eta:
            return parse_dt(delivery_eta).strftime("%A, %B %d")

        status = self._get_order_status(order)
        if status == "out_for_delivery":
            out_for_delivery_at = self._get_status_timestamp(order, {"out_for_delivery"})
            if out_for_delivery_at:
                return out_for_delivery_at.strftime("%A, %B %d")
        if status == "shipped":
            shipped_at = self._get_status_timestamp(order, {"shipped"})
            if shipped_at:
                return (shipped_at + timedelta(days=2)).strftime("%A, %B %d")
        return None

    def _get_status_timestamp(self, order: Dict[str, Any], statuses: Set[str]):
        timeline = order.get("timeline") or []
        for entry in reversed(timeline):
            if entry.get("status") in statuses and entry.get("created_at"):
                return parse_dt(entry["created_at"])

        fulfillment = order.get("fulfillment") or {}
        if "delivered" in statuses and fulfillment.get("delivered_at"):
            return parse_dt(fulfillment["delivered_at"])

        current_status = self._get_order_status(order)
        if current_status in statuses:
            if order.get("updated_at"):
                return parse_dt(order["updated_at"])
            if order.get("created_at"):
                return parse_dt(order["created_at"])
        return None

    def _get_last_update(self, order: Dict[str, Any]) -> Optional[str]:
        timeline = order.get("timeline") or []
        if timeline:
            latest_entry = timeline[-1]
            if latest_entry.get("created_at"):
                label = latest_entry.get("label") or latest_entry.get("status", "Update")
                return f"{label} on {parse_dt(latest_entry['created_at']).strftime('%A, %B %d')}"

        if order.get("updated_at"):
            return parse_dt(order["updated_at"]).strftime("%A, %B %d")
        return None

    def _get_next_step(self, status: str) -> Optional[str]:
        steps = {
            "order_placed": "Waiting for payment confirmation before fulfillment starts.",
            "payment_confirmed": "We're preparing the order for packing.",
            "processing": "The warehouse is packing and labeling your shipment.",
            "shipped": "The carrier has the parcel and the next scan should update the route.",
            "out_for_delivery": "The delivery driver is on the way today.",
        }
        return steps.get(status)
