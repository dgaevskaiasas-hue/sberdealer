from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.deps import get_current_employee
from app.models.employee import Employee
from app.models.news import News, NewsReadStatus
from app.schemas.news import NewsOut

router = APIRouter(prefix="/api/v1", tags=["news"])


@router.get("/news", response_model=list[NewsOut])
async def get_news(
    employee: Employee = Depends(get_current_employee),
    db: AsyncSession = Depends(get_db),
):
    news_result = await db.execute(select(News).order_by(News.published_at.desc()))
    news_list = news_result.scalars().all()

    read_result = await db.execute(
        select(NewsReadStatus.news_id).where(NewsReadStatus.employee_id == employee.id)
    )
    read_ids = {row[0] for row in read_result.all()}

    return [
        NewsOut(
            id=n.id,
            title=n.title,
            summary=n.summary,
            body=n.body,
            image_url=n.image_url,
            category=n.category,
            published_at=n.published_at,
            is_read=n.id in read_ids,
        )
        for n in news_list
    ]


@router.post("/news/{news_id}/read", status_code=204)
async def mark_news_read(
    news_id: str,
    employee: Employee = Depends(get_current_employee),
    db: AsyncSession = Depends(get_db),
):
    news_result = await db.execute(select(News).where(News.id == news_id))
    news = news_result.scalar_one_or_none()
    if not news:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "News not found"})

    existing = await db.execute(
        select(NewsReadStatus).where(
            NewsReadStatus.employee_id == employee.id,
            NewsReadStatus.news_id == news_id,
        )
    )
    if not existing.scalar_one_or_none():
        db.add(NewsReadStatus(employee_id=employee.id, news_id=news_id))
        await db.commit()
