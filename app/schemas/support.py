from pydantic import BaseModel, field_serializer
from datetime import datetime, timezone
from typing import Optional


class ManagerInfo(BaseModel):
    name: str
    position: str
    avatar_url: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None


class MessageOut(BaseModel):
    id: str
    text: str
    sender: str
    timestamp: datetime
    is_read: bool

    model_config = {"from_attributes": True}

    @field_serializer("timestamp")
    def serialize_dt(self, dt: datetime) -> str:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


class SupportResponse(BaseModel):
    manager: ManagerInfo
    messages: list[MessageOut]


class MessageCreate(BaseModel):
    text: str


class GigaChatRequest(BaseModel):
    text: Optional[str] = None
    message: Optional[str] = None

    @property
    def actual_text(self) -> str:
        return self.text or self.message or ""
