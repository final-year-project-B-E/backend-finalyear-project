import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from dotenv import load_dotenv

load_dotenv()

class MongoDatabase:
    """MongoDB implementation of the database layer"""
    
    def __init__(self, mongo_uri: Optional[str] = None):
        """Initialize MongoDB connection
        
        Args:
            mongo_uri: MongoDB connection URI. If None, uses MONGODB_URI env var
                      Default format: mongodb+srv://username:password@cluster.mongodb.net/dbname
                      or for local: mongodb://localhost:27017/dbname
        """
        self.mongo_uri = mongo_uri or os.getenv(
            "MONGODB_URI", 
            "mongodb://localhost:27017/retail_agent"
        )
        
        try:
            self.client = MongoClient(self.mongo_uri, serverSelectionTimeoutMS=5000)
            # Test connection
            self.client.admin.command('ping')
            print("✓ Connected to MongoDB successfully")
        except ServerSelectionTimeoutError:
            raise ConnectionError(
                f"Could not connect to MongoDB at {self.mongo_uri}. "
                "Make sure MongoDB is running or MONGODB_URI is correct."
            )
        
        self.db = self.client.get_database()
        self._ensure_indexes()
    
    def _ensure_indexes(self):
        """Create necessary indexes for performance"""
        # User indexes
        self.db.users.create_index("id", unique=True)
        self.db.users.create_index("email", unique=True)
        
        # Product indexes
        self.db.products.create_index("id", unique=True)
        self.db.products.create_index("dress_category")
        self.db.products.create_index("occasion")
        self.db.products.create_index([("price", 1)])
        
        # Cart indexes
        self.db.carts.create_index([("user_id", 1), ("product_id", 1)], unique=True)
        
        # Order indexes
        self.db.orders.create_index("id", unique=True)
        self.db.orders.create_index("user_id")
        self.db.orders.create_index("created_at")
        
        # Order items indexes
        self.db.order_items.create_index("order_id")
        
        # Chat indexes
        self.db.chat_sessions.create_index("session_id", unique=True)
        self.db.chat_sessions.create_index("user_id")
        self.db.chat_messages.create_index("session_id")
        self.db.chat_messages.create_index("timestamp")
        
        # Agent tasks indexes
        self.db.agent_tasks.create_index("task_id", unique=True)
        self.db.agent_tasks.create_index("user_id")
    
    # ==================== User Operations ====================
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        return self.db.users.find_one({"id": user_id})
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        return self.db.users.find_one({"email": {"$regex": f"^{email}$", "$options": "i"}})
    
    def create_user(self, user_data: Dict) -> Dict:
        """Create a new user"""
        user_data["created_at"] = datetime.now().isoformat()
        user_data["updated_at"] = datetime.now().isoformat()
        result = self.db.users.insert_one(user_data)
        return {**user_data, "_id": str(result.inserted_id)}
    
    def update_user(self, user_id: int, update_data: Dict) -> bool:
        """Update user data"""
        update_data["updated_at"] = datetime.now().isoformat()
        result = self.db.users.update_one(
            {"id": user_id},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    def update_user_loyalty(self, user_id: int, points: int):
        """Update user's loyalty points"""
        self.db.users.update_one(
            {"id": user_id},
            {
                "$inc": {"loyalty_score": points},
                "$set": {"updated_at": datetime.now().isoformat()}
            }
        )
    
    # ==================== Product Operations ====================
    
    def get_product(self, product_id: int) -> Optional[Dict]:
        """Get product by ID"""
        return self.db.products.find_one({"id": product_id})
    
    def get_all_products(self) -> List[Dict]:
        """Get all products"""
        return list(self.db.products.find({}))
    
    def search_products(self, category: Optional[str] = None, 
                       occasion: Optional[str] = None,
                       min_price: Optional[float] = None,
                       max_price: Optional[float] = None) -> List[Dict]:
        """Search products with filters"""
        query = {}
        
        if category:
            query["dress_category"] = category
        if occasion:
            query["occasion"] = occasion
        if min_price is not None:
            query["price"] = {"$gte": min_price}
        if max_price is not None:
            if "price" in query:
                query["price"]["$lte"] = max_price
            else:
                query["price"] = {"$lte": max_price}
        
        return list(self.db.products.find(query))
    
    def update_stock(self, product_id: int, quantity: int):
        """Update product stock"""
        self.db.products.update_one(
            {"id": product_id},
            {
                "$inc": {"stock": -quantity},
                "$set": {"updated_at": datetime.now().isoformat()}
            }
        )
    
    def create_product(self, product_data: Dict) -> Dict:
        """Create a new product"""
        product_data["created_at"] = datetime.now().isoformat()
        product_data["updated_at"] = datetime.now().isoformat()
        result = self.db.products.insert_one(product_data)
        return {**product_data, "_id": str(result.inserted_id)}
    
    # ==================== Cart Operations ====================
    
    def get_user_cart(self, user_id: int) -> List[Dict]:
        """Get user's cart items with product details"""
        cart_items = list(self.db.carts.find({"user_id": user_id}))
        
        # Enrich with product details
        enriched_items = []
        for item in cart_items:
            product = self.get_product(item["product_id"])
            if product:
                enriched_items.append({
                    **item,
                    "product": product
                })
        
        return enriched_items
    
    def add_to_cart(self, user_id: int, product_id: int, quantity: int = 1):
        """Add item to cart or update quantity"""
        self.db.carts.update_one(
            {"user_id": user_id, "product_id": product_id},
            {
                "$inc": {"quantity": quantity},
                "$set": {"updated_at": datetime.now().isoformat()}
            },
            upsert=True
        )
    
    def remove_from_cart(self, user_id: int, product_id: int):
        """Remove item from cart"""
        self.db.carts.delete_one({"user_id": user_id, "product_id": product_id})
    
    def clear_cart(self, user_id: int):
        """Clear entire cart for user"""
        self.db.carts.delete_many({"user_id": user_id})
    
    # ==================== Order Operations ====================
    
    def create_order(self, user_id: int, cart_items: List[Dict], 
                    shipping_address: str, billing_address: str, 
                    payment_method: str) -> Dict:
        """Create a new order"""
        order_id = str(os.urandom(8).hex())  # Generate unique order ID
        
        total_price = sum(item.get("product", {}).get("price", 0) * item.get("quantity", 1) 
                         for item in cart_items)
        
        order = {
            "id": order_id,
            "user_id": user_id,
            "total_price": total_price,
            "shipping_address": shipping_address,
            "billing_address": billing_address,
            "payment_method": payment_method,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        self.db.orders.insert_one(order)
        
        # Create order items
        for item in cart_items:
            order_item = {
                "order_id": order_id,
                "product_id": item["product_id"],
                "quantity": item.get("quantity", 1),
                "price": item.get("product", {}).get("price", 0),
                "created_at": datetime.now().isoformat()
            }
            self.db.order_items.insert_one(order_item)
        
        return order
    
    def get_order(self, order_id: str) -> Optional[Dict]:
        """Get order by ID with items"""
        order = self.db.orders.find_one({"id": order_id})
        if order:
            items = list(self.db.order_items.find({"order_id": order_id}))
            return {**order, "items": items}
        return None
    
    def get_user_orders(self, user_id: int) -> List[Dict]:
        """Get all orders for a user"""
        orders = list(self.db.orders.find({"user_id": user_id}).sort("created_at", -1))
        
        enriched_orders = []
        for order in orders:
            items = list(self.db.order_items.find({"order_id": order["id"]}))
            enriched_orders.append({**order, "items": items})
        
        return enriched_orders
    
    def update_order_status(self, order_id: str, status: str):
        """Update order status"""
        self.db.orders.update_one(
            {"id": order_id},
            {
                "$set": {
                    "status": status,
                    "updated_at": datetime.now().isoformat()
                }
            }
        )
    
    # ==================== Chat Operations ====================
    
    def create_chat_session(self, user_id: int, channel: str) -> Dict:
        """Create a new chat session"""
        session_id = str(os.urandom(8).hex())
        session = {
            "session_id": session_id,
            "user_id": user_id,
            "channel": channel,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        self.db.chat_sessions.insert_one(session)
        return session
    
    def get_chat_session(self, session_id: str) -> Optional[Dict]:
        """Get chat session"""
        return self.db.chat_sessions.find_one({"session_id": session_id})
    
    def add_chat_message(self, session_id: str, role: str, content: str, 
                        channel: Optional[str] = None) -> Dict:
        """Add message to chat session"""
        message = {
            "session_id": session_id,
            "role": role,
            "content": content,
            "channel": channel,
            "timestamp": datetime.now().isoformat()
        }
        result = self.db.chat_messages.insert_one(message)
        return {**message, "_id": str(result.inserted_id)}
    
    def get_chat_history(self, session_id: str) -> List[Dict]:
        """Get chat history for a session"""
        return list(
            self.db.chat_messages.find({"session_id": session_id}).sort("timestamp", 1)
        )
    
    # ==================== Agent Tasks Operations ====================
    
    def create_agent_task(self, user_id: int, agent_name: str, 
                         task_data: Dict) -> Dict:
        """Create a new agent task"""
        task_id = str(os.urandom(8).hex())
        task = {
            "task_id": task_id,
            "user_id": user_id,
            "agent_name": agent_name,
            "status": "pending",
            "data": task_data,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        self.db.agent_tasks.insert_one(task)
        return task
    
    def get_agent_task(self, task_id: str) -> Optional[Dict]:
        """Get agent task by ID"""
        return self.db.agent_tasks.find_one({"task_id": task_id})
    
    def update_agent_task(self, task_id: str, update_data: Dict):
        """Update agent task"""
        update_data["updated_at"] = datetime.now().isoformat()
        self.db.agent_tasks.update_one(
            {"task_id": task_id},
            {"$set": update_data}
        )
    
    def get_user_agent_tasks(self, user_id: int) -> List[Dict]:
        """Get all agent tasks for a user"""
        return list(self.db.agent_tasks.find({"user_id": user_id}).sort("created_at", -1))
    
    # ==================== Database Management ====================
    
    def health_check(self) -> bool:
        """Check database connection health"""
        try:
            self.client.admin.command('ping')
            return True
        except Exception:
            return False
    
    def clear_all_data(self):
        """Clear all collections (use with caution!)"""
        collections = [
            "users", "products", "carts", "orders", "order_items",
            "chat_sessions", "chat_messages", "agent_tasks"
        ]
        for collection in collections:
            self.db[collection].delete_many({})
    
    def close(self):
        """Close database connection"""
        self.client.close()


# Global database instance
_db_instance = None

def get_db() -> MongoDatabase:
    """Get or create the global database instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = MongoDatabase()
    return _db_instance

# For backward compatibility with imports like "from mongo_database import db"
db = get_db()
