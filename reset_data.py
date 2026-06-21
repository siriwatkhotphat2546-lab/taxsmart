"""
reset_data.py — ล้างข้อมูลเดิมทั้งหมดใน TaxSmart ให้เริ่มจากศูนย์
รันครั้งเดียว: python reset_data.py
"""
import sqlite3
import os

DB = "taxsmart.db"

if not os.path.exists(DB):
    print("ℹ️ ยังไม่มีไฟล์ฐานข้อมูล (taxsmart.db) — เริ่มต้นใหม่อยู่แล้ว ไม่ต้องล้าง")
else:
    conn = sqlite3.connect(DB)
    try:
        before = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
    except sqlite3.OperationalError:
        before = 0

    conn.execute("DELETE FROM transactions")
    try:
        conn.execute("DELETE FROM sqlite_sequence WHERE name='transactions'")
    except sqlite3.OperationalError:
        pass
    conn.commit()
    conn.close()

    print(f"✅ ล้างข้อมูลเรียบร้อย — ลบไป {before} รายการ")
    print("   ระบบพร้อมเริ่มใช้งานใหม่เหมือนไม่เคยมีข้อมูลเลย")