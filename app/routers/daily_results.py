from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from datetime import date, timedelta
import uuid

from app.core.database import get_db
from app.core.deps import get_current_employee
from app.models.employee import Employee
from app.models.daily_result import DailyResult
from app.models.monthly_task import MonthlyTask
from app.models.rating_plan import RatingPlan
from app.schemas.daily_result import DailyResultCreate, DailyResultOut
from app.services.rating import month_start

router = APIRouter(prefix="/api/v1", tags=["daily-results"])


@router.get("/daily-results", response_model=list[DailyResultOut])
async def get_daily_results(
    month: str = Query(None, description="YYYY-MM"),
    employee: Employee = Depends(get_current_employee),
    db: AsyncSession = Depends(get_db),
):
    today = date.today()
    if month:
        try:
            year, m = map(int, month.split("-"))
            start = date(year, m, 1)
            end = date(year, m, 28) + timedelta(days=4)
            end = end.replace(day=1) - timedelta(days=1)
        except Exception:
            raise HTTPException(status_code=400, detail={"code": "VALIDATION_ERROR", "message": "Invalid month format, use YYYY-MM"})
    else:
        start = month_start(today)
        end = today

    result = await db.execute(
        select(DailyResult).where(
            and_(
                DailyResult.employee_id == employee.id,
                DailyResult.date >= start,
                DailyResult.date <= end,
            )
        ).order_by(DailyResult.date.desc())
    )
    rows = result.scalars().all()
    return [
        DailyResultOut(
            id=r.id,
            date=r.date,
            deals_closed=r.deals_closed,
            loan_volume=float(r.loan_volume),
            additional_products=r.additional_products,
        )
        for r in rows
    ]


@router.post("/daily-results", response_model=DailyResultOut, status_code=201)
async def create_daily_result(
    body: DailyResultCreate,
    employee: Employee = Depends(get_current_employee),
    db: AsyncSession = Depends(get_db),
):
    today = date.today()

    # Validate date
    if body.date > today:
        raise HTTPException(status_code=400, detail={"code": "VALIDATION_ERROR", "message": "Date cannot be in the future", "field": "date"})
    if (today - body.date).days > 7:
        raise HTTPException(status_code=400, detail={"code": "VALIDATION_ERROR", "message": "Date cannot be older than 7 days", "field": "date"})

    # UPSERT
    existing = await db.execute(
        select(DailyResult).where(
            and_(DailyResult.employee_id == employee.id, DailyResult.date == body.date)
        )
    )
    record = existing.scalar_one_or_none()

    if record:
        record.deals_closed = body.deals_closed
        record.loan_volume = body.loan_volume
        record.additional_products = body.additional_products
    else:
        record = DailyResult(
            id=str(uuid.uuid4()),
            employee_id=employee.id,
            date=body.date,
            deals_closed=body.deals_closed,
            loan_volume=body.loan_volume,
            additional_products=body.additional_products,
        )
        db.add(record)

    await db.flush()

    # Recalculate monthly tasks current values
    month_start_date = month_start(body.date)
    month_end = date(month_start_date.year + (month_start_date.month // 12),
                     ((month_start_date.month % 12) + 1), 1) - timedelta(days=1)

    agg = await db.execute(
        select(
            func.coalesce(func.sum(DailyResult.loan_volume), 0).label("total_volume"),
            func.coalesce(func.sum(DailyResult.deals_closed), 0).label("total_deals"),
        ).where(
            and_(
                DailyResult.employee_id == employee.id,
                DailyResult.date >= month_start_date,
                DailyResult.date <= month_end,
            )
        )
    )
    agg_row = agg.one()

    # Update monthly tasks
    tasks_result = await db.execute(
        select(MonthlyTask).where(
            and_(MonthlyTask.employee_id == employee.id, MonthlyTask.month == month_start_date)
        )
    )
    tasks = tasks_result.scalars().all()
    for task in tasks:
        if task.category == "sales":
            task.current = float(agg_row.total_deals)

    await db.commit()

    return DailyResultOut(
        id=record.id,
        date=record.date,
        deals_closed=record.deals_closed,
        loan_volume=float(record.loan_volume),
        additional_products=record.additional_products,
    )
