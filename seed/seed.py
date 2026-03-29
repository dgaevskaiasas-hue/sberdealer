"""
Seed script: populates the database with test data.
Run: cd backend && venv/bin/python seed/seed.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import asyncio
from datetime import date, timedelta, datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select, text
import uuid

from app.core.config import settings
from app.core.security import hash_password
from app.models.employee import Employee
from app.models.rating_plan import RatingPlan
from app.models.daily_result import DailyResult
from app.models.monthly_task import MonthlyTask
from app.models.privilege import Privilege
from app.models.support_message import SupportMessage
from app.models.personal_manager import PersonalManager
from app.models.news import News

engine = create_async_engine(settings.DATABASE_URL, echo=False)
Session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

TODAY = date.today()
MONTH_START = TODAY.replace(day=1)


EMPLOYEES = [
    {"id": "emp-001", "first_name": "Алексей",  "last_name": "Петров",   "code": "DC-MSK-042-001", "password": "petrov123",   "phone": "+79165551001", "dealership_code": "DC-MSK-042", "dealership": "АвтоЦентр Сбер Москва",   "region": "Москва",          "position": "Старший менеджер по продажам"},
    {"id": "emp-002", "first_name": "Мария",     "last_name": "Иванова",  "code": "DC-MSK-042-002", "password": "ivanova123",  "phone": "+79165551002", "dealership_code": "DC-MSK-042", "dealership": "АвтоЦентр Сбер Москва",   "region": "Москва",          "position": "Менеджер по продажам"},
    {"id": "emp-003", "first_name": "Дмитрий",   "last_name": "Козлов",   "code": "DC-MSK-042-003", "password": "kozlov123",   "phone": "+79165551003", "dealership_code": "DC-MSK-042", "dealership": "АвтоЦентр Сбер Москва",   "region": "Москва",          "position": "Менеджер по продажам"},
    {"id": "emp-004", "first_name": "Елена",     "last_name": "Сидорова", "code": "DC-MSK-042-004", "password": "sidorova123", "phone": "+79165551004", "dealership_code": "DC-MSK-042", "dealership": "АвтоЦентр Сбер Москва",   "region": "Москва",          "position": "Специалист по кредитованию"},
    {"id": "emp-005", "first_name": "Артём",     "last_name": "Волков",   "code": "DC-MSK-042-005", "password": "volkov123",   "phone": "+79165551005", "dealership_code": "DC-MSK-042", "dealership": "АвтоЦентр Сбер Москва",   "region": "Москва",          "position": "Менеджер по продажам"},
    {"id": "emp-006", "first_name": "Игорь",     "last_name": "Белов",    "code": "DC-MSK-015-001", "password": "belov123",    "phone": "+79165551006", "dealership_code": "DC-MSK-015", "dealership": "СберАвто Химки",           "region": "Москва",          "position": "Руководитель отдела"},
    {"id": "emp-007", "first_name": "Павел",     "last_name": "Горин",    "code": "DC-MSK-015-002", "password": "gorin123",    "phone": "+79165551007", "dealership_code": "DC-MSK-015", "dealership": "СберАвто Химки",           "region": "Москва",          "position": "Старший менеджер"},
    {"id": "emp-008", "first_name": "Анна",      "last_name": "Морозова", "code": "DC-SPB-003-001", "password": "morozova123", "phone": "+79165551008", "dealership_code": "DC-SPB-003", "dealership": "СберАвто Санкт-Петербург", "region": "Санкт-Петербург", "position": "Менеджер по продажам"},
    {"id": "emp-009", "first_name": "Сергей",    "last_name": "Новиков",  "code": "DC-SPB-003-002", "password": "novikov123",  "phone": "+79165551009", "dealership_code": "DC-SPB-003", "dealership": "СберАвто Санкт-Петербург", "region": "Санкт-Петербург", "position": "Менеджер по продажам"},
    {"id": "emp-010", "first_name": "Ольга",     "last_name": "Лебедева", "code": "DC-NSK-001-001", "password": "lebedeva123", "phone": "+79165551010", "dealership_code": "DC-NSK-001", "dealership": "СберАвто Новосибирск",    "region": "Новосибирск",     "position": "Специалист по кредитованию"},
]

# daily results to produce the target points per spec
DAILY_RESULTS_CONFIG = {
    "emp-001": {"volume": 6.0,  "deals": 7},   # 65 pts silver
    "emp-002": {"volume": 14.0, "deals": 13},  # 93 pts black
    "emp-003": {"volume": 10.5, "deals": 11},  # 82 pts gold
    "emp-004": {"volume": 4.5,  "deals": 6},   # 58 pts silver
    "emp-005": {"volume": 3.0,  "deals": 4},   # 45 pts silver
    "emp-006": {"volume": 15.5, "deals": 14},  # 96 pts black
    "emp-007": {"volume": 11.0, "deals": 12},  # 85 pts gold
    "emp-008": {"volume": 8.5,  "deals": 10},  # 77 pts gold
    "emp-009": {"volume": 7.5,  "deals": 9},   # 71 pts gold
    "emp-010": {"volume": 5.5,  "deals": 7},   # 62 pts silver
}

PRIVILEGES = [
    {"id": "p-1", "title": "Базовая комиссия +5%",      "description": "Повышенная ставка с каждой продажи",        "category": "commission", "available_from": "silver", "financial_effect": 37500,  "detail_text": "Базовая ставка комиссии повышается на 5% от суммы каждой закрытой сделки. Применяется автоматически с первого дня программы.", "sort_order": 1},
    {"id": "p-2", "title": "Приоритетный график",        "description": "Выбор удобной смены",                       "category": "schedule",   "available_from": "silver", "financial_effect": None,   "detail_text": "Возможность выбирать рабочие смены в приоритетном порядке перед другими сотрудниками.", "sort_order": 2},
    {"id": "p-3", "title": "Комиссия +10%",              "description": "Увеличенная ставка для уровня Золото",       "category": "commission", "available_from": "gold",   "financial_effect": 75000,  "detail_text": "Ставка комиссии повышается на 10% от суммы каждой закрытой сделки.", "sort_order": 3},
    {"id": "p-4", "title": "Премиальные лиды",           "description": "Приоритетная передача горячих лидов",       "category": "leads",      "available_from": "gold",   "financial_effect": 20000,  "detail_text": "Вы получаете первоочередный доступ к лидам с высоким потенциалом конверсии.", "sort_order": 4},
    {"id": "p-5", "title": "Гибкий график",              "description": "Возможность работать удалённо",              "category": "schedule",   "available_from": "gold",   "financial_effect": None,   "detail_text": "Частичная возможность работать из дома или выбирать нестандартный график.", "sort_order": 5},
    {"id": "p-6", "title": "Комиссия +15%",              "description": "Максимальная ставка уровня Black",        "category": "commission", "available_from": "black",  "financial_effect": 112500, "detail_text": "Максимальная ставка комиссии +15% от суммы каждой сделки.", "sort_order": 6},
    {"id": "p-7", "title": "Годовой бонус",              "description": "Ежегодная премия за уровень Platinum",       "category": "bonus",      "available_from": "black",  "financial_effect": 200000, "detail_text": "Ежегодная денежная премия за удержание уровня Black в течение года.", "sort_order": 7},
    {"id": "p-8", "title": "Персональный коучинг",       "description": "Индивидуальные сессии с бизнес-тренером",   "category": "education",  "available_from": "black",  "financial_effect": None,   "detail_text": "Ежемесячные персональные сессии с сертифицированным бизнес-тренером.", "sort_order": 8},
]

NEWS_DATA = [
    {"id": "news-1", "title": "Двойные баллы за электромобили", "summary": "В марте начисляем x2 за продажи электромобилей", "body": "В период с 1 по 31 марта 2026 года действует акция: за каждую закрытую сделку по электромобилю начисляется двойное количество баллов рейтинга. Воспользуйтесь возможностью ускорить достижение следующего уровня!", "category": "promo", "published_at": datetime(2026, 3, 18, 10, 0, tzinfo=timezone.utc)},
    {"id": "news-2", "title": "Обновление программы мотивации", "summary": "С апреля 2026 вводятся новые компоненты рейтинга", "body": "С нового квартала в расчёт рейтинга добавляется новый компонент — NPS клиентов. Весовой коэффициент составит 0.10, остальные компоненты пересчитаются пропорционально.", "category": "program", "published_at": datetime(2026, 3, 15, 9, 0, tzinfo=timezone.utc)},
    {"id": "news-3", "title": "Мартовские лидеры", "summary": "Топ-5 сотрудников по итогам февраля", "body": "Поздравляем лидеров февраля! Игорь Белов — 1 место, Мария Иванова — 2 место. Продолжайте в том же духе!", "category": "company", "published_at": datetime(2026, 3, 1, 8, 0, tzinfo=timezone.utc)},
    {"id": "news-4", "title": "Совет: как повысить долю банка", "summary": "5 проверенных техник увеличения доли банковского финансирования", "body": "1. Предлагайте кредит на этапе тест-драйва. 2. Акцентируйте выгоду низкой ставки. 3. Используйте калькулятор платежей прямо на встрече. 4. Предложите страховку в пакете. 5. Работайте с возражениями о первоначальном взносе.", "category": "tip", "published_at": datetime(2026, 2, 28, 12, 0, tzinfo=timezone.utc)},
]


async def seed():
    async with Session() as db:
        # Check if already seeded
        result = await db.execute(select(Employee).limit(1))
        if result.scalar_one_or_none():
            print("Database already seeded, skipping.")
            return

        print("Seeding employees...")
        for e in EMPLOYEES:
            emp = Employee(
                id=e["id"],
                first_name=e["first_name"],
                last_name=e["last_name"],
                position=e["position"],
                dealership=e["dealership"],
                dealership_code=e["dealership_code"],
                region=e["region"],
                employee_code=e["code"],
                password_hash=hash_password(e["password"]),
                phone=e["phone"],
                email=f"{e['last_name'].lower()}@sber-dealer.ru",
                program_join_date=date(2025, 6, 15),
            )
            db.add(emp)

        await db.flush()

        print("Seeding rating plans...")
        for e in EMPLOYEES:
            db.add(RatingPlan(
                employee_id=e["id"],
                month=MONTH_START,
                volume_plan=10.0,
                deals_plan=10,
                bank_share_target=50.0,
                volume_max_index=120,
            ))

        await db.flush()

        print("Seeding daily results...")
        for emp_id, cfg in DAILY_RESULTS_CONFIG.items():
            days_passed = TODAY.day - 1
            if days_passed <= 0:
                days_passed = 1
            volume_per_day = cfg["volume"] / days_passed
            deals_per_day_base = cfg["deals"] // days_passed

            for day_offset in range(days_passed):
                day = MONTH_START + timedelta(days=day_offset)
                if day > TODAY:
                    break
                deals = deals_per_day_base + (1 if day_offset < cfg["deals"] % days_passed else 0)
                db.add(DailyResult(
                    id=str(uuid.uuid4()),
                    employee_id=emp_id,
                    date=day,
                    deals_closed=deals,
                    loan_volume=round(volume_per_day, 2),
                    additional_products=1,
                ))

        await db.flush()

        print("Seeding monthly tasks...")
        for e in EMPLOYEES:
            db.add(MonthlyTask(
                id=str(uuid.uuid4()),
                employee_id=e["id"],
                month=MONTH_START,
                title="Закрыть 10 сделок",
                description="Основная цель на месяц",
                target=10.0,
                current=float(DAILY_RESULTS_CONFIG[e["id"]]["deals"]),
                unit="шт.",
                category="sales",
                deadline=date(TODAY.year, TODAY.month, 31) if TODAY.month in [1,3,5,7,8,10,12] else date(TODAY.year, TODAY.month, 30),
                reward_points=10,
            ))
            db.add(MonthlyTask(
                id=str(uuid.uuid4()),
                employee_id=e["id"],
                month=MONTH_START,
                title="Достичь объёма 10 млн ₽",
                description="Суммарный объём кредитов за месяц",
                target=10.0,
                current=float(DAILY_RESULTS_CONFIG[e["id"]]["volume"]),
                unit="млн ₽",
                category="sales",
                deadline=None,
                reward_points=15,
            ))

        await db.flush()

        print("Seeding privileges...")
        for p in PRIVILEGES:
            db.add(Privilege(**p))

        await db.flush()

        print("Seeding personal managers...")
        db.add(PersonalManager(
            id=str(uuid.uuid4()),
            employee_id="emp-001",
            name="Елена Сидорова",
            position="Руководитель программы мотивации",
            phone="+7 (495) 123-45-67",
            email="e.sidorova@sber-dealer.ru",
        ))

        await db.flush()

        print("Seeding news...")
        for n in NEWS_DATA:
            db.add(News(**n))

        await db.flush()

        print("Seeding welcome support message...")
        db.add(SupportMessage(
            id=str(uuid.uuid4()),
            employee_id="emp-001",
            text="Добро пожаловать в программу лояльности Сбер Дилер! Если у вас есть вопросы — пишите.",
            sender="manager",
            is_read=True,
        ))

        await db.commit()
        print("✅ Seed complete!")


if __name__ == "__main__":
    asyncio.run(seed())
