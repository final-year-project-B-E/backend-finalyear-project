#!/usr/bin/env python3
"""
Migration script to transfer data from JSON files to MongoDB
Run this script to migrate your existing data to MongoDB
"""

import json
import os
import sys
from pathlib import Path
from mongo_database import MongoDatabase

def migrate_json_to_mongodb(data_dir: str = "data", mongo_uri: str = None):
    """Migrate data from JSON files to MongoDB"""
    
    print("Starting migration from JSON to MongoDB...\n")
    
    try:
        # Initialize MongoDB connection
        db = MongoDatabase(mongo_uri)
        print("Connected to MongoDB\n")
    except ConnectionError as e:
        print(f"Error: {e}")
        print("\nTo set up MongoDB:")
        print("1. Local: brew install mongodb-community && brew services start mongodb-community")
        print("2. Cloud: Create a cluster at https://www.mongodb.com/cloud/atlas")
        print("3. Set MONGODB_URI in your .env file")
        sys.exit(1)
    
    # Define migration tasks
    migrations = [
        ("users.json", "users"),
        ("products.json", "products"),
        ("carts.json", "carts"),
        ("orders.json", "orders"),
        ("order_items.json", "order_items"),
        ("chat_sessions.json", "chat_sessions"),
        ("chat_messages.json", "chat_messages"),
        ("agent_tasks.json", "agent_tasks"),
    ]
    
    total_documents = 0
    
    for json_file, collection_name in migrations:
        file_path = os.path.join(data_dir, json_file)
        
        if not os.path.exists(file_path):
            print(f"Skipped {json_file} (not found)")
            continue
        
        try:
            # Read JSON file
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Ensure data is a list
            if isinstance(data, dict):
                data = [data]
            
            if not data:
                print(f"Skipped {json_file} (empty)")
                continue
            
            # Clear existing collection
            db.db[collection_name].delete_many({})
            
            # Insert documents
            if data:
                result = db.db[collection_name].insert_many(data)
                count = len(result.inserted_ids)
                total_documents += count
                print(f"{json_file}: {count} documents migrated to '{collection_name}'")
            
        except json.JSONDecodeError as e:
            print(f"Error reading {json_file}: {e}")
        except Exception as e:
            print(f"Error migrating {json_file}: {e}")

    print(f"\nMigration complete! Total documents: {total_documents}")
    print("\nNext steps:")
    print("1. Update your code to use mongo_database instead of database.py")
    print("2. Change imports from 'from database import db' to 'from mongo_database import db'")
    print("3. Keep JSON files as backup or remove them when comfortable")
    print("4. Update your agents to use the new database module")
    
    db.close()

def main():
    """Main entry point"""
    import argparse
    from dotenv import load_dotenv
    
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Migrate data from JSON to MongoDB")
    parser.add_argument(
        "--data-dir",
        default="data",
        help="Path to data directory (default: data)"
    )
    parser.add_argument(
        "--mongo-uri",
        default=None,
        help="MongoDB URI (default: MONGODB_URI env var or mongodb://localhost:27017/retail_agent)"
    )
    
    args = parser.parse_args()
    
    migrate_json_to_mongodb(args.data_dir, args.mongo_uri)

if __name__ == "__main__":
    main()
