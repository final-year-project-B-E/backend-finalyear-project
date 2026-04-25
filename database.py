import os
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
from datetime import datetime
from pymongo import MongoClient

# Load environment variables from .env file
load_dotenv()
from pymongo.errors import ConnectionFailure
from passlib.context import CryptContext
import logging
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class Database:
    def __init__(self):
        # Get MongoDB URI from environment variable
        self.mongodb_uri = os.getenv(
            "MONGODB_URI",
            "mongodb+srv://username:password@your-cluster.mongodb.net/?retryWrites=true&w=majority"
        )
        self.db_name = os.getenv("MONGODB_DB_NAME", "abfrl_fashion")
        
        try:
            self.client = MongoClient(self.mongodb_uri, serverSelectionTimeoutMS=5000)
            # Verify connection
            self.client.admin.command('ping')
            logger.info("✓ Connected to MongoDB")
        except ConnectionFailure as e:
            logger.error(f"✗ Failed to connect to MongoDB: {e}")
            raise
        
        self.db = self.client[self.db_name]
        self._create_collections()
    
    def _create_collections(self):
        """Create collections with proper indexing"""
        collections = {
            "users": [("email", 1), ("user_id", 1)],
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
            "agent_tasks": [("task_id", 1), ("status", 1)]
        }
        
        for collection_name, indexes in collections.items():
            if collection_name not in self.db.list_collection_names():
                self.db.create_collection(collection_name)
                logger.info(f"✓ Created collection: {collection_name}")
            
            # Create indexes
            collection = self.db[collection_name]
            for field, direction in indexes:
                collection.create_index([(field, direction)])
    
    def get_collection(self, collection_name: str):
        """Get a MongoDB collection"""
        return self.db[collection_name]
    
    # User methods
    def create_user(self, user_data: Dict[str, Any]) -> str:
        result = self.db.users.insert_one(user_data)
        return str(result.inserted_id)
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        return self.db.users.find_one({"user_id": user_id})
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        return self.db.users.find_one({"email": email})
    
    def update_user(self, user_id: int, update_data: Dict) -> bool:
        result = self.db.users.update_one({"user_id": user_id}, {"$set": update_data})
        return result.modified_count > 0
    
    # Product methods
    def get_all_products(self) -> List[Dict]:
        return list(self.db.products.find())
    
    def get_product(self, product_id: int) -> Optional[Dict]:
        return self.db.products.find_one({"id": product_id})
    
    def get_products_by_category(self, category: str) -> List[Dict]:
        return list(self.db.products.find({"dress_category": category}))
    
    def insert_products(self, products: List[Dict]) -> List[str]:
        result = self.db.products.insert_many(products)
        return [str(id) for id in result.inserted_ids]
    
    # Cart methods
    def get_cart(self, user_id: int) -> Optional[Dict]:
        return self.db.carts.find_one({"user_id": user_id})
    
    def update_cart(self, user_id: int, items: List[Dict]) -> bool:
        result = self.db.carts.update_one(
            {"user_id": user_id},
            {"$set": {"items": items, "updated_at": datetime.utcnow()}},
            upsert=True
        )
        return result.modified_count > 0 or result.upserted_id is not None
    
    # Order methods
    def create_order(self, order_data: Dict[str, Any]) -> str:
        result = self.db.orders.insert_one(order_data)
        return str(result.inserted_id)
    
    def get_order(self, order_number: str) -> Optional[Dict]:
        return self.db.orders.find_one({"order_number": order_number})
    
    def get_user_orders(self, user_id: int) -> List[Dict]:
        return list(self.db.orders.find({"user_id": user_id}).sort("created_at", -1))
    
    def update_order_status(self, order_number: str, status: str) -> bool:
        result = self.db.orders.update_one(
            {"order_number": order_number},
            {"$set": {"status": status, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0
    
    # Chat methods
    def create_chat_session(self, session_data: Dict[str, Any]) -> str:
        result = self.db.chat_sessions.insert_one(session_data)
        return str(result.inserted_id)
    
    def add_chat_message(self, session_id: str, message: Dict[str, Any]) -> str:
        message["session_id"] = session_id
        message["created_at"] = datetime.utcnow()
        result = self.db.chat_messages.insert_one(message)
        return str(result.inserted_id)
    
    def get_chat_history(self, session_id: str) -> List[Dict]:
        return list(self.db.chat_messages.find({"session_id": session_id}).sort("created_at", 1))
    
    # Agent task methods
    def create_agent_task(self, task_data: Dict[str, Any]) -> str:
        result = self.db.agent_tasks.insert_one(task_data)
        return str(result.inserted_id)
    
    def get_agent_task(self, task_id: str) -> Optional[Dict]:
        return self.db.agent_tasks.find_one({"task_id": task_id})
    
    def update_agent_task(self, task_id: str, update_data: Dict) -> bool:
        result = self.db.agent_tasks.update_one(
            {"task_id": task_id},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    def close(self):
        """Close MongoDB connection"""
        self.client.close()
        logger.info("MongoDB connection closed")
    
    # ==================== Authentication Methods ====================
    
    def register_user(self, email: str, password: str, first_name: str, last_name: str) -> Optional[Dict]:
        """Register a new user"""
        # Check if user already exists
        if self.db.users.find_one({"email": email.lower()}):
            return None
        
        # Hash password
        hashed_password = pwd_context.hash(password)
        
        user_data = {
            "email": email.lower(),
            "password_hash": hashed_password,
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
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        result = self.db.users.insert_one(user_data)
        user_data["_id"] = str(result.inserted_id)
        return user_data
    
    def authenticate_user(self, email: str, password: str) -> Optional[Dict]:
        """Authenticate a user and return user data if valid"""
        user = self.db.users.find_one({"email": email.lower()})
        
        if not user:
            return None
        
        # Verify password
        if not pwd_context.verify(password, user.get("password_hash", "")):
            return None
        
        # Remove password hash from response
        user_data = dict(user)
        user_data.pop("password_hash", None)
        user_data["id"] = str(user_data.pop("_id"))
        
        return user_data
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Get user by MongoDB ID"""
        from bson import ObjectId
        try:
            user = self.db.users.find_one({"_id": ObjectId(user_id)})
            if user:
                user.pop("password_hash", None)
                user["id"] = str(user.pop("_id"))
                return user
        except:
            pass
        return None

    def get_user_flexible(self, user_id: Optional[str]) -> Optional[Dict]:
        """Get user using either MongoDB _id or legacy numeric user_id."""
        if not user_id:
            return None

        user = self.get_user_by_id(str(user_id))
        if user:
            return user

        try:
            legacy_id = int(user_id)
        except (TypeError, ValueError):
            return None

        legacy_user = self.get_user(legacy_id)
        if not legacy_user:
            return None

        user_data = dict(legacy_user)
        if "_id" in user_data:
            user_data["id"] = str(user_data.pop("_id"))
        return user_data
    
    def update_user_profile(self, user_id: str, **kwargs) -> bool:
        """Update user profile"""
        from bson import ObjectId
        try:
            kwargs["updated_at"] = datetime.utcnow().isoformat()
            result = self.db.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": kwargs}
            )
            return result.modified_count > 0
        except:
            return False

    def update_user_loyalty(self, user_id: str, points_delta: int) -> bool:
        """Increment a user's loyalty score."""
        from bson import ObjectId

        try:
            result = self.db.users.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$inc": {"loyalty_score": points_delta},
                    "$set": {"updated_at": datetime.utcnow().isoformat()},
                },
            )
            return result.modified_count > 0
        except Exception:
            try:
                legacy_id = int(user_id)
            except (TypeError, ValueError):
                return False

            result = self.db.users.update_one(
                {"user_id": legacy_id},
                {
                    "$inc": {"loyalty_score": points_delta},
                    "$set": {"updated_at": datetime.utcnow().isoformat()},
                },
            )
            return result.modified_count > 0
    
    # Product operations
    def get_all_products(self) -> List[Dict]:
        """Get all products from MongoDB."""
        products = list(self.db.products.find())
        return products
    
    def get_product(self, product_id: int) -> Optional[Dict]:
        """Get a single product by ID from MongoDB."""
        product = self.db.products.find_one({"id": product_id})
        return product
    
    def get_products_by_category(self, category: str) -> List[Dict]:
        """Get products by category from MongoDB."""
        products = list(self.db.products.find({"dress_category": category}))
        return products
    
    def insert_products(self, products: List[Dict]) -> List[str]:
        """Insert multiple products into MongoDB."""
        if not products:
            return []
        result = self.db.products.insert_many(products)
        return [str(id) for id in result.inserted_ids]
    
    def search_products(self, category: Optional[str] = None, 
                       occasion: Optional[str] = None,
                       min_price: Optional[float] = None,
                       max_price: Optional[float] = None,
                       query: Optional[str] = None) -> List[Dict]:
        """Search products with filters from MongoDB."""
        filters = {}
        if category:
            if category in {"women", "men", "kids"}:
                filters["dress_category"] = {"$regex": f"^{category}-", "$options": "i"}
            else:
                filters["dress_category"] = {"$regex": f"^{category}$", "$options": "i"}
        if occasion:
            filters["occasion"] = {"$regex": f"^{occasion}$", "$options": "i"}
        if min_price is not None:
            filters["price"] = {"$gte": min_price}
        if max_price is not None:
            if "price" in filters:
                filters["price"]["$lte"] = max_price
            else:
                filters["price"] = {"$lte": max_price}
        if filters:
            mongo_query = filters
        else:
            mongo_query = {}

        if query:
            text_match = {
                "$or": [
                    {"product_name": {"$regex": query, "$options": "i"}},
                    {"description": {"$regex": query, "$options": "i"}},
                    {"dress_category": {"$regex": query, "$options": "i"}},
                    {"occasion": {"$regex": query, "$options": "i"}},
                ]
            }
            if mongo_query:
                mongo_query = {"$and": [mongo_query, text_match]}
            else:
                mongo_query = text_match

        results = list(self.db.products.find(mongo_query))
        return results

    def get_catalog_metadata(self) -> Dict[str, Any]:
        """Build catalog categories and occasion metadata from products."""
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
        """Update product stock in MongoDB."""
        result = self.db.products.update_one(
            {"id": product_id},
            {"$inc": {"stock": -quantity}, "$set": {"updated_at": datetime.utcnow().isoformat()}}
        )
        return result.modified_count > 0
    
    # Cart operations
    def get_cart(self, user_id: str) -> Optional[Dict]:
        """Get user's cart from MongoDB."""
        return self.db.carts.find_one({"user_id": user_id})
    
    def update_cart(self, user_id: str, items: List[Dict]) -> bool:
        """Update user's cart in MongoDB."""
        result = self.db.carts.update_one(
            {"user_id": user_id},
            {"$set": {"items": items, "updated_at": datetime.utcnow()}},
            upsert=True
        )
        return result.modified_count > 0 or result.upserted_id is not None
    
    def get_user_cart(self, user_id: str) -> List[Dict]:
        """Get cart items with product details."""
        cart = self.db.carts.find_one({"user_id": user_id})
        if not cart:
            return []
        
        cart_items = []
        for item in cart.get("items", []):
            product = self.get_product(item.get("product_id"))
            if product:
                cart_items.append({**item, "product": product})
        return cart_items
    
    def add_to_cart(self, user_id: str, product_id: int, quantity: int = 1) -> bool:
        """Add item to cart in MongoDB."""
        cart = self.db.carts.find_one({"user_id": user_id})
        
        if cart:
            # Check if product already in cart
            for item in cart.get("items", []):
                if item["product_id"] == product_id:
                    item["quantity"] += quantity
                    return self.update_cart(user_id, cart["items"])
            # Add new item
            cart["items"].append({"product_id": product_id, "quantity": quantity})
        else:
            # Create new cart
            cart = {"user_id": user_id, "items": [{"product_id": product_id, "quantity": quantity}]}
        
        return self.update_cart(user_id, cart.get("items", []))

    def clear_user_cart(self, user_id: str) -> bool:
        """Clear user's cart."""
        result = self.db.carts.delete_one({"user_id": user_id})
        return result.deleted_count > 0

    def get_wishlist(self, user_id: str) -> Optional[Dict]:
        """Get user's wishlist document."""
        return self.db.wishlists.find_one({"user_id": user_id})

    def get_user_wishlist(self, user_id: str) -> List[Dict]:
        """Get wishlist items with product details."""
        wishlist = self.get_wishlist(user_id)
        if not wishlist:
            return []

        products: List[Dict] = []
        for product_id in wishlist.get("product_ids", []):
            product = self.get_product(product_id)
            if product:
                products.append(product)
        return products

    def add_to_wishlist(self, user_id: str, product_id: int) -> bool:
        """Add a product to a user's wishlist."""
        result = self.db.wishlists.update_one(
            {"user_id": user_id},
            {
                "$addToSet": {"product_ids": product_id},
                "$set": {"updated_at": datetime.utcnow().isoformat()},
                "$setOnInsert": {"created_at": datetime.utcnow().isoformat()},
            },
            upsert=True,
        )
        return result.modified_count > 0 or result.upserted_id is not None

    def remove_from_wishlist(self, user_id: str, product_id: int) -> bool:
        """Remove a product from a user's wishlist."""
        result = self.db.wishlists.update_one(
            {"user_id": user_id},
            {
                "$pull": {"product_ids": product_id},
                "$set": {"updated_at": datetime.utcnow().isoformat()},
            },
        )
        return result.modified_count > 0
    
    # Order operations
    def create_order(self, order_data: Dict[str, Any]) -> str:
        """Create order in MongoDB."""
        result = self.db.orders.insert_one(order_data)
        return str(result.inserted_id)
    
    def get_order(self, order_number: str) -> Optional[Dict]:
        """Get order by order number."""
        return self.db.orders.find_one({"order_number": order_number})
    
    def get_user_orders(self, user_id: str) -> List[Dict]:
        """Get all orders for a user."""
        from bson import ObjectId
        try:
            user_id_obj = ObjectId(user_id)
            orders = list(self.db.orders.find({"user_id": user_id_obj}).sort("created_at", -1))
        except:
            orders = list(self.db.orders.find({"user_id": user_id}).sort("created_at", -1))
        return orders
    
    def update_order_status(self, order_number: str, status: str) -> bool:
        """Update order status."""
        result = self.db.orders.update_one(
            {"order_number": order_number},
            {"$set": {"order_status": status, "updated_at": datetime.utcnow().isoformat()}}
        )
        return result.modified_count > 0
    
    # Chat operations
    def create_chat_session(self, user_id: Optional[str] = None, channel: str = "web") -> str:
        """Create a new chat session."""
        import uuid
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        new_session = {
            "session_id": session_id,
            "user_id": user_id,
            "channel": channel,
            "status": "active",
            "current_agent": "sales_agent",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        result = self.db.chat_sessions.insert_one(new_session)
        return session_id

    def get_or_create_chat_session(self, user_id: Optional[str] = None, session_id: Optional[str] = None,
                                   channel: str = "web") -> str:
        """Get existing chat session or create new one."""
        if session_id:
            session = self.db.chat_sessions.find_one({"session_id": session_id})
            if session:
                return session_id
        return self.create_chat_session(user_id, channel)
    
    def add_chat_message(self, session_id: str, role: str, 
                        content: str, agent_type: Optional[str] = None) -> str:
        """Add a chat message to MongoDB."""
        new_message = {
            "session_id": session_id,
            "message_type": role,
            "agent_type": agent_type,
            "content": content,
            "metadata": {},
            "created_at": datetime.utcnow().isoformat()
        }
        result = self.db.chat_messages.insert_one(new_message)
        self.db.chat_sessions.update_one(
            {"session_id": session_id},
            {"$set": {"updated_at": datetime.utcnow().isoformat()}},
        )
        return str(result.inserted_id)

    def get_user_recent_messages(self, user_id: str, limit: int = 12, exclude_session_id: Optional[str] = None) -> List[Dict]:
        """Get recent messages for a user across sessions/channels."""
        # Get all session IDs for this user
        sessions = self.db.chat_sessions.find({"user_id": user_id})
        session_ids = [s["session_id"] for s in sessions]
        
        if exclude_session_id and exclude_session_id in session_ids:
            session_ids.remove(exclude_session_id)
        
        # Get recent messages from these sessions
        messages = list(
            self.db.chat_messages.find({"session_id": {"$in": session_ids}})
            .sort("created_at", -1)
            .limit(limit)
        )
        return list(reversed(messages))

    def get_user_chat_sessions(self, user_id: str, limit: int = 20) -> List[Dict]:
        """List chat sessions for a user with lightweight thread previews."""
        sessions = list(
            self.db.chat_sessions.find({"user_id": user_id})
            .sort("updated_at", -1)
            .limit(limit)
        )

        session_summaries: List[Dict[str, Any]] = []
        for session in sessions:
            session_id = session.get("session_id")
            if not session_id:
                continue

            messages = list(
                self.db.chat_messages.find({"session_id": session_id})
                .sort("created_at", 1)
            )
            if not messages:
                continue

            first_user_message = next(
                (message for message in messages if message.get("message_type") == "user" and message.get("content")),
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

    def get_chat_history(self, session_id: str, limit: int = 10) -> List[Dict]:
        """Get chat history for a session."""
        messages = list(
            self.db.chat_messages.find({"session_id": session_id})
            .sort("created_at", 1)
            .limit(limit)
        )
        return messages

# Singleton instance
db = Database()
