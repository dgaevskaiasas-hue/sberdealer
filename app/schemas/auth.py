from typing import Optional

from pydantic import BaseModel, field_validator
import re


def _normalize_phone(v: str) -> str:
    """Strip everything except digits, then normalize to +7XXXXXXXXXX."""
    digits = re.sub(r"\D", "", v)
    if len(digits) == 11 and digits.startswith("8"):
        digits = "7" + digits[1:]
    if len(digits) == 10:
        digits = "7" + digits
    if len(digits) != 11 or not digits.startswith("7"):
        raise ValueError("Неверный формат номера телефона")
    return "+" + digits


# ── Login ─────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    """Login by email OR employee_code + password."""
    identifier: str   # email or employee_code
    password: str


class LoginByPhoneRequest(BaseModel):
    """Login by phone + password (кнопка 'По телефону и паролю')."""
    phone: str
    password: str

    @field_validator("phone")
    @classmethod
    def normalize(cls, v: str) -> str:
        return _normalize_phone(v)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int = 3600


class RefreshRequest(BaseModel):
    refresh_token: str


# ── Registration ──────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    """
    Activate account by employee_code (код выдаётся в ДЦ).
    Если аккаунт уже существует без пароля — устанавливаем пароль.
    Если не существует — создаём нового сотрудника.
    """
    employee_code: str
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Пароль должен быть не менее 6 символов")
        return v

    @field_validator("phone")
    @classmethod
    def normalize_phone(cls, v: Optional[str]) -> Optional[str]:
        if v:
            return _normalize_phone(v)
        return v


class SignupRequest(BaseModel):
    """
    Self-service registration via email + password.
    All fields are required.
    """
    email: str
    password: str
    first_name: str
    last_name: str
    phone: str
    position: str
    dealership: str
    dealership_code: Optional[str] = None   # опционально — ДЦ без кода тоже допустим
    region: Optional[str] = None            # определяется автоматически по ДЦ

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Неверный формат email")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Пароль должен быть не менее 6 символов")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Телефон обязателен")
        return _normalize_phone(v)

    @field_validator("first_name", "last_name", "position", "dealership")
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Поле не может быть пустым")
        return v.strip()


class RegisterResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int = 3600
    is_new_account: bool  # True = новый, False = активация существующего


# ── Password management ───────────────────────────────────────────────────────

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Пароль должен быть не менее 6 символов")
        return v


class SetPasswordRequest(BaseModel):
    """Admin: set initial password for an employee by code."""
    employee_code: str
    new_password: str


# ── Forgot / Reset password ───────────────────────────────────────────────────

class ForgotPasswordRequest(BaseModel):
    """
    Request a reset code. identifier = employee_code OR phone number.
    В реальном продакшне — отправляем СМС/email, здесь возвращаем код в ответе.
    """
    identifier: str  # employee_code or phone


class ForgotPasswordResponse(BaseModel):
    message: str
    reset_code: str   # В продакшне убрать — только для разработки/демо
    expires_in_minutes: int = 10


class ResetPasswordRequest(BaseModel):
    identifier: str   # employee_code or phone (тот же что при forgot)
    code: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Пароль должен быть не менее 6 символов")
        return v
