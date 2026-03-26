from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional
import asyncio
import logging

from bson import ObjectId
from datetime import datetime
from dotenv import load_dotenv
from fastapi import Body, FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import uvicorn

from commerce_service import commerce_service
from database import db
from orchestrator import Orchestrator
from schemas import (
    ActivityRequest,
    CheckoutRequest,
    LoginResponse,
    OrderAdvanceRequest,
    PaymentRetryRequest,
    SalesRequest,
    SalesResponse,
    UserLogin,
    UserRegister,
    UserResponse,
    VoiceAgentRequest,
    VoiceAgentResponse,
    WhatsAppConnectionRequest,
)
from voice_agent import build_voice_fallback, build_voice_prompt, call_gemini, get_next_stage

load_dotenv()

logger = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parent
orchestrator = Orchestrator()


def serialize_document(doc: Any) -> Any:
    if isinstance(doc, dict):
        return {key: serialize_document(value) for key, value in doc.items()}
    if isinstance(doc, list):
        return [serialize_document(item) for item in doc]
    if isinstance(doc, ObjectId):
        return str(doc)
    if isinstance(doc, datetime):
        return doc.isoformat()
    return doc


def user_to_response(user: Dict[str, Any]) -> UserResponse:
    return UserResponse(
        id=user.get("id", user.get("_id", "")),
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
        whatsapp_connection=user.get("whatsapp_connection"),
        created_at=user.get("created_at", ""),
        updated_at=user.get("updated_at", ""),
    )


async def simulation_loop() -> None:
    while True:
        try:
            commerce_service.process_due_simulations()
        except Exception:
            logger.exception("Simulation worker tick failed")
        await asyncio.sleep(15)


@asynccontextmanager
async def lifespan(_: FastAPI):
    commerce_service.process_due_simulations()
    task = asyncio.create_task(simulation_loop())
    try:
        yield
    finally:
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)


app = FastAPI(
    title="Retail Sales Agent API",
    description="Omnichannel AI Sales Assistant for Fashion Retail",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def dashboard():
    return FileResponse(BASE_DIR / "index.html")


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)


@app.post("/sales", response_model=SalesResponse)
async def sales_chat(req: SalesRequest):
    try:
        commerce_service.process_due_simulations()
        return await orchestrator.process_message(req)
    except Exception as error:
        logger.exception("Sales endpoint failed")
        raise HTTPException(status_code=500, detail=str(error))


@app.post("/voice-agent", response_model=VoiceAgentResponse)
async def voice_agent(req: VoiceAgentRequest):
    next_stage = get_next_stage(req.stage)
    prompt = build_voice_prompt(req.stage, req.message)

    try:
        reply = call_gemini(prompt)
    except Exception as error:
        logger.warning("Voice agent fell back after Gemini error: %s", error)
        reply = build_voice_fallback(req.stage)

    return VoiceAgentResponse(reply=reply, next_stage=next_stage)


@app.post("/auth/register", response_model=LoginResponse)
async def register(user_data: UserRegister):
    try:
        new_user = db.register_user(
            email=user_data.email,
            password=user_data.password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
        )
        if not new_user:
            raise HTTPException(status_code=400, detail="Email already registered")

        return LoginResponse(
            success=True,
            message="User registered successfully",
            user=user_to_response(new_user),
            token=str(new_user.get("_id", "")),
        )
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@app.post("/auth/login", response_model=LoginResponse)
async def login(credentials: UserLogin):
    try:
        user = db.authenticate_user(email=credentials.email, password=credentials.password)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        return LoginResponse(
            success=True,
            message="Login successful",
            user=user_to_response(user),
            token=user.get("id", ""),
        )
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@app.get("/auth/me/{user_id}", response_model=UserResponse)
async def get_profile(user_id: str):
    try:
        user = db.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user_to_response(user)
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@app.put("/auth/me/{user_id}", response_model=UserResponse)
async def update_profile(user_id: str, updates: dict):
    try:
        allowed_fields = {
            "phone",
            "address",
            "city",
            "state",
            "country",
            "postal_code",
        }
        filtered_updates = {key: value for key, value in updates.items() if key in allowed_fields}
        if not filtered_updates:
            raise HTTPException(status_code=400, detail="No valid fields to update")

        success = db.update_user_profile(user_id, **filtered_updates)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to update profile")

        user = db.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user_to_response(user)
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@app.put("/auth/me/{user_id}/whatsapp", response_model=UserResponse)
async def update_whatsapp_connection(user_id: str, payload: WhatsAppConnectionRequest):
    user = commerce_service.update_whatsapp_connection(
        user_id=user_id,
        phone_number=payload.phone_number,
        connected=payload.connected,
        opt_in=payload.opt_in,
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user_to_response(user)


@app.get("/products")
async def get_products(
    category: str = None,
    occasion: str = None,
    min_price: float = None,
    max_price: float = None,
    q: str = None,
):
    if category or occasion or min_price is not None or max_price is not None or q:
        products = db.search_products(
            category=category,
            occasion=occasion,
            min_price=min_price,
            max_price=max_price,
            query=q,
        )
    else:
        products = db.get_all_products()
    return {"products": [serialize_document(product) for product in products]}


@app.get("/products/meta")
async def get_product_metadata():
    return serialize_document(db.get_catalog_metadata())


@app.get("/products/{product_id}")
async def get_product(product_id: int):
    product = db.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return serialize_document(product)


@app.get("/user/{user_id}/cart")
async def get_user_cart(user_id: str):
    cart = db.get_cart(user_id)
    if not cart:
        return {"user_id": user_id, "items": []}
    return {"user_id": user_id, "items": cart.get("items", [])}


@app.post("/user/{user_id}/cart/add/{product_id}")
async def add_to_cart(
    user_id: str,
    product_id: int,
    quantity: int = Query(1, ge=1),
    size: Optional[str] = Query(None),
    color: Optional[str] = Query(None),
):
    product = db.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    cart = db.get_cart(user_id) or {"user_id": user_id, "items": []}
    for item in cart.get("items", []):
        if (
            item["product_id"] == product_id
            and item.get("size") == size
            and item.get("color") == color
        ):
            item["quantity"] += quantity
            break
    else:
        cart.setdefault("items", []).append(
            {
                "product_id": product_id,
                "quantity": quantity,
                "price": product["price"],
                "size": size,
                "color": color,
            }
        )

    db.update_cart(user_id, cart.get("items", []))
    commerce_service.record_user_activity(
        user_id,
        "cart_add",
        {
            "product_id": product_id,
            "quantity": quantity,
            "size": size,
            "color": color,
        },
    )
    return {"message": "Item added to cart", "user_id": user_id, "product_id": product_id}


@app.delete("/user/{user_id}/cart/remove/{product_id}")
async def remove_from_cart(user_id: str, product_id: int):
    cart = db.get_cart(user_id) or {"user_id": user_id, "items": []}
    original_length = len(cart.get("items", []))
    cart["items"] = [item for item in cart.get("items", []) if item["product_id"] != product_id]

    if len(cart["items"]) == original_length:
        raise HTTPException(status_code=404, detail="Product not found in cart")

    db.update_cart(user_id, cart["items"])
    commerce_service.record_user_activity(
        user_id,
        "cart_remove",
        {"product_id": product_id},
    )
    return {"message": "Item removed from cart", "user_id": user_id, "product_id": product_id}


@app.post("/user/{user_id}/checkout")
async def checkout(
    user_id: str,
    checkout_payload: Optional[CheckoutRequest] = Body(None),
    shipping_address: Optional[str] = Query(None),
    billing_address: Optional[str] = Query(None),
    payment_method: Optional[str] = Query(None),
    payment_scenario: Optional[str] = Query(None),
):
    try:
        payload = checkout_payload or CheckoutRequest(
            shipping_address=shipping_address or "",
            billing_address=billing_address or shipping_address or "",
            payment_method=payment_method or "card",
            payment_scenario=payment_scenario or "success",
            items=[],
        )
        order = commerce_service.create_checkout(
            user_id=user_id,
            shipping_address=payload.shipping_address,
            billing_address=payload.billing_address,
            payment_method=payload.payment_method,
            payment_scenario=payload.payment_scenario,
            items=[item.model_dump() for item in payload.items],
        )
        return {
            "message": "Order created",
            "order_id": serialize_document(order.get("_id")),
            "order_number": order["order_number"],
            "payment_status": order.get("payment_status"),
            "order_status": order.get("order_status"),
            "final_amount": order.get("final_amount"),
            "timeline": serialize_document(order.get("timeline", [])),
        }
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@app.get("/orders/{order_number}")
async def get_order_detail(order_number: str):
    commerce_service.process_due_simulations()
    order = commerce_service.get_order(order_number)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return serialize_document(order)


@app.get("/orders/{order_number}/timeline")
async def get_order_timeline(order_number: str):
    commerce_service.process_due_simulations()
    order = commerce_service.get_order(order_number)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return {
        "order_number": order_number,
        "timeline": serialize_document(order.get("timeline", [])),
    }


@app.post("/orders/{order_number}/advance")
async def advance_order(order_number: str, payload: OrderAdvanceRequest):
    order = commerce_service.advance_order(order_number, payload.target_status.value, note=payload.note)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return serialize_document(order)


@app.post("/orders/{order_number}/payments/{payment_id}/retry")
async def retry_payment(order_number: str, payment_id: str, payload: PaymentRetryRequest):
    order = commerce_service.retry_payment(order_number, payment_id, scenario=payload.scenario)
    if not order:
        raise HTTPException(status_code=404, detail="Order or payment not found")
    return serialize_document(order)


@app.get("/user/{user_id}/orders")
async def get_orders(user_id: str):
    commerce_service.process_due_simulations()
    orders = commerce_service.list_user_orders(user_id)
    return {"user_id": user_id, "orders": [serialize_document(order) for order in orders]}


@app.get("/user/{user_id}/wishlist")
async def get_wishlist(user_id: str):
    items = db.get_user_wishlist(user_id)
    return {"user_id": user_id, "items": [serialize_document(item) for item in items]}


@app.post("/user/{user_id}/wishlist/{product_id}")
async def add_to_wishlist(user_id: str, product_id: int):
    product = db.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.add_to_wishlist(user_id, product_id)
    return {"message": "Item added to wishlist", "user_id": user_id, "product_id": product_id}


@app.delete("/user/{user_id}/wishlist/{product_id}")
async def remove_from_wishlist(user_id: str, product_id: int):
    success = db.remove_from_wishlist(user_id, product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found in wishlist")
    return {"message": "Item removed from wishlist", "user_id": user_id, "product_id": product_id}


@app.get("/chat/{session_id}/messages")
async def get_chat_messages(session_id: str):
    messages = db.get_chat_history(session_id, limit=100)
    return {
        "session_id": session_id,
        "messages": [serialize_document(message) for message in messages],
    }


@app.get("/user/{user_id}/chat/sessions")
async def get_user_chat_sessions(user_id: str):
    sessions = db.get_user_chat_sessions(user_id, limit=20)
    return {
        "user_id": user_id,
        "sessions": [serialize_document(session) for session in sessions],
    }


@app.post("/user/{user_id}/activity")
async def record_activity(user_id: str, payload: ActivityRequest):
    activity = commerce_service.record_user_activity(
        user_id,
        payload.activity_type,
        {
            "product_id": payload.product_id,
            "order_number": payload.order_number,
            **payload.metadata,
        },
    )
    return serialize_document(activity)


@app.get("/user/{user_id}/activity/summary")
async def get_activity_summary(user_id: str):
    return serialize_document(commerce_service.get_user_activity_summary(user_id))


@app.get("/user/{user_id}/communications")
async def get_communications(user_id: str):
    commerce_service.process_due_simulations()
    return serialize_document(commerce_service.get_user_communications(user_id))


@app.get("/admin/simulation/orders")
async def get_admin_simulation_orders():
    commerce_service.process_due_simulations()
    return {
        "orders": [serialize_document(order) for order in commerce_service.list_admin_orders()],
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
