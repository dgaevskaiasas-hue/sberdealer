from sqlalchemy import String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
import uuid


class News(Base):
    __tablename__ = "news"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(300))
    summary: Mapped[str] = mapped_column(Text)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(20), default="company")
    published_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())


class NewsReadStatus(Base):
    __tablename__ = "news_read_status"

    employee_id: Mapped[str] = mapped_column(String(36), ForeignKey("employees.id", ondelete="CASCADE"), primary_key=True)
    news_id: Mapped[str] = mapped_column(String(36), ForeignKey("news.id", ondelete="CASCADE"), primary_key=True)
    read_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())
