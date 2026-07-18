import streamlit as st
import hashlib
import secrets as _secrets_mod
from datetime import datetime

from core.db import get_conn, read_sql

def _hash_password(password, salt=None):
    """เข้ารหัสรหัสผ่านด้วย PBKDF2-HMAC-SHA256 (ปลอดภัย ไม่เก็บรหัสจริง)"""
    if salt is None:
        salt = _secrets_mod.token_hex(16)
    pw_hash = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()
    return f"{salt}${pw_hash}"

def _verify_password(password, stored):
    """ตรวจรหัสผ่านว่าตรงกับที่เก็บไว้ไหม"""
    try:
        salt, _ = stored.split("$", 1)
        return _hash_password(password, salt) == stored
    except Exception:
        return False

def register_user(username, password, email=""):
    """สมัครสมาชิกใหม่ คืน (สำเร็จ, ข้อความ)"""
    username = username.strip()
    email = (email or "").strip()
    if not username or not password:
        return False, "กรุณากรอกชื่อผู้ใช้และรหัสผ่าน"
    if len(password) < 6:
        return False, "รหัสผ่านต้องยาวอย่างน้อย 6 ตัวอักษร"
    if email and ("@" not in email or "." not in email):
        return False, "รูปแบบอีเมลไม่ถูกต้อง"
    conn = get_conn()
    existing = read_sql("SELECT username FROM users WHERE username=?", conn, params=(username,))
    if not existing.empty:
        conn.close()
        return False, "ชื่อผู้ใช้นี้มีคนใช้แล้ว กรุณาเลือกชื่ออื่น หรือเข้าสู่ระบบ"
    pw_hash = _hash_password(password)
    conn.execute("INSERT INTO users (username, pw_hash, email, plan) VALUES (?,?,?,?)",
                 (username, pw_hash, email, "free"))
    conn.commit()
    conn.close()
    return True, "สมัครสมาชิกสำเร็จ!"

# =====================================================================
#  ระบบส่งอีเมล (ผ่าน Gmail SMTP — ฟรี)
# =====================================================================
def send_email(to_email, subject, body):
    """ส่งอีเมลผ่าน Gmail SMTP คืน (สำเร็จ, ข้อความ)"""
    try:
        gmail_user = st.secrets.get("GMAIL_USER", "")
        gmail_pw = st.secrets.get("GMAIL_APP_PASSWORD", "")
    except Exception:
        gmail_user = gmail_pw = ""
    if not gmail_user or not gmail_pw:
        return False, "ยังไม่ได้ตั้งค่าอีเมลผู้ส่ง (GMAIL_USER / GMAIL_APP_PASSWORD ใน Secrets)"
    if not to_email:
        return False, "ไม่มีอีเมลผู้รับ"
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        msg = MIMEMultipart()
        msg["From"] = f"เงินไทย <{gmail_user}>"
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))

        server = smtplib.SMTP("smtp.gmail.com", 587, timeout=20)
        server.starttls()
        server.login(gmail_user, gmail_pw)
        server.send_message(msg)
        server.quit()
        return True, "ส่งอีเมลสำเร็จ"
    except Exception as e:
        return False, f"ส่งอีเมลไม่สำเร็จ: {str(e)[:100]}"

def reset_password_by_email(username):
    """รีเซ็ตรหัสผ่านและส่งรหัสใหม่เข้าอีเมล"""
    username = username.strip()
    conn = get_conn()
    rows = read_sql("SELECT email FROM users WHERE username=?", conn, params=(username,))
    if rows.empty:
        conn.close()
        return False, "ไม่พบชื่อผู้ใช้นี้"
    email = rows.iloc[0]["email"]
    if not email or str(email).strip() == "" or str(email) == "None":
        conn.close()
        return False, "บัญชีนี้ไม่ได้ผูกอีเมลไว้ กรุณาติดต่อผู้ดูแล LINE: 0610950531"
    # สร้างรหัสใหม่แบบสุ่ม
    new_pw = _secrets_mod.token_urlsafe(8)
    conn.execute("UPDATE users SET pw_hash=? WHERE username=?", (_hash_password(new_pw), username))
    conn.commit()
    conn.close()
    body = (
        f"สวัสดีคุณ {username}\n\n"
        f"เราได้รีเซ็ตรหัสผ่านของคุณตามที่ร้องขอ\n\n"
        f"รหัสผ่านใหม่ของคุณคือ: {new_pw}\n\n"
        f"กรุณาเข้าสู่ระบบด้วยรหัสนี้ และเปลี่ยนรหัสผ่านทันทีที่เข้าใช้งาน\n\n"
        f"เข้าสู่ระบบที่: https://taxsmart-2vv2pvoaftam7shbq4eyzz.streamlit.app/\n\n"
        f"หากคุณไม่ได้ร้องขอ กรุณาติดต่อเราทันที\n\n"
        f"— ทีมงาน เงินไทย\nLINE: 0610950531"
    )
    ok, msg = send_email(email, "เงินไทย — รหัสผ่านใหม่ของคุณ", body)
    if ok:
        return True, f"ส่งรหัสผ่านใหม่ไปที่อีเมล {email[:3]}***{email[-10:]} แล้ว กรุณาตรวจสอบกล่องจดหมาย (รวมถึง Spam)"
    return False, msg

def login_user(username, password):
    """เข้าสู่ระบบ คืน (สำเร็จ, ข้อความ)"""
    username = username.strip()
    conn = get_conn()
    rows = read_sql("SELECT pw_hash FROM users WHERE username=?", conn, params=(username,))
    if rows.empty:
        conn.close()
        return False, "ไม่พบชื่อผู้ใช้นี้ กรุณาสมัครสมาชิกก่อน"
    stored = rows.iloc[0]["pw_hash"]
    if _verify_password(password, stored):
        # อัปเดตเวลาเข้าล่าสุด
        conn.execute("UPDATE users SET last_login=? WHERE username=?",
                     (datetime.now().isoformat(timespec="seconds"), username))
        conn.commit()
        conn.close()
        return True, "เข้าสู่ระบบสำเร็จ"
    conn.close()
    return False, "รหัสผ่านไม่ถูกต้อง"

