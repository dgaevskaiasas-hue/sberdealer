from sqlalchemy import String, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
import uuid


class Privilege(Base):
    __tablename__ = "privileges"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(20), default="other")
    available_from: Mapped[str] = mapped_column(String(10), default="silver")
    financial_effect: Mapped[int | None] = mapped_column(Integer, nullable=True)
    detail_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
