import aiosqlite
from datetime import datetime

DB_PATH = "database/bot.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            side TEXT,
            score INTEGER,
            entry TEXT,
            tp1 TEXT,
            tp2 TEXT,
            sl TEXT,
            created_at TEXT
        )
        """)
        await db.commit()

async def save_signal(symbol, side, score, entry, tp1, tp2, sl):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO signals(symbol, side, score, entry, tp1, tp2, sl, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (symbol, side, score, str(entry), str(tp1), str(tp2), str(sl), datetime.utcnow().isoformat())
        )
        await db.commit()
