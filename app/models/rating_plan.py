from sqlalchemy import Integer, String, Date, Numeric, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class RatingPlan(Base):
    __tablename__ = "rating_plans"
    __table_args__ = (UniqueConstraint("employee_id", "month"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[str] = mapped_column(String(36), ForeignKey("employees.id", ondelete="CASCADE"))
    month: Mapped[object] = mapped_column(Date)
    volume_plan: Mapped[float] = mapped_column(Numeric(10, 2), default=10.0)
    deals_plan: Mapped[int] = mapped_column(Integer, default=10)
    bank_share_target: Mapped[float] = mapped_column(Numeric(5, 2), default=50.0)
    volume_max_index: Mapped[int] = mapped_column(Integer, default=120)
    bank_share_actual: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    conversion_actual: Mapped[float] = mapped_column(Numeric(5, 2), default=0)

    employee: Mapped[object] = relationship("Employee", back_populates="rating_plans")
