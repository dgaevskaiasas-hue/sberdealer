"""
Admin endpoints for managing news.
In production these should be protected by an admin token.
For MVP — open to any authenticated user.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
from pydantic import BaseModel, field_serializer
import uuid

from app.core.database import get_db
from app.core.deps import get_current_employee
from app.models.employee import Employee
from app.models.news import News
from app.schemas.news import NewsOut as PublicNewsOut

router = APIRouter(prefix="/api/v1/admin/news", tags=["admin-news"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class NewsCreate(BaseModel):
    title: str
    summary: str
    body: Optional[str] = None
    image_url: Optional[str] = None
    category: str = "company"    # program | promo | company | tip
    published_at: Optional[datetime] = None


class NewsUpdate(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    body: Optional[str] = None
    image_url: Optional[str] = None
    category: Optional[str] = None


class NewsOut(BaseModel):
    id: str
    title: str
    summary: str
    body: Optional[str]
    image_url: Optional[str]
    category: str
    published_at: datetime

    @field_serializer("published_at")
    def serialize_dt(self, dt: datetime) -> str:
        from datetime import timezone
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


# ── POST /admin/news ──────────────────────────────────────────────────────────

@router.post("", response_model=NewsOut, status_code=201, summary="Создать новость")
async def create_news(
    body: NewsCreate,
    _: Employee = Depends(get_current_employee),   # любой авторизованный
    db: AsyncSession = Depends(get_db),
):
    news = News(
        id=str(uuid.uuid4()),
        title=body.title.strip(),
        summary=body.summary.strip(),
        body=body.body,
        image_url=body.image_url,
        category=body.category,
        published_at=body.published_at or datetime.now(timezone.utc),
    )
    db.add(news)
    await db.commit()
    await db.refresh(news)
    return NewsOut(
        id=news.id,
        title=news.title,
        summary=news.summary,
        body=news.body,
        image_url=news.image_url,
        category=news.category,
        published_at=news.published_at,
    )


# ── PATCH /admin/news/{id} ────────────────────────────────────────────────────

@router.patch("/{news_id}", response_model=NewsOut, summary="Обновить новость")
async def update_news(
    news_id: str,
    body: NewsUpdate,
    _: Employee = Depends(get_current_employee),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(News).where(News.id == news_id))
    news = result.scalar_one_or_none()
    if not news:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Новость не найдена"})

    if body.title is not None:     news.title = body.title.strip()
    if body.summary is not None:   news.summary = body.summary.strip()
    if body.body is not None:      news.body = body.body
    if body.image_url is not None: news.image_url = body.image_url
    if body.category is not None:  news.category = body.category

    await db.commit()
    await db.refresh(news)
    return NewsOut(
        id=news.id, title=news.title, summary=news.summary,
        body=news.body, image_url=news.image_url,
        category=news.category, published_at=news.published_at,
    )


# ── DELETE /admin/news/{id} ───────────────────────────────────────────────────

@router.delete("/{news_id}", status_code=204, summary="Удалить новость")
async def delete_news(
    news_id: str,
    _: Employee = Depends(get_current_employee),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(News).where(News.id == news_id))
    news = result.scalar_one_or_none()
    if not news:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Новость не найдена"})
    await db.delete(news)
    await db.commit()
