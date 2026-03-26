#!/usr/bin/env python3
"""
Script to add sample products directly to MongoDB
Run this after setting up MongoDB connection in .env
"""

import os
from dotenv import load_dotenv
from database import Database
from datetime import datetime

load_dotenv()

def add_sample_products():
    """Add sample products to MongoDB"""
    
    db = Database()
    
    print("🚀 Adding sample products to MongoDB...\n")
    
    sample_products = [
        {
            "id": 1,
            "product_name": "Ethereal Silk Evening Gown",
            "description": "Stunning floor-length silk gown with hand-sewn beading and dramatic low back",
            "dress_category": "women-dresses",
            "occasion": "formal",
            "price": 899.00,
            "stock": 15,
            "material": "100% Mulberry Silk",
            "available_sizes": "XS,S,M,L,XL",
            "colors": "Midnight Black,Champagne,Burgundy",
            "image_url": "https://images.unsplash.com/photo-1566174053879-31528523f8ae?w=800",
            "featured_dress": True,
            "created_at": datetime.utcnow()
        },
        {
            "id": 2,
            "product_name": "Luxe Velvet Cocktail Dress",
            "description": "Sophisticated knee-length velvet dress with A-line silhouette and hidden pockets",
            "dress_category": "women-dresses",
            "occasion": "cocktail",
            "price": 450.00,
            "stock": 25,
            "material": "80% Velvet, 20% Elastane",
            "available_sizes": "XS,S,M,L,XL",
            "colors": "Deep Emerald,Burgundy,Charcoal",
            "image_url": "https://images.unsplash.com/photo-1595859707806-fcf3ccb3c14f?w=800",
            "featured_dress": True,
            "created_at": datetime.utcnow()
        },
        {
            "id": 3,
            "product_name": "Boho Printed Midi Dress",
            "description": "Flowy midi dress with bohemian prints, perfect for summer occasions and casual outings",
            "dress_category": "women-dresses",
            "occasion": "casual",
            "price": 199.00,
            "stock": 40,
            "material": "100% Cotton",
            "available_sizes": "XS,S,M,L,XL,XXL",
            "colors": "Floral Blue,Terracotta,Ivory",
            "image_url": "https://images.unsplash.com/photo-1618886412700-ea82b72b0aec?w=800",
            "featured_dress": False,
            "created_at": datetime.utcnow()
        },
        {
            "id": 4,
            "product_name": "Classic White Dress Shirt",
            "description": "Timeless white dress shirt made from premium cotton, perfect for professional and formal wear",
            "dress_category": "women-shirts",
            "occasion": "formal",
            "price": 129.00,
            "stock": 60,
            "material": "100% Premium Cotton",
            "available_sizes": "S,M,L,XL,XXL",
            "colors": "White,Ivory,Light Blue",
            "image_url": "https://images.unsplash.com/photo-1595938277183-970f4cba8bda?w=800",
            "featured_dress": False,
            "created_at": datetime.utcnow()
        },
        {
            "id": 5,
            "product_name": "Leather Jacket & Jeans Set",
            "description": "Edgy motorcycle-style leather jacket paired with classic denim jeans",
            "dress_category": "women-jackets",
            "occasion": "casual",
            "price": 350.00,
            "stock": 20,
            "material": "Genuine Leather & Denim",
            "available_sizes": "XS,S,M,L,XL",
            "colors": "Black,Brown,Tan",
            "image_url": "https://images.unsplash.com/photo-1577005534666-7aff03c70b10?w=800",
            "featured_dress": False,
            "created_at": datetime.utcnow()
        },
        {
            "id": 6,
            "product_name": "Printed Summer Saree",
            "description": "Beautiful printed cotton saree with traditional border design, modern meets traditional",
            "dress_category": "women-traditional",
            "occasion": "casual",
            "price": 79.99,
            "stock": 35,
            "material": "50% Cotton, 50% Silk",
            "available_sizes": "One Size (6 yards)",
            "colors": "Navy Blue,Maroon,Green",
            "image_url": "https://images.unsplash.com/photo-1563552132-ec4ed465a45a?w=800",
            "featured_dress": True,
            "created_at": datetime.utcnow()
        }
    ]
    
    try:
        # Clear existing products for fresh start
        db.db.products.delete_many({})
        print("🗑️  Cleared existing products")
        
        # Insert new products
        result = db.insert_products(sample_products)
        print(f"✅ Successfully added {len(result)} products!\n")
        
        # Display added products
        all_products = db.get_all_products()
        print("📦 Products in database:")
        print("-" * 80)
        for product in all_products:
            print(f"  • {product['product_name']}")
            print(f"    Price: ${product['price']} | Stock: {product['stock']} units")
            print(f"    Category: {product['dress_category']} | Occasion: {product['occasion']}")
            print()
        
        print("🎉 Sample data loaded successfully!")
        
    except Exception as e:
        print(f"❌ Error loading products: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    add_sample_products()
