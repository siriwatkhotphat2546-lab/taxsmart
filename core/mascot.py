import streamlit as st
import pandas as pd
from datetime import date

from core.db import get_conn, read_sql

# =====================================================================
#  ยายนึก (Mascot) — สะท้อนสุขภาพการเงิน
# =====================================================================
OUTFITS = {
    "ธรรมดา": {"emoji": "🐷", "cost": 0, "desc": "ยายนึกตัวจริง"},
    "ผ้าขาวม้า": {"emoji": "🐷🧣", "cost": 50, "desc": "ลุคไทยแท้"},
    "มงกุฎทอง": {"emoji": "🐷👑", "cost": 150, "desc": "เศรษฐีน้อย"},
    "หมวกชาวนา": {"emoji": "🐷👒", "cost": 80, "desc": "สายเกษตร"},
    "แว่นกันแดด": {"emoji": "🐷🕶️", "cost": 100, "desc": "คูลๆ"},
    "พวงมาลัย": {"emoji": "🐷💐", "cost": 120, "desc": "เฮงๆ รวยๆ"},
    "ชุดนักบัญชี": {"emoji": "🐷👔", "cost": 200, "desc": "มือโปร"},
}

@st.cache_data(ttl=60)
def get_mascot(username):
    conn = get_conn()
    m = read_sql("SELECT * FROM mascot WHERE user_id=?", conn, params=(username,))
    if m.empty:
        conn.execute("INSERT INTO mascot (user_id) VALUES (?)", (username,))
        conn.commit()
        m = read_sql("SELECT * FROM mascot WHERE user_id=?", conn, params=(username,))
    conn.close()
    return m.iloc[0] if not m.empty else None

def get_mascot_mood(username):
    """คืน (อีโมจิสถานะ, ชื่อสถานะ, ข้อความ, วันที่ไม่ได้บันทึก)"""
    conn = get_conn()
    df = read_sql("SELECT txn_date FROM transactions WHERE user_id=? ORDER BY txn_date DESC", conn, params=(username,))
    conn.close()
    if df.empty:
        return "👵", "ยายรอหลานอยู่", "ยายนึกยังรอหลานมาบันทึกครั้งแรกอยู่เลย มาเริ่มกันนะลูก", 999
    last = pd.to_datetime(df.iloc[0]["txn_date"]).date()
    days = (date.today() - last).days
    if days == 0:
        return "😊", "ยายภูมิใจ", "วันนี้หลานบันทึกแล้ว ยายนึกภูมิใจในตัวหลานมากเลย!", 0
    elif days <= 2:
        return "🙂", "ยายสดใส", f"ยายนึกสบายใจ หลานยังจำที่จะดูแลเงินอยู่ (ล่าสุด {days} วันก่อน)", days
    elif days <= 7:
        return "😟", "ยายเป็นห่วง", f"ยายนึกเริ่มเป็นห่วงแล้วนะ ไม่ได้บันทึก {days} วันแล้ว", days
    else:
        return "🥺", "ยายหิว-ยายคิดถึง", f"ยายนึกคิดถึงหลานจัง ไม่ได้เจอ {days} วันแล้ว กลับมาบันทึกกันนะ", days

def feed_mascot(username):
    """ให้อาหารน้อง (เรียกเมื่อบันทึกรายการ) — เพิ่มเหรียญ + streak"""
    conn = get_conn()
    m = read_sql("SELECT * FROM mascot WHERE user_id=?", conn, params=(username,))
    today = date.today().isoformat()
    if m.empty:
        conn.execute("INSERT INTO mascot (user_id, coins, streak, last_fed) VALUES (?,?,?,?)",
                     (username, 10, 1, today))
    else:
        row = m.iloc[0]
        last_fed = row["last_fed"]
        coins = int(row["coins"] or 0)
        streak = int(row["streak"] or 0)
        if last_fed == today:
            conn.close()
            return coins, streak, False  # ให้อาหารแล้ววันนี้
        # เช็ค streak ต่อเนื่อง
        if last_fed:
            try:
                gap = (date.today() - date.fromisoformat(str(last_fed))).days
                streak = streak + 1 if gap == 1 else 1
            except Exception:
                streak = 1
        else:
            streak = 1
        bonus = 20 if streak % 7 == 0 else 0  # โบนัสครบ 7 วัน
        coins += 10 + bonus
        conn.execute("UPDATE mascot SET coins=?, streak=?, last_fed=? WHERE user_id=?",
                     (coins, streak, today, username))
    conn.commit(); conn.close()
    get_mascot.clear()
    m2 = get_mascot(username)
    return int(m2["coins"]), int(m2["streak"]), True

