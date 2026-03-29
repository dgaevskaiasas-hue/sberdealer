import httpx
import uuid
from app.core.config import settings


async def get_gigachat_token() -> str | None:
    if not settings.GIGACHAT_AUTH_KEY:
        return None
    rq_uid = str(uuid.uuid4())
    async with httpx.AsyncClient(verify=False) as client:
        resp = await client.post(
            "https://ngw.devices.sberbank.ru:9443/api/v2/oauth",
            headers={
                "Authorization": f"Basic {settings.GIGACHAT_AUTH_KEY}",
                "RqUID": rq_uid,
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={"scope": settings.GIGACHAT_SCOPE},
            timeout=10,
        )
        if resp.status_code == 200:
            return resp.json().get("access_token")
    return None


async def ask_gigachat(question: str, context: dict) -> str:
    token = await get_gigachat_token()
    if not token:
        return _fallback_answer(question, context)

    system_prompt = (
        f"Ты персональный ИИ-ассистент программы мотивации дилерских центров Сбербанка. "
        f"Текущий сотрудник: уровень {context.get('level', 'silver')}, "
        f"баллы {context.get('total_points', 0)}/100. "
        f"Компоненты рейтинга: объём сделок {context.get('volume_fact', 0)} из {context.get('volume_plan', 10)} млн ₽, "
        f"сделок {context.get('deals_fact', 0)} из {context.get('deals_plan', 10)} шт. "
        f"Отвечай кратко и по делу на русском языке."
    )

    async with httpx.AsyncClient(verify=False) as client:
        resp = await client.post(
            "https://gigachat.devices.sberbank.ru/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={
                "model": "GigaChat",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question},
                ],
                "max_tokens": 512,
            },
            timeout=30,
        )
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"]

    return _fallback_answer(question, context)


def _fallback_answer(question: str, context: dict) -> str:
    level = context.get("level", "silver")
    points = context.get("total_points", 0)
    next_threshold = 70 if level == "silver" else 90 if level == "gold" else 100
    delta = next_threshold - points

    if delta <= 0:
        return f"Вы уже достигли максимального уровня Black! Поддерживайте результат."

    level_names = {"silver": "Серебро", "gold": "Золото", "black": "Black"}
    next_level_names = {"silver": "Золото", "gold": "Black"}
    next_name = next_level_names.get(level, "Black")

    return (
        f"На основе вашего текущего рейтинга {points} баллов (уровень {level_names.get(level, level)}), "
        f"до уровня {next_name} вам нужно ещё {delta} баллов. "
        f"Сосредоточьтесь на увеличении объёма сделок (вес 35%) и доли банка (вес 25%). "
        f"Выполните план по количеству сделок — это принесёт дополнительные 17.5 баллов при 100% выполнении."
    )
