#!/usr/bin/env python3
"""
Script to add sample products to the retail backend database
Run this script to populate your database with test products
"""

import requests
import json
import time

# Backend API base URL
BASE_URL = "http://localhost:8000"

def add_product(product_data):
    """Add a single product to the database"""
    try:
        response = requests.post(f"{BASE_URL}/products", json=product_data)
        if response.status_code == 201:
            print(f"✅ Added: {product_data['product_name']}")
            return True
        else:
            print(f"❌ Failed to add {product_data['product_name']}: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error adding {product_data['product_name']}: {e}")
        return False

def main():
    print("🚀 Adding sample products to retail backend...")
    print(f"📡 Connecting to: {BASE_URL}")
    
    # Sample products data
    products = [
        {
            "product_name": "Ethereal Silk Evening Gown",
            "description": "A stunning floor-length silk gown featuring delicate hand-sewn beading and a dramatic low back. Perfect for black-tie events and galas.",
            "dress_category": "women-dresses",
            "occasion": "formal",
            "price": 899.00,
            "stock": 15,
            "material": "100% Mulberry Silk",
            "available_sizes": "XS,S,M,L,XL",
            "colors": "Midnight Black,Champagne,Burgundy",
            "image_url": "https://images.unsplash.com/photo-1566174053879-31528523f8ae?w=800",
            "featured_dress": True
        },
        {
            "product_name": "Luxe Velvet Cocktail Dress",
            "description": "Sophisticated knee-length velvet dress with subtle shoulder detailing. Features a flattering A-line silhouette and hidden pockets.",
            "dress_category": "women-dresses",
            "occasion": "party",
            "price": 425.00,
            "stock": 28,
            "material": "Italian Velvet, Silk Lining",
            "available_sizes": "XS,S,M,L",
            "colors": "Deep Emerald,Royal Blue,Wine",
            "image_url": "https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=800",
            "featured_dress": True
        },
        {
            "product_name": "Cashmere Blend Wrap Dress",
            "description": "Elegant wrap dress crafted from premium cashmere blend. Features a self-tie waist and flowing skirt. Perfect transition piece from office to evening.",
            "dress_category": "women-dresses",
            "occasion": "office",
            "price": 345.00,
            "stock": 42,
            "material": "70% Cashmere, 30% Wool",
            "available_sizes": "XS,S,M,L,XL",
            "colors": "Camel,Charcoal,Cream",
            "image_url": "https://images.unsplash.com/photo-1515372039744-b8f02a3ae446?w=800",
            "featured_dress": False
        },
        {
            "product_name": "Floral Printed Maxi Dress",
            "description": "Romantic maxi dress with exclusive hand-painted floral print. Features flutter sleeves and a cinched waist. Perfect for garden parties and vacation getaways.",
            "dress_category": "women-dresses",
            "occasion": "vacation",
            "price": 289.00,
            "stock": 35,
            "material": "100% Organic Cotton",
            "available_sizes": "S,M,L,XL",
            "colors": "Garden Rose,Ocean Blue,Sunset",
            "image_url": "https://images.unsplash.com/photo-1572804013309-59a88b7e92f1?w=800",
            "featured_dress": True
        },
        {
            "product_name": "Silk Charmeuse Blouse",
            "description": "Timeless silk blouse with mother-of-pearl buttons. Features French cuffs and a relaxed fit. A wardrobe essential for the modern woman.",
            "dress_category": "women-tops",
            "occasion": "office",
            "price": 195.00,
            "stock": 55,
            "material": "100% Silk Charmeuse",
            "available_sizes": "XS,S,M,L,XL",
            "colors": "Ivory,Blush,Navy",
            "image_url": "https://images.unsplash.com/photo-1485968579580-b6d095142e6e?w=800",
            "featured_dress": False
        },
        {
            "product_name": "Embroidered Lace Camisole",
            "description": "Delicate lace camisole with intricate floral embroidery. Perfect for layering or wearing alone. Features adjustable straps and scalloped hem.",
            "dress_category": "women-tops",
            "occasion": "party",
            "price": 145.00,
            "stock": 48,
            "material": "French Lace, Silk Lining",
            "available_sizes": "XS,S,M,L",
            "colors": "Champagne,Black,Dusty Rose",
            "image_url": "https://images.unsplash.com/photo-1564246544814-5c7a09a46f7f?w=800",
            "featured_dress": False
        },
        {
            "product_name": "Italian Cotton Dress Shirt",
            "description": "Impeccably tailored dress shirt in premium Italian cotton. Features mother-of-pearl buttons and a spread collar. The perfect foundation for any formal ensemble.",
            "dress_category": "men-shirts",
            "occasion": "formal",
            "price": 185.00,
            "stock": 65,
            "material": "100% Egyptian Cotton",
            "available_sizes": "S,M,L,XL,XXL",
            "colors": "White,Light Blue,Pink",
            "image_url": "https://images.unsplash.com/photo-1602810318383-e386cc2a3ccf?w=800",
            "featured_dress": True
        },
        {
            "product_name": "Linen Resort Shirt",
            "description": "Relaxed-fit linen shirt with Cuban collar. Breathable and stylish, perfect for warm weather occasions. Features coconut buttons and side slits.",
            "dress_category": "men-shirts",
            "occasion": "vacation",
            "price": 145.00,
            "stock": 40,
            "material": "100% European Linen",
            "available_sizes": "S,M,L,XL,XXL",
            "colors": "Natural,Sky Blue,Terracotta",
            "image_url": "https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=800",
            "featured_dress": False
        },
        {
            "product_name": "Bespoke Wool Suit",
            "description": "Hand-tailored two-piece suit in superfine merino wool. Features half-canvas construction and hand-finished details. The epitome of sartorial elegance.",
            "dress_category": "men-suits",
            "occasion": "formal",
            "price": 1450.00,
            "stock": 12,
            "material": "Super 150s Merino Wool",
            "available_sizes": "38R,40R,42R,44R,46R",
            "colors": "Navy,Charcoal,Black",
            "image_url": "https://images.unsplash.com/photo-1594938298603-c8148c4dae35?w=800",
            "featured_dress": True
        },
        {
            "product_name": "Summer Linen Suit",
            "description": "Unstructured linen suit perfect for summer weddings and events. Lightweight yet elegant, with natural texture and breathability.",
            "dress_category": "men-suits",
            "occasion": "wedding",
            "price": 895.00,
            "stock": 18,
            "material": "100% Irish Linen",
            "available_sizes": "38R,40R,42R,44R,46R",
            "colors": "Sand,Light Grey,Cream",
            "image_url": "https://images.unsplash.com/photo-1507679799987-c73779587ccf?w=800",
            "featured_dress": False
        },
        {
            "product_name": "Tailored Wool Trousers",
            "description": "Classic flat-front trousers in premium wool. Features a subtle stretch for comfort and movement. Perfect for the office or formal occasions.",
            "dress_category": "men-pants",
            "occasion": "office",
            "price": 225.00,
            "stock": 50,
            "material": "98% Wool, 2% Elastane",
            "available_sizes": "30,32,34,36,38,40",
            "colors": "Navy,Charcoal,Black,Tan",
            "image_url": "https://images.unsplash.com/photo-1624378439575-d8705ad7ae80?w=800",
            "featured_dress": False
        },
        {
            "product_name": "Princess Tulle Party Dress",
            "description": "Enchanting party dress with layers of soft tulle and delicate sequin bodice. Perfect for special occasions and celebrations. Features a comfortable cotton lining.",
            "dress_category": "kids-girls",
            "occasion": "party",
            "price": 125.00,
            "stock": 30,
            "material": "Tulle, Cotton Lining, Sequin Embellishment",
            "available_sizes": "4,5,6,7,8,10,12",
            "colors": "Blush Pink,Lavender,Mint",
            "image_url": "https://images.unsplash.com/photo-1518831959646-742c3a14ebf7?w=800",
            "featured_dress": True
        },
        {
            "product_name": "Organic Cotton Sundress",
            "description": "Playful sundress in certified organic cotton. Features adjustable straps and a twirl-worthy skirt. Perfect for everyday adventures.",
            "dress_category": "kids-girls",
            "occasion": "casual",
            "price": 65.00,
            "stock": 45,
            "material": "100% GOTS Certified Organic Cotton",
            "available_sizes": "4,5,6,7,8,10",
            "colors": "Sunshine Yellow,Coral,Sky Blue",
            "image_url": "https://images.unsplash.com/photo-1503944168849-8bf86875bbd8?w=800",
            "featured_dress": False
        },
        {
            "product_name": "Little Gentleman Suit Set",
            "description": "Three-piece suit set including jacket, vest, and trousers. Perfect for weddings, formal events, and special occasions. Easy-care fabric blend.",
            "dress_category": "kids-boys",
            "occasion": "formal",
            "price": 145.00,
            "stock": 25,
            "material": "Polyester-Wool Blend",
            "available_sizes": "4,5,6,7,8,10,12",
            "colors": "Navy,Grey,Black",
            "image_url": "https://images.unsplash.com/photo-1519238263530-99bdd11df2ea?w=800",
            "featured_dress": True
        },
        {
            "product_name": "Casual Linen Set",
            "description": "Comfortable linen shirt and shorts set. Breathable and perfect for warm weather. Features natural coconut buttons.",
            "dress_category": "kids-boys",
            "occasion": "vacation",
            "price": 75.00,
            "stock": 35,
            "material": "100% Linen",
            "available_sizes": "4,5,6,7,8,10",
            "colors": "Natural,Light Blue,Sage",
            "image_url": "https://images.unsplash.com/photo-1503944583220-79d8926ad5e2?w=800",
            "featured_dress": False
        }
    ]
    
    # Add products one by one
    success_count = 0
    for product in products:
        if add_product(product):
            success_count += 1
        time.sleep(0.1)  # Small delay between requests
    
    print(f"\n🎉 Done! Added {success_count}/{len(products)} products to the database.")
    print(f"🌐 Visit http://localhost:8080/products to see your products!")
    
    if success_count == 0:
        print("\n⚠️  No products were added. Make sure your backend server is running on port 8000.")
        print("💡 Start your backend with: uvicorn main:app --reload --port 8000")

if __name__ == "__main__":
    main()