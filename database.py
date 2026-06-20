import aiosqlite
from datetime import datetime
from config import DB_PATH


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS telethon_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_name TEXT UNIQUE NOT NULL,
                phone TEXT NOT NULL,
                api_id INTEGER NOT NULL,
                api_hash TEXT NOT NULL,
                username TEXT,
                is_active INTEGER DEFAULT 1
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER,
                name TEXT NOT NULL,
                link TEXT,
                description TEXT,
                has_avatar INTEGER DEFAULT 0,
                is_open INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                account_id INTEGER,
                is_for_sale INTEGER DEFAULT 1
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS purchase_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                group_id INTEGER NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TEXT NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS support_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                group_id INTEGER NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at TEXT NOT NULL
            )
        """)
        await db.commit()


async def add_telethon_account(session_name: str, phone: str, api_id: int, api_hash: str, username: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT OR REPLACE INTO telethon_accounts
               (session_name, phone, api_id, api_hash, username) VALUES (?, ?, ?, ?, ?)""",
            (session_name, phone, api_id, api_hash, username)
        )
        await db.commit()


async def get_all_accounts():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM telethon_accounts WHERE is_active = 1") as cur:
            return [dict(r) for r in await cur.fetchall()]


async def get_active_account():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM telethon_accounts WHERE is_active = 1 LIMIT 1") as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def add_group(telegram_id, name, link, description, has_avatar, is_open, account_id):
    async with aiosqlite.connect(DB_PATH) as db:
        created_at = datetime.now().isoformat()
        cursor = await db.execute(
            """INSERT INTO groups (telegram_id, name, link, description, has_avatar, is_open, created_at, account_id, is_for_sale)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)""",
            (telegram_id, name, link, description, int(has_avatar), int(is_open), created_at, account_id)
        )
        await db.commit()
        return cursor.lastrowid


async def get_groups_for_sale():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM groups WHERE is_for_sale = 1 ORDER BY id") as cur:
            return [dict(r) for r in await cur.fetchall()]


async def get_all_groups():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM groups ORDER BY id") as cur:
            return [dict(r) for r in await cur.fetchall()]


async def get_group(group_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM groups WHERE id = ?", (group_id,)) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def delete_group(group_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM groups WHERE id = ?", (group_id,))
        await db.commit()


async def set_group_for_sale(group_id: int, for_sale: bool):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE groups SET is_for_sale = ? WHERE id = ?", (int(for_sale), group_id))
        await db.commit()


async def add_purchase_request(user_id, username, first_name, last_name, group_id):
    async with aiosqlite.connect(DB_PATH) as db:
        created_at = datetime.now().isoformat()
        cursor = await db.execute(
            """INSERT INTO purchase_requests (user_id, username, first_name, last_name, group_id, status, created_at)
               VALUES (?, ?, ?, ?, ?, 'pending', ?)""",
            (user_id, username, first_name, last_name, group_id, created_at)
        )
        await db.commit()
        return cursor.lastrowid


async def get_pending_requests():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT pr.*, g.name as group_name, g.link as group_link, g.created_at as group_created_at
               FROM purchase_requests pr
               JOIN groups g ON pr.group_id = g.id
               WHERE pr.status = 'pending'
               ORDER BY pr.created_at"""
        ) as cur:
            return [dict(r) for r in await cur.fetchall()]


async def get_request(request_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT pr.*, g.name as group_name, g.link as group_link
               FROM purchase_requests pr
               JOIN groups g ON pr.group_id = g.id
               WHERE pr.id = ?""",
            (request_id,)
        ) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def delete_request(request_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM purchase_requests WHERE id = ?", (request_id,))
        await db.commit()


async def create_support_session(user_id: int, group_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE support_sessions SET is_active = 0 WHERE user_id = ?", (user_id,)
        )
        created_at = datetime.now().isoformat()
        cursor = await db.execute(
            "INSERT INTO support_sessions (user_id, group_id, is_active, created_at) VALUES (?, ?, 1, ?)",
            (user_id, group_id, created_at)
        )
        await db.commit()
        return cursor.lastrowid


async def get_active_session(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM support_sessions WHERE user_id = ? AND is_active = 1 ORDER BY id DESC LIMIT 1",
            (user_id,)
        ) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def close_session(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE support_sessions SET is_active = 0 WHERE user_id = ?", (user_id,)
        )
        await db.commit()
