import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from database import db
from orchestrator import Orchestrator
from schemas import AuthResponse, SalesRequest, SalesResponse, SignInRequest, SignUpRequest

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

orchestrator = Orchestrator()
BASE_DIR = Path(__file__).resolve().parent
security = HTTPBearer()

JWT_SECRET = os.getenv("JWT_SECRET", "replace-this-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRES_MINUTES = int(os.getenv("JWT_EXPIRES_MINUTES", "1440"))


def create_access_token(payload: Dict[str, str]) -> str:
    to_encode = payload.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRES_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> Dict[str, str]:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from exc


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    payload = decode_access_token(credentials.credentials)
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    user = db.get_user(int(user_id))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    user.pop("password_hash", None)
    return user


@app.get("/")
async def dashboard():
    """Serve local HTML dashboard for manual endpoint testing."""
    return FileResponse(BASE_DIR / "index.html")


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Avoid browser 404 noise when loading the dashboard."""
    return Response(status_code=204)


@app.post("/auth/signup", response_model=AuthResponse)
async def signup(req: SignUpRequest):
    try:
        user = db.create_user(req.first_name, req.last_name, req.email, req.password)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    token = create_access_token({"user_id": str(user["id"]), "email": user["email"]})
    return AuthResponse(access_token=token, user=user)


@app.post("/auth/signin", response_model=AuthResponse)
async def signin(req: SignInRequest):
    user = db.authenticate_user(req.email, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"user_id": str(user["id"]), "email": user["email"]})
    return AuthResponse(access_token=token, user=user)


@app.get("/auth/me")
async def me(current_user: Dict = Depends(get_current_user)):
    return {"user": current_user}


@app.post("/sales", response_model=SalesResponse)
async def sales_chat(req: SalesRequest):
    try:
        return await orchestrator.process_message(req)
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@app.get("/user/{user_id}/cart")
async def get_cart(user_id: int):
    cart_items = db.get_user_cart(user_id)
    return {"user_id": user_id, "cart_items": cart_items}


@app.post("/user/{user_id}/cart/add/{product_id}")
async def add_to_cart(user_id: int, product_id: int, quantity: int = 1):
    db.add_to_cart(user_id, product_id, quantity)
    return {"message": "Item added to cart", "user_id": user_id, "product_id": product_id}


@app.post("/user/{user_id}/checkout")
async def checkout(user_id: int, shipping_address: str, billing_address: str, payment_method: str):
    cart_items = db.get_user_cart(user_id)
    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    order = db.create_order(user_id, cart_items, shipping_address, billing_address, payment_method)

    db.clear_user_cart(user_id)

    return {"message": "Order created", "order": order}


@app.get("/products")
async def get_products(
    category: str = None,
    occasion: str = None,
    min_price: float = None,
    max_price: float = None,
):
    products = db.search_products(category, occasion, min_price, max_price)
    return {"products": products}


@app.get("/user/{user_id}/orders")
async def get_orders(user_id: int):
    orders = db.get_user_orders(user_id)
    return {"user_id": user_id, "orders": orders}


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
