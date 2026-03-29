import math
from datetime import date


LEVEL_THRESHOLDS = {
    "black": 90,
    "gold": 70,
    "silver": 0,
}

LEVEL_YEARLY_BONUS = {
    "silver": 15_000,
    "gold": 95_000,
    "black": 215_000,
}

INCOME_PER_DEAL = 45_000

COMPONENTS_CONFIG = [
    {"id": "volume",     "name": "Объём сделок",       "weight": 0.35, "unit": "млн ₽", "max_index": 120},
    {"id": "deals",      "name": "Количество сделок",  "weight": 0.25, "unit": "шт.",   "max_index": None},
    {"id": "bank_share", "name": "Доля банка",          "weight": 0.25, "unit": "%",     "max_index": None},
    {"id": "conversion", "name": "Конверсия заявок",    "weight": 0.15, "unit": "%",     "max_index": None},
]


def get_level(points: int) -> str:
    if points >= 90:
        return "black"
    if points >= 70:
        return "gold"
    return "silver"


def get_next_level(level: str) -> str | None:
    order = ["silver", "gold", "black"]
    idx = order.index(level)
    return order[idx + 1] if idx + 1 < len(order) else None


def calculate_index(fact: float, plan: float, max_index: int | None) -> float:
    if plan == 0:
        return 0.0
    raw = (fact / plan) * 100
    if max_index is not None:
        raw = min(max_index, raw)
    return raw


def calculate_total_points(components: list[dict]) -> int:
    """components: list of {weight, fact_value, plan_value, max_index}"""
    total = 0.0
    for c in components:
        idx = calculate_index(c["fact_value"], c["plan_value"], c.get("max_index"))
        total += c["weight"] * idx
    return math.floor(total)


def calculate_financial_benefit(
    current_deals: float,
    plan_deals: float,
    current_points: int,
) -> dict:
    current_level = get_level(current_points)
    next_level = get_next_level(current_level)

    current_yearly = int(current_deals * INCOME_PER_DEAL) + LEVEL_YEARLY_BONUS[current_level]
    projected_level = next_level or current_level
    projected_yearly = int(plan_deals * INCOME_PER_DEAL) + LEVEL_YEARLY_BONUS[projected_level]

    return {
        "current_level": current_level,
        "next_level": next_level,
        "current_yearly_income": current_yearly,
        "projected_yearly_income": projected_yearly,
        "yearly_delta": projected_yearly - current_yearly,
    }


def build_rating_components(
    volume_fact: float,
    deals_fact: float,
    bank_share_fact: float,
    conversion_fact: float,
    volume_plan: float,
    deals_plan: float,
    bank_share_target: float,
    volume_max_index: int = 120,
) -> list[dict]:
    return [
        {
            "id": "volume",
            "name": "Объём сделок",
            "weight": 0.35,
            "fact_value": volume_fact,
            "plan_value": volume_plan,
            "unit": "млн ₽",
            "max_index": volume_max_index,
        },
        {
            "id": "deals",
            "name": "Количество сделок",
            "weight": 0.25,
            "fact_value": deals_fact,
            "plan_value": deals_plan,
            "unit": "шт.",
            "max_index": None,
        },
        {
            "id": "bank_share",
            "name": "Доля банка",
            "weight": 0.25,
            "fact_value": bank_share_fact,
            "plan_value": bank_share_target,
            "unit": "%",
            "max_index": None,
        },
        {
            "id": "conversion",
            "name": "Конверсия заявок",
            "weight": 0.15,
            "fact_value": conversion_fact,
            "plan_value": 100.0,
            "unit": "%",
            "max_index": None,
        },
    ]


def month_start(d: date) -> date:
    return d.replace(day=1)
