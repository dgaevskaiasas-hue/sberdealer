from pydantic import BaseModel


class SimulateRequest(BaseModel):
    volume_fact: float
    volume_plan: float
    deals_fact: int
    deals_plan: int
    bank_share_fact: float
    bank_share_target: float
    conversion_fact: float


class SimulateResponse(BaseModel):
    projected_points: int
    projected_level: str
    points_delta: int
    level_changed: bool
    projected_yearly_income: int
    yearly_income_delta: int
