from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, field_serializer

from app.core.database import get_db
from app.core.deps import get_current_employee
from app.models.employee import Employee
from app.models.learning import LearningModule, UserModuleProgress

router = APIRouter(prefix="/api/v1/learning", tags=["learning"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class LearningModuleOut(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    icon: str
    module_type: str
    duration_minutes: int
    points: int
    sort_order: int
    is_locked: bool
    content: Optional[str] = None
    progress: float
    is_completed: bool
    completed_at: Optional[datetime] = None

    @field_serializer("completed_at")
    def serialize_dt(self, dt: Optional[datetime]) -> Optional[str]:
        if dt is None:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


class ProgressUpdate(BaseModel):
    progress: float            # 0.0 – 1.0

    def model_post_init(self, _):
        if not 0.0 <= self.progress <= 1.0:
            raise ValueError("progress must be between 0.0 and 1.0")


# ── GET /learning/modules ─────────────────────────────────────────────────────

@router.get("/modules", response_model=list[LearningModuleOut])
async def get_modules(
    employee: Employee = Depends(get_current_employee),
    db: AsyncSession = Depends(get_db),
):
    modules_result = await db.execute(
        select(LearningModule).order_by(LearningModule.sort_order)
    )
    modules = modules_result.scalars().all()

    progress_result = await db.execute(
        select(UserModuleProgress).where(UserModuleProgress.employee_id == employee.id)
    )
    progress_map = {p.module_id: p for p in progress_result.scalars().all()}

    return [
        LearningModuleOut(
            id=m.id,
            title=m.title,
            description=m.description,
            icon=m.icon,
            module_type=m.module_type,
            duration_minutes=m.duration_minutes,
            points=m.points,
            sort_order=m.sort_order,
            is_locked=m.is_locked_default,
            content=m.content,
            progress=float(progress_map[m.id].progress) if m.id in progress_map else 0.0,
            is_completed=m.id in progress_map and float(progress_map[m.id].progress) >= 1.0,
            completed_at=progress_map[m.id].completed_at if m.id in progress_map else None,
        )
        for m in modules
    ]


# ── PATCH /learning/modules/{id}/progress ────────────────────────────────────

@router.patch("/modules/{module_id}/progress", response_model=LearningModuleOut)
async def update_progress(
    module_id: str,
    body: ProgressUpdate,
    employee: Employee = Depends(get_current_employee),
    db: AsyncSession = Depends(get_db),
):
    module_result = await db.execute(
        select(LearningModule).where(LearningModule.id == module_id)
    )
    module = module_result.scalar_one_or_none()
    if not module:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Module not found"})

    progress_result = await db.execute(
        select(UserModuleProgress).where(
            UserModuleProgress.employee_id == employee.id,
            UserModuleProgress.module_id == module_id,
        )
    )
    record = progress_result.scalar_one_or_none()

    now = datetime.now(timezone.utc)
    if record:
        record.progress = body.progress
        record.updated_at = now
        if body.progress >= 1.0 and record.completed_at is None:
            record.completed_at = now
        elif body.progress < 1.0:
            record.completed_at = None
    else:
        record = UserModuleProgress(
            employee_id=employee.id,
            module_id=module_id,
            progress=body.progress,
            completed_at=now if body.progress >= 1.0 else None,
            updated_at=now,
        )
        db.add(record)

    await db.commit()

    return LearningModuleOut(
        id=module.id,
        title=module.title,
        description=module.description,
        icon=module.icon,
        module_type=module.module_type,
        duration_minutes=module.duration_minutes,
        points=module.points,
        sort_order=module.sort_order,
        is_locked=module.is_locked_default,
        content=module.content,
        progress=float(record.progress),
        is_completed=float(record.progress) >= 1.0,
        completed_at=record.completed_at,
    )
