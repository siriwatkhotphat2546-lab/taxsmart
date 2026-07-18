import streamlit as st
import sqlite3
import pandas as pd

# =====================================================================
#  ฐานข้อมูลกลาง (Single Source of Truth) — รองรับทั้ง SQLite และ Supabase(Postgres)
# =====================================================================
DB = "taxsmart.db"

# ตรวจว่ามี Supabase connection string ใน Secrets หรือไม่
def _get_pg_url():
    try:
        url = st.secrets.get("DB_CONNECTION", None)
        return url if url else None
    except Exception:
        return None

USE_PG = _get_pg_url() is not None

if USE_PG:
    from sqlalchemy import create_engine, text as _sql_text

    @st.cache_resource
    def _get_engine():
        # ใช้ SQLAlchemy engine ล้วน (เสถียร รองรับ pandas โดยตรง)
        pg_url = _get_pg_url()
        # ใช้ pg8000 (Python ล้วน ไม่มีปัญหา segfault) แทน psycopg2
        if pg_url.startswith("postgresql://"):
            pg_url = pg_url.replace("postgresql://", "postgresql+pg8000://", 1)
        elif pg_url.startswith("postgres://"):
            pg_url = pg_url.replace("postgres://", "postgresql+pg8000://", 1)
        return create_engine(pg_url, pool_pre_ping=True, pool_recycle=280)

    _engine = _get_engine()

class _PGConnWrapper:
    """ห่อ SQLAlchemy connection ให้ใช้งานเหมือน sqlite3 (execute/executemany/commit/close + แปลง ? เป็น :p0,:p1)"""
    def __init__(self, sa_conn):
        self._c = sa_conn
    def _prep(self, sql, params):
        # แปลง ? เป็น named parameter :p0 :p1 ... สำหรับ SQLAlchemy text()
        if params:
            parts = sql.split("?")
            new_sql = ""
            pdict = {}
            for i, part in enumerate(parts[:-1]):
                new_sql += part + f":p{i}"
                pdict[f"p{i}"] = params[i]
            new_sql += parts[-1]
            return _sql_text(new_sql), pdict
        return _sql_text(sql), {}
    def execute(self, sql, params=None):
        s, p = self._prep(sql, params)
        return self._c.execute(s, p)
    def executemany(self, sql, seq):
        for params in seq:
            self.execute(sql, params)
    def commit(self):
        self._c.commit()
    def close(self):
        self._c.close()
    @property
    def engine(self):
        return _engine

def _create_tables_sqlite(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            txn_date TEXT NOT NULL,
            txn_type TEXT NOT NULL,
            income_type TEXT,
            category TEXT NOT NULL,
            description TEXT,
            amount REAL NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    existing = [r[1] for r in conn.execute("PRAGMA table_info(transactions)").fetchall()]
    migrations = {
        "income_type": "ALTER TABLE transactions ADD COLUMN income_type TEXT",
        "description": "ALTER TABLE transactions ADD COLUMN description TEXT",
        "created_at": "ALTER TABLE transactions ADD COLUMN created_at TEXT",
        "user_id": "ALTER TABLE transactions ADD COLUMN user_id TEXT",
    }
    for col, sql in migrations.items():
        if col not in existing:
            conn.execute(sql)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT, fb_type TEXT, message TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT, move_date TEXT NOT NULL, product TEXT NOT NULL,
            move_type TEXT NOT NULL, qty REAL NOT NULL, unit_cost REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS consult_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT, service TEXT, contact TEXT, detail TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            pw_hash TEXT NOT NULL,
            email TEXT,
            plan TEXT DEFAULT 'free',
            plan_expiry TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            last_login TEXT
        )
    """)
    # auto-migration: เพิ่มคอลัมน์ใหม่ให้ตาราง users เดิม
    ucols = [r[1] for r in conn.execute("PRAGMA table_info(users)").fetchall()]
    for col, sql in {
        "email": "ALTER TABLE users ADD COLUMN email TEXT",
        "plan": "ALTER TABLE users ADD COLUMN plan TEXT DEFAULT 'free'",
        "plan_expiry": "ALTER TABLE users ADD COLUMN plan_expiry TEXT",
    }.items():
        if col not in ucols:
            conn.execute(sql)
    # ===== ระบบกระเป๋าเงิน =====
    conn.execute("""
        CREATE TABLE IF NOT EXISTS wallets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            name TEXT NOT NULL,
            wtype TEXT DEFAULT 'ธนาคาร',
            opening_balance REAL DEFAULT 0,
            is_business INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # auto-migration: เพิ่มคอลัมน์กระเป๋า + เงินได้/ไม่ใช่เงินได้
    tcols = [r[1] for r in conn.execute("PRAGMA table_info(transactions)").fetchall()]
    for col, sql in {
        "wallet": "ALTER TABLE transactions ADD COLUMN wallet TEXT",
        "is_taxable": "ALTER TABLE transactions ADD COLUMN is_taxable INTEGER DEFAULT 1",
        "non_income_type": "ALTER TABLE transactions ADD COLUMN non_income_type TEXT",
    }.items():
        if col not in tcols:
            conn.execute(sql)
    # ตารางการชำระเงิน
    conn.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            plan TEXT NOT NULL,
            amount REAL NOT NULL,
            months INTEGER DEFAULT 1,
            ref_code TEXT,
            slip_note TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            approved_at TEXT
        )
    """)
    # ===== ยายนึก (Mascot) =====
    conn.execute("""
        CREATE TABLE IF NOT EXISTS mascot (
            user_id TEXT PRIMARY KEY,
            name TEXT DEFAULT 'ยายนึก',
            coins INTEGER DEFAULT 0,
            streak INTEGER DEFAULT 0,
            last_fed TEXT,
            outfit TEXT DEFAULT 'ธรรมดา',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # ===== โหมดออมด้วยกัน (Partner Mode) =====
    conn.execute("""
        CREATE TABLE IF NOT EXISTS partners (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner TEXT NOT NULL,
            partner TEXT NOT NULL,
            nickname TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS shared_goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner TEXT NOT NULL,
            partner TEXT,
            goal_name TEXT NOT NULL,
            target_amount REAL NOT NULL,
            saved_amount REAL DEFAULT 0,
            deadline TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # ตารางค่าใช้จ่ายกิจการ (สำหรับ Dashboard เจ้าของ)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS biz_expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exp_date TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            amount REAL NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

_PG_TABLES_READY = False
def _create_tables_pg():
    stmts = [
        """CREATE TABLE IF NOT EXISTS transactions (
            id SERIAL PRIMARY KEY, txn_date TEXT NOT NULL, txn_type TEXT NOT NULL,
            income_type TEXT, category TEXT NOT NULL, description TEXT,
            amount REAL NOT NULL, user_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""",
        """CREATE TABLE IF NOT EXISTS feedback (
            id SERIAL PRIMARY KEY, user_id TEXT, fb_type TEXT, message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""",
        """CREATE TABLE IF NOT EXISTS inventory (
            id SERIAL PRIMARY KEY, user_id TEXT, move_date TEXT NOT NULL, product TEXT NOT NULL,
            move_type TEXT NOT NULL, qty REAL NOT NULL, unit_cost REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""",
        """CREATE TABLE IF NOT EXISTS consult_requests (
            id SERIAL PRIMARY KEY, user_id TEXT, service TEXT, contact TEXT, detail TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""",
        """CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY, pw_hash TEXT NOT NULL,
            email TEXT, plan TEXT DEFAULT 'free', plan_expiry TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, last_login TIMESTAMP)""",
        """ALTER TABLE users ADD COLUMN IF NOT EXISTS email TEXT""",
        """ALTER TABLE users ADD COLUMN IF NOT EXISTS plan TEXT DEFAULT 'free'""",
        """ALTER TABLE users ADD COLUMN IF NOT EXISTS plan_expiry TEXT""",
        """CREATE TABLE IF NOT EXISTS payments (
            id SERIAL PRIMARY KEY, user_id TEXT NOT NULL, plan TEXT NOT NULL,
            amount REAL NOT NULL, months INTEGER DEFAULT 1, ref_code TEXT,
            slip_note TEXT, status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, approved_at TIMESTAMP)""",
        """CREATE TABLE IF NOT EXISTS biz_expenses (
            id SERIAL PRIMARY KEY, exp_date TEXT NOT NULL, category TEXT NOT NULL,
            description TEXT, amount REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""",
        """CREATE TABLE IF NOT EXISTS mascot (
            user_id TEXT PRIMARY KEY, name TEXT DEFAULT 'ยายนึก',
            coins INTEGER DEFAULT 0, streak INTEGER DEFAULT 0, last_fed TEXT,
            outfit TEXT DEFAULT 'ธรรมดา',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""",
        """CREATE TABLE IF NOT EXISTS partners (
            id SERIAL PRIMARY KEY, owner TEXT NOT NULL, partner TEXT NOT NULL,
            nickname TEXT, status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""",
        """CREATE TABLE IF NOT EXISTS shared_goals (
            id SERIAL PRIMARY KEY, owner TEXT NOT NULL, partner TEXT,
            goal_name TEXT NOT NULL, target_amount REAL NOT NULL,
            saved_amount REAL DEFAULT 0, deadline TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""",
        """CREATE TABLE IF NOT EXISTS wallets (
            id SERIAL PRIMARY KEY, user_id TEXT NOT NULL, name TEXT NOT NULL,
            wtype TEXT DEFAULT 'ธนาคาร', opening_balance REAL DEFAULT 0,
            is_business INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""",
        """ALTER TABLE transactions ADD COLUMN IF NOT EXISTS wallet TEXT""",
        """ALTER TABLE transactions ADD COLUMN IF NOT EXISTS is_taxable INTEGER DEFAULT 1""",
        """ALTER TABLE transactions ADD COLUMN IF NOT EXISTS non_income_type TEXT""",
    ]
    with _engine.begin() as c:
        for s in stmts:
            c.execute(_sql_text(s))

def get_conn():
    if USE_PG:
        global _PG_TABLES_READY
        if not _PG_TABLES_READY:
            _create_tables_pg()
            _PG_TABLES_READY = True
        return _PGConnWrapper(_engine.connect())
    else:
        conn = sqlite3.connect(DB)
        _create_tables_sqlite(conn)
        return conn

# ตัวช่วยอ่านข้อมูลเป็น DataFrame ให้ทำงานได้ทั้ง 2 ฐานข้อมูล
def read_sql(sql, conn, params=None):
    if USE_PG:
        # แปลง ? เป็น named param แล้วอ่านผ่าน SQLAlchemy engine (pandas รองรับ)
        if params:
            parts = sql.split("?")
            new_sql = ""
            pdict = {}
            for i, part in enumerate(parts[:-1]):
                new_sql += part + f":p{i}"
                pdict[f"p{i}"] = params[i]
            new_sql += parts[-1]
            return pd.read_sql_query(_sql_text(new_sql), _engine, params=pdict)
        return pd.read_sql_query(_sql_text(sql), _engine)
    else:
        return pd.read_sql_query(sql, conn, params=params)


# ===== ระบบกระเป๋าเงิน (Wallets) + แยกเงินได้ / ไม่ใช่เงินได้ =====
# =====================================================================
#  ระบบกระเป๋าเงิน (Wallets) + แยกเงินได้ / ไม่ใช่เงินได้
# =====================================================================
NON_INCOME_TYPES = {
    "เงินโอนจากญาติ/เพื่อน": "เงินให้เปล่าจากบุคคล ไม่ถือเป็นเงินได้พึงประเมิน",
    "เงินกู้ยืม": "เป็นหนี้สิน ไม่ใช่รายได้",
    "เงินคืนภาษี": "เป็นเงินที่จ่ายเกินไปแล้วได้คืน ไม่ใช่รายได้ใหม่",
    "โอนระหว่างบัญชีตัวเอง": "แค่ย้ายเงิน ไม่ใช่รายได้ (สำคัญ! ถ้านับผิดจะเสียภาษีเกิน)",
    "เงินทอน/คืนสินค้า": "เงินที่ได้คืนจากการซื้อ ไม่ใช่รายได้",
    "เงินลงทุนจากเจ้าของ": "เงินทุนที่ใส่เข้ากิจการ ไม่ใช่รายได้",
    "รางวัล/ของขวัญ (ไม่เกินเกณฑ์)": "ตรวจสอบเกณฑ์ยกเว้นกับสรรพากร",
    "อื่นๆ (ไม่ใช่เงินได้)": "ระบุเพิ่มในรายละเอียด",
}

def get_wallets(username):
    conn = get_conn()
    w = read_sql("SELECT * FROM wallets WHERE user_id=? ORDER BY id", conn, params=(username,))
    conn.close()
    return w

def calc_wallet_balance(username, wallet_name, opening):
    """ยอดคงเหลือ = ยอดยกมา + รายรับ - รายจ่าย (ทุกรายการ ไม่ว่าจะเป็นเงินได้หรือไม่)"""
    conn = get_conn()
    df = read_sql("SELECT txn_type, amount FROM transactions WHERE user_id=? AND wallet=?",
                  conn, params=(username, wallet_name))
    conn.close()
    if df.empty:
        return float(opening), 0.0, 0.0
    inflow = df[df.txn_type == "รายรับ"]["amount"].sum()
    outflow = df[df.txn_type == "รายจ่าย"]["amount"].sum()
    return float(opening) + inflow - outflow, inflow, outflow

