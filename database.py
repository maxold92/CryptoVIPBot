import aiosqlite
from datetime import datetime, timedelta, timezone
from config import config


class Database:
    def __init__(self, path: str = config.database_path):
        self.path = path

    async def init(self):
        async with aiosqlite.connect(self.path) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    is_admin INTEGER DEFAULT 0,
                    vip_until TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            ''')
            await db.execute('''
                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    days INTEGER DEFAULT 30,
                    note TEXT,
                    created_at TEXT NOT NULL
                )
            ''')
            await db.commit()

    async def upsert_user(self, user):
        now = datetime.now(timezone.utc).isoformat()
        is_admin = 1 if user.id in config.admin_ids else 0
        async with aiosqlite.connect(self.path) as db:
            await db.execute('''
                INSERT INTO users(user_id, username, first_name, is_admin, created_at, updated_at)
                VALUES(?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    username=excluded.username,
                    first_name=excluded.first_name,
                    is_admin=excluded.is_admin,
                    updated_at=excluded.updated_at
            ''', (user.id, user.username, user.first_name, is_admin, now, now))
            await db.commit()

    async def is_vip(self, user_id: int) -> bool:
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute('SELECT vip_until FROM users WHERE user_id=?', (user_id,))
            row = await cur.fetchone()
        if not row or not row[0]:
            return False
        try:
            return datetime.fromisoformat(row[0]) > datetime.now(timezone.utc)
        except ValueError:
            return False

    async def vip_until(self, user_id: int) -> str | None:
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute('SELECT vip_until FROM users WHERE user_id=?', (user_id,))
            row = await cur.fetchone()
        return row[0] if row else None

    async def add_vip(self, user_id: int, days: int = 30, note: str = 'admin'):
        now = datetime.now(timezone.utc)
        current = await self.vip_until(user_id)
        start = now
        if current:
            try:
                old = datetime.fromisoformat(current)
                if old > now:
                    start = old
            except ValueError:
                pass
        vip_until = (start + timedelta(days=days)).isoformat()
        async with aiosqlite.connect(self.path) as db:
            await db.execute('UPDATE users SET vip_until=?, updated_at=? WHERE user_id=?', (vip_until, now.isoformat(), user_id))
            await db.execute('INSERT INTO payments(user_id, status, days, note, created_at) VALUES(?, ?, ?, ?, ?)',
                             (user_id, 'approved', days, note, now.isoformat()))
            await db.commit()
        return vip_until

    async def remove_vip(self, user_id: int):
        now = datetime.now(timezone.utc).isoformat()
        async with aiosqlite.connect(self.path) as db:
            await db.execute('UPDATE users SET vip_until=NULL, updated_at=? WHERE user_id=?', (now, user_id))
            await db.commit()

    async def stats(self) -> dict:
        async with aiosqlite.connect(self.path) as db:
            total = (await (await db.execute('SELECT COUNT(*) FROM users')).fetchone())[0]
            vip_rows = await (await db.execute('SELECT vip_until FROM users WHERE vip_until IS NOT NULL')).fetchall()
        active_vip = 0
        now = datetime.now(timezone.utc)
        for (vip_until,) in vip_rows:
            try:
                if datetime.fromisoformat(vip_until) > now:
                    active_vip += 1
            except ValueError:
                pass
        return {'users': total, 'active_vip': active_vip}


db = Database()
