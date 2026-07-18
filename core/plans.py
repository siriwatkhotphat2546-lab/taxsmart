import streamlit as st
from datetime import date, datetime

from core.db import get_conn, read_sql

# =====================================================================
#  ระบบแพ็กเกจสมาชิก
# =====================================================================
PLANS = {
    "free": {"name": "🆓 ฟรี", "price": 0, "desc": "ใช้งานพื้นฐาน จำกัด 50 รายการ/เดือน"},
    "premium": {"name": "⭐ พรีเมียม", "price": 199, "desc": "บันทึกไม่จำกัด + Export + พยากรณ์กระแสเงินสด"},
    "consult": {"name": "👑 ที่ปรึกษาส่วนตัว", "price": 999, "desc": "ทุกอย่างในพรีเมียม + ที่ปรึกษาดูแลโดยตรง"},
}
FREE_TXN_LIMIT = 50

@st.cache_data(ttl=60)
def get_user_plan(username):
    """ดึงแพ็กเกจปัจจุบันของผู้ใช้ (เช็ควันหมดอายุด้วย)"""
    conn = get_conn()
    rows = read_sql("SELECT plan, plan_expiry FROM users WHERE username=?", conn, params=(username,))
    conn.close()
    if rows.empty:
        return "free", None
    plan = rows.iloc[0]["plan"] or "free"
    expiry = rows.iloc[0]["plan_expiry"]
    # ถ้าหมดอายุแล้ว กลับเป็น free
    if plan != "free" and expiry:
        try:
            exp_date = datetime.fromisoformat(str(expiry)).date()
            if exp_date < date.today():
                return "free", expiry
        except Exception:
            pass
    return plan, expiry

