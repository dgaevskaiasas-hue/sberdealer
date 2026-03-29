from sqlalchemy import String, Integer, Boolean, Numeric, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class LearningModule(Base):
    __tablename__ = "learning_modules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(nullable=True)
    icon: Mapped[str] = mapped_column(String(50), default="book.fill")
    module_type: Mapped[str] = mapped_column(String(10))
    duration_minutes: Mapped[int] = mapped_column(Integer, default=15)
    points: Mapped[int] = mapped_column(Integer, default=50)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_locked_default: Mapped[bool] = mapped_column(Boolean, default=False)
    content: Mapped[str | None] = mapped_column(nullable=True)


class UserModuleProgress(Base):
    __tablename__ = "user_module_progress"

    employee_id: Mapped[str] = mapped_column(String(36), ForeignKey("employees.id", ondelete="CASCADE"), primary_key=True)
    module_id: Mapped[str] = mapped_column(String(36), ForeignKey("learning_modules.id", ondelete="CASCADE"), primary_key=True)
    progress: Mapped[float] = mapped_column(Numeric(5, 4), default=0)
    completed_at: Mapped[object | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
