"""
services/llm.py — Generates human-like (and slightly toxic) verdict messages.
"""
import os

LLM_URL = os.getenv("LLM_URL", "")


async def get_verdict_message(purchase: str, amount: float, verdict: str, context: dict) -> str:
    survival_raw = context.get("survival_probability", 0.5)
    survival = int(survival_raw * 100)  # convert 0.0–1.0 fraction to % for display
    overshoot = context.get("overshoot_pct", 0)
    amt = f"{amount:,.0f}"

    if verdict == "approved":
        if survival > 85:
            return f"✅ Отлично! {amt} сом на «{purchase}» — можно брать.\nМолодец!"
        else:
            return f"✅ Ладно, разрешаю {amt} на «{purchase}».\nНо будь осторожен, до зарплаты ещё {context.get('days', 5)} дней."

    else:
        if survival < 30:
            return f"🚨 КАТЕГОРИЧЕСКИ НЕТ!\n\n{amt} сом на «{purchase}» — слишком рискованно.\nШанс дотянуть — всего {survival}%. Иди к холодильнику 💸"
        else:
            return f"⛔ Нет, не стоит.\n\n{amt} сом на «{purchase}» — мы превысили лимит на {overshoot:.0f}%.\nДавай найдём что-то дешевле?"