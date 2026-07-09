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
        # Admins from ADMIN_IDS always have lifetime VIP access.
        if user_id in config.admin_ids:
            return True
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute('SELECT vip_until FROM users WHERE user_id=?', (user_id,))
            row = await cur.fetchone()
        if not row or not row[0]:
            return False
        if row[0] == 'lifetime':
            return True
        try:
            return datetime.fromisoformat(row[0]) > datetime.now(timezone.utc)
        except ValueError:
            return False

    async def vip_until(self, user_id: int) -> str | None:
        # Admins from ADMIN_IDS are shown as lifetime VIP.
        if user_id in config.admin_ids:
            return 'Бессрочно'
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute('SELECT vip_until FROM users WHERE user_id=?', (user_id,))
            row = await cur.fetchone()
        if not row:
            return None
        return 'Бессрочно' if row[0] == 'lifetime' else row[0]

    async def add_lifetime_vip(self, user_id: int, note: str = 'admin_lifetime'):
        now = datetime.now(timezone.utc).isoformat()
        async with aiosqlite.connect(self.path) as db:
            await db.execute("""
                INSERT INTO users(user_id, username, first_name, is_admin, vip_until, created_at, updated_at)
                VALUES(?, '', '', 0, 'lifetime', ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET vip_until='lifetime', updated_at=excluded.updated_at
            """, (user_id, now, now))
            await db.execute('INSERT INTO payments(user_id, status, days, note, created_at) VALUES(?, ?, ?, ?, ?)',
                             (user_id, 'approved', 999999, note, now))
            await db.commit()
        return 'Бессрочно'

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
            await db.execute('''
                INSERT INTO users(user_id, username, first_name, is_admin, vip_until, created_at, updated_at)
                VALUES(?, '', '', 0, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET vip_until=excluded.vip_until, updated_at=excluded.updated_at
            ''', (user_id, vip_until, now.isoformat(), now.isoformat()))
            await db.execute('INSERT INTO payments(user_id, status, days, note, created_at) VALUES(?, ?, ?, ?, ?)',
                             (user_id, 'approved', days, note, now.isoformat()))
            await db.commit()
        return vip_until

    async def create_payment_request(self, user_id: int, days: int = 30, note: str = 'user_pressed_paid'):
        now = datetime.now(timezone.utc).isoformat()
        async with aiosqlite.connect(self.path) as db:
            await db.execute('INSERT INTO payments(user_id, status, days, note, created_at) VALUES(?, ?, ?, ?, ?)',
                             (user_id, 'pending', days, note, now))
            await db.commit()

    async def remove_vip(self, user_id: int):
        now = datetime.now(timezone.utc).isoformat()
        async with aiosqlite.connect(self.path) as db:
            await db.execute('UPDATE users SET vip_until=NULL, updated_at=? WHERE user_id=?', (now, user_id))
            await db.commit()

    async def stats(self) -> dict:
        async with aiosqlite.connect(self.path) as db:
            total = (await (await db.execute('SELECT COUNT(*) FROM users')).fetchone())[0]
            pending = (await (await db.execute("SELECT COUNT(*) FROM payments WHERE status='pending'")).fetchone())[0]
            vip_rows = await (await db.execute('SELECT vip_until FROM users WHERE vip_until IS NOT NULL')).fetchall()
        active_vip = 0
        now = datetime.now(timezone.utc)
        for (vip_until,) in vip_rows:
            try:
                if datetime.fromisoformat(vip_until) > now:
                    active_vip += 1
            except ValueError:
                pass
        return {'users': total, 'active_vip': active_vip, 'pending': pending}

    async def list_users(self, limit: int = 10) -> list[dict]:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute('SELECT user_id, username, first_name, vip_until, created_at FROM users ORDER BY updated_at DESC LIMIT ?', (limit,))
            rows = await cur.fetchall()
        return [dict(r) for r in rows]


db = Database()
