from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from datetime import date
import uuid

from app.core.database import get_db
from app.core.deps import get_current_employee
from app.models.employee import Employee
from app.models.support_message import SupportMessage
from app.models.personal_manager import PersonalManager
from app.models.daily_result import DailyResult
from app.models.rating_plan import RatingPlan
from app.schemas.support import SupportResponse, MessageOut, MessageCreate, GigaChatRequest, ManagerInfo
from app.services.gigachat import ask_gigachat
from app.services.rating import build_rating_components, calculate_total_points, get_level, month_start

router = APIRouter(prefix="/api/v1/support", tags=["support"])

DEFAULT_MANAGER = ManagerInfo(
    name="Елена Сидорова",
    position="Руководитель программы мотивации",
    avatar_url=None,
    phone="+7 (495) 123-45-67",
    email="e.sidorova@sber-dealer.ru",
)


@router.get("/messages", response_model=SupportResponse)
async def get_messages(
    employee: Employee = Depends(get_current_employee),
    db: AsyncSession = Depends(get_db),
):
    # Get personal manager or use default
    pm_result = await db.execute(
        select(PersonalManager).where(PersonalManager.employee_id == employee.id)
    )
    pm = pm_result.scalar_one_or_none()
    manager = ManagerInfo(
        name=pm.name,
        position=pm.position,
        avatar_url=pm.avatar_url,
        phone=pm.phone,
        email=pm.email,
    ) if pm else DEFAULT_MANAGER

    msgs_result = await db.execute(
        select(SupportMessage)
        .where(SupportMessage.employee_id == employee.id)
        .order_by(SupportMessage.timestamp.asc())
    )
    messages = msgs_result.scalars().all()
    return SupportResponse(
        manager=manager,
        messages=[MessageOut.model_validate(m) for m in messages],
    )


@router.post("/messages", response_model=MessageOut, status_code=201)
async def post_message(
    body: MessageCreate,
    employee: Employee = Depends(get_current_employee),
    db: AsyncSession = Depends(get_db),
):
    msg = SupportMessage(
        id=str(uuid.uuid4()),
        employee_id=employee.id,
        text=body.text,
        sender="employee",
        is_read=False,
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return MessageOut.model_validate(msg)


@router.post("/gigachat", response_model=MessageOut)
async def gigachat(
    body: GigaChatRequest,
    employee: Employee = Depends(get_current_employee),
    db: AsyncSession = Depends(get_db),
):
    today = date.today()
    ms = month_start(today)

    plan_result = await db.execute(
        select(RatingPlan).where(and_(RatingPlan.employee_id == employee.id, RatingPlan.month == ms))
    )
    plan = plan_result.scalar_one_or_none()

    agg = await db.execute(
        select(
            func.coalesce(func.sum(DailyResult.loan_volume), 0).label("v"),
            func.coalesce(func.sum(DailyResult.deals_closed), 0).label("d"),
        ).where(and_(DailyResult.employee_id == employee.id, DailyResult.date >= ms))
    )
    row = agg.one()

    components = build_rating_components(
        volume_fact=float(row.v),
        deals_fact=float(row.d),
        bank_share_fact=40.0,
        conversion_fact=45.0,
        volume_plan=float(plan.volume_plan) if plan else 10.0,
        deals_plan=float(plan.deals_plan) if plan else 10.0,
        bank_share_target=float(plan.bank_share_target) if plan else 50.0,
    )
    total_points = calculate_total_points(components)
    level = get_level(total_points)

    context = {
        "level": level,
        "total_points": total_points,
        "volume_fact": float(row.v),
        "volume_plan": float(plan.volume_plan) if plan else 10.0,
        "deals_fact": float(row.d),
        "deals_plan": float(plan.deals_plan) if plan else 10.0,
    }

    user_text = body.actual_text

    # Save employee question
    q_msg = SupportMessage(
        id=str(uuid.uuid4()),
        employee_id=employee.id,
        text=user_text,
        sender="employee",
        is_read=True,
    )
    db.add(q_msg)

    # Get AI answer
    answer_text = await ask_gigachat(user_text, context)

    # Save AI answer
    a_msg = SupportMessage(
        id=str(uuid.uuid4()),
        employee_id=employee.id,
        text=answer_text,
        sender="manager",
        is_read=False,
    )
    db.add(a_msg)
    await db.commit()
    await db.refresh(a_msg)
    return MessageOut.model_validate(a_msg)
