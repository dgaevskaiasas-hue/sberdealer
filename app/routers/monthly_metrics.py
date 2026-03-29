from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import date
from pydantic import BaseModel, field_validator

from app.core.database import get_db
from app.core.deps import get_current_employee
from app.models.employee import Employee
from app.models.rating_plan import RatingPlan
from app.models.monthly_task import MonthlyTask
from app.services.rating import month_start

router = APIRouter(prefix="/api/v1", tags=["monthly-metrics"])


class MonthlyMetricsUpdate(BaseModel):
    bank_share_actual: float | None = None   # % сделок с банковским финансированием
    conversion_actual: float | None = None   # % конверсии заявок

    @field_validator("bank_share_actual")
    @classmethod
    def validate_bank_share(cls, v: float | None) -> float | None:
        if v is not None and not (0 <= v <= 100):
            raise HTTPException(status_code=400, detail={"code": "VALIDATION_ERROR", "message": "bank_share_actual must be 0–100"})
        return v

    @field_validator("conversion_actual")
    @classmethod
    def validate_conversion(cls, v: float | None) -> float | None:
        if v is not None and not (0 <= v <= 100):
            raise HTTPException(status_code=400, detail={"code": "VALIDATION_ERROR", "message": "conversion_actual must be 0–100"})
        return v


class MonthlyMetricsOut(BaseModel):
    bank_share_actual: float
    bank_share_target: float
    conversion_actual: float
    month: date


@router.get("/monthly-metrics", response_model=MonthlyMetricsOut)
async def get_monthly_metrics(
    employee: Employee = Depends(get_current_employee),
    db: AsyncSession = Depends(get_db),
):
    ms = month_start(date.today())
    result = await db.execute(
        select(RatingPlan).where(
            and_(RatingPlan.employee_id == employee.id, RatingPlan.month == ms)
        )
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "No rating plan for current month"})

    return MonthlyMetricsOut(
        bank_share_actual=float(plan.bank_share_actual),
        bank_share_target=float(plan.bank_share_target),
        conversion_actual=float(plan.conversion_actual),
        month=plan.month,
    )


@router.patch("/monthly-metrics", response_model=MonthlyMetricsOut)
async def update_monthly_metrics(
    body: MonthlyMetricsUpdate,
    employee: Employee = Depends(get_current_employee),
    db: AsyncSession = Depends(get_db),
):
    """
    Пользователь вносит свои KPI вручную:
    - Доля банка (% сделок с финансированием Сбера)
    - Конверсия заявок (% одобренных заявок)
    """
    ms = month_start(date.today())
    result = await db.execute(
        select(RatingPlan).where(
            and_(RatingPlan.employee_id == employee.id, RatingPlan.month == ms)
        )
    )
    plan = result.scalar_one_or_none()
    if not plan:
        # Auto-create plan if missing
        plan = RatingPlan(employee_id=employee.id, month=ms)
        db.add(plan)
        await db.flush()

    if body.bank_share_actual is not None:
        plan.bank_share_actual = body.bank_share_actual
        # Sync monthly task if exists
        task_result = await db.execute(
            select(MonthlyTask).where(
                and_(
                    MonthlyTask.employee_id == employee.id,
                    MonthlyTask.month == ms,
                    MonthlyTask.category == "calls",  # bank_share stored as 'calls' category
                )
            )
        )
        task = task_result.scalar_one_or_none()
        if task:
            task.current = body.bank_share_actual

    if body.conversion_actual is not None:
        plan.conversion_actual = body.conversion_actual
        task_result = await db.execute(
            select(MonthlyTask).where(
                and_(
                    MonthlyTask.employee_id == employee.id,
                    MonthlyTask.month == ms,
                    MonthlyTask.category == "clients",  # conversion stored as 'clients' category
                )
            )
        )
        task = task_result.scalar_one_or_none()
        if task:
            task.current = body.conversion_actual

    await db.commit()

    return MonthlyMetricsOut(
        bank_share_actual=float(plan.bank_share_actual),
        bank_share_target=float(plan.bank_share_target),
        conversion_actual=float(plan.conversion_actual),
        month=plan.month,
    )
