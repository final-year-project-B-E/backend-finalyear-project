from pydantic import BaseModel, Field, model_validator
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
    history: Optional[List[Message]] = Field(default_factory=list)

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

class OrderStatus(str, Enum):
    ORDER_PLACED = "order_placed"
    PAYMENT_CONFIRMED = "payment_confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    PAYMENT_FAILED = "payment_failed"

class PaymentStatus(str, Enum):
    INITIATED = "initiated"
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"

class EventType(str, Enum):
    ORDER_CREATED = "order_created"
    PAYMENT_INITIATED = "payment_initiated"
    PAYMENT_CONFIRMED = "payment_confirmed"
    PAYMENT_FAILED = "payment_failed"
    ORDER_PROCESSING = "order_processing"
    ORDER_SHIPPED = "order_shipped"
    ORDER_OUT_FOR_DELIVERY = "order_out_for_delivery"
    ORDER_DELIVERED = "order_delivered"
    PRODUCT_VIEWED = "product_viewed"
    CART_ABANDONED = "cart_abandoned"
    WHATSAPP_CONNECTED = "whatsapp_connected"
    WHATSAPP_DISCONNECTED = "whatsapp_disconnected"

class NotificationStatus(str, Enum):
    QUEUED = "queued"
    SIMULATED_SENT = "simulated_sent"
    FAILED = "failed"

class CallScenario(str, Enum):
    CART_ABANDONMENT = "cart_abandonment"
    PRODUCT_INTEREST = "product_interest"
    ORDER_UPDATE = "order_update"
    POST_DELIVERY_FOLLOWUP = "post_delivery_followup"

class CallWorkflowStatus(str, Enum):
    SCHEDULED = "scheduled"
    READY = "ready"
    COMPLETED = "completed"

class OrderTimelineEntry(BaseModel):
    status: str
    label: str
    description: str
    source: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: str

class WhatsAppConnection(BaseModel):
    provider: str = "openclaw"
    mode: str = "simulated"
    status: str = "disconnected"
    phone_number: Optional[str] = None
    opt_in: bool = True
    connected_at: Optional[str] = None
    updated_at: Optional[str] = None

class CheckoutItemRequest(BaseModel):
    product_id: str
    product_name: Optional[str] = None
    quantity: int = 1
    price: Optional[float] = None
    size: Optional[str] = None
    color: Optional[str] = None

class CheckoutRequest(BaseModel):
    shipping_address: str
    billing_address: str
    payment_method: str
    payment_scenario: Literal["success", "pending", "failed"] = "success"
    items: List[CheckoutItemRequest] = Field(default_factory=list)

class OrderAdvanceRequest(BaseModel):
    target_status: OrderStatus
    note: Optional[str] = None

class PaymentRetryRequest(BaseModel):
    scenario: Literal["success", "pending", "failed"] = "success"

class ActivityRequest(BaseModel):
    activity_type: str
    product_id: Optional[int] = None
    order_number: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class WhatsAppConnectionRequest(BaseModel):
    phone_number: Optional[str] = None
    connected: bool
    opt_in: bool = True

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
    payment_status: Optional[str] = None
    timeline: List[OrderTimelineEntry] = Field(default_factory=list)

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
    whatsapp_connection: Optional[WhatsAppConnection] = None
    created_at: str
    updated_at: str

class LoginResponse(BaseModel):
    success: bool
    message: str
    user: Optional[UserResponse] = None
    token: Optional[str] = None
