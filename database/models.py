"""
database/models.py — CRUD operations for users and transactions.
"""
from datetime import datetime, timezone
from typing import Optional, TypedDict

import aiosqlite

from database.db import get_db


class UserStatsSnapshot(TypedDict):
    avg_daily_spend: float
    std_daily_spend: float
    spend_velocity: float
    risk_tolerance: float
    last_computed_at: str


# ─────────────────────────── USER CRUD ────────────────────────────


async def get_user(user_id: int) -> Optional[aiosqlite.Row]:
    """Fetch a user row by Telegram user_id. Returns None if not found."""
    async with get_db() as db:
        async with db.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        ) as cursor:
            return await cursor.fetchone()


async def create_user(user_id: int) -> None:
    """Insert a new user skeleton (onboarded=0) if not already present."""
    now = datetime.now(timezone.utc).isoformat()
    async with get_db() as db:
        await db.execute(
            """
            INSERT OR IGNORE INTO users
                (user_id, balance, reserve, next_income_date, onboarded, created_at)
            VALUES (?, 0, 0, '', 0, ?)
            """,
            (user_id, now),
        )
        await db.commit()


async def update_user_balance(user_id: int, balance: float) -> None:
    async with get_db() as db:
        await db.execute(
            "UPDATE users SET balance = ? WHERE user_id = ?", (balance, user_id)
        )
        await db.commit()


async def update_user_reserve(user_id: int, reserve: float) -> None:
    async with get_db() as db:
        await db.execute(
            "UPDATE users SET reserve = ? WHERE user_id = ?", (reserve, user_id)
        )
        await db.commit()


async def update_user_income_date(user_id: int, date_str: str) -> None:
    async with get_db() as db:
        await db.execute(
            "UPDATE users SET next_income_date = ? WHERE user_id = ?",
            (date_str, user_id),
        )
        await db.commit()


async def set_onboarded(
    user_id: int,
    balance: float,
    reserve: float,
    income_date: str,
) -> None:
    """Finalize onboarding: save all three fields and mark onboarded=1."""
    period_available = max(balance - reserve, 0.0)
    async with get_db() as db:
        await db.execute(
            """
            UPDATE users
            SET balance = ?, reserve = ?, next_income_date = ?, 
                period_available = ?, onboarded = 1
            WHERE user_id = ?
            """,
            (balance, reserve, income_date, period_available, user_id),
        )
        await db.commit()


async def reset_period_available(user_id: int, new_period_available: float) -> None:
    """Reset the period baseline (used when user updates settings manually)."""
    async with get_db() as db:
        await db.execute(
            "UPDATE users SET period_available = ? WHERE user_id = ?",
            (max(new_period_available, 0.0), user_id),
        )
        await db.commit()


# ─────────────────────────── TRANSACTION CRUD ─────────────────────


async def add_transaction(
    user_id: int,
    amount: float,
    description: str,
    verdict: str,
) -> None:
    """Persist a purchase evaluation result."""
    now = datetime.now(timezone.utc).isoformat()
    async with get_db() as db:
        await db.execute(
            """
            INSERT INTO transactions (user_id, amount, description, verdict, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, amount, description, verdict, now),
        )
        await db.commit()


async def get_recent_transactions(
    user_id: int, limit: int = 5
) -> list[aiosqlite.Row]:
    """Return the most recent `limit` transactions for a user."""
    async with get_db() as db:
        async with db.execute(
            """
            SELECT * FROM transactions
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (user_id, limit),
        ) as cursor:
            return await cursor.fetchall()


# ─────────────────────────── STATS CRUD ──────────────────────────────


async def get_user_stats(user_id: int) -> UserStatsSnapshot | None:
    """Fetch per-user spending stats from the users table."""
    async with get_db() as db:
        async with db.execute(
            "SELECT avg_daily_spend, std_daily_spend, spend_velocity, "
            "risk_tolerance, last_computed_at FROM users WHERE user_id = ?",
            (user_id,),
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            return UserStatsSnapshot(
                avg_daily_spend=row["avg_daily_spend"],
                std_daily_spend=row["std_daily_spend"],
                spend_velocity=row["spend_velocity"],
                risk_tolerance=row["risk_tolerance"],
                last_computed_at=row["last_computed_at"],
            )


async def upsert_user_stats(
    user_id: int,
    avg: float,
    std: float,
    velocity: float,
    tolerance: float,
) -> None:
    """Update the 5 stats columns in the users table, set last_computed_at."""
    now = datetime.now(timezone.utc).isoformat()
    async with get_db() as db:
        await db.execute(
            """UPDATE users SET avg_daily_spend = ?, std_daily_spend = ?,
            spend_velocity = ?, risk_tolerance = ?, last_computed_at = ?
            WHERE user_id = ?""",
            (avg, std, velocity, tolerance, now, user_id),
        )
        await db.commit()


async def get_category_stats(user_id: int, category: str) -> aiosqlite.Row | None:
    """Fetch category-level stats for a user."""
    async with get_db() as db:
        async with db.execute(
            "SELECT * FROM user_category_stats WHERE user_id = ? AND category = ?",
            (user_id, category),
        ) as cursor:
            return await cursor.fetchone()


async def upsert_category_stats(
    user_id: int, category: str, amount: float
) -> None:
    """Insert or update avg_amount and tx_count in user_category_stats.

    Uses an incremental moving average: new_avg = (old_avg * count + amount) / (count + 1)
    """
    now = datetime.now(timezone.utc).isoformat()
    async with get_db() as db:
        async with db.execute(
            "SELECT avg_amount, tx_count FROM user_category_stats "
            "WHERE user_id = ? AND category = ?",
            (user_id, category),
        ) as cursor:
            row = await cursor.fetchone()
        if row:
            new_avg = (row["avg_amount"] * row["tx_count"] + amount) / (row["tx_count"] + 1)
            new_count = row["tx_count"] + 1
            await db.execute(
                "UPDATE user_category_stats SET avg_amount = ?, tx_count = ?, "
                "last_seen_at = ? WHERE user_id = ? AND category = ?",
                (new_avg, new_count, now, user_id, category),
            )
        else:
            await db.execute(
                "INSERT INTO user_category_stats (user_id, category, avg_amount, tx_count, last_seen_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (user_id, category, amount, 1, now),
            )
        await db.commit()


async def get_recurring_spends(user_id: int) -> list[aiosqlite.Row]:
    """Return all recurring spend rows for a user."""
    async with get_db() as db:
        async with db.execute(
            "SELECT * FROM user_recurring_spends WHERE user_id = ? ORDER BY id",
            (user_id,),
        ) as cursor:
            return await cursor.fetchall()


async def upsert_recurring_spend(
    user_id: int,
    category: str,
    avg_amount: float,
    interval_days: int,
    last_amount: float,
    last_date: str,
    confidence: float,
    next_expected: str,
) -> None:
    """Insert or replace a row in user_recurring_spends."""
    async with get_db() as db:
        await db.execute(
            """INSERT OR REPLACE INTO user_recurring_spends
            (user_id, category, avg_amount, interval_days, last_amount,
             last_date, confidence, next_expected)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, category, avg_amount, interval_days, last_amount,
             last_date, confidence, next_expected),
        )
        await db.commit()
