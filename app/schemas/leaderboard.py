from typing import Optional

from pydantic import BaseModel


class LeaderboardEntry(BaseModel):
    id: str
    rank: int
    employee_name: str
    dealership: str
    level: str
    total_points: int
    avatar_url: Optional[str]
    is_current_user: bool
