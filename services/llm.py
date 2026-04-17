"""
services/llm.py — LLM integration stub for FinGuard verdict messages.

When you're ready to plug in a real LLM, uncomment the httpx block
and remove or wrap the stub section.
"""
from __future__ import annotations

# TODO: Uncomment when integrating a real LLM endpoint.
# import httpx
# from config import LLM_URL


async def get_verdict_message(
    purchase: str,
    amount: float,
    verdict: str,       # "approved" or "blocked"
    context: dict,      # keys: overshoot_pct, days, days_left_after, limit
) -> str:
    """
    Return a personality-rich verdict message for the user.

    Stub implementation returns hardcoded templates based on verdict severity.
    Signature is kept identical to what a real LLM call would require.

    Real LLM call (commented out):
    ---
    # async with httpx.AsyncClient(timeout=10) as client:
    #     payload = {
    #         "model": "finguard-guardian-v1",
    #         "messages": [
    #             {"role": "system", "content": SYSTEM_PROMPT},
    #             {"role": "user", "content": user_prompt},
    #         ]
    #     }
    #     resp = await client.post(LLM_URL, json=payload)
    #     resp.raise_for_status()
    #     return resp.json()["choices"][0]["message"]["content"]
    ---
    """
    overshoot: float = context.get("overshoot_pct", 0)
    days: int = context.get("days", 1)
    days_left: float = context.get("days_left_after", 0)
    limit: float = context.get("limit", 0)
    amt = f"{amount:,.0f}"

    if verdict == "approved":
        if overshoot <= 25:
            # Comfortable approval
            return (
                f"✅ Окей, {amt} на «{purchase}» — в рамках разумного. "
                f"Лимит на сегодня: {limit:,.0f}. Не расслабляйся! 😤"
            )
        else:
            # Borderline approval (25–50 % over)
            return (
                f"✅ Ладно... разрешаю. Но это последняя крупная трата сегодня. "
                f"Ты превысил дневной лимит на {overshoot:.0f}%. Я слежу. 👀"
            )
    else:
        # blocked
        if overshoot <= 100:
            # 50–100 % over limit
            return (
                f"⛔ {amt} на «{purchase}»?! Это на {overshoot:.0f}% выше твоего "
                f"дневного лимита ({limit:,.0f}). До получки {days} дн. "
                f"Серьёзно подумай о своих жизненных выборах. 🤦"
            )
        else:
            # 100 %+ over limit — critical
            return (
                f"🚨 КАТЕГОРИЧЕСКИ НЕТ. Если купишь это, денег хватит ещё на "
                f"{max(days_left, 0):.1f} дн. — а до зарплаты {days} дн. "
                f"Положи телефон и открой холодильник. 💸"
            )
