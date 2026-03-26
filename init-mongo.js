// This script runs automatically when MongoDB container starts
// It creates the database and collections with proper structure

db = db.getSiblingDB('abfrl_fashion');

// Create collections if they don't exist
db.createCollection('users');
db.createCollection('products');
db.createCollection('carts');
db.createCollection('orders');
db.createCollection('order_items');
db.createCollection('chat_sessions');
db.createCollection('chat_messages');
db.createCollection('agent_tasks');

// Create indexes for better query performance
db.users.createIndex({ email: 1 }, { unique: true });
db.users.createIndex({ user_id: 1 });

db.products.createIndex({ id: 1 });
db.products.createIndex({ product_name: 1 });
db.products.createIndex({ dress_category: 1 });

db.carts.createIndex({ user_id: 1 });

db.orders.createIndex({ order_number: 1 });
db.orders.createIndex({ user_id: 1 });
db.orders.createIndex({ created_at: -1 });

db.order_items.createIndex({ order_id: 1 });

db.chat_sessions.createIndex({ session_id: 1 });
db.chat_sessions.createIndex({ user_id: 1 });
db.chat_sessions.createIndex({ created_at: -1 });

db.chat_messages.createIndex({ session_id: 1 });
db.chat_messages.createIndex({ created_at: 1 });

db.agent_tasks.createIndex({ task_id: 1 });
db.agent_tasks.createIndex({ status: 1 });

print("✓ Database 'abfrl_fashion' initialized successfully!");
print("✓ All collections created");
print("✓ All indexes created");
