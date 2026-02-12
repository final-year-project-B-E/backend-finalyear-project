from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


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
