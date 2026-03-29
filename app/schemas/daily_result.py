from pydantic import BaseModel, field_validator
from datetime import date


class DailyResultCreate(BaseModel):
    date: date
    deals_closed: int
    loan_volume: float
    additional_products: int

    @field_validator("deals_closed")
    @classmethod
    def validate_deals(cls, v: int) -> int:
        if not 0 <= v <= 10:
            raise ValueError("deals_closed must be between 0 and 10")
        return v

    @field_validator("loan_volume")
    @classmethod
    def validate_volume(cls, v: float) -> float:
        if not 0 <= v <= 50:
            raise ValueError("loan_volume must be between 0 and 50")
        return v

    @field_validator("additional_products")
    @classmethod
    def validate_products(cls, v: int) -> int:
        if not 0 <= v <= 20:
            raise ValueError("additional_products must be between 0 and 20")
        return v


class DailyResultOut(BaseModel):
    id: str
    date: date
    deals_closed: int
    loan_volume: float
    additional_products: int

    model_config = {"from_attributes": True}
