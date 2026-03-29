from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import date

from app.core.database import get_db
from app.core.deps import get_current_employee
from app.models.employee import Employee
from app.models.rating_plan import RatingPlan
from app.models.daily_result import DailyResult
from app.models.monthly_task import MonthlyTask
from app.models.privilege import Privilege
from app.schemas.dashboard import DashboardResponse
from app.services.rating import (
    build_rating_components,
    calculate_total_points,
    calculate_financial_benefit,
    get_level,
    month_start,
)

router = APIRouter(prefix="/api/v1", tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    employee: Employee = Depends(get_current_employee),
    db: AsyncSession = Depends(get_db),
):
    today = date.today()
    month_start_date = month_start(today)
    month_end = today

    # Load rating plan for current month
    plan_result = await db.execute(
        select(RatingPlan).where(
            and_(RatingPlan.employee_id == employee.id, RatingPlan.month == month_start_date)
        )
    )
    plan = plan_result.scalar_one_or_none()

    volume_plan = float(plan.volume_plan) if plan else 10.0
    deals_plan = float(plan.deals_plan) if plan else 10.0
    bank_share_target = float(plan.bank_share_target) if plan else 50.0
    volume_max_index = plan.volume_max_index if plan else 120

    # Aggregate daily_results for current month
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
    volume_fact = float(agg_row.total_volume)
    deals_fact = float(agg_row.total_deals)

    # bank_share and conversion come from user's own monthly plan (user updates via PATCH /monthly-metrics)
    bank_share_fact = float(plan.bank_share_actual) if plan else 0.0
    conversion_fact = float(plan.conversion_actual) if plan else 0.0

    rating_components = build_rating_components(
        volume_fact=volume_fact,
        deals_fact=deals_fact,
        bank_share_fact=bank_share_fact,
        conversion_fact=conversion_fact,
        volume_plan=volume_plan,
        deals_plan=deals_plan,
        bank_share_target=bank_share_target,
        volume_max_index=volume_max_index,
    )
    total_points = calculate_total_points(rating_components)
    level = get_level(total_points)

    # Monthly tasks
    tasks_result = await db.execute(
        select(MonthlyTask).where(
            and_(MonthlyTask.employee_id == employee.id, MonthlyTask.month == month_start_date)
        )
    )
    tasks = tasks_result.scalars().all()

    # Financial benefit
    fin = calculate_financial_benefit(deals_fact, deals_plan, total_points)

    # Privileges
    privs_result = await db.execute(select(Privilege).order_by(Privilege.sort_order))
    privileges = privs_result.scalars().all()

    return DashboardResponse(
        employee={
            "id": employee.id,
            "first_name": employee.first_name,
            "last_name": employee.last_name,
            "position": employee.position,
            "dealership": employee.dealership,
            "dealership_code": employee.dealership_code,
            "phone": employee.phone,
            "email": employee.email,
            "avatar_url": employee.avatar_url,
            "level": level,
            "total_points": total_points,
            "rating_components": rating_components,
            "month_start_date": month_start_date,
            "program_join_date": employee.program_join_date,
        },
        monthly_tasks=[
            {
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "target": float(t.target),
                "current": float(t.current),
                "unit": t.unit,
                "category": t.category,
                "deadline": t.deadline,
                "reward_points": t.reward_points,
            }
            for t in tasks
        ],
        financial_benefit=fin,
        privileges=[
            {
                "id": p.id,
                "title": p.title,
                "description": p.description,
                "category": p.category,
                "available_from": p.available_from,
                "financial_effect": p.financial_effect,
                "detail_text": p.detail_text,
            }
            for p in privileges
        ],
    )
