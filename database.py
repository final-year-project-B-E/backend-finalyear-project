import os
import uuid
import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional

from pymongo import MongoClient, ASCENDING
from pymongo.collection import Collection


class Database:
    def __init__(self):
        username = os.getenv("MONGODB_USERNAME", "<db_username>")
        password = os.getenv("MONGODB_PASSWORD", "<db_password>")
        uri_template = os.getenv(
            "MONGODB_URI",
            "mongodb+srv://<db_username>:<db_password>@cluster0.xlq8iwb.mongodb.net/abfrl?appName=Cluster0",
        )
        uri = uri_template.replace("<db_username>", username).replace("<db_password>", password)
        self.client = MongoClient(uri)
        self.db = self.client[os.getenv("MONGODB_DB", "abfrl")]

        self.users: Collection = self.db["users"]
        self.products: Collection = self.db["products"]
        self.carts: Collection = self.db["carts"]
        self.orders: Collection = self.db["orders"]
        self.order_items: Collection = self.db["order_items"]
        self.chat_sessions: Collection = self.db["chat_sessions"]
        self.chat_messages: Collection = self.db["chat_messages"]
        self.auth_tokens: Collection = self.db["auth_tokens"]

        self._ensure_indexes()
        self._seed_products_if_empty()

    def _ensure_indexes(self):
        self.users.create_index([("id", ASCENDING)], unique=True)
        self.users.create_index([("email", ASCENDING)], unique=True)
        self.products.create_index([("id", ASCENDING)], unique=True)
        self.carts.create_index([("id", ASCENDING)], unique=True)
        self.orders.create_index([("id", ASCENDING)], unique=True)
        self.order_items.create_index([("id", ASCENDING)], unique=True)
        self.chat_sessions.create_index([("session_id", ASCENDING)], unique=True)
        self.auth_tokens.create_index([("token", ASCENDING)], unique=True)

    def _seed_products_if_empty(self):
        if self.products.count_documents({}) > 0:
            return
        try:
            import json
            from pathlib import Path

            data_file = Path(__file__).resolve().parent / "data" / "products.json"
            if data_file.exists():
                with open(data_file, "r", encoding="utf-8") as f:
                    products = json.load(f)
                if products:
                    self.products.insert_many(products)
        except Exception:
            pass

    def _next_id(self, collection: Collection) -> int:
        doc = collection.find_one(sort=[("id", -1)])
        return (doc.get("id", 0) if doc else 0) + 1

    def _clean(self, doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not doc:
            return doc
        doc.pop("_id", None)
        return doc

    def _hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    # Auth & users
    def create_user(self, email: str, password: str, first_name: str, last_name: str) -> Dict[str, Any]:
        now = datetime.utcnow().isoformat()
        user = {
            "id": self._next_id(self.users),
            "email": email.lower(),
            "password_hash": self._hash_password(password),
            "first_name": first_name,
            "last_name": last_name,
            "phone": None,
            "address": None,
            "city": None,
            "state": None,
            "country": None,
            "postal_code": None,
            "loyalty_score": 0,
            "is_active": True,
            "is_admin": False,
            "created_at": now,
            "updated_at": now,
        }
        self.users.insert_one(user)
        return self._sanitize_user(user)

    def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        user = self.users.find_one({"email": email.lower()})
        if not user:
            return None
        if user.get("password_hash") != self._hash_password(password):
            return None
        return self._clean(user)

    def create_auth_token(self, user_id: int) -> str:
        token = f"tok_{uuid.uuid4().hex}"
        self.auth_tokens.insert_one({
            "token": token,
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat(),
        })
        return token

    def get_user_by_token(self, token: str) -> Optional[Dict[str, Any]]:
        mapping = self.auth_tokens.find_one({"token": token})
        if not mapping:
            return None
        return self.get_user(mapping["user_id"])

    def delete_token(self, token: str):
        self.auth_tokens.delete_one({"token": token})

    def _sanitize_user(self, user: Dict[str, Any]) -> Dict[str, Any]:
        clean = self._clean(dict(user))
        clean.pop("password_hash", None)
        return clean

    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        user = self.users.find_one({"id": user_id})
        if not user:
            return None
        return self._sanitize_user(user)

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        user = self.users.find_one({"email": email.lower()})
        if not user:
            return None
        return self._sanitize_user(user)

    def update_user_loyalty(self, user_id: int, points: int):
        self.users.update_one(
            {"id": user_id},
            {"$inc": {"loyalty_score": points}, "$set": {"updated_at": datetime.utcnow().isoformat()}},
        )

    # Products
    def get_product(self, product_id: int) -> Optional[Dict[str, Any]]:
        return self._clean(self.products.find_one({"id": product_id}))

    def search_products(
        self,
        category: Optional[str] = None,
        occasion: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        query: Dict[str, Any] = {}
        if category:
            query["dress_category"] = category
        if occasion:
            query["occasion"] = occasion
        if min_price is not None or max_price is not None:
            query["price"] = {}
            if min_price is not None:
                query["price"]["$gte"] = min_price
            if max_price is not None:
                query["price"]["$lte"] = max_price
        return [self._clean(d) for d in self.products.find(query)]

    def update_stock(self, product_id: int, quantity: int):
        product = self.get_product(product_id)
        if not product:
            return
        new_stock = max(0, int(product.get("stock", 0)) - quantity)
        self.products.update_one(
            {"id": product_id},
            {"$set": {"stock": new_stock, "updated_at": datetime.utcnow().isoformat()}},
        )

    # Cart
    def get_user_cart(self, user_id: int) -> List[Dict[str, Any]]:
        items = [self._clean(d) for d in self.carts.find({"user_id": user_id})]
        output = []
        for item in items:
            product = self.get_product(item["product_id"])
            if product:
                output.append({**item, "product": product})
        return output

    def add_to_cart(self, user_id: int, product_id: int, quantity: int = 1):
        item = self.carts.find_one({"user_id": user_id, "product_id": product_id})
        if item:
            self.carts.update_one(
                {"id": item["id"]},
                {"$inc": {"quantity": quantity}, "$set": {"added_at": datetime.utcnow().isoformat()}},
            )
            return
        self.carts.insert_one({
            "id": self._next_id(self.carts),
            "user_id": user_id,
            "product_id": product_id,
            "quantity": quantity,
            "added_at": datetime.utcnow().isoformat(),
        })

    def clear_user_cart(self, user_id: int):
        self.carts.delete_many({"user_id": user_id})

    # Orders
    def create_order(self, user_id: int, cart_items: List[Dict[str, Any]], shipping_address: str, billing_address: str, payment_method: str) -> Dict[str, Any]:
        subtotal = sum(item["product"]["price"] * item["quantity"] for item in cart_items)
        tax = subtotal * 0.08
        shipping = 9.99 if subtotal < 100 else 0
        final_amount = subtotal + tax + shipping
        order_id = self._next_id(self.orders)
        order = {
            "id": order_id,
            "order_number": f"ORD-{datetime.utcnow().strftime('%Y%m%d')}-{order_id:04d}",
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
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        self.orders.insert_one(order)

        for cart_item in cart_items:
            order_item = {
                "id": self._next_id(self.order_items),
                "order_id": order_id,
                "product_id": cart_item["product_id"],
                "product_name": cart_item["product"]["product_name"],
                "quantity": cart_item["quantity"],
                "unit_price": float(cart_item["product"]["price"]),
                "total_price": float(cart_item["product"]["price"] * cart_item["quantity"]),
                "created_at": datetime.utcnow().isoformat(),
            }
            self.order_items.insert_one(order_item)
            self.update_stock(cart_item["product_id"], cart_item["quantity"])

        return order

    def get_user_orders(self, user_id: int) -> List[Dict[str, Any]]:
        orders = [self._clean(o) for o in self.orders.find({"user_id": user_id})]
        output = []
        for order in orders:
            items = [self._clean(i) for i in self.order_items.find({"order_id": order["id"]})]
            output.append({**order, "items": items})
        return output

    # Chat
    def create_chat_session(self, user_id: int, channel: str = "web") -> str:
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        self.chat_sessions.insert_one({
            "id": self._next_id(self.chat_sessions),
            "session_id": session_id,
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "status": "active",
            "current_agent": "sales_agent",
            "context": {"channel": channel, "conversation_history": [], "current_task": None},
            "metadata": {"channel": channel, "device": "unknown"},
        })
        return session_id

    def get_or_create_chat_session(self, user_id: int, session_id: Optional[str] = None, channel: str = "web") -> str:
        if session_id and self.chat_sessions.find_one({"session_id": session_id}):
            return session_id
        return self.create_chat_session(user_id, channel)

    def add_chat_message(self, session_id: str, role: str, content: str, agent_type: Optional[str] = None):
        self.chat_messages.insert_one({
            "id": self._next_id(self.chat_messages),
            "session_id": session_id,
            "message_type": role,
            "agent_type": agent_type,
            "content": content,
            "metadata": {},
            "created_at": datetime.utcnow().isoformat(),
        })

    def get_user_recent_messages(self, user_id: int, limit: int = 12, exclude_session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        sessions = [self._clean(s) for s in self.chat_sessions.find({"user_id": user_id})]
        ids = {s["session_id"] for s in sessions}
        if exclude_session_id:
            ids.discard(exclude_session_id)
        query = {"session_id": {"$in": list(ids)}} if ids else {"session_id": ""}
        msgs = [self._clean(m) for m in self.chat_messages.find(query).sort("id", -1).limit(limit)]
        return list(reversed(msgs))

    def get_chat_history(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        msgs = [self._clean(m) for m in self.chat_messages.find({"session_id": session_id}).sort("id", -1).limit(limit)]
        return list(reversed(msgs))


db = Database()
