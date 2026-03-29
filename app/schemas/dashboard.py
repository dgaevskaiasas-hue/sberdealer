from typing import Optional

from pydantic import BaseModel
from datetime import date


class RatingComponent(BaseModel):
    id: str
    name: str
    weight: float
    fact_value: float
    plan_value: float
    unit: str
    max_index: Optional[int] = None


class EmployeeDashboard(BaseModel):
    id: str
    first_name: str
    last_name: str
    position: str
    dealership: str
    dealership_code: str
    phone: Optional[str]
    email: Optional[str]
    avatar_url: Optional[str]
    level: str
    total_points: int
    rating_components: list[RatingComponent]
    month_start_date: date
    program_join_date: date


class MonthlyTaskOut(BaseModel):
    id: str
    title: str
    description: Optional[str]
    target: float
    current: float
    unit: str
    category: str
    deadline: Optional[date]
    reward_points: int


class FinancialBenefit(BaseModel):
    current_level: str
    next_level: Optional[str]
    current_yearly_income: int
    projected_yearly_income: int
    yearly_delta: int


class PrivilegeOut(BaseModel):
    id: str
    title: str
    description: str
    category: str
    available_from: str
    financial_effect: Optional[int]
    detail_text: Optional[str]


class DashboardResponse(BaseModel):
    employee: EmployeeDashboard
    monthly_tasks: list[MonthlyTaskOut]
    financial_benefit: FinancialBenefit
    privileges: list[PrivilegeOut]
