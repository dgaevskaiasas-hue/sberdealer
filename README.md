<p align="center">
  <img src="https://upload.wikimedia.org/wikipedia/commons/2/2a/Sberbank.svg" width="120" alt="Sber Logo"/>
</p>

<h1 align="center">СберДилер — Платформа мотивации дилерских центров</h1>

<p align="center">
  <b>Хакатон-проект: геймифицированная система повышения эффективности сотрудников автодилерских центров Сбербанка</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.13-blue?logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql&logoColor=white" alt="PostgreSQL"/>
  <img src="https://img.shields.io/badge/GigaChat-AI-green?logo=openai&logoColor=white" alt="GigaChat"/>
  <img src="https://img.shields.io/badge/iOS-SwiftUI-F05138?logo=swift&logoColor=white" alt="SwiftUI"/>
</p>

---

## Проблема

Дилерские центры Сбербанка работают с тысячами сотрудников по всей стране. Мотивация и отслеживание показателей каждого менеджера — сложная задача. Сотрудники не понимают, как их ежедневные действия влияют на бонусы, не видят свой рейтинг среди коллег и не получают персональных рекомендаций по улучшению.

## Решение

**СберДилер** — мобильное приложение с AI-ассистентом, которое превращает рабочий процесс в понятную игру:

- Каждый сотрудник видит свой **рейтинг в реальном времени** и уровень (Silver → Gold → Black)
- **GigaChat** анализирует показатели и даёт персональные советы
- **Лидерборд** создаёт здоровую конкуренцию внутри ДЦ, региона и всей сети
- **Калькулятор** позволяет моделировать "а что, если я закрою ещё 3 сделки?"
- **Обучение** с геймификацией — модули, прогресс, баллы за прохождение

---

## Архитектура

```
┌─────────────────┐        ┌──────────────────┐        ┌─────────────────┐
│   iOS-клиент    │◄──────►│  FastAPI Backend  │◄──────►│   PostgreSQL    │
│   (SwiftUI)     │  REST  │  Python 3.13     │  async │                 │
└─────────────────┘        └────────┬─────────┘        └─────────────────┘
                                    │
                           ┌────────▼─────────┐
                           │  GigaChat API    │
                           │  (Sber AI)       │
                           └──────────────────┘
```

| Компонент | Технологии |
|-----------|-----------|
| **Backend** | Python 3.13, FastAPI, SQLAlchemy 2.0 (async), asyncpg |
| **База данных** | PostgreSQL 16 |
| **AI** | GigaChat API (Сбер) — персональный ассистент |
| **Аутентификация** | JWT (access + refresh tokens), bcrypt |
| **Планировщик** | APScheduler — cron-задачи (ежемесячный сброс, очистка токенов) |
| **iOS-клиент** | Swift, SwiftUI |
| **Деплой** | Ubuntu 24.04, Nginx, systemd, rsync |

---

## Ключевые фичи

### 1. Рейтинговая система с тремя уровнями

Формула расчёта баллов (взвешенный композит):

```
Итого = 0.35 × Объём сделок + 0.25 × Кол-во сделок + 0.25 × Доля банка + 0.15 × Конверсия
```

| Уровень | Баллы | Годовой бонус | Комиссия |
|---------|-------|---------------|----------|
| 🥈 Silver | 0 — 69 | 15 000 ₽ | +5% |
| 🥇 Gold | 70 — 89 | 95 000 ₽ | +10% |
| 🖤 Black | 90+ | 215 000 ₽ | +15% |

### 2. GigaChat AI — персональный ассистент

Интеграция со Сбер GigaChat API. ИИ знает:
- Текущий уровень и баллы сотрудника
- Факт и план по каждому компоненту рейтинга
- Сколько баллов до следующего уровня

На основе этого даёт персонализированные рекомендации. Если API недоступен — срабатывает fallback с rule-based советами.

### 3. Лидерборд (3 уровня)

- **Дилерский центр** — соревнование внутри своего ДЦ
- **Регион** — рейтинг среди всех ДЦ региона
- **Вся сеть** — национальный рейтинг

### 4. Калькулятор "Что, если?"

Сотрудник моделирует сценарии: "Если закрою ещё 5 сделок на 2 млн — какой будет уровень и бонус?" Показывает дельту баллов и дохода.

### 5. Ежедневный трекинг

Менеджер вносит результаты дня (сделки, объёмы, доп. продукты) → система автоматически пересчитывает рейтинг и прогресс по задачам.

### 6. Обучение с геймификацией

Модули (статьи, видео, квизы) с прогресс-баром и наградными баллами за прохождение.

### 7. Новости и уведомления

Лента новостей компании, акций, советов с отслеживанием прочитанности.

---

## API

Полная документация доступна по адресу `/docs` (Swagger UI) после запуска сервера.

<details>
<summary><b>Все эндпоинты</b></summary>

| Метод | Путь | Описание |
|-------|------|----------|
| `POST` | `/api/v1/auth/signup` | Регистрация нового сотрудника |
| `POST` | `/api/v1/auth/login` | Вход (email / телефон / код сотрудника) |
| `POST` | `/api/v1/auth/login-by-phone` | Вход по телефону |
| `POST` | `/api/v1/auth/refresh` | Обновление токена |
| `POST` | `/api/v1/auth/forgot-password` | Запрос кода сброса пароля |
| `POST` | `/api/v1/auth/reset-password` | Сброс пароля |
| `POST` | `/api/v1/auth/change-password` | Смена пароля |
| `POST` | `/api/v1/auth/logout` | Выход |
| `DELETE` | `/api/v1/auth/account` | Удаление аккаунта |
| `GET` | `/api/v1/dashboard` | Главный экран (рейтинг, задачи, прогноз) |
| `GET` | `/api/v1/daily-results` | Результаты за месяц |
| `POST` | `/api/v1/daily-results` | Внести результат дня |
| `GET` | `/api/v1/monthly-metrics` | KPI текущего месяца |
| `PATCH` | `/api/v1/monthly-metrics` | Обновить KPI |
| `GET` | `/api/v1/leaderboard` | Лидерборд (scope: dealership/region/national) |
| `POST` | `/api/v1/calculator/simulate` | Калькулятор "что, если?" |
| `GET` | `/api/v1/support/messages` | Чат поддержки |
| `POST` | `/api/v1/support/messages` | Отправить сообщение |
| `POST` | `/api/v1/support/gigachat` | AI-ассистент (GigaChat) |
| `GET` | `/api/v1/news` | Лента новостей |
| `POST` | `/api/v1/news/{id}/read` | Отметить прочитанной |
| `POST` | `/api/v1/admin/news` | Создать новость |
| `PATCH` | `/api/v1/admin/news/{id}` | Редактировать |
| `DELETE` | `/api/v1/admin/news/{id}` | Удалить |
| `GET` | `/api/v1/learning/modules` | Модули обучения |
| `PATCH` | `/api/v1/learning/modules/{id}/progress` | Обновить прогресс |

</details>

---

## Быстрый старт

```bash
# 1. Клонировать репозиторий
git clone https://github.com/kheladzedev/SberDealerServer.git
cd SberDealerServer

# 2. Создать виртуальное окружение
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Создать базу данных и применить миграции
createdb sber_dealer
psql sber_dealer -f migrations/001_init.sql
psql sber_dealer -f migrations/002_auth_registration.sql
psql sber_dealer -f migrations/003_per_user_metrics.sql
psql sber_dealer -f migrations/004_learning.sql

# 4. Заполнить тестовыми данными (10 сотрудников, привилегии, новости, обучение)
python seed/seed.py
python seed/seed_learning.py
python seed/seed_learning_content.py

# 5. Запустить сервер
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Сервер будет доступен на `http://localhost:8000/docs`

---

## Переменные окружения

```env
DATABASE_URL=postgresql+asyncpg://user@localhost/sber_dealer
SYNC_DATABASE_URL=postgresql://user@localhost/sber_dealer
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=30
GIGACHAT_AUTH_KEY=<ключ от GigaChat API>
GIGACHAT_SCOPE=GIGACHAT_API_PERS
REDIS_URL=redis://localhost:6379/0
```

---

## Структура проекта

```
backend/
├── app/
│   ├── main.py              # Точка входа FastAPI
│   ├── core/
│   │   ├── config.py        # Конфигурация (pydantic-settings)
│   │   ├── database.py      # Подключение к БД (async)
│   │   ├── security.py      # JWT, хэширование паролей
│   │   └── deps.py          # Dependency injection
│   ├── models/              # SQLAlchemy ORM-модели
│   ├── routers/             # Обработчики API-эндпоинтов
│   ├── schemas/             # Pydantic-схемы запросов/ответов
│   └── services/
│       ├── rating.py        # Расчёт рейтинга и уровней
│       ├── gigachat.py      # Интеграция с GigaChat API
│       └── scheduler.py     # Фоновые задачи (cron)
├── migrations/              # SQL-миграции
├── seed/                    # Скрипты заполнения тестовыми данными
├── requirements.txt
├── Procfile
└── deploy.sh                # Скрипт деплоя на Ubuntu
```

---

## Тестовые пользователи

| Код сотрудника | Имя | Телефон | Пароль | Уровень |
|----------------|-----|---------|--------|---------|
| DC-MSK-042-001 | Алексей Петров | +79165551001 | petrov123 | Silver (65 б.) |
| DC-MSK-042-002 | Мария Иванова | +79165551002 | ivanova123 | Black (93 б.) |
| DC-MSK-042-003 | Дмитрий Козлов | +79165551003 | kozlov123 | Gold (82 б.) |

> Вход по телефону: `POST /api/v1/auth/login` с `{"identifier": "+79165551001", "password": "petrov123"}`

---

## Команда

Проект разработан на хакатоне командой **Dottys**.

---

<p align="center">
  <sub>Built with FastAPI + GigaChat AI for Sberbank Dealer Motivation Program</sub>
</p>
