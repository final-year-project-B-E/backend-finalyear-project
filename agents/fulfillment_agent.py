from typing import Dict, Any, List
import random
from datetime import datetime, timedelta
from mongo_database import db

class FulfillmentAgent:
    async def arrange_fulfillment(self, user_message: str, user_context: Dict[str, Any]) -> str:
        """Arrange delivery or in-store pickup"""
        
        user_id = user_context.get("user_id")
        if not user_id:
            return "I need to know who you are to arrange fulfillment. Please provide your account details."
        
        # Check if user has pending orders
        pending_orders = self._get_pending_orders(user_id)
        
        if "delivery" in user_message.lower() or "ship" in user_message.lower():
            return self._handle_delivery(user_id, user_message)
        elif "pickup" in user_message.lower() or "store" in user_message.lower():
            return self._handle_store_pickup(user_id, user_message)
        elif "when" in user_message.lower() and "arrive" in user_message.lower():
            return self._check_delivery_status(user_id)
        else:
            return self._show_fulfillment_options(pending_orders)
    
    def _handle_delivery(self, user_id: int, message: str) -> str:
        """Handle home delivery arrangement"""
        
        # Extract delivery address
        address = self._extract_address(message)
        if not address:
            address = "Your default shipping address"
        
        # Calculate delivery dates
        today = datetime.now()
        standard_date = today + timedelta(days=3)
        express_date = today + timedelta(days=1)
        premium_date = today + timedelta(days=0)  # Same day
        
        response = f"**Delivery Options to {address}:**\n\n"
        response += f"1. **Standard Delivery (FREE)**\n"
        response += f"   - Estimated delivery: {standard_date.strftime('%A, %B %d')}\n"
        response += f"   - 3-5 business days\n\n"
        
        response += f"2. **Express Delivery ($12.99)**\n"
        response += f"   - Estimated delivery: {express_date.strftime('%A, %B %d')}\n"
        response += f"   - 1-2 business days\n\n"
        
        response += f"3. **Premium Same-Day ($24.99)**\n"
        response += f"   - Estimated delivery: Today by 9 PM\n"
        response += f"   - Order before 2 PM for same-day delivery\n\n"
        
        response += "Please select an option or say 'schedule for specific date'."
        
        return response
    
    def _handle_store_pickup(self, user_id: int, message: str) -> str:
        """Handle in-store pickup arrangement"""
        
        # Get user's location (simulated)
        user_city = self._get_user_city(user_id)
        
        # Get nearby stores with availability
        stores = self._get_nearby_stores(user_city)
        
        response = f"**In-Store Pickup Options near {user_city}:**\n\n"
        
        for i, store in enumerate(stores, 1):
            response += f"{i}. **{store['name']}**\n"
            response += f"   Address: {store['address']}\n"
            response += f"   Hours: {store['hours']}\n"
            response += f"   Ready in: {store['ready_time']}\n"
            response += f"   Parking: {store['parking']}\n"
            if store['has_fitting_rooms']:
                response += f"   ✅ Fitting rooms available\n"
            response += "\n"
        
        response += "**How it works:**\n"
        response += "1. Select a store and pickup time\n"
        response += "2. We'll prepare your order\n"
        response += "3. You'll receive a pickup QR code\n"
        response += "4. Show QR code at store for quick pickup\n\n"
        
        response += "Would you like to reserve a specific time slot?"
        
        return response
    
    def _check_delivery_status(self, user_id: int) -> str:
        """Check delivery status of recent orders"""
        
        # Get recent orders
        recent_orders = []
        for order in db.orders:
            if order["user_id"] == user_id and order["order_status"] in ["processing", "shipped"]:
                recent_orders.append(order)
        
        if not recent_orders:
            return "You don't have any pending deliveries."
        
        response = "**Your Delivery Status:**\n\n"
        
        for order in recent_orders[:3]:  # Show only 3 most recent
            tracking_number = order.get("tracking_number", "Not assigned yet")
            status = order["order_status"]
            
            response += f"**Order {order['order_number']}**\n"
            response += f"- Status: {status.upper()}\n"
            response += f"- Tracking: {tracking_number}\n"
            
            if status == "shipped":
                estimated_delivery = self._calculate_delivery_estimate(order["created_at"])
                response += f"- Estimated Delivery: {estimated_delivery}\n"
            
            response += "\n"
        
        response += "Would you like to:\n"
        response += "1. Track a specific package\n"
        response += "2. Change delivery instructions\n"
        response += "3. Contact the carrier\n"
        
        return response
    
    def _show_fulfillment_options(self, pending_orders: List[Dict]) -> str:
        """Show all fulfillment options"""
        
        response = "**How would you like to receive your order?**\n\n"
        
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
        """Extract address from message (simplified)"""
        # In production, use proper NLP
        address_keywords = ["address", "street", "avenue", "road", "drive", "boulevard"]
        words = message.lower().split()
        
        for i, word in enumerate(words):
            if word in address_keywords and i < len(words) - 1:
                # Return next few words as potential address
                return " ".join(words[i-1:i+3]).title()
        
        return ""
    
    def _get_user_city(self, user_id: int) -> str:
        """Get user's city from profile"""
        user = db.get_user(user_id)
        return user.get("city", "New York") if user else "New York"
    
    def _get_nearby_stores(self, city: str) -> List[Dict]:
        """Get nearby stores (simulated)"""
        stores_data = {
            "New York": [
                {
                    "name": "NYC Flagship Store",
                    "address": "123 Fifth Avenue, New York, NY 10001",
                    "hours": "10 AM - 9 PM Daily",
                    "ready_time": "2 hours",
                    "parking": "Valet available",
                    "has_fitting_rooms": True
                },
                {
                    "name": "Soho Boutique",
                    "address": "456 Broadway, New York, NY 10013",
                    "hours": "11 AM - 8 PM Daily",
                    "ready_time": "1 hour",
                    "parking": "Street parking",
                    "has_fitting_rooms": True
                }
            ],
            "Los Angeles": [
                {
                    "name": "Beverly Hills Boutique",
                    "address": "789 Rodeo Drive, Beverly Hills, CA 90210",
                    "hours": "10 AM - 8 PM Daily",
                    "ready_time": "3 hours",
                    "parking": "Valet parking",
                    "has_fitting_rooms": True
                }
            ],
            "Chicago": [
                {
                    "name": "Magnificent Mile Store",
                    "address": "101 Michigan Avenue, Chicago, IL 60611",
                    "hours": "10 AM - 7 PM Daily",
                    "ready_time": "2.5 hours",
                    "parking": "Garage available",
                    "has_fitting_rooms": True
                }
            ]
        }
        
        return stores_data.get(city, stores_data["New York"])
    
    def _get_pending_orders(self, user_id: int) -> List[Dict]:
        """Get user's pending orders"""
        pending = []
        for order in db.orders:
            if order["user_id"] == user_id and order["order_status"] in ["processing", "confirmed"]:
                pending.append(order)
        return pending
    
    def _calculate_delivery_estimate(self, order_date: str) -> str:
        """Calculate delivery estimate"""
        order_dt = datetime.fromisoformat(order_date.replace('Z', '+00:00'))
        delivery_dt = order_dt + timedelta(days=random.randint(2, 5))
        return delivery_dt.strftime("%A, %B %d")