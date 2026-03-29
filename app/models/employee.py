from sqlalchemy import String, Date, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
import uuid


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    position: Mapped[str] = mapped_column(String(200))
    dealership: Mapped[str] = mapped_column(String(200))
    dealership_code: Mapped[str] = mapped_column(String(20))
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(nullable=True)
    program_join_date: Mapped[object] = mapped_column(Date)
    region: Mapped[str] = mapped_column(String(100), default="Москва")
    employee_code: Mapped[str] = mapped_column(String(50), unique=True)
    password_hash: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[object] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[object] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    daily_results: Mapped[list] = relationship("DailyResult", back_populates="employee", lazy="select")
    rating_plans: Mapped[list] = relationship("RatingPlan", back_populates="employee", lazy="select")
    monthly_tasks: Mapped[list] = relationship("MonthlyTask", back_populates="employee", lazy="select")
    support_messages: Mapped[list] = relationship("SupportMessage", back_populates="employee", lazy="select")
    personal_manager: Mapped[object] = relationship("PersonalManager", back_populates="employee", uselist=False, lazy="select")
