from fastapi import FastAPI, HTTPException, Body, UploadFile, File, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from schemas import SalesRequest, SalesResponse
from orchestrator import Orchestrator
from voice_assistant.voice_assistant import VoiceAssistant
import os
import tempfile
import subprocess

import uvicorn
import asyncio
from pathlib import Path

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
BASE_DIR = Path(__file__).resolve().parent

@app.get("/")
async def dashboard():
    """Serve local HTML dashboard for manual endpoint testing."""
    return FileResponse(BASE_DIR / "index.html")

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Avoid browser 404 noise when loading the dashboard."""
    return Response(status_code=204)

@app.get("/")
async def dashboard():
    """Serve local HTML dashboard for manual endpoint testing."""
    return FileResponse("index.html")

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
    from database import db
    cart_items = db.get_user_cart(user_id)
    return {"user_id": user_id, "cart_items": cart_items}

@app.post("/user/{user_id}/cart/add/{product_id}")
async def add_to_cart(user_id: int, product_id: int, quantity: int = 1):
    """Add item to cart"""
    from database import db
    db.add_to_cart(user_id, product_id, quantity)
    return {"message": "Item added to cart", "user_id": user_id, "product_id": product_id}

@app.post("/user/{user_id}/checkout")
async def checkout(user_id: int, shipping_address: str, 
                  billing_address: str, payment_method: str):
    """Process checkout"""
    from database import db
    cart_items = db.get_user_cart(user_id)
    
    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty")
    
    order = db.create_order(user_id, cart_items, shipping_address, 
                           billing_address, payment_method)
    
    # Clear cart after order
    db.clear_user_cart(user_id)
    
    return {"message": "Order created", "order": order}

@app.get("/products")
async def get_products(category: str = None, occasion: str = None, 
                      min_price: float = None, max_price: float = None):
    """Search products"""
    from database import db
    products = db.search_products(category, occasion, min_price, max_price)
    return {"products": products}

@app.get("/user/{user_id}/orders")
async def get_orders(user_id: int):
    """Get user's orders"""
    from database import db
    orders = db.get_user_orders(user_id)
    return {"user_id": user_id, "orders": orders}

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