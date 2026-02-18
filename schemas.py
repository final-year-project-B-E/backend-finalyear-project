from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    AGENT = "agent"


class Channel(str, Enum):
    WEB = "web"
    MOBILE = "mobile"
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"
    KIOSK = "kiosk"
    VOICE = "voice"


class Message(BaseModel):
    role: str
    content: str
    timestamp: Optional[datetime] = None


class SalesRequest(BaseModel):
    message: str
    user_id: Optional[int] = None
    session_id: Optional[str] = None
    channel: Channel = Channel.WEB
    history: Optional[List[Message]] = []


class SalesResponse(BaseModel):
    reply: str
    session_id: Optional[str] = None
    requires_action: bool = False
    action_type: Optional[str] = None
    action_data: Optional[Dict[str, Any]] = None


class Product(BaseModel):
    id: int
    product_name: str
    description: str
    dress_category: str
    occasion: str
    price: float
    stock: int
    material: str
    available_sizes: str
    colors: str
    image_url: str
    featured_dress: bool = False


class CartItem(BaseModel):
    product_id: int
    quantity: int
    product: Optional[Product] = None


class Order(BaseModel):
    order_number: str
    total_amount: float
    final_amount: float
    status: str
    items: List[Dict[str, Any]]


class AgentTask(BaseModel):
    task_id: str
    agent_type: str
    status: str
    parameters: Dict[str, Any]
    result: Optional[Dict[str, Any]] = None


class SignUpRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=80)
    last_name: str = Field(min_length=1, max_length=80)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class SignInRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]
