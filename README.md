# FinGuard 🛡 — Telegram Financial Guard Bot

> A strict-but-caring parent that **approves ✅ or blocks ⛔** every purchase based on your daily spending limit.

---

## Quick Start

```bash
# 1. Clone / enter the project
cd finguard

# 2. Create & activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure your token
cp .env.example .env
# edit .env and set BOT_TOKEN=<your Telegram bot token>

# 5. Run
python bot.py
```

The SQLite database (`finguard.db`) is created automatically on first run.

---

## Project Structure

```
finguard/
├── bot.py                     # Entry point — starts long-polling
├── config.py                  # Loads BOT_TOKEN / LLM_URL from .env
├── .env.example               # Copy to .env and fill in
├── requirements.txt
├── database/
│   ├── db.py                  # SQLite init + get_db()
│   └── models.py              # CRUD for users & transactions
├── handlers/
│   ├── start.py               # /start + FSM onboarding (3 steps)
│   ├── purchase.py            # Free-text purchase evaluator
│   ├── status.py              # /status — health bar + forecast
│   └── settings.py            # /settings — inline update + history
├── services/
│   ├── calculator.py          # Core math: evaluate_purchase()
│   └── llm.py                 # Verdict messages (stub, LLM-ready)
├── states/
│   └── fsm.py                 # OnboardingStates, PurchaseStates, SettingsStates
├── keyboards/
│   └── reply.py               # Main menu ReplyKeyboardMarkup
└── middlewares/
    └── onboarding_check.py    # Redirect unboarded users to /start
```

---

## Core Algorithm

```
available    = balance - reserve
daily_limit  = available / days_until_income
overshoot%   = (amount - daily_limit) / daily_limit × 100

APPROVED  if overshoot% ≤ 50%
BLOCKED   if overshoot% > 50%
```

---

## Demo Scenarios

Set up with **balance = 2000, reserve = 500, income in 5 days → limit = 300/day**

| Input | Expected |
|---|---|
| `250 обед` | ✅ Approved — within limit |
| `1200 steam` | ⛔ Blocked — 300% over limit |
| `/status` | 📊 Health bar + days-left forecast |

---

## Input Formats Supported

```
300 кофе        →  amount=300  description="кофе"
кофе 300        →  amount=300  description="кофе"
300             →  amount=300  description="покупка"
хочу купить кофе за 300  →  same result
```

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `BOT_TOKEN` | ✅ | Your BotFather token |
| `LLM_URL` | ❌ | Real LLM endpoint (future use) |

---

## LLM Integration (Future)

`services/llm.py` has the full async signature ready.  
Uncomment the `httpx` block and point `LLM_URL` at your model endpoint.
