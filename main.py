import aiosqlite
from datetime import datetime

DB_PATH = "signals.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            direction TEXT,
            score INTEGER,
            entry REAL,
            tp1 REAL,
            tp2 REAL,
            tp3 REAL,
            sl REAL,
            created_at TEXT
        )
        """)
        await db.commit()

async def save_signal(s):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO signals(symbol,direction,score,entry,tp1,tp2,tp3,sl,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
            (s.symbol, s.direction, s.score, s.entry, s.tp1, s.tp2, s.tp3, s.sl, datetime.utcnow().isoformat())
        )
        await db.commit()
