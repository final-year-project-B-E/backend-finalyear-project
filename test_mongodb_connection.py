#!/usr/bin/env python3
"""
Quick MongoDB Connection Tester
Run this to verify your MongoDB credentials and connection
"""

import os
from dotenv import load_dotenv
from pymongo import MongoClient

def test_connection():
    """Test MongoDB connection with provided credentials"""
    
    print("=" * 60)
    print("🧪 MongoDB Connection Tester")
    print("=" * 60)
    
    load_dotenv()
    
    uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("MONGODB_DB_NAME", "abfrl_fashion")
    
    if not uri:
        print("\n❌ ERROR: MONGODB_URI not found in .env file")
        print("\nPlease create .env file with:")
        print("  MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority")
        print("  MONGODB_DB_NAME=abfrl_fashion")
        return False
    
    # Mask password for display
    display_uri = uri.replace(uri.split('@')[0], "mongodb+srv://***:***")
    print(f"\n📝 Connection Details:")
    print(f"  URI: {display_uri}")
    print(f"  Database: {db_name}")
    
    try:
        print("\n🔄 Attempting connection...")
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        
        # Test connection
        client.admin.command('ping')
        print("✅ Successfully connected to MongoDB!")
        
        # List collections
        db = client[db_name]
        collections = db.list_collection_names()
        print(f"\n📊 Collections in '{db_name}':")
        
        if collections:
            for collection in collections:
                count = db[collection].count_documents({})
                print(f"  ✓ {collection}: {count} documents")
        else:
            print("  (No collections yet - will be created on first use)")
        
        client.close()
        print("\n🎉 MongoDB is ready to use!")
        return True
        
    except Exception as e:
        print(f"\n❌ Connection failed: {type(e).__name__}")
        print(f"   Error: {str(e)}")
        
        # Provide troubleshooting hints
        print("\n🆘 Troubleshooting Tips:")
        if "dns" in str(e).lower():
            print("  • Check internet connection")
            print("  • Verify cluster name in URI is correct")
            print("  • Ensure MongoDB Atlas cluster is created")
        elif "auth" in str(e).lower() or "username" in str(e).lower():
            print("  • Double-check username and password")
            print("  • Ensure special characters are URL-encoded")
            print("  • Verify user exists in Database Access")
        elif "timeout" in str(e).lower():
            print("  • Your IP may be blocked - check Network Access settings")
            print("  • Try adding 0.0.0.0/0 to allowed IPs (development only)")
            print("  • Increase timeout or check MongoDB cluster is running")
        
        return False

if __name__ == "__main__":
    test_connection()
