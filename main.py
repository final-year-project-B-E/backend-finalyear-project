from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import Body, FastAPI, Header, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, EmailStr

from database import db
from orchestrator import Orchestrator
from schemas import SalesRequest, SalesResponse

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


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@app.get("/")
async def dashboard():
    return FileResponse(BASE_DIR / "index.html")


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)


@app.post("/auth/signup")
async def signup(payload: SignupRequest):
    if db.get_user_by_email(payload.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    user = db.create_user(payload.email, payload.password, payload.first_name, payload.last_name)
    token = db.create_auth_token(user["id"])
    return {"user": user, "token": token}


@app.post("/auth/login")
async def login(payload: LoginRequest):
    user = db.authenticate_user(payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = db.create_auth_token(user["id"])
    user.pop("password_hash", None)
    return {"user": user, "token": token}


@app.get("/auth/me")
async def me(authorization: Optional[str] = Header(default=None)):
    token = (authorization or "").replace("Bearer ", "")
    user = db.get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {"user": user}


@app.post("/auth/logout")
async def logout(authorization: Optional[str] = Header(default=None)):
    token = (authorization or "").replace("Bearer ", "")
    if token:
        db.delete_token(token)
    return {"message": "Logged out"}


@app.post("/sales", response_model=SalesResponse)
async def sales_chat(req: SalesRequest):
    try:
        return await orchestrator.process_message(req)
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@app.get("/products")
async def get_products(category: str = None, occasion: str = None, min_price: float = None, max_price: float = None):
    products = db.search_products(category, occasion, min_price, max_price)
    return {"products": products}


@app.get("/user/{user_id}/cart")
async def get_cart(user_id: int):
    cart_items = db.get_user_cart(user_id)
    return {"user_id": user_id, "cart_items": cart_items}


@app.post("/user/{user_id}/cart/add/{product_id}")
async def add_to_cart(user_id: int, product_id: int, quantity: int = 1):
    db.add_to_cart(user_id, product_id, quantity)
    return {"message": "Item added to cart", "user_id": user_id, "product_id": product_id}


@app.post("/user/{user_id}/checkout")
async def checkout(user_id: int, shipping_address: str = Body(...), billing_address: str = Body(...), payment_method: str = Body(...)):
    cart_items = db.get_user_cart(user_id)
    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    order = db.create_order(user_id, cart_items, shipping_address, billing_address, payment_method)
    db.clear_user_cart(user_id)
    return {"message": "Order created", "order": order}


@app.get("/user/{user_id}/orders")
async def get_orders(user_id: int):
    orders = db.get_user_orders(user_id)
    return {"user_id": user_id, "orders": orders}


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
