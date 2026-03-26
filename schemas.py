from pydantic import BaseModel, model_validator
from typing import List, Dict, Any, Optional, Literal
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
    message: str = ""
    prompt: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    channel: Channel = Channel.WEB
    history: Optional[List[Message]] = []

    @model_validator(mode="before")
    @classmethod
    def normalize_message(cls, data: Any):
        if not isinstance(data, dict):
            return data

        message = data.get("message")
        prompt = data.get("prompt")

        if (message is None or str(message).strip() == "") and prompt is not None:
            data["message"] = prompt

        return data

class SalesResponse(BaseModel):
    reply: str
    session_id: Optional[str] = None
    requires_action: bool = False
    action_type: Optional[str] = None
    action_data: Optional[Dict[str, Any]] = None

VoiceAgentStage = Literal["intro", "qualification", "closing"]

class VoiceAgentRequest(BaseModel):
    message: str
    stage: VoiceAgentStage

class VoiceAgentResponse(BaseModel):
    reply: str
    next_stage: VoiceAgentStage

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

# ==================== Authentication Schemas ====================

class UserRegister(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    loyalty_score: int = 0
    is_active: bool = True
    is_admin: bool = False
    created_at: str
    updated_at: str

class LoginResponse(BaseModel):
    success: bool
    message: str
    user: Optional[UserResponse] = None
    token: Optional[str] = None
