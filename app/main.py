from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.routers import auth, dashboard, daily_results, leaderboard, calculator, support, news
from app.routers import monthly_metrics
from app.routers import learning
from app.routers import admin_news
from app.services.scheduler import start_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield


app = FastAPI(
    title="Sber Dealer API",
    version="1.0.0",
    description="""
## Программа мотивации дилеров Сбера

API для мобильного приложения программы лояльности автодилеров.

### Основные разделы

| Раздел | Описание |
|--------|----------|
| **Auth** | Регистрация, вход, JWT-токены, сброс пароля |
| **Dashboard** | Главный экран: профиль, рейтинг, задачи, привилегии |
| **Daily Results** | Ежедневный ввод результатов продаж |
| **Leaderboard** | Рейтинг сотрудников (дилерский / региональный / национальный) |
| **Calculator** | Калькулятор «Что если» — симуляция баллов и дохода |
| **Monthly Metrics** | КПЭ за месяц: доля банка, конверсия |
| **Support** | Чат с менеджером + ИИ-ассистент (GigaChat) |
| **News** | Новости и акции программы |
| **Learning** | Обучающие модули с отслеживанием прогресса |
| **Admin** | Управление новостями |

### Формула рейтинга

```
Балл = 0.35 × (объём/план×100, max 120)
     + 0.25 × (сделки/план×100)
     + 0.25 × (доля_банка/цель×100)
     + 0.15 × конверсия
```

### Уровни

| Уровень | Баллы | Бонус/год | Комиссия |
|---------|-------|-----------|----------|
| Silver  | 0–69  | 15 000 ₽  | +5%      |
| Gold    | 70–89 | 95 000 ₽  | +10%     |
| Black   | 90+   | 215 000 ₽ | +15%     |

### Авторизация

Все эндпоинты (кроме `/health` и auth) требуют JWT-токен:
```
Authorization: Bearer <access_token>
```
""",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "auth", "description": "Регистрация, авторизация, управление паролем"},
        {"name": "dashboard", "description": "Главный экран — профиль, рейтинг, задачи, финансовый прогноз"},
        {"name": "daily-results", "description": "Ежедневный ввод результатов продаж (сделки, объём, доп. продукты)"},
        {"name": "leaderboard", "description": "Рейтинг сотрудников по дилерскому центру, региону или всей сети"},
        {"name": "calculator", "description": "Калькулятор «Что если» — симуляция баллов и финансового эффекта"},
        {"name": "monthly-metrics", "description": "КПЭ за месяц — доля банка и конверсия заявок"},
        {"name": "support", "description": "Чат с персональным менеджером и ИИ-ассистент"},
        {"name": "news", "description": "Новости, акции и советы программы мотивации"},
        {"name": "learning", "description": "Обучающие модули (уроки, видео, тесты) с прогрессом"},
        {"name": "admin-news", "description": "Администрирование новостей (создание, редактирование, удаление)"},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_ERROR", "message": str(exc)}},
    )


app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(daily_results.router)
app.include_router(leaderboard.router)
app.include_router(calculator.router)
app.include_router(support.router)
app.include_router(news.router)
app.include_router(monthly_metrics.router)
app.include_router(learning.router)
app.include_router(admin_news.router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "sber-dealer-api"}
