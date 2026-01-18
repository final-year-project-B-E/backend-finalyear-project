from fastapi import FastAPI, HTTPException, Body, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from schemas import (
    SalesRequest, SalesResponse, UserRegistration, UserLogin,
    UserResponse, AuthResponse
)
from orchestrator import Orchestrator
from voice_assistant.voice_assistant import VoiceAssistant
import os
import tempfile
import subprocess
import bcrypt
from jose import jwt
from datetime import datetime, timedelta

import uvicorn
import asyncio

# JWT settings
SECRET_KEY = "your-secret-key-here"  # In production, use environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI(title="Retail Sales Agent API", 
              description="Omnichannel AI Sales Assistant for Fashion Retail")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = Orchestrator()
voice_assistant = VoiceAssistant()

# Authentication helper functions
def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict):
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@app.post("/sales", response_model=SalesResponse)
async def sales_chat(req: SalesRequest):
    """Main endpoint for sales conversations"""
    try:
        response = await orchestrator.process_message(req)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/user/{user_id}/cart")
async def get_cart(user_id: int):
    """Get user's shopping cart"""
    from mongo_database import db
    cart_items = db.get_user_cart(user_id)
    return {"user_id": user_id, "cart_items": cart_items}

@app.post("/user/{user_id}/cart/add/{product_id}")
async def add_to_cart(user_id: int, product_id: int, quantity: int = 1):
    """Add item to cart"""
    from mongo_database import db
    db.add_to_cart(user_id, product_id, quantity)
    return {"message": "Item added to cart", "user_id": user_id, "product_id": product_id}

@app.post("/user/{user_id}/checkout")
async def checkout(user_id: int, shipping_address: str, 
                  billing_address: str, payment_method: str):
    """Process checkout"""
    from mongo_database import db
    cart_items = db.get_user_cart(user_id)
    
    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty")
    
    order = db.create_order(user_id, cart_items, shipping_address, 
                           billing_address, payment_method)
    
    # Clear cart after order
    db.clear_cart(user_id)
    
    return {"message": "Order created", "order": order}

@app.get("/products")
async def get_products(category: str = None, occasion: str = None, 
                      min_price: float = None, max_price: float = None):
    """Search products"""
    from mongo_database import db
    products = db.search_products(category, occasion, min_price, max_price)
    return {"products": products}

@app.get("/user/{user_id}/orders")
async def get_orders(user_id: int):
    """Get user's orders"""
    from mongo_database import db
    orders = db.get_user_orders(user_id)
    return {"user_id": user_id, "orders": orders}

# Authentication endpoints
@app.post("/auth/register", response_model=AuthResponse)
async def register_user(user_data: UserRegistration):
    """Register a new user"""
    from mongo_database import db

    # Check if user already exists
    existing_user = db.get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Hash password
    hashed_password = hash_password(user_data.password)

    # Prepare user data
    user_dict = user_data.dict()
    user_dict["password_hash"] = hashed_password
    user_dict.pop("password")  # Remove plain password

    # Generate user ID
    # For simplicity, we'll use a simple increment. In production, use MongoDB's ObjectId
    last_user = list(db.db.users.find().sort("id", -1).limit(1))
    next_id = (last_user[0]["id"] + 1) if last_user else 1
    user_dict["id"] = next_id
    user_dict["loyalty_score"] = 0
    user_dict["is_active"] = True
    user_dict["is_admin"] = False

    # Create user
    created_user = db.create_user(user_dict)

    # Create response
    user_response = UserResponse(
        id=created_user["id"],
        email=created_user["email"],
        first_name=created_user["first_name"],
        last_name=created_user["last_name"],
        phone=created_user.get("phone"),
        loyalty_score=created_user.get("loyalty_score", 0),
        is_active=created_user.get("is_active", True),
        created_at=created_user.get("created_at", datetime.now().isoformat())
    )

    # Create access token
    access_token = create_access_token(data={"sub": str(created_user["id"])})

    return AuthResponse(user=user_response, token=access_token)

@app.post("/auth/login", response_model=AuthResponse)
async def login_user(login_data: UserLogin):
    """Authenticate user login"""
    from mongo_database import db

    # Find user by email
    user = db.get_user_by_email(login_data.email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Verify password
    if not verify_password(login_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Check if user is active
    if not user.get("is_active", True):
        raise HTTPException(status_code=401, detail="Account is deactivated")

    # Create response
    user_response = UserResponse(
        id=user["id"],
        email=user["email"],
        first_name=user["first_name"],
        last_name=user["last_name"],
        phone=user.get("phone"),
        loyalty_score=user.get("loyalty_score", 0),
        is_active=user.get("is_active", True),
        created_at=user.get("created_at", datetime.now().isoformat())
    )

    # Create access token
    access_token = create_access_token(data={"sub": str(user["id"])})

    return AuthResponse(user=user_response, token=access_token)

@app.get("/auth/me", response_model=UserResponse)
async def get_current_user(user_id: int):
    """Get current user profile"""
    from mongo_database import db
    user = db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(
        id=user["id"],
        email=user["email"],
        first_name=user["first_name"],
        last_name=user["last_name"],
        phone=user.get("phone"),
        loyalty_score=user.get("loyalty_score", 0),
        is_active=user.get("is_active", True),
        created_at=user.get("created_at", datetime.now().isoformat())
    )

@app.post("/call")
async def initiate_call(data: dict = Body(...)):
    """Initiate a call to the given phone number"""
    phone_number = data.get("phone_number")
    if not phone_number or not isinstance(phone_number, str):
        raise HTTPException(status_code=400, detail="Invalid phone_number")
    if not phone_number.startswith("+"):
        raise HTTPException(status_code=400, detail="Phone number must be in E.164 format")
    # Import here to avoid loading heavy modules on startup
    from calling_agent.calling_agent import make_call
    # Run in background since make_call is blocking
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, make_call, phone_number, 3)
    return {"message": "Call initiated", "to": phone_number}

@app.post("/voice")
async def process_voice(file: UploadFile = File(...), session_id: str = None, user_id: int = 1):
    """Process voice message: upload audio, transcribe, and get response"""
    supported_formats = ('.wav', '.mp3', '.m4a', '.flac', '.webm')
    if not file.filename.lower().endswith(supported_formats):
        raise HTTPException(status_code=400, detail=f"Unsupported file format. Use {', '.join(supported_formats)}.")

    # Save uploaded file temporarily
    input_suffix = os.path.splitext(file.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=input_suffix) as temp_file:
        temp_file.write(await file.read())
        input_path = temp_file.name

    temp_path = input_path
    try:
        # Convert webm to wav if necessary
        if input_suffix.lower() == '.webm':
            wav_path = input_path.replace('.webm', '.wav')
            # Convert WebM to WAV using ffmpeg
            subprocess.check_call([
                "ffmpeg", "-y",
                "-i", input_path,
                "-ar", "16000",  # 16kHz sample rate for Whisper
                "-ac", "1",      # mono
                wav_path
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            temp_path = wav_path

        # Process voice message
        response = voice_assistant.process_voice_message(
            audio_path=temp_path,
            session_id=session_id,
            user_id=user_id,
            channel="web"
        )
        return {"reply": response, "session_id": session_id}
    finally:
        # Clean up temp files
        paths_to_remove = set([input_path, temp_path])
        for path in paths_to_remove:
            if os.path.exists(path):
                os.remove(path)

# 👇 THIS IS WHAT ALLOWS: python main.py
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )