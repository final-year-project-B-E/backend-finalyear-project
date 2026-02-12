"""FastAPI entrypoint for sales, products, cart, checkout, and orders APIs.
Calling/voice modules were intentionally removed from this codebase.
"""

from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

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


@app.get("/user/{user_id}/cart")
async def get_cart(user_id: int):
    """Get user's shopping cart."""
    from database import db

    cart_items = db.get_user_cart(user_id)
    return {"user_id": user_id, "cart_items": cart_items}


@app.post("/user/{user_id}/cart/add/{product_id}")
async def add_to_cart(user_id: int, product_id: int, quantity: int = 1):
    """Add item to cart."""
    from database import db

    db.add_to_cart(user_id, product_id, quantity)
    return {"message": "Item added to cart", "user_id": user_id, "product_id": product_id}


@app.post("/user/{user_id}/checkout")
async def checkout(user_id: int, shipping_address: str, billing_address: str, payment_method: str):
    """Process checkout."""
    from database import db

    cart_items = db.get_user_cart(user_id)
    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    order = db.create_order(user_id, cart_items, shipping_address, billing_address, payment_method)
    db.clear_user_cart(user_id)
    return {"message": "Order created", "order": order}


@app.get("/products")
async def get_products(category: str = None, occasion: str = None, min_price: float = None, max_price: float = None):
    """Search products."""
    from database import db

    products = db.search_products(category, occasion, min_price, max_price)
    return {"products": products}


@app.get("/user/{user_id}/orders")
async def get_orders(user_id: int):
    """Get user's orders."""
    from database import db

    orders = db.get_user_orders(user_id)
    return {"user_id": user_id, "orders": orders}


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
