import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
from threading import RLock

class Database:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self._lock = RLock()
        self._managed_files = {
            "users": "users.json",
            "products": "products.json",
            "carts": "carts.json",
            "orders": "orders.json",
            "order_items": "order_items.json",
            "chat_sessions": "chat_sessions.json",
            "chat_messages": "chat_messages.json",
            "agent_tasks": "agent_tasks.json"
        }
        self._ensure_data_files()
        self.load_all_data()

    def _ensure_data_files(self):
        """Ensure the data directory and managed JSON files exist."""
        os.makedirs(self.data_dir, exist_ok=True)
        for filename in self._managed_files.values():
            filepath = os.path.join(self.data_dir, filename)
            if not os.path.exists(filepath):
                with open(filepath, 'w') as f:
                    json.dump([], f)
    
    def load_all_data(self):
        """Load all JSON files into memory"""
        self.users = self._load_json("users.json")
        self.products = self._load_json("products.json")
        self.carts = self._load_json("carts.json")
        self.orders = self._load_json("orders.json")
        self.order_items = self._load_json("order_items.json")
        self.chat_sessions = self._load_json("chat_sessions.json")
        self.chat_messages = self._load_json("chat_messages.json")
        self.agent_tasks = self._load_json("agent_tasks.json")
    
    def _load_json(self, filename: str) -> List[Dict]:
        filepath = os.path.join(self.data_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                return json.load(f)
        return []
    
    def _save_json(self, filename: str, data: List[Dict]):
        filepath = os.path.join(self.data_dir, filename)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    def _persist(self, key: str):
        """Persist a managed in-memory collection to the backing JSON file."""
        filename = self._managed_files[key]
        self._save_json(filename, getattr(self, key))

    def _next_id(self, items: List[Dict]) -> int:
        return max([item.get("id", 0) for item in items], default=0) + 1
    
    # User operations
    def get_user(self, user_id: int) -> Optional[Dict]:
        for user in self.users:
            if user["id"] == user_id:
                return user
        return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        for user in self.users:
            if user["email"].lower() == email.lower():
                return user
        return None
    
    def update_user_loyalty(self, user_id: int, points: int):
        with self._lock:
            for user in self.users:
                if user["id"] == user_id:
                    user["loyalty_score"] = user.get("loyalty_score", 0) + points
                    user["updated_at"] = datetime.now().isoformat()
                    self._persist("users")
                    return
    
    # Product operations
    def get_product(self, product_id: int) -> Optional[Dict]:
        for product in self.products:
            if product["id"] == product_id:
                return product
        return None
    
    def search_products(self, category: Optional[str] = None, 
                       occasion: Optional[str] = None,
                       min_price: Optional[float] = None,
                       max_price: Optional[float] = None) -> List[Dict]:
        results = []
        for product in self.products:
            if category and product["dress_category"] != category:
                continue
            if occasion and product["occasion"] != occasion:
                continue
            if min_price and product["price"] < min_price:
                continue
            if max_price and product["price"] > max_price:
                continue
            results.append(product)
        return results
    
    def update_stock(self, product_id: int, quantity: int):
        with self._lock:
            for product in self.products:
                if product["id"] == product_id:
                    product["stock"] = max(0, product["stock"] - quantity)
                    product["updated_at"] = datetime.now().isoformat()
                    self._persist("products")
                    return
    
    # Cart operations
    def get_user_cart(self, user_id: int) -> List[Dict]:
        cart_items = []
        for item in self.carts:
            if item["user_id"] == user_id:
                product = self.get_product(item["product_id"])
                if product:
                    cart_items.append({
                        **item,
                        "product": product
                    })
        return cart_items
    
    def add_to_cart(self, user_id: int, product_id: int, quantity: int = 1):
        with self._lock:
        # Check if item already in cart
            for item in self.carts:
                if item["user_id"] == user_id and item["product_id"] == product_id:
                    item["quantity"] += quantity
                    item["added_at"] = datetime.now().isoformat()
                    self._persist("carts")
                    return
        
        # Add new item
            new_item = {
                "id": self._next_id(self.carts),
                "user_id": user_id,
                "product_id": product_id,
                "quantity": quantity,
                "added_at": datetime.now().isoformat()
            }
            self.carts.append(new_item)
            self._persist("carts")

    def clear_user_cart(self, user_id: int):
        with self._lock:
            self.carts = [item for item in self.carts if item["user_id"] != user_id]
            self._persist("carts")
    
    # Order operations
    def create_order(self, user_id: int, cart_items: List[Dict], 
                    shipping_address: str, billing_address: str,
                    payment_method: str) -> Dict:
        with self._lock:
            # Calculate totals
            subtotal = sum(item["product"]["price"] * item["quantity"] for item in cart_items)
            tax = subtotal * 0.08  # 8% tax
            shipping = 9.99 if subtotal < 100 else 0
            final_amount = subtotal + tax + shipping

            # Generate order number
            order_number = f"ORD-{datetime.now().strftime('%Y%m%d')}-{len(self.orders) + 1:04d}"

            # Create order
            new_order_id = self._next_id(self.orders)
            order = {
                "id": new_order_id,
                "order_number": order_number,
                "user_id": user_id,
                "total_amount": float(subtotal),
                "tax_amount": float(tax),
                "shipping_amount": float(shipping),
                "discount_amount": 0.0,
                "final_amount": float(final_amount),
                "payment_status": "pending",
                "payment_method": payment_method,
                "transaction_id": None,
                "shipping_address": shipping_address,
                "billing_address": billing_address,
                "order_status": "processing",
                "tracking_number": None,
                "notes": "",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            self.orders.append(order)

            # Create order items
            for cart_item in cart_items:
                order_item = {
                    "id": self._next_id(self.order_items),
                    "order_id": new_order_id,
                    "product_id": cart_item["product_id"],
                    "product_name": cart_item["product"]["product_name"],
                    "quantity": cart_item["quantity"],
                    "unit_price": float(cart_item["product"]["price"]),
                    "total_price": float(cart_item["product"]["price"] * cart_item["quantity"]),
                    "created_at": datetime.now().isoformat()
                }
                self.order_items.append(order_item)

                # Reduce stock for each ordered item
                self.update_stock(cart_item["product_id"], cart_item["quantity"])

            self._persist("orders")
            self._persist("order_items")

            return order

    def get_user_orders(self, user_id: int) -> List[Dict]:
        orders = []
        for order in self.orders:
            if order["user_id"] == user_id:
                items = [item for item in self.order_items if item["order_id"] == order["id"]]
                orders.append({**order, "items": items})
        return orders
    
    # Chat operations
    def create_chat_session(self, user_id: int, channel: str = "web") -> str:
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        new_session = {
            "id": self._next_id(self.chat_sessions),
            "session_id": session_id,
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "status": "active",
            "current_agent": "sales_agent",
            "context": {
                "channel": channel,
                "conversation_history": [],
                "current_task": None
            },
            "metadata": {
                "channel": channel,
                "device": "unknown"
            }
        }
        with self._lock:
            self.chat_sessions.append(new_session)
            self._persist("chat_sessions")
        return session_id

    def get_or_create_chat_session(self, user_id: int, session_id: Optional[str] = None,
                                   channel: str = "web") -> str:
        if session_id:
            for session in self.chat_sessions:
                if session["session_id"] == session_id:
                    return session_id
        return self.create_chat_session(user_id, channel)
    
    def add_chat_message(self, session_id: str, role: str, 
                        content: str, agent_type: Optional[str] = None):
        new_message = {
            "id": self._next_id(self.chat_messages),
            "session_id": session_id,
            "message_type": role,
            "agent_type": agent_type,
            "content": content,
            "metadata": {},
            "created_at": datetime.now().isoformat()
        }
        with self._lock:
            self.chat_messages.append(new_message)
            self._persist("chat_messages")
    
    def get_chat_history(self, session_id: str, limit: int = 10) -> List[Dict]:
        messages = []
        for msg in reversed(self.chat_messages):
            if msg["session_id"] == session_id:
                messages.append(msg)
                if len(messages) >= limit:
                    break
        return list(reversed(messages))

# Singleton instance
db = Database()
