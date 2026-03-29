from pydantic import BaseModel, field_serializer
from datetime import datetime, timezone
from typing import Optional


class NewsOut(BaseModel):
    id: str
    title: str
    summary: str
    body: Optional[str] = None
    image_url: Optional[str] = None
    category: str
    published_at: datetime
    is_read: bool

    model_config = {"from_attributes": True}

    @field_serializer("published_at")
    def serialize_dt(self, dt: datetime) -> str:
        """Always return ISO 8601 with Z so iOS can parse it."""
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
