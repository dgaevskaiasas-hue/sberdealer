import random
import string
import uuid
import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete as sql_delete
from datetime import datetime, timedelta, timezone, date

from app.core.database import get_db
from app.core.security import create_access_token, create_refresh_token, decode_token, verify_password, hash_password
from app.core.config import settings
from app.core.deps import get_current_employee
from app.models.employee import Employee
from app.models.refresh_token import RefreshToken
from app.models.reset_code import PasswordResetCode
from app.schemas.auth import (
    LoginRequest,
    LoginByPhoneRequest,
    TokenResponse,
    RefreshRequest,
    RegisterRequest,
    RegisterResponse,
    SignupRequest,
    ChangePasswordRequest,
    SetPasswordRequest,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
)
from jose import JWTError

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

RESET_CODE_EXPIRE_MINUTES = 10


# ── Helpers ───────────────────────────────────────────────────────────────────

def _normalize_phone(v: str) -> str:
    digits = re.sub(r"\D", "", v)
    if len(digits) == 11 and digits.startswith("8"):
        digits = "7" + digits[1:]
    if len(digits) == 10:
        digits = "7" + digits
    return "+" + digits if digits.startswith("7") and len(digits) == 11 else v


def _unauthorized(message: str = "Неверный логин или пароль"):
    raise HTTPException(status_code=401, detail={"code": "UNAUTHORIZED", "message": message})


async def _issue_tokens(employee_id: str, db: AsyncSession) -> TokenResponse:
    access_token = create_access_token({"sub": employee_id})
    refresh_token = create_refresh_token({"sub": employee_id})
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    db.add(RefreshToken(
        employee_id=employee_id,
        token=refresh_token,
        expires_at=expires_at,
        created_at=datetime.now(timezone.utc),
    ))
    await db.commit()
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


def _generate_code(length: int = 6) -> str:
    return "".join(random.choices(string.digits, k=length))


async def _find_by_identifier(identifier: str, db: AsyncSession) -> Employee | None:
    """Find employee by email, phone, or employee_code."""
    # 1. Email
    if "@" in identifier:
        result = await db.execute(select(Employee).where(Employee.email == identifier.lower().strip()))
        return result.scalar_one_or_none()
    # 2. Phone
    try:
        normalized = _normalize_phone(identifier)
        if normalized.startswith("+"):
            result = await db.execute(select(Employee).where(Employee.phone == normalized))
            return result.scalar_one_or_none()
    except Exception:
        pass
    # 3. Employee code
    result = await db.execute(select(Employee).where(Employee.employee_code == identifier))
    return result.scalar_one_or_none()


# ── POST /auth/login ──────────────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse, summary="Вход по email, телефону или коду сотрудника")
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """identifier = email | phone | employee_code"""
    identifier = body.identifier.strip()

    # 1. Try email
    if "@" in identifier:
        result = await db.execute(select(Employee).where(Employee.email == identifier.lower()))
    # 2. Try phone (normalized)
    elif re.sub(r"\D", "", identifier):
        normalized = _normalize_phone(identifier)
        result = await db.execute(select(Employee).where(Employee.phone == normalized))
    # 3. Try employee_code
    else:
        result = await db.execute(select(Employee).where(Employee.employee_code == identifier))

    employee = result.scalar_one_or_none()

    if not employee or not employee.password_hash:
        _unauthorized()
    if not verify_password(body.password, employee.password_hash):
        _unauthorized()

    return await _issue_tokens(employee.id, db)


# ── POST /auth/signup ─────────────────────────────────────────────────────────

@router.post(
    "/signup",
    response_model=RegisterResponse,
    status_code=201,
    summary="Регистрация по email — самостоятельная, без кода сотрудника",
)
async def signup(body: SignupRequest, db: AsyncSession = Depends(get_db)):
    # Check email uniqueness
    existing = await db.execute(select(Employee).where(Employee.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail={
                "code": "DUPLICATE_ENTRY",
                "message": "Аккаунт с этим email уже существует. Войдите или восстановите пароль.",
            },
        )

    # Auto-generate a unique employee_code from email prefix
    code_base = body.email.split("@")[0].upper().replace(".", "-")[:20]
    suffix = str(uuid.uuid4())[:6].upper()
    employee_code = f"EMP-{code_base}-{suffix}"

    employee = Employee(
        id=str(uuid.uuid4()),
        employee_code=employee_code,
        password_hash=hash_password(body.password),
        first_name=body.first_name.strip(),
        last_name=body.last_name.strip(),
        email=body.email,
        phone=body.phone,
        position=body.position or "Менеджер по продажам",
        dealership=body.dealership or "Не указан",
        dealership_code=body.dealership_code or "UNKNOWN",
        region=body.region or "Москва",
        program_join_date=date.today(),
    )
    db.add(employee)
    await db.flush()

    # Create default rating plan + all 4 KPI tasks for current month
    from app.models.rating_plan import RatingPlan
    from app.models.monthly_task import MonthlyTask
    from app.services.rating import month_start
    ms = month_start(date.today())
    today = date.today()
    # Last day of current month
    import calendar
    last_day = calendar.monthrange(today.year, today.month)[1]
    deadline = date(today.year, today.month, last_day)

    db.add(RatingPlan(
        employee_id=employee.id,
        month=ms,
        volume_plan=10.0,
        deals_plan=10,
        bank_share_target=50.0,
        volume_max_index=120,
        bank_share_actual=0.0,
        conversion_actual=0.0,
    ))

    kpi_tasks = [
        dict(title="Закрыть 10 сделок",      description="План по количеству сделок за месяц",      target=10.0,  unit="шт.", category="sales",   reward_points=10),
        dict(title="Объём 10 млн ₽",          description="План по объёму кредитования",              target=10.0,  unit="млн ₽", category="sales", reward_points=8),
        dict(title="Доля банка 50%",           description="Целевая доля банковских продуктов",        target=50.0,  unit="%",   category="calls",   reward_points=6),
        dict(title="Конверсия заявок 60%",     description="Качество подаваемых заявок",              target=60.0,  unit="%",   category="clients", reward_points=5),
    ]
    for t in kpi_tasks:
        db.add(MonthlyTask(
            id=str(uuid.uuid4()),
            employee_id=employee.id,
            month=ms,
            deadline=deadline,
            current=0.0,
            **t,
        ))

    tokens = await _issue_tokens(employee.id, db)
    return RegisterResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        expires_in=tokens.expires_in,
        is_new_account=True,
    )


# ── POST /auth/login-by-phone ─────────────────────────────────────────────────

@router.post("/login-by-phone", response_model=TokenResponse, summary="Вход по телефону и паролю")
async def login_by_phone(body: LoginByPhoneRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Employee).where(Employee.phone == body.phone))
    employee = result.scalar_one_or_none()

    if not employee or not employee.password_hash:
        _unauthorized()
    if not verify_password(body.password, employee.password_hash):
        _unauthorized()

    return await _issue_tokens(employee.id, db)


# ── POST /auth/register ───────────────────────────────────────────────────────

@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=201,
    summary="Регистрация / активация аккаунта по коду сотрудника",
)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Employee).where(Employee.employee_code == body.employee_code))
    employee = result.scalar_one_or_none()
    is_new = False

    if employee:
        # Account exists — check it's not already activated
        if employee.password_hash:
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "DUPLICATE_ENTRY",
                    "message": "Аккаунт с этим кодом уже зарегистрирован. Используйте вход.",
                },
            )
        # Activate: set password and optional profile fields
        employee.password_hash = hash_password(body.password)
        if body.phone:
            employee.phone = body.phone
        if body.email:
            employee.email = body.email
        if body.first_name:
            employee.first_name = body.first_name
        if body.last_name:
            employee.last_name = body.last_name

    else:
        # New employee — create full record
        is_new = True
        employee = Employee(
            id=str(uuid.uuid4()),
            employee_code=body.employee_code,
            password_hash=hash_password(body.password),
            first_name=body.first_name or "Сотрудник",
            last_name=body.last_name or body.employee_code,
            position="Менеджер по продажам",
            dealership="Не указан",
            dealership_code=body.employee_code.rsplit("-", 1)[0] if "-" in body.employee_code else "UNKNOWN",
            region="Москва",
            phone=body.phone,
            email=body.email,
            program_join_date=date.today(),
        )
        db.add(employee)
        await db.flush()

        # Create default rating plan + all 4 KPI tasks for current month
        from app.models.rating_plan import RatingPlan
        from app.models.monthly_task import MonthlyTask
        from app.services.rating import month_start
        import calendar as _cal
        ms = month_start(date.today())
        _today = date.today()
        _last = _cal.monthrange(_today.year, _today.month)[1]
        _deadline = date(_today.year, _today.month, _last)

        db.add(RatingPlan(
            employee_id=employee.id, month=ms,
            volume_plan=10.0, deals_plan=10, bank_share_target=50.0,
            volume_max_index=120, bank_share_actual=0.0, conversion_actual=0.0,
        ))
        for t in [
            dict(title="Закрыть 10 сделок",    description="План по количеству сделок за месяц",    target=10.0,  unit="шт.", category="sales",   reward_points=10),
            dict(title="Объём 10 млн ₽",        description="План по объёму кредитования",            target=10.0,  unit="млн ₽", category="sales", reward_points=8),
            dict(title="Доля банка 50%",         description="Целевая доля банковских продуктов",      target=50.0,  unit="%",   category="calls",   reward_points=6),
            dict(title="Конверсия заявок 60%",   description="Качество подаваемых заявок",            target=60.0,  unit="%",   category="clients", reward_points=5),
        ]:
            db.add(MonthlyTask(id=str(uuid.uuid4()), employee_id=employee.id, month=ms, deadline=_deadline, current=0.0, **t))

    await db.flush()

    tokens = await _issue_tokens(employee.id, db)
    return RegisterResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        expires_in=tokens.expires_in,
        is_new_account=is_new,
    )


# ── POST /auth/refresh ────────────────────────────────────────────────────────

@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    try:
        payload = decode_token(body.refresh_token)
        if payload.get("type") != "refresh":
            _unauthorized("Invalid refresh token")
        employee_id = payload.get("sub")
    except JWTError:
        _unauthorized("Invalid refresh token")

    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token == body.refresh_token,
            RefreshToken.expires_at > datetime.now(timezone.utc),
        )
    )
    stored = result.scalar_one_or_none()
    if not stored:
        _unauthorized("Refresh token expired")

    await db.delete(stored)
    return await _issue_tokens(employee_id, db)


# ── POST /auth/forgot-password ────────────────────────────────────────────────

@router.post(
    "/forgot-password",
    response_model=ForgotPasswordResponse,
    summary="Запросить код сброса пароля (SMS/email в продакшне)",
)
async def forgot_password(body: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    employee = await _find_by_identifier(body.identifier, db)

    # Always return 200 to not reveal whether account exists
    dummy_message = "Если аккаунт найден, код отправлен"

    if not employee:
        return ForgotPasswordResponse(
            message=dummy_message,
            reset_code="000000",   # fake — account not found
            expires_in_minutes=RESET_CODE_EXPIRE_MINUTES,
        )

    code = _generate_code(6)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=RESET_CODE_EXPIRE_MINUTES)
    db.add(PasswordResetCode(
        employee_id=employee.id,
        code=code,
        expires_at=expires_at,
    ))
    await db.commit()

    # TODO: в продакшне — отправить SMS через Sber или email
    # sms_service.send(employee.phone, f"Код сброса пароля: {code}")

    return ForgotPasswordResponse(
        message=f"Код отправлен на {employee.phone or employee.email or 'контакт'}",
        reset_code=code,   # ← убрать в продакшне, здесь для удобства разработки
        expires_in_minutes=RESET_CODE_EXPIRE_MINUTES,
    )


# ── POST /auth/reset-password ─────────────────────────────────────────────────

@router.post("/reset-password", status_code=204, summary="Сбросить пароль по коду")
async def reset_password(body: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    employee = await _find_by_identifier(body.identifier, db)
    if not employee:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Аккаунт не найден"})

    result = await db.execute(
        select(PasswordResetCode).where(
            PasswordResetCode.employee_id == employee.id,
            PasswordResetCode.code == body.code,
            PasswordResetCode.used == False,
            PasswordResetCode.expires_at > datetime.now(timezone.utc),
        )
    )
    reset = result.scalar_one_or_none()
    if not reset:
        raise HTTPException(
            status_code=400,
            detail={"code": "VALIDATION_ERROR", "message": "Код неверный или истёк. Запросите новый."},
        )

    reset.used = True
    employee.password_hash = hash_password(body.new_password)
    await db.commit()


# ── POST /auth/change-password ────────────────────────────────────────────────

@router.post("/change-password", status_code=204, summary="Изменить пароль (авторизованный)")
async def change_password(
    body: ChangePasswordRequest,
    employee: Employee = Depends(get_current_employee),
    db: AsyncSession = Depends(get_db),
):
    if not employee.password_hash or not verify_password(body.current_password, employee.password_hash):
        _unauthorized("Неверный текущий пароль")
    employee.password_hash = hash_password(body.new_password)
    await db.commit()


# ── POST /auth/logout ────────────────────────────────────────────────────────

@router.post("/logout", status_code=204, summary="Выход из аккаунта")
async def logout(
    body: RefreshRequest,
    employee: Employee = Depends(get_current_employee),
    db: AsyncSession = Depends(get_db),
):
    """Invalidates the refresh token so it can no longer be used."""
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token == body.refresh_token,
            RefreshToken.employee_id == employee.id,
        )
    )
    stored = result.scalar_one_or_none()
    if stored:
        await db.delete(stored)
        await db.commit()


# ── DELETE /auth/account ─────────────────────────────────────────────────────

@router.delete("/account", status_code=204, summary="Удалить аккаунт и все данные")
async def delete_account(
    employee: Employee = Depends(get_current_employee),
    db: AsyncSession = Depends(get_db),
):
    """
    Permanently deletes the authenticated employee and all their data.
    Uses raw DELETE to let PostgreSQL CASCADE handle all related tables:
    daily_results, monthly_tasks, rating_plans, support_messages,
    refresh_tokens, news_read_status, user_module_progress, password_reset_codes.
    """
    employee_id = employee.id
    # Expunge from session so SQLAlchemy doesn't try to lazy-load relationships
    db.expunge(employee)
    await db.execute(sql_delete(Employee).where(Employee.id == employee_id))
    await db.commit()


# ── POST /auth/set-password (admin) ──────────────────────────────────────────

@router.post("/set-password", status_code=204, summary="[Admin] Установить первичный пароль сотруднику")
async def set_password(body: SetPasswordRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Employee).where(Employee.employee_code == body.employee_code))
    employee = result.scalar_one_or_none()
    if not employee:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Employee not found"})
    employee.password_hash = hash_password(body.new_password)
    await db.commit()
