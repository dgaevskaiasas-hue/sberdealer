from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from datetime import date

from app.core.database import get_db
from app.core.deps import get_current_employee
from app.models.employee import Employee
from app.models.daily_result import DailyResult
from app.models.rating_plan import RatingPlan
from app.schemas.calculator import SimulateRequest, SimulateResponse
from app.services.rating import (
    build_rating_components,
    calculate_total_points,
    get_level,
    month_start,
    LEVEL_YEARLY_BONUS,
    INCOME_PER_DEAL,
)

router = APIRouter(prefix="/api/v1/calculator", tags=["calculator"])


@router.post("/simulate", response_model=SimulateResponse)
async def simulate(
    body: SimulateRequest,
    employee: Employee = Depends(get_current_employee),
    db: AsyncSession = Depends(get_db),
):
    today = date.today()
    ms = month_start(today)

    # Get current points
    plan_result = await db.execute(
        select(RatingPlan).where(and_(RatingPlan.employee_id == employee.id, RatingPlan.month == ms))
    )
    plan = plan_result.scalar_one_or_none()

    agg = await db.execute(
        select(
            func.coalesce(func.sum(DailyResult.loan_volume), 0).label("v"),
            func.coalesce(func.sum(DailyResult.deals_closed), 0).label("d"),
        ).where(and_(DailyResult.employee_id == employee.id, DailyResult.date >= ms, DailyResult.date <= today))
    )
    row = agg.one()

    current_components = build_rating_components(
        volume_fact=float(row.v),
        deals_fact=float(row.d),
        bank_share_fact=40.0,
        conversion_fact=45.0,
        volume_plan=float(plan.volume_plan) if plan else 10.0,
        deals_plan=float(plan.deals_plan) if plan else 10.0,
        bank_share_target=float(plan.bank_share_target) if plan else 50.0,
        volume_max_index=plan.volume_max_index if plan else 120,
    )
    current_points = calculate_total_points(current_components)
    current_level = get_level(current_points)

    # Simulate projected
    projected_components = build_rating_components(
        volume_fact=body.volume_fact,
        deals_fact=float(body.deals_fact),
        bank_share_fact=body.bank_share_fact,
        conversion_fact=body.conversion_fact,
        volume_plan=body.volume_plan,
        deals_plan=float(body.deals_plan),
        bank_share_target=body.bank_share_target,
        volume_max_index=plan.volume_max_index if plan else 120,
    )
    projected_points = calculate_total_points(projected_components)
    projected_level = get_level(projected_points)

    current_yearly = int(float(row.d) * INCOME_PER_DEAL) + LEVEL_YEARLY_BONUS[current_level]
    projected_yearly = int(body.deals_fact * INCOME_PER_DEAL) + LEVEL_YEARLY_BONUS[projected_level]

    return SimulateResponse(
        projected_points=projected_points,
        projected_level=projected_level,
        points_delta=projected_points - current_points,
        level_changed=projected_level != current_level,
        projected_yearly_income=projected_yearly,
        yearly_income_delta=projected_yearly - current_yearly,
    )
