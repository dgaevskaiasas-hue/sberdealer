from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, and_
from datetime import datetime, timezone, date, timedelta
import uuid

scheduler = AsyncIOScheduler()


async def monthly_reset():
    """Create new rating_plans and monthly_tasks on the 1st of each month."""
    from app.core.database import AsyncSessionLocal
    from app.models.employee import Employee
    from app.models.rating_plan import RatingPlan
    from app.models.monthly_task import MonthlyTask

    async with AsyncSessionLocal() as db:
        today = date.today()
        month_start = today.replace(day=1)

        result = await db.execute(select(Employee))
        employees = result.scalars().all()

        for emp in employees:
            existing = await db.execute(
                select(RatingPlan).where(
                    and_(RatingPlan.employee_id == emp.id, RatingPlan.month == month_start)
                )
            )
            if not existing.scalar_one_or_none():
                db.add(RatingPlan(
                    employee_id=emp.id,
                    month=month_start,
                    volume_plan=10.0,
                    deals_plan=10,
                    bank_share_target=50.0,
                    volume_max_index=120,
                ))
                db.add(MonthlyTask(
                    id=str(uuid.uuid4()),
                    employee_id=emp.id,
                    month=month_start,
                    title="Закрыть 10 сделок",
                    target=10.0,
                    current=0,
                    unit="шт.",
                    category="sales",
                    deadline=date(today.year, today.month, 31) if today.month in [1,3,5,7,8,10,12] else date(today.year, today.month, 30),
                    reward_points=10,
                ))

        await db.commit()
        print(f"[Cron] Monthly reset done for {month_start}")


async def cleanup_tokens():
    """Delete expired refresh tokens daily."""
    from app.core.database import AsyncSessionLocal
    from app.models.refresh_token import RefreshToken

    async with AsyncSessionLocal() as db:
        await db.execute(
            delete(RefreshToken).where(RefreshToken.expires_at < datetime.now(timezone.utc))
        )
        await db.commit()
        print("[Cron] Expired tokens cleaned up")


def start_scheduler():
    scheduler.add_job(monthly_reset, CronTrigger(day=1, hour=0, minute=0), id="monthly_reset", replace_existing=True)
    scheduler.add_job(cleanup_tokens, CronTrigger(hour=3, minute=0), id="cleanup_tokens", replace_existing=True)
    scheduler.start()
    print("[Scheduler] Started")
