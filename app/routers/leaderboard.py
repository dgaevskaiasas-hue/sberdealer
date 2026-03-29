from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from datetime import date

from app.core.database import get_db
from app.core.deps import get_current_employee
from app.models.employee import Employee
from app.models.daily_result import DailyResult
from app.models.rating_plan import RatingPlan
from app.schemas.leaderboard import LeaderboardEntry
from app.services.rating import build_rating_components, calculate_total_points, get_level, month_start

router = APIRouter(prefix="/api/v1", tags=["leaderboard"])


async def _calc_points_for_employee(emp_id: str, db: AsyncSession, today: date) -> int:
    ms = month_start(today)
    plan_result = await db.execute(
        select(RatingPlan).where(and_(RatingPlan.employee_id == emp_id, RatingPlan.month == ms))
    )
    plan = plan_result.scalar_one_or_none()

    agg = await db.execute(
        select(
            func.coalesce(func.sum(DailyResult.loan_volume), 0).label("total_volume"),
            func.coalesce(func.sum(DailyResult.deals_closed), 0).label("total_deals"),
        ).where(
            and_(DailyResult.employee_id == emp_id, DailyResult.date >= ms, DailyResult.date <= today)
        )
    )
    row = agg.one()

    components = build_rating_components(
        volume_fact=float(row.total_volume),
        deals_fact=float(row.total_deals),
        bank_share_fact=40.0,
        conversion_fact=45.0,
        volume_plan=float(plan.volume_plan) if plan else 10.0,
        deals_plan=float(plan.deals_plan) if plan else 10.0,
        bank_share_target=float(plan.bank_share_target) if plan else 50.0,
        volume_max_index=plan.volume_max_index if plan else 120,
    )
    return calculate_total_points(components)


@router.get("/leaderboard", response_model=list[LeaderboardEntry])
async def get_leaderboard(
    scope: str = Query("dealership", description="dealership | region | national"),
    employee: Employee = Depends(get_current_employee),
    db: AsyncSession = Depends(get_db),
):
    # Filter employees by scope
    query = select(Employee)
    if scope == "dealership":
        query = query.where(Employee.dealership_code == employee.dealership_code)
    elif scope == "region":
        query = query.where(Employee.region == employee.region)
    # national = all

    result = await db.execute(query)
    employees = result.scalars().all()

    today = date.today()
    scored = []
    for emp in employees:
        pts = await _calc_points_for_employee(emp.id, db, today)
        scored.append((emp, pts))

    scored.sort(key=lambda x: x[1], reverse=True)

    entries = []
    current_in_top = False
    for rank, (emp, pts) in enumerate(scored[:50], start=1):
        is_current = emp.id == employee.id
        if is_current:
            current_in_top = True
        entries.append(LeaderboardEntry(
            id=f"entry-{rank}",
            rank=rank,
            employee_name=f"{emp.first_name} {emp.last_name}",
            dealership=emp.dealership,
            level=get_level(pts),
            total_points=pts,
            avatar_url=emp.avatar_url,
            is_current_user=is_current,
        ))

    # Append current user if not in top-50
    if not current_in_top:
        full_rank = next((i + 1 for i, (e, _) in enumerate(scored) if e.id == employee.id), len(scored))
        pts = next((p for e, p in scored if e.id == employee.id), 0)
        entries.append(LeaderboardEntry(
            id=f"entry-{full_rank}",
            rank=full_rank,
            employee_name=f"{employee.first_name} {employee.last_name}",
            dealership=employee.dealership,
            level=get_level(pts),
            total_points=pts,
            avatar_url=employee.avatar_url,
            is_current_user=True,
        ))

    return entries
