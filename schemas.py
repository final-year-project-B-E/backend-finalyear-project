from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

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