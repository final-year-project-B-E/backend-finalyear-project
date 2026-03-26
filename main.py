from fastapi import FastAPI, HTTPException, Body, UploadFile, File, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from schemas import SalesRequest, SalesResponse, UserRegister, UserLogin, UserResponse, LoginResponse
from orchestrator import Orchestrator
from database import Database
import os
import tempfile
import subprocess
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
import json
from bson import ObjectId
from typing import Any, Dict, List

# Load environment variables from .env file
load_dotenv()

import uvicorn
import asyncio

# ==================== Helper Functions ====================

def serialize_document(doc: Any) -> Any:
    """Convert MongoDB documents to JSON-serializable format."""
    if isinstance(doc, dict):
        return {key: serialize_document(value) for key, value in doc.items()}
    elif isinstance(doc, list):
        return [serialize_document(item) for item in doc]
    elif isinstance(doc, ObjectId):
        return str(doc)
    elif isinstance(doc, datetime):
        return doc.isoformat()
    else:
        return doc

app = FastAPI(
    title="Retail Sales Agent API",
    description="Omnichannel AI Sales Assistant for Fashion Retail",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Database and Orchestrator
db = Database()
orchestrator = Orchestrator()

BASE_DIR = Path(__file__).resolve().parent

@app.get("/")
async def dashboard():
    """Serve local HTML dashboard for manual endpoint testing."""
    return FileResponse(BASE_DIR / "index.html")

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Avoid browser 404 noise when loading the dashboard."""
    return Response(status_code=204)

@app.post("/sales", response_model=SalesResponse)
async def sales_chat(req: SalesRequest):
    """Main endpoint for sales conversations."""
    try:
        return await orchestrator.process_message(req)
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


# ==================== Authentication Endpoints ====================

@app.post("/auth/register", response_model=LoginResponse)
async def register(user_data: UserRegister):
    """Register a new user."""
    try:
        # Register user in database
        new_user = db.register_user(
            email=user_data.email,
            password=user_data.password,
            first_name=user_data.first_name,
            last_name=user_data.last_name
        )
        
        if not new_user:
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )
        
        # Return user response
        user_response = UserResponse(
            id=new_user.get("_id", ""),
            email=new_user["email"],
            first_name=new_user["first_name"],
            last_name=new_user["last_name"],
            phone=new_user.get("phone"),
            address=new_user.get("address"),
            city=new_user.get("city"),
            state=new_user.get("state"),
            country=new_user.get("country"),
            postal_code=new_user.get("postal_code"),
            loyalty_score=new_user.get("loyalty_score", 0),
            is_active=new_user.get("is_active", True),
            is_admin=new_user.get("is_admin", False),
            created_at=new_user.get("created_at", ""),
            updated_at=new_user.get("updated_at", "")
        )
        
        return LoginResponse(
            success=True,
            message="User registered successfully",
            user=user_response,
            token=str(new_user.get("_id", ""))
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/auth/login", response_model=LoginResponse)
async def login(credentials: UserLogin):
    """Login user and return user data."""
    try:
        # Authenticate user
        user = db.authenticate_user(
            email=credentials.email,
            password=credentials.password
        )
        
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )
        
        # Return user response
        user_response = UserResponse(
            id=user.get("id", ""),
            email=user["email"],
            first_name=user["first_name"],
            last_name=user["last_name"],
            phone=user.get("phone"),
            address=user.get("address"),
            city=user.get("city"),
            state=user.get("state"),
            country=user.get("country"),
            postal_code=user.get("postal_code"),
            loyalty_score=user.get("loyalty_score", 0),
            is_active=user.get("is_active", True),
            is_admin=user.get("is_admin", False),
            created_at=user.get("created_at", ""),
            updated_at=user.get("updated_at", "")
        )
        
        return LoginResponse(
            success=True,
            message="Login successful",
            user=user_response,
            token=user.get("id", "")
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/auth/me/{user_id}", response_model=UserResponse)
async def get_profile(user_id: str):
    """Get current user profile."""
    try:
        user = db.get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return UserResponse(
            id=user.get("id", ""),
            email=user["email"],
            first_name=user["first_name"],
            last_name=user["last_name"],
            phone=user.get("phone"),
            address=user.get("address"),
            city=user.get("city"),
            state=user.get("state"),
            country=user.get("country"),
            postal_code=user.get("postal_code"),
            loyalty_score=user.get("loyalty_score", 0),
            is_active=user.get("is_active", True),
            is_admin=user.get("is_admin", False),
            created_at=user.get("created_at", ""),
            updated_at=user.get("updated_at", "")
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/auth/me/{user_id}", response_model=UserResponse)
async def update_profile(user_id: str, updates: dict):
    """Update user profile."""
    try:
        # Only allow specific fields to be updated
        allowed_fields = {
            "phone", "address", "city", "state", "country", "postal_code"
        }
        filtered_updates = {
            k: v for k, v in updates.items() if k in allowed_fields
        }
        
        if not filtered_updates:
            raise HTTPException(status_code=400, detail="No valid fields to update")
        
        success = db.update_user_profile(user_id, **filtered_updates)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to update profile")
        
        # Return updated user
        user = db.get_user_by_id(user_id)
        
        return UserResponse(
            id=user.get("id", ""),
            email=user["email"],
            first_name=user["first_name"],
            last_name=user["last_name"],
            phone=user.get("phone"),
            address=user.get("address"),
            city=user.get("city"),
            state=user.get("state"),
            country=user.get("country"),
            postal_code=user.get("postal_code"),
            loyalty_score=user.get("loyalty_score", 0),
            is_active=user.get("is_active", True),
            is_admin=user.get("is_admin", False),
            created_at=user.get("created_at", ""),
            updated_at=user.get("updated_at", "")
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== End Authentication Endpoints ====================
async def get_cart(user_id: int):
    """Get user's shopping cart."""
    cart = db.get_cart(user_id)
    if not cart:
        return {"user_id": user_id, "items": []}
    return {"user_id": user_id, "items": cart.get("items", [])}


@app.post("/user/{user_id}/cart/add/{product_id}")
async def add_to_cart(user_id: str, product_id: int, quantity: int = 1):
    """Add item to cart."""
    product = db.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    cart = db.get_cart(user_id) or {"user_id": user_id, "items": []}
    
    # Check if product already in cart
    for item in cart.get("items", []):
        if item["product_id"] == product_id:
            item["quantity"] += quantity
            break
    else:
        cart.setdefault("items", []).append({
            "product_id": product_id,
            "quantity": quantity,
            "price": product["price"]
        })
    
    db.update_cart(user_id, cart.get("items", []))
    return {"message": "Item added to cart", "user_id": user_id, "product_id": product_id}


@app.post("/user/{user_id}/checkout")
async def checkout(user_id: int, shipping_address: str, billing_address: str, payment_method: str):
    """Process checkout."""
    from uuid import uuid4
    
    cart = db.get_cart(user_id)
    if not cart or not cart.get("items"):
        raise HTTPException(status_code=400, detail="Cart is empty")
    
    # Create order
    order_data = {
        "order_number": f"ORD-{uuid4().hex[:8]}",
        "user_id": user_id,
        "items": cart.get("items", []),
        "shipping_address": shipping_address,
        "billing_address": billing_address,
        "payment_method": payment_method,
        "status": "pending",
        "created_at": datetime.utcnow()
    }
    
    order_id = db.create_order(order_data)
    db.update_cart(user_id, [])  # Clear cart
    
    return {"message": "Order created", "order_id": order_id, "order_number": order_data["order_number"]}


@app.get("/products")
async def get_products(category: str = None):
    """Get all products or filter by category."""
    if category:
        products = db.get_products_by_category(category)
    else:
        products = db.get_all_products()
    return {"products": [serialize_document(p) for p in products]}


@app.get("/products/{product_id}")
async def get_product(product_id: int):
    """Get a single product by ID."""
    product = db.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return serialize_document(product)


@app.get("/user/{user_id}/cart")
async def get_user_cart(user_id: str):
    """Get user's shopping cart."""
    cart = db.get_cart(user_id)
    if not cart:
        return {"user_id": user_id, "items": []}
    return {"user_id": user_id, "items": cart.get("items", [])}


@app.delete("/user/{user_id}/cart/remove/{product_id}")
async def remove_from_cart(user_id: str, product_id: int):
    """Remove item from cart."""
    cart = db.get_cart(user_id) or {"user_id": user_id, "items": []}
    
    # Filter out the product
    original_length = len(cart.get("items", []))
    cart["items"] = [item for item in cart.get("items", []) if item["product_id"] != product_id]
    
    if len(cart["items"]) < original_length:
        db.update_cart(user_id, cart["items"])
        return {"message": "Item removed from cart", "user_id": user_id, "product_id": product_id}
    else:
        raise HTTPException(status_code=404, detail="Product not found in cart")


@app.get("/orders/{order_number}")
async def get_order_detail(order_number: str):
    """Get a single order by order number."""
    order = db.get_order(order_number)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return serialize_document(order)


@app.get("/user/{user_id}/orders")
async def get_orders(user_id: str):
    """Get user's orders."""
    orders = db.get_user_orders(user_id)
    return {"user_id": user_id, "orders": [serialize_document(o) for o in orders]}


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
