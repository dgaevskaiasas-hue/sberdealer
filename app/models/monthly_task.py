from sqlalchemy import String, Date, Integer, Numeric, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
import uuid


class MonthlyTask(Base):
    __tablename__ = "monthly_tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    employee_id: Mapped[str] = mapped_column(String(36), ForeignKey("employees.id", ondelete="CASCADE"))
    month: Mapped[object] = mapped_column(Date)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    target: Mapped[float] = mapped_column(Numeric(10, 2))
    current: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    unit: Mapped[str] = mapped_column(String(20), default="шт.")
    category: Mapped[str] = mapped_column(String(20), default="sales")
    deadline: Mapped[object | None] = mapped_column(Date, nullable=True)
    reward_points: Mapped[int] = mapped_column(Integer, default=10)

    employee: Mapped[object] = relationship("Employee", back_populates="monthly_tasks")
