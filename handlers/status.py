"""
handlers/status.py — /status command and "📊 Статус" button.
"""
from datetime import date

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from database.models import get_user
from keyboards.reply import main_menu
from services.calculator import evaluate_purchase

router = Router()


@router.message(Command("status"))
@router.message(F.text == "📊 Статус")
async def cmd_status(message: Message) -> None:
    user_id = message.from_user.id
    user = await get_user(user_id)

    if not user or not user["onboarded"]:
        await message.answer(
            "❌ Ты ещё не настроил FinGuard. Начни с /start",
            reply_markup=main_menu,
        )
        return

    balance = user["balance"]
    reserve = user["reserve"]
    income_date_iso = user["next_income_date"]

    result = evaluate_purchase(0, balance, reserve, income_date_iso)
    days = result["days"]
    limit = result["limit"]
    available = result["available"]

    # Financial health: available / (available + reserve)
    total = available + reserve
    health_ratio = available / total if total > 0 else 0
    bar = _health_bar(health_ratio)

    # Forecast
    income_date = date.fromisoformat(income_date_iso)
    forecast = _forecast(available, limit, days)

    await message.answer(
        f"📊 *Твой финансовый статус*\n\n"
        f"  💰 Баланс:        `{balance:,.2f}`\n"
        f"  🛡 Резерв:        `{reserve:,.2f}`\n"
        f"  ✅ Доступно:      `{available:,.2f}`\n"
        f"  🎯 Дневной лимит: `{limit:,.2f}`\n"
        f"  📅 До зарплаты:   `{days}` дн. "
        f"(_{ income_date.strftime('%d.%m.%Y')}_)\n\n"
        f"💚 Финансовое здоровье:\n{bar}\n\n"
        f"{forecast}",
        parse_mode="Markdown",
        reply_markup=main_menu,
    )


# ─────────────────────────── Helpers ──────────────────────────────

def _health_bar(ratio: float, length: int = 12) -> str:
    ratio = max(0.0, min(1.0, ratio))
    filled = round(ratio * length)
    empty = length - filled
    bar = "█" * filled + "░" * empty
    pct = int(ratio * 100)
    emoji = "🟢" if ratio > 0.6 else "🟡" if ratio > 0.3 else "🔴"
    return f"{emoji} `[{bar}]` {pct}%"


def _forecast(available: float, limit: float, days_until_income: int) -> str:
    if limit <= 0:
        return "⚠️ *Прогноз:* Нет доступных средств. Дождись зарплаты."

    days_budget_covers = available / limit
    deficit = days_until_income - days_budget_covers

    if deficit <= 0:
        return (
            f"✅ *Прогноз:* Деньги должны дотянуть до зарплаты. "
            f"При текущем режиме у тебя останется запас на "
            f"`{abs(deficit):.1f}` дн. 🎉"
        )
    else:
        return (
            f"⚠️ *Прогноз:* При текущих расходах деньги кончатся "
            f"через `{days_budget_covers:.1f}` дн. — за "
            f"`{deficit:.1f}` дн. до зарплаты.\n"
            f"Сократи расходы до `{available / days_until_income:,.2f}` в день!"
        )
