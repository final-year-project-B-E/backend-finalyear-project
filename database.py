from __future__ import annotations

import logging
import os
import re
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from bson import ObjectId
from dotenv import load_dotenv
from passlib.context import CryptContext
from pymongo import MongoClient
from pymongo.errors import PyMongoError

load_dotenv()

logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def utc_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat()


class DatabaseUnavailableError(RuntimeError):
    """Raised when MongoDB cannot be reached for an operation."""


class Database:
    COLLECTION_INDEXES = {
        "users": [("email", 1), ("user_id", 1), ("id", 1)],
        "products": [("id", 1), ("product_name", 1), ("dress_category", 1)],
        "carts": [("user_id", 1)],
        "wishlists": [("user_id", 1)],
        "orders": [("order_number", 1), ("user_id", 1), ("created_at", -1)],
        "payments": [("payment_id", 1), ("order_number", 1), ("user_id", 1), ("created_at", -1)],
        "commerce_events": [("event_id", 1), ("event_type", 1), ("user_id", 1), ("order_number", 1), ("created_at", -1)],
        "notifications": [("notification_id", 1), ("user_id", 1), ("order_number", 1), ("created_at", -1)],
        "call_workflows": [("call_workflow_id", 1), ("user_id", 1), ("order_number", 1), ("scenario", 1), ("created_at", -1)],
        "user_activity": [("activity_id", 1), ("user_id", 1), ("activity_type", 1), ("product_id", 1), ("created_at", -1)],
        "order_items": [("order_id", 1)],
        "chat_sessions": [("session_id", 1), ("user_id", 1), ("created_at", -1)],
        "chat_messages": [("session_id", 1), ("created_at", 1)],
        "agent_tasks": [("task_id", 1), ("status", 1)],
    }

    def __init__(
        self,
        mongodb_uri: Optional[str] = None,
        db_name: Optional[str] = None,
        server_selection_timeout_ms: int = 5000,
    ) -> None:
        self.mongodb_uri = mongodb_uri or os.getenv(
            "MONGODB_URI",
            "mongodb+srv://username:password@your-cluster.mongodb.net/?retryWrites=true&w=majority",
        )
        self.db_name = db_name or os.getenv("MONGODB_DB_NAME", "abfrl_fashion")
        self.server_selection_timeout_ms = server_selection_timeout_ms
        self.client: Optional[MongoClient] = None
        self._db = None

    def connect(self):
        if self._db is not None:
            return self._db

        try:
            client = MongoClient(
                self.mongodb_uri,
                serverSelectionTimeoutMS=self.server_selection_timeout_ms,
            )
            client.admin.command("ping")
            database = client[self.db_name]
            self.client = client
            self._db = database
            self._ensure_collections()
            logger.info("Connected to MongoDB database '%s'", self.db_name)
            return self._db
        except PyMongoError as error:
            logger.error("MongoDB connection unavailable: %s", error)
            raise DatabaseUnavailableError("MongoDB is unavailable") from error

    @property
    def db(self):
        return self.connect()

    def _ensure_collections(self) -> None:
        database = self._db
        if database is None:
            return

        existing_collections = set(database.list_collection_names())
        for collection_name, indexes in self.COLLECTION_INDEXES.items():
            if collection_name not in existing_collections:
                database.create_collection(collection_name)
                logger.info("Created collection: %s", collection_name)

            collection = database[collection_name]
            for field, direction in indexes:
                collection.create_index([(field, direction)])

    def close(self) -> None:
        if self.client is not None:
            self.client.close()
        self.client = None
        self._db = None

    def get_collection(self, collection_name: str):
        return self.db[collection_name]

    def _user_document_filters(self, user_id: Optional[str]) -> List[Dict[str, Any]]:
        filters: List[Dict[str, Any]] = []
        if user_id is None:
            return filters

        filters.append({"user_id": user_id})
        filters.append({"id": user_id})

        try:
            filters.append({"_id": ObjectId(str(user_id))})
        except Exception:
            pass

        try:
            legacy_id = int(str(user_id))
            filters.append({"user_id": legacy_id})
            filters.append({"id": legacy_id})
        except (TypeError, ValueError):
            pass

        return filters

    def _user_reference_filters(self, user_id: Optional[str]) -> List[Dict[str, Any]]:
        filters: List[Dict[str, Any]] = []
        if user_id is None:
            return filters

        filters.append({"user_id": user_id})

        try:
            filters.append({"user_id": ObjectId(str(user_id))})
        except Exception:
            pass

        try:
            filters.append({"user_id": int(str(user_id))})
        except (TypeError, ValueError):
            pass

        return filters

    def _public_user(self, user: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not user:
            return None

        user_data = dict(user)
        user_data.pop("password_hash", None)
        if "_id" in user_data:
            user_data["id"] = str(user_data.pop("_id"))
        elif "id" in user_data:
            user_data["id"] = str(user_data["id"])
        elif "user_id" in user_data:
            user_data["id"] = str(user_data["user_id"])
        return user_data

    # User operations
    def create_user(self, user_data: Dict[str, Any]) -> str:
        result = self.db.users.insert_one(user_data)
        return str(result.inserted_id)

    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        return self.db.users.find_one({"$or": [{"user_id": user_id}, {"id": user_id}]})

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        return self.db.users.find_one({"email": email.lower()})

    def update_user(self, user_id: int, update_data: Dict[str, Any]) -> bool:
        result = self.db.users.update_one(
            {"$or": [{"user_id": user_id}, {"id": user_id}]},
            {"$set": update_data},
        )
        return result.modified_count > 0

    def register_user(self, email: str, password: str, first_name: str, last_name: str) -> Optional[Dict[str, Any]]:
        if self.db.users.find_one({"email": email.lower()}):
            return None

        user_data = {
            "email": email.lower(),
            "password_hash": pwd_context.hash(password),
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
            "created_at": utc_iso(),
            "updated_at": utc_iso(),
        }

        result = self.db.users.insert_one(user_data)
        user_data["id"] = str(result.inserted_id)
        user_data["_id"] = user_data["id"]
        return user_data

    def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        user = self.db.users.find_one({"email": email.lower()})
        if not user:
            return None

        if not pwd_context.verify(password, user.get("password_hash", "")):
            return None

        return self._public_user(user)

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        for lookup in self._user_document_filters(user_id):
            user = self.db.users.find_one(lookup)
            if user:
                return self._public_user(user)
        return None

    def get_user_flexible(self, user_id: Optional[str]) -> Optional[Dict[str, Any]]:
        if not user_id:
            return None
        return self.get_user_by_id(str(user_id))

    def update_user_profile(self, user_id: str, **kwargs: Any) -> bool:
        updates = {**kwargs, "updated_at": utc_iso()}
        for lookup in self._user_document_filters(user_id):
            result = self.db.users.update_one(lookup, {"$set": updates})
            if result.modified_count > 0:
                return True
        return False

    def update_user_loyalty(self, user_id: str, points_delta: int) -> bool:
        updates = {
            "$inc": {"loyalty_score": points_delta},
            "$set": {"updated_at": utc_iso()},
        }
        for lookup in self._user_document_filters(user_id):
            result = self.db.users.update_one(lookup, updates)
            if result.modified_count > 0:
                return True
        return False

    # Product operations
    def get_all_products(self) -> List[Dict[str, Any]]:
        return list(self.db.products.find())

    def get_product(self, product_id: int) -> Optional[Dict[str, Any]]:
        return self.db.products.find_one({"id": product_id})

    def get_products_by_category(self, category: str) -> List[Dict[str, Any]]:
        return list(self.db.products.find({"dress_category": category}))

    def insert_products(self, products: List[Dict[str, Any]]) -> List[str]:
        if not products:
            return []
        result = self.db.products.insert_many(products)
        return [str(inserted_id) for inserted_id in result.inserted_ids]

    def search_products(
        self,
        category: Optional[str] = None,
        occasion: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        query: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        filters: Dict[str, Any] = {}

        if category:
            escaped_category = re.escape(category)
            if category in {"women", "men", "kids"}:
                filters["dress_category"] = {"$regex": f"^{escaped_category}-", "$options": "i"}
            else:
                filters["dress_category"] = {"$regex": f"^{escaped_category}$", "$options": "i"}

        if occasion:
            filters["occasion"] = {"$regex": f"^{re.escape(occasion)}$", "$options": "i"}

        if min_price is not None:
            filters["price"] = {"$gte": min_price}
        if max_price is not None:
            filters.setdefault("price", {})
            filters["price"]["$lte"] = max_price

        mongo_query: Dict[str, Any] = filters if filters else {}
        if query:
            escaped_query = re.escape(query)
            text_match = {
                "$or": [
                    {"product_name": {"$regex": escaped_query, "$options": "i"}},
                    {"description": {"$regex": escaped_query, "$options": "i"}},
                    {"dress_category": {"$regex": escaped_query, "$options": "i"}},
                    {"occasion": {"$regex": escaped_query, "$options": "i"}},
                ]
            }
            mongo_query = {"$and": [mongo_query, text_match]} if mongo_query else text_match

        return list(self.db.products.find(mongo_query))

    def get_catalog_metadata(self) -> Dict[str, Any]:
        products = self.get_all_products()
        categories: Dict[str, Dict[str, Any]] = {}
        occasions: Dict[str, int] = {}

        for product in products:
            category_id = str(product.get("dress_category") or "uncategorized")
            category_entry = categories.setdefault(
                category_id,
                {
                    "id": category_id,
                    "name": category_id.replace("-", " ").title(),
                    "count": 0,
                    "image_url": product.get("image_url"),
                },
            )
            category_entry["count"] += 1
            if not category_entry.get("image_url") and product.get("image_url"):
                category_entry["image_url"] = product.get("image_url")

            occasion = str(product.get("occasion") or "").strip()
            if occasion:
                occasions[occasion] = occasions.get(occasion, 0) + 1

        return {
            "categories": sorted(categories.values(), key=lambda item: item["name"]),
            "occasions": [
                {"id": occasion.lower().replace(" ", "-"), "name": occasion, "count": count}
                for occasion, count in sorted(occasions.items(), key=lambda item: item[0].lower())
            ],
        }

    def update_stock(self, product_id: int, quantity: int) -> bool:
        result = self.db.products.update_one(
            {"id": product_id},
            {"$inc": {"stock": -quantity}, "$set": {"updated_at": utc_iso()}},
        )
        return result.modified_count > 0

    def increment_product_view_count(self, product_id: int) -> bool:
        """
        PHASE 1: Track product popularity by incrementing view count
        Used by RAG system to boost popular products in search results
        """
        result = self.db.products.update_one(
            {"id": product_id},
            {
                "$inc": {"view_count": 1},
                "$set": {"last_viewed_at": utc_iso()}
            },
            upsert=False  # Only update if product exists
        )
        return result.modified_count > 0

    # Cart operations
    def get_cart(self, user_id: str) -> Optional[Dict[str, Any]]:
        return self.db.carts.find_one({"user_id": user_id})

    def update_cart(self, user_id: str, items: List[Dict[str, Any]]) -> bool:
        result = self.db.carts.update_one(
            {"user_id": user_id},
            {
                "$set": {"items": items, "updated_at": utc_iso()},
                "$setOnInsert": {"created_at": utc_iso()},
            },
            upsert=True,
        )
        return result.modified_count > 0 or result.upserted_id is not None

    def get_user_cart(self, user_id: str) -> List[Dict[str, Any]]:
        cart = self.db.carts.find_one({"user_id": user_id})
        if not cart:
            return []

        cart_items: List[Dict[str, Any]] = []
        for item in cart.get("items", []):
            product = self.get_product(item.get("product_id"))
            if product:
                cart_items.append({**item, "product": product})
        return cart_items

    def add_to_cart(self, user_id: str, product_id: int, quantity: int = 1) -> bool:
        cart = self.get_cart(user_id)
        if cart:
            for item in cart.get("items", []):
                if item.get("product_id") == product_id:
                    item["quantity"] += quantity
                    return self.update_cart(user_id, cart["items"])
            cart["items"].append({"product_id": product_id, "quantity": quantity})
            return self.update_cart(user_id, cart["items"])

        return self.update_cart(user_id, [{"product_id": product_id, "quantity": quantity}])

    def clear_user_cart(self, user_id: str) -> bool:
        result = self.db.carts.delete_one({"user_id": user_id})
        return result.deleted_count > 0

    # Wishlist operations
    def get_wishlist(self, user_id: str) -> Optional[Dict[str, Any]]:
        return self.db.wishlists.find_one({"user_id": user_id})

    def get_user_wishlist(self, user_id: str) -> List[Dict[str, Any]]:
        wishlist = self.get_wishlist(user_id)
        if not wishlist:
            return []

        products: List[Dict[str, Any]] = []
        for product_id in wishlist.get("product_ids", []):
            product = self.get_product(product_id)
            if product:
                products.append(product)
        return products

    def add_to_wishlist(self, user_id: str, product_id: int) -> bool:
        result = self.db.wishlists.update_one(
            {"user_id": user_id},
            {
                "$addToSet": {"product_ids": product_id},
                "$set": {"updated_at": utc_iso()},
                "$setOnInsert": {"created_at": utc_iso()},
            },
            upsert=True,
        )
        return result.modified_count > 0 or result.upserted_id is not None

    def remove_from_wishlist(self, user_id: str, product_id: int) -> bool:
        result = self.db.wishlists.update_one(
            {"user_id": user_id},
            {
                "$pull": {"product_ids": product_id},
                "$set": {"updated_at": utc_iso()},
            },
        )
        return result.modified_count > 0

    # Order operations
    def create_order(self, order_data: Dict[str, Any]) -> str:
        result = self.db.orders.insert_one(order_data)
        return str(result.inserted_id)

    def get_order(self, order_number: str) -> Optional[Dict[str, Any]]:
        return self.db.orders.find_one({"order_number": order_number})

    def get_user_orders(self, user_id: str) -> List[Dict[str, Any]]:
        user_filters = self._user_reference_filters(user_id)
        if not user_filters:
            return []
        return list(self.db.orders.find({"$or": user_filters}).sort("created_at", -1))

    def update_order_status(self, order_number: str, status: str) -> bool:
        result = self.db.orders.update_one(
            {"order_number": order_number},
            {"$set": {"order_status": status, "status": status, "updated_at": utc_iso()}},
        )
        return result.modified_count > 0

    # Chat operations
    def create_chat_session(self, user_id: Optional[str] = None, channel: str = "web") -> str:
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        session = {
            "session_id": session_id,
            "user_id": user_id,
            "channel": channel,
            "status": "active",
            "current_agent": "sales_agent",
            "created_at": utc_iso(),
            "updated_at": utc_iso(),
        }
        self.db.chat_sessions.insert_one(session)
        return session_id

    def get_or_create_chat_session(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        channel: str = "web",
    ) -> str:
        if session_id and self.db.chat_sessions.find_one({"session_id": session_id}):
            return session_id
        return self.create_chat_session(user_id=user_id, channel=channel)

    def add_chat_message(
        self,
        session_id: str,
        role: str,
        content: str,
        agent_type: Optional[str] = None,
    ) -> str:
        message = {
            "session_id": session_id,
            "message_type": role,
            "agent_type": agent_type,
            "content": content,
            "metadata": {},
            "created_at": utc_iso(),
        }
        result = self.db.chat_messages.insert_one(message)
        self.db.chat_sessions.update_one(
            {"session_id": session_id},
            {"$set": {"updated_at": utc_iso()}},
        )
        return str(result.inserted_id)

    def get_chat_history(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        return list(
            self.db.chat_messages.find({"session_id": session_id}).sort("created_at", 1).limit(limit)
        )

    def get_user_recent_messages(
        self,
        user_id: str,
        limit: int = 12,
        exclude_session_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        sessions = list(self.db.chat_sessions.find({"user_id": user_id}, {"session_id": 1}))
        session_ids = [session["session_id"] for session in sessions if session.get("session_id")]
        if exclude_session_id in session_ids:
            session_ids.remove(exclude_session_id)
        if not session_ids:
            return []

        messages = list(
            self.db.chat_messages.find({"session_id": {"$in": session_ids}})
            .sort("created_at", -1)
            .limit(limit)
        )
        return list(reversed(messages))

    def get_user_chat_sessions(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        sessions = list(
            self.db.chat_sessions.find({"user_id": user_id}).sort("updated_at", -1).limit(limit)
        )

        session_summaries: List[Dict[str, Any]] = []
        for session in sessions:
            session_id = session.get("session_id")
            if not session_id:
                continue

            messages = list(
                self.db.chat_messages.find({"session_id": session_id}).sort("created_at", 1)
            )
            if not messages:
                continue

            first_user_message = next(
                (
                    message
                    for message in messages
                    if message.get("message_type") == "user" and message.get("content")
                ),
                messages[0],
            )
            last_message = messages[-1]

            session_summaries.append(
                {
                    "session_id": session_id,
                    "channel": session.get("channel", "web"),
                    "status": session.get("status", "active"),
                    "created_at": session.get("created_at"),
                    "updated_at": session.get("updated_at"),
                    "message_count": len(messages),
                    "title": str(first_user_message.get("content") or "New chat")[:80],
                    "last_message_preview": str(last_message.get("content") or "")[:120],
                }
            )

        return session_summaries

    # Agent task operations
    def create_agent_task(self, task_data: Dict[str, Any]) -> str:
        result = self.db.agent_tasks.insert_one(task_data)
        return str(result.inserted_id)

    def get_agent_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        return self.db.agent_tasks.find_one({"task_id": task_id})

    def update_agent_task(self, task_id: str, update_data: Dict[str, Any]) -> bool:
        result = self.db.agent_tasks.update_one(
            {"task_id": task_id},
            {"$set": update_data},
        )
        return result.modified_count > 0


db = Database()
