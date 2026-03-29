from sqlalchemy import String, Date, Integer, Numeric, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
import uuid


class DailyResult(Base):
    __tablename__ = "daily_results"
    __table_args__ = (UniqueConstraint("employee_id", "date"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    employee_id: Mapped[str] = mapped_column(String(36), ForeignKey("employees.id", ondelete="CASCADE"))
    date: Mapped[object] = mapped_column(Date)
    deals_closed: Mapped[int] = mapped_column(Integer, default=0)
    loan_volume: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    additional_products: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[object] = mapped_column(DateTime, server_default=func.now())

    employee: Mapped[object] = relationship("Employee", back_populates="daily_results")
