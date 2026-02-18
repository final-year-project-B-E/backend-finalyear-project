import json
import os
import uuid
from datetime import datetime, timezone
from threading import RLock
from typing import Any, Dict, List, Optional

from passlib.context import CryptContext
from pymongo import ASCENDING, MongoClient
from pymongo.collection import Collection


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
            "agent_tasks": "agent_tasks.json",
        }
        self._pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

        mongo_uri = os.getenv(
            "MONGODB_URI",
            "mongodb+srv://2022cs0365_db_user:n3ssaPo1oq0oMXad@final-year-project.zz3crai.mongodb.net/?appName=final-year-project",
        )
        db_name = os.getenv("MONGODB_DB", "finalyear_project")

        self.client = MongoClient(mongo_uri)
        self.mongo_db = self.client[db_name]

        self._collections: Dict[str, Collection] = {
            key: self.mongo_db[key] for key in self._managed_files
        }

        self._ensure_indexes()
        self._auto_seed_from_json()
        self.load_all_data()

    def _ensure_indexes(self):
        self._collections["users"].create_index([("id", ASCENDING)], unique=True)
        self._collections["users"].create_index([("email", ASCENDING)], unique=True)
        self._collections["products"].create_index([("id", ASCENDING)], unique=True)
        self._collections["carts"].create_index([("id", ASCENDING)], unique=True)
        self._collections["orders"].create_index([("id", ASCENDING)], unique=True)
        self._collections["order_items"].create_index([("id", ASCENDING)], unique=True)
        self._collections["chat_sessions"].create_index([("id", ASCENDING)], unique=True)
        self._collections["chat_sessions"].create_index([("session_id", ASCENDING)], unique=True)
        self._collections["chat_messages"].create_index([("id", ASCENDING)], unique=True)
        self._collections["agent_tasks"].create_index([("id", ASCENDING)], unique=True)

    def _load_json_file(self, filename: str) -> List[Dict[str, Any]]:
        filepath = os.path.join(self.data_dir, filename)
        if not os.path.exists(filepath):
            return []
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def _auto_seed_from_json(self):
        for key, filename in self._managed_files.items():
            collection = self._collections[key]
            if collection.estimated_document_count() > 0:
                continue

            data = self._load_json_file(filename)
            if not data:
                continue

            sanitized = []
            for item in data:
                row = dict(item)
                row.pop("_id", None)
                sanitized.append(row)

            if sanitized:
                collection.insert_many(sanitized)

    def load_all_data(self):
        self.users = self._read_all("users")
        self.products = self._read_all("products")
        self.carts = self._read_all("carts")
        self.orders = self._read_all("orders")
        self.order_items = self._read_all("order_items")
        self.chat_sessions = self._read_all("chat_sessions")
        self.chat_messages = self._read_all("chat_messages")
        self.agent_tasks = self._read_all("agent_tasks")

    def _read_all(self, key: str) -> List[Dict[str, Any]]:
        docs = list(self._collections[key].find({}, {"_id": 0}))
        docs.sort(key=lambda item: item.get("id", 0))
        return docs

    def _next_id(self, key: str) -> int:
        last = self._collections[key].find_one(sort=[("id", -1)], projection={"id": 1, "_id": 0})
        return (last or {}).get("id", 0) + 1

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _refresh_cache(self, *keys: str):
        if not keys:
            self.load_all_data()
            return
        for key in keys:
            setattr(self, key, self._read_all(key))

    # Authentication helpers
    def hash_password(self, password: str) -> str:
        return self._pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        if not hashed_password:
            return False
        return self._pwd_context.verify(plain_password, hashed_password)

    def create_user(self, first_name: str, last_name: str, email: str, password: str) -> Dict[str, Any]:
        with self._lock:
            email_norm = email.strip().lower()
            if self.get_user_by_email(email_norm):
                raise ValueError("Email is already registered")

            user = {
                "id": self._next_id("users"),
                "first_name": first_name.strip(),
                "last_name": last_name.strip(),
                "email": email_norm,
                "password_hash": self.hash_password(password),
                "loyalty_score": 0,
                "created_at": self._now(),
                "updated_at": self._now(),
            }
            self._collections["users"].insert_one(user)
            self._refresh_cache("users")
            return {k: v for k, v in user.items() if k != "password_hash"}

    def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        user = self.get_user_by_email(email)
        if not user:
            return None
        if not self.verify_password(password, user.get("password_hash", "")):
            return None
        return {k: v for k, v in user.items() if k != "password_hash"}

    # User operations
    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        return self._collections["users"].find_one({"id": user_id}, {"_id": 0})

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        return self._collections["users"].find_one({"email": email.strip().lower()}, {"_id": 0})

    def update_user_loyalty(self, user_id: int, points: int):
        self._collections["users"].update_one(
            {"id": user_id},
            {"$inc": {"loyalty_score": points}, "$set": {"updated_at": self._now()}},
        )
        self._refresh_cache("users")

    # Product operations
    def get_product(self, product_id: int) -> Optional[Dict[str, Any]]:
        return self._collections["products"].find_one({"id": product_id}, {"_id": 0})

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

        return list(self._collections["products"].find(query, {"_id": 0}))

    def update_stock(self, product_id: int, quantity: int):
        self._collections["products"].update_one(
            {"id": product_id},
            {"$inc": {"stock": -abs(quantity)}, "$set": {"updated_at": self._now()}},
        )
        self._collections["products"].update_one({"id": product_id, "stock": {"$lt": 0}}, {"$set": {"stock": 0}})
        self._refresh_cache("products")

    # Cart operations
    def get_user_cart(self, user_id: int) -> List[Dict[str, Any]]:
        cart_items = list(self._collections["carts"].find({"user_id": user_id}, {"_id": 0}))
        results = []
        for item in cart_items:
            product = self.get_product(item["product_id"])
            if product:
                results.append({**item, "product": product})
        return results

    def add_to_cart(self, user_id: int, product_id: int, quantity: int = 1):
        with self._lock:
            existing = self._collections["carts"].find_one({"user_id": user_id, "product_id": product_id}, {"_id": 0})
            if existing:
                self._collections["carts"].update_one(
                    {"id": existing["id"]},
                    {"$inc": {"quantity": quantity}, "$set": {"added_at": self._now()}},
                )
            else:
                new_item = {
                    "id": self._next_id("carts"),
                    "user_id": user_id,
                    "product_id": product_id,
                    "quantity": quantity,
                    "added_at": self._now(),
                }
                self._collections["carts"].insert_one(new_item)

            self._refresh_cache("carts")

    def clear_user_cart(self, user_id: int):
        self._collections["carts"].delete_many({"user_id": user_id})
        self._refresh_cache("carts")

    # Order operations
    def create_order(
        self,
        user_id: int,
        cart_items: List[Dict[str, Any]],
        shipping_address: str,
        billing_address: str,
        payment_method: str,
    ) -> Dict[str, Any]:
        with self._lock:
            subtotal = sum(item["product"]["price"] * item["quantity"] for item in cart_items)
            tax = subtotal * 0.08
            shipping = 9.99 if subtotal < 100 else 0
            final_amount = subtotal + tax + shipping

            order_number = f"ORD-{datetime.now().strftime('%Y%m%d')}-{self._next_id('orders'):04d}"

            new_order_id = self._next_id("orders")
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
                "created_at": self._now(),
                "updated_at": self._now(),
            }
            self._collections["orders"].insert_one(order)

            for cart_item in cart_items:
                order_item = {
                    "id": self._next_id("order_items"),
                    "order_id": new_order_id,
                    "product_id": cart_item["product_id"],
                    "product_name": cart_item["product"]["product_name"],
                    "quantity": cart_item["quantity"],
                    "unit_price": float(cart_item["product"]["price"]),
                    "total_price": float(cart_item["product"]["price"] * cart_item["quantity"]),
                    "created_at": self._now(),
                }
                self._collections["order_items"].insert_one(order_item)
                self.update_stock(cart_item["product_id"], cart_item["quantity"])

            self._refresh_cache("orders", "order_items")
            return order

    def get_user_orders(self, user_id: int) -> List[Dict[str, Any]]:
        user_orders = list(self._collections["orders"].find({"user_id": user_id}, {"_id": 0}))
        for order in user_orders:
            items = list(self._collections["order_items"].find({"order_id": order["id"]}, {"_id": 0}))
            order["items"] = items
        return user_orders

    # Chat operations
    def create_chat_session(self, user_id: int, channel: str = "web") -> str:
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        new_session = {
            "id": self._next_id("chat_sessions"),
            "session_id": session_id,
            "user_id": user_id,
            "created_at": self._now(),
            "updated_at": self._now(),
            "status": "active",
            "current_agent": "sales_agent",
            "context": {
                "channel": channel,
                "conversation_history": [],
                "current_task": None,
            },
            "metadata": {
                "channel": channel,
                "device": "unknown",
            },
        }
        self._collections["chat_sessions"].insert_one(new_session)
        self._refresh_cache("chat_sessions")
        return session_id

    def get_or_create_chat_session(self, user_id: int, session_id: Optional[str] = None, channel: str = "web") -> str:
        if session_id:
            existing = self._collections["chat_sessions"].find_one({"session_id": session_id}, {"_id": 0})
            if existing:
                return session_id
        return self.create_chat_session(user_id, channel)

    def add_chat_message(self, session_id: str, role: str, content: str, agent_type: Optional[str] = None):
        new_message = {
            "id": self._next_id("chat_messages"),
            "session_id": session_id,
            "message_type": role,
            "agent_type": agent_type,
            "content": content,
            "metadata": {},
            "created_at": self._now(),
        }
        self._collections["chat_messages"].insert_one(new_message)
        self._refresh_cache("chat_messages")

    def get_user_recent_messages(
        self, user_id: int, limit: int = 12, exclude_session_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        sessions = list(self._collections["chat_sessions"].find({"user_id": user_id}, {"_id": 0, "session_id": 1}))
        session_ids = {s.get("session_id") for s in sessions if s.get("session_id")}

        if exclude_session_id:
            session_ids.discard(exclude_session_id)

        if not session_ids:
            return []

        recent = list(
            self._collections["chat_messages"].find(
                {"session_id": {"$in": list(session_ids)}}, {"_id": 0}
            ).sort("id", -1).limit(limit)
        )
        return list(reversed(recent))

    def get_chat_history(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        messages = list(
            self._collections["chat_messages"].find({"session_id": session_id}, {"_id": 0}).sort("id", -1).limit(limit)
        )
        return list(reversed(messages))


db = Database()
