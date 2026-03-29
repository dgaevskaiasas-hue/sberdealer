"""
Seed learning modules catalog.
Run: cd backend && venv/bin/python seed/seed_learning.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.models.learning import LearningModule

engine = create_async_engine(settings.DATABASE_URL, echo=False)
Session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

MODULES = [
    {"id": "lm-01", "title": "Основы продаж",               "description": "Базовые техники работы с клиентами",               "icon": "book.fill",            "module_type": "lesson", "duration_minutes": 15, "points": 50,  "sort_order": 1,  "is_locked_default": False},
    {"id": "lm-02", "title": "Работа с возражениями",        "description": "Как отвечать на типичные вопросы клиентов",         "icon": "play.rectangle.fill",  "module_type": "video",  "duration_minutes": 12, "points": 40,  "sort_order": 2,  "is_locked_default": False},
    {"id": "lm-03", "title": "Тест: Основы продаж",          "description": "Проверьте знания по модулю «Основы продаж»",        "icon": "checklist",            "module_type": "test",   "duration_minutes": 10, "points": 100, "sort_order": 3,  "is_locked_default": False},
    {"id": "lm-04", "title": "Кредитные продукты",           "description": "Обзор линейки кредитных предложений Сбера",         "icon": "book.fill",            "module_type": "lesson", "duration_minutes": 20, "points": 60,  "sort_order": 4,  "is_locked_default": False},
    {"id": "lm-05", "title": "Презентация автомобиля",       "description": "Эффективная демонстрация и тест-драйв",             "icon": "play.rectangle.fill",  "module_type": "video",  "duration_minutes": 18, "points": 45,  "sort_order": 5,  "is_locked_default": False},
    {"id": "lm-06", "title": "Тест: Кредитные продукты",     "description": "Проверка знаний по кредитным предложениям",        "icon": "checklist",            "module_type": "test",   "duration_minutes": 15, "points": 120, "sort_order": 6,  "is_locked_default": False},
    {"id": "lm-07", "title": "Страховые продукты",           "description": "КАСКО, ОСАГО и дополнительные программы",          "icon": "book.fill",            "module_type": "lesson", "duration_minutes": 25, "points": 70,  "sort_order": 7,  "is_locked_default": False},
    {"id": "lm-08", "title": "Мастер-класс: Закрытие сделки","description": "Продвинутые техники от лучших продавцов",          "icon": "play.rectangle.fill",  "module_type": "video",  "duration_minutes": 30, "points": 80,  "sort_order": 8,  "is_locked_default": True},
    {"id": "lm-09", "title": "Финальный тест",               "description": "Комплексная проверка по всем модулям",             "icon": "checklist",            "module_type": "test",   "duration_minutes": 25, "points": 200, "sort_order": 9,  "is_locked_default": True},
]

async def seed():
    async with Session() as db:
        existing = await db.execute(select(LearningModule).limit(1))
        if existing.scalar_one_or_none():
            print("Learning modules already seeded.")
            return

        for m in MODULES:
            db.add(LearningModule(**m))
        await db.commit()
        print(f"✅ Seeded {len(MODULES)} learning modules.")

if __name__ == "__main__":
    asyncio.run(seed())
