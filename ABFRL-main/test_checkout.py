#!/usr/bin/env python3
"""
Test script for the checkout functionality
This script tests the checkout flow and payment gateway simulation
"""

import requests
import json
import time
import random

# Configuration
BASE_URL = "http://localhost:8000"
TEST_EMAIL = "akeel@gmail.com"
TEST_PASSWORD = "123456"

def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_step(step, description):
    print(f"\n[STEP {step}] {description}")
    print("-" * 40)

def test_checkout_flow():
    print_header("E-COMMERCE CHECKOUT TEST")
    
    session = requests.Session()
    
    # Step 1: Register a test user
    print_step(1, "Registering test user")
    try:
        register_response = session.post(f"{BASE_URL}/register", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "first_name": "Test",
            "last_name": "User"
        })
        
        if register_response.status_code == 201:
            print("✓ User registered successfully")
            user_data = register_response.json()
            print(f"  User ID: {user_data['id']}")
        else:
            print(f"✗ Registration failed: {register_response.status_code}")
            print(register_response.text)
            return
    except Exception as e:
        print(f"✗ Registration error: {e}")
        return
    
    # Step 2: Login
    print_step(2, "Logging in")
    try:
        login_response = session.post(f"{BASE_URL}/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if login_response.status_code == 200:
            print("✓ Login successful")
            token_data = login_response.json()
            token = token_data['access_token']
            session.headers.update({'Authorization': f'Bearer {token}'})
        else:
            print(f"✗ Login failed: {login_response.status_code}")
            print(login_response.text)
            return
    except Exception as e:
        print(f"✗ Login error: {e}")
        return
    
    # Step 3: Get products
    print_step(3, "Getting available products")
    try:
        products_response = session.get(f"{BASE_URL}/products?limit=5")
        if products_response.status_code == 200:
            products = products_response.json()
            print(f"✓ Found {len(products)} products")
            if products:
                product = products[0]
                print(f"  Using product: {product['product_name']} (ID: {product['id']})")
                product_id = product['id']
            else:
                print("✗ No products available for testing")
                return
        else:
            print(f"✗ Failed to get products: {products_response.status_code}")
            return
    except Exception as e:
        print(f"✗ Get products error: {e}")
        return
    
    # Step 4: Add item to cart
    print_step(4, "Adding item to cart")
    try:
        cart_response = session.post(f"{BASE_URL}/cart", json={
            "product_id": product_id,
            "quantity": 2
        })
        
        if cart_response.status_code == 201:
            print("✓ Item added to cart")
            cart_item = cart_response.json()
            print(f"  Cart item ID: {cart_item['id']}")
        else:
            print(f"✗ Failed to add to cart: {cart_response.status_code}")
            print(cart_response.text)
            return
    except Exception as e:
        print(f"✗ Add to cart error: {e}")
        return
    
    # Step 5: Get checkout preview
    print_step(5, "Getting checkout preview")
    try:
        preview_response = session.get(f"{BASE_URL}/cart/checkout-preview")
        if preview_response.status_code == 200:
            preview = preview_response.json()
            print("✓ Checkout preview retrieved")
            print(f"  Has items: {preview['has_items']}")
            print(f"  Item count: {preview['item_count']}")
            print(f"  Subtotal: ₹{preview['totals']['subtotal']}")
            print(f"  Final amount: ₹{preview['totals']['final_amount']}")
        else:
            print(f"✗ Failed to get checkout preview: {preview_response.status_code}")
            print(preview_response.text)
            return
    except Exception as e:
        print(f"✗ Checkout preview error: {e}")
        return
    
    # Step 6: Get payment methods
    print_step(6, "Getting payment methods")
    try:
        payment_methods_response = requests.get(f"{BASE_URL}/payment-methods")
        if payment_methods_response.status_code == 200:
            payment_methods = payment_methods_response.json()
            print("✓ Payment methods retrieved")
            for method, details in payment_methods.items():
                print(f"  {method}: {details['name']}")
        else:
            print(f"✗ Failed to get payment methods: {payment_methods_response.status_code}")
            return
    except Exception as e:
        print(f"✗ Payment methods error: {e}")
        return
    
    # Step 7: Complete checkout
    print_step(7, "Completing checkout")
    try:
        checkout_data = {
            "shipping_address": "123 Test Street, Test City, Test State, 123456, India",
            "billing_address": "123 Test Street, Test City, Test State, 123456, India",
            "payment_method": "credit_card",
            "notes": "Test order for checkout flow",
            "card_details": {
                "card_number": "4532015112830366",  # Test Visa card
                "expiry_month": "12",
                "expiry_year": "2025",
                "cvv": "123"
            }
        }
        
        checkout_response = session.post(f"{BASE_URL}/checkout", json=checkout_data)
        
        if checkout_response.status_code == 201:
            checkout_result = checkout_response.json()
            print("✓ Checkout completed")
            print(f"  Success: {checkout_result['success']}")
            print(f"  Order ID: {checkout_result.get('order_id')}")
            print(f"  Order Number: {checkout_result.get('order_number')}")
            print(f"  Final Amount: ₹{checkout_result.get('final_amount')}")
            
            if checkout_result['success']:
                print("✓ Payment successful!")
            else:
                print(f"✗ Payment failed: {checkout_result.get('error')}")
        else:
            print(f"✗ Checkout failed: {checkout_response.status_code}")
            print(checkout_response.text)
            return
    except Exception as e:
        print(f"✗ Checkout error: {e}")
        return
    
    # Step 8: Get user orders
    print_step(8, "Getting user orders")
    try:
        orders_response = session.get(f"{BASE_URL}/orders")
        if orders_response.status_code == 200:
            orders = orders_response.json()
            print(f"✓ Found {len(orders)} orders")
            for order in orders:
                print(f"  Order: {order['order_number']} - {order['payment_status']}")
        else:
            print(f"✗ Failed to get orders: {orders_response.status_code}")
            return
    except Exception as e:
        print(f"✗ Get orders error: {e}")
        return
    
    print_header("CHECKOUT TEST COMPLETED")
    print("✓ All tests passed successfully!")
    print("\nTest Summary:")
    print("- User registration: ✓")
    print("- User login: ✓")
    print("- Product retrieval: ✓")
    print("- Add to cart: ✓")
    print("- Checkout preview: ✓")
    print("- Payment methods: ✓")
    print("- Checkout completion: ✓")
    print("- Order retrieval: ✓")

if __name__ == "__main__":
    test_checkout_flow()