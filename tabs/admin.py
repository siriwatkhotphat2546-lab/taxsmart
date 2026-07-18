import streamlit as st
import pandas as pd
from datetime import date, datetime

from core.db import get_conn, read_sql
from core.plans import PLANS, get_user_plan
from core.auth import _hash_password, send_email


def render(USER):
    st.title("🛠️ แดชบอร์ดผู้ดูแลระบบ")
    st.caption("ภาพรวมการใช้งานทั้งระบบ — เฉพาะผู้ดูแลเท่านั้น")

    conn = get_conn()
    all_users = read_sql("SELECT * FROM users", conn)
    all_txn = read_sql("SELECT * FROM transactions", conn)
    all_consult = read_sql("SELECT * FROM consult_requests", conn)
    try:
        all_fb = read_sql("SELECT * FROM feedback", conn)
    except Exception:
        all_fb = pd.DataFrame()
    conn.close()

    # ===== ตัวเลขสำคัญ =====
    st.markdown("##### 📊 สถิติรวม")
    a1, a2, a3, a4 = st.columns(4)
    a1.metric("👥 ผู้ใช้ทั้งหมด", f"{len(all_users)} คน")
    a2.metric("📒 รายการบันทึก", f"{len(all_txn)} รายการ")
    a3.metric("🤝 คำขอปรึกษา", f"{len(all_consult)} รายการ")
    a4.metric("💬 ข้อความแจ้ง", f"{len(all_fb)} ข้อความ")

    # ผู้ใช้ที่ active (มีการบันทึกข้อมูล)
    if not all_txn.empty and "user_id" in all_txn.columns:
        active_users = all_txn["user_id"].nunique()
        st.caption(f"📈 ผู้ใช้ที่มีการบันทึกข้อมูลจริง (Active): {active_users} คน")

    st.divider()

    # ===== รายชื่อผู้ใช้ =====
    st.markdown("##### 👥 รายชื่อผู้ใช้ทั้งหมด")
    if not all_users.empty:
        show_users = all_users.copy()
        if "pw_hash" in show_users.columns:
            show_users = show_users.drop(columns=["pw_hash"])  # ไม่โชว์รหัสผ่าน
        st.dataframe(show_users, use_container_width=True, hide_index=True)
    else:
        st.info("ยังไม่มีผู้ใช้")

    # ===== คำขอปรึกษา (สำคัญ — มีลูกค้าติดต่อมา) =====
    st.divider()
    st.markdown("##### 🤝 คำขอปรึกษาจากลูกค้า")
    if not all_consult.empty:
        st.dataframe(all_consult, use_container_width=True, hide_index=True)
    else:
        st.info("ยังไม่มีคำขอปรึกษา")

    # ===== ข้อความแจ้งปัญหา =====
    if not all_fb.empty:
        st.divider()
        st.markdown("##### 💬 ข้อความแจ้งปัญหา/ข้อเสนอแนะ")
        st.dataframe(all_fb, use_container_width=True, hide_index=True)

    st.divider()
    # =====================================================================
    #  💰 ระบบรายได้ — อนุมัติสลิป + Dashboard รายได้ + ค่าใช้จ่ายกิจการ
    # =====================================================================
    st.divider()
    st.markdown("## 💰 ระบบรายได้ (Business Dashboard)")

    conn = get_conn()
    all_pay = read_sql("SELECT * FROM payments", conn)
    try:
        all_exp = read_sql("SELECT * FROM biz_expenses", conn)
    except Exception:
        all_exp = pd.DataFrame()
    conn.close()

    approved = all_pay[all_pay["status"] == "approved"] if not all_pay.empty else pd.DataFrame()
    pending = all_pay[all_pay["status"] == "pending"] if not all_pay.empty else pd.DataFrame()

    # ---------- ตัวเลขสำคัญ ----------
    total_rev = approved["amount"].sum() if not approved.empty else 0.0
    total_exp = all_exp["amount"].sum() if not all_exp.empty else 0.0
    net_profit = total_rev - total_exp

    # MRR = รายได้ต่อเดือน (จากสมาชิกที่ยัง active)
    mrr = 0.0
    if not all_users.empty and "plan" in all_users.columns:
        for _, u in all_users.iterrows():
            up = u.get("plan", "free")
            if up in ("premium", "consult"):
                exp = u.get("plan_expiry")
                try:
                    if exp and datetime.fromisoformat(str(exp)).date() >= date.today():
                        mrr += PLANS[up]["price"]
                except Exception:
                    pass

    r1, r2, r3, r4 = st.columns(4)
    r1.metric("💵 รายได้รวม", f"{total_rev:,.0f} ฿")
    r2.metric("💸 ค่าใช้จ่ายกิจการ", f"{total_exp:,.0f} ฿")
    r3.metric("📊 กำไรสุทธิ", f"{net_profit:,.0f} ฿")
    r4.metric("🔄 MRR (รายได้ประจำ/เดือน)", f"{mrr:,.0f} ฿")

    # จำนวนสมาชิกแต่ละแพ็ก
    st.markdown("##### 👥 สมาชิกแต่ละแพ็กเกจ")
    if not all_users.empty and "plan" in all_users.columns:
        plan_counts = all_users["plan"].fillna("free").value_counts()
        pl1, pl2, pl3 = st.columns(3)
        pl1.metric("🆓 ฟรี", f"{plan_counts.get('free', 0)} คน")
        pl2.metric("⭐ พรีเมียม", f"{plan_counts.get('premium', 0)} คน")
        pl3.metric("👑 ที่ปรึกษา", f"{plan_counts.get('consult', 0)} คน")

    # ---------- สลิปรอตรวจสอบ (สำคัญที่สุด) ----------
    st.divider()
    st.markdown(f"##### ⏳ การชำระเงินรอตรวจสอบ ({len(pending)} รายการ)")
    if not pending.empty:
        for _, p in pending.iterrows():
            with st.container():
                pc1, pc2, pc3 = st.columns([2, 2, 1])
                with pc1:
                    st.markdown(f"**{p['user_id']}** — {PLANS.get(p['plan'], {}).get('name', p['plan'])}")
                    st.caption(f"ยอด {p['amount']:,.0f} ฿ · {p['months']} เดือน")
                with pc2:
                    st.caption(f"อ้างอิง: {p['ref_code']}")
                    st.caption(f"{p['slip_note']}")
                with pc3:
                    if st.button("✅ อนุมัติ", key=f"appr_{p['id']}"):
                        # คำนวณวันหมดอายุ
                        exp_date = date.today()
                        m = int(p["months"])
                        y, mo = exp_date.year, exp_date.month + m
                        while mo > 12:
                            mo -= 12; y += 1
                        try:
                            new_exp = date(y, mo, exp_date.day).isoformat()
                        except ValueError:
                            new_exp = date(y, mo, 28).isoformat()
                        c = get_conn()
                        c.execute("UPDATE payments SET status='approved', approved_at=? WHERE id=?",
                                  (datetime.now().isoformat(timespec="seconds"), int(p["id"])))
                        c.execute("UPDATE users SET plan=?, plan_expiry=? WHERE username=?",
                                  (p["plan"], new_exp, p["user_id"]))
                        c.commit()
                        get_user_plan.clear()
                        # ส่งอีเมลยืนยัน
                        urow = read_sql("SELECT email FROM users WHERE username=?", c, params=(p["user_id"],))
                        c.close()
                        if not urow.empty and urow.iloc[0]["email"]:
                            send_email(
                                urow.iloc[0]["email"],
                                "เงินไทย — ยืนยันการชำระเงินสำเร็จ",
                                f"สวัสดีคุณ {p['user_id']}\\n\\n"
                                f"เราได้รับการชำระเงินของคุณเรียบร้อยแล้ว\\n"
                                f"แพ็กเกจ: {PLANS.get(p['plan'],{}).get('name', p['plan'])}\\n"
                                f"ยอด: {p['amount']:,.0f} บาท ({p['months']} เดือน)\\n"
                                f"ใช้งานได้ถึง: {new_exp}\\n\\n"
                                f"ขอบคุณที่ใช้บริการ เงินไทย\\n— ทีมงาน เงินไทย"
                            )
                        st.success(f"อนุมัติ {p['user_id']} แล้ว (ถึง {new_exp})")
                        st.rerun()
                    if st.button("❌ ปฏิเสธ", key=f"rej_{p['id']}"):
                        c = get_conn()
                        c.execute("UPDATE payments SET status='rejected' WHERE id=?", (int(p["id"]),))
                        c.commit(); c.close()
                        st.rerun()
                st.divider()
    else:
        st.info("ไม่มีรายการรอตรวจสอบ")

    # ---------- แนวโน้มรายได้ + พยากรณ์ ----------
    if not approved.empty:
        st.markdown("##### 📈 แนวโน้มรายได้")
        ap = approved.copy()
        ap["created_at"] = pd.to_datetime(ap["created_at"], errors="coerce")
        ap["เดือน"] = ap["created_at"].dt.to_period("M").astype(str)
        rev_by_month = ap.groupby("เดือน")["amount"].sum()
        st.bar_chart(rev_by_month)

        # พยากรณ์ 3 เดือนข้างหน้า (เฉลี่ยเชิงเส้น)
        if len(rev_by_month) >= 2:
            avg_rev = rev_by_month.mean()
            growth = (rev_by_month.iloc[-1] - rev_by_month.iloc[0]) / max(len(rev_by_month)-1, 1)
            st.markdown("**🔮 พยากรณ์กระแสเงินสด 3 เดือนข้างหน้า**")
            f1, f2, f3 = st.columns(3)
            for i, c in enumerate([f1, f2, f3], 1):
                proj = max(0, rev_by_month.iloc[-1] + growth * i)
                c.metric(f"เดือนที่ +{i}", f"{proj:,.0f} ฿")
            st.caption(f"อิงจากค่าเฉลี่ย {avg_rev:,.0f} ฿/เดือน และแนวโน้ม {growth:+,.0f} ฿/เดือน")

    # ---------- บันทึกค่าใช้จ่ายกิจการ ----------
    st.divider()
    st.markdown("##### 💸 ค่าใช้จ่ายของกิจการ (เงินไทย)")
    with st.form("biz_exp_form", clear_on_submit=True):
        e1, e2, e3 = st.columns(3)
        with e1:
            exp_date_in = st.text_input("วันที่ (YYYY-MM-DD)", value=date.today().isoformat())
        with e2:
            exp_cat = st.selectbox("หมวด", ["ค่าเซิร์ฟเวอร์/โฮสติ้ง", "ค่าโดเมน", "ค่าการตลาด/โฆษณา",
                                            "ค่าเครื่องมือ/ซอฟต์แวร์", "ค่าจ้างงาน", "อื่นๆ"])
        with e3:
            exp_amt = st.number_input("จำนวนเงิน (บาท)", min_value=0.0, step=100.0, format="%.2f")
        exp_desc = st.text_input("รายละเอียด (ไม่บังคับ)")
        if st.form_submit_button("บันทึกค่าใช้จ่าย", use_container_width=True):
            if exp_amt > 0:
                c = get_conn()
                c.execute("INSERT INTO biz_expenses (exp_date, category, description, amount) VALUES (?,?,?,?)",
                          (exp_date_in, exp_cat, exp_desc, float(exp_amt)))
                c.commit(); c.close()
                st.success("✅ บันทึกค่าใช้จ่ายแล้ว")
                st.rerun()
            else:
                st.error("กรุณากรอกจำนวนเงิน")

    if not all_exp.empty:
        st.dataframe(all_exp[["exp_date", "category", "description", "amount"]],
                     use_container_width=True, hide_index=True)

    # ===== จัดการผู้ใช้ (ลบ / รีเซ็ตรหัสผ่าน) =====
    st.divider()
    st.markdown("##### ⚙️ จัดการผู้ใช้")
    if not all_users.empty:
        mg1, mg2 = st.columns(2)
        user_list = all_users["username"].tolist()

        with mg1:
            st.markdown("**🔑 รีเซ็ตรหัสผ่านผู้ใช้**")
            reset_user = st.selectbox("เลือกผู้ใช้", user_list, key="reset_user_sel")
            new_pw = st.text_input("รหัสผ่านใหม่ (อย่างน้อย 6 ตัว)", type="password", key="reset_new_pw")
            if st.button("รีเซ็ตรหัสผ่าน", key="do_reset_pw"):
                if len(new_pw) < 6:
                    st.error("รหัสผ่านต้องยาวอย่างน้อย 6 ตัว")
                else:
                    c = get_conn()
                    c.execute("UPDATE users SET pw_hash=? WHERE username=?",
                              (_hash_password(new_pw), reset_user))
                    c.commit(); c.close()
                    st.success(f"✅ รีเซ็ตรหัสผ่านของ {reset_user} แล้ว")

        with mg2:
            st.markdown("**🗑️ ลบผู้ใช้ (พร้อมข้อมูลทั้งหมด)**")
            del_user = st.selectbox("เลือกผู้ใช้ที่จะลบ", user_list, key="del_user_sel")
            st.caption("⚠️ ลบถาวร กู้คืนไม่ได้")
            if st.session_state.get("confirm_del_user"):
                st.error(f"ยืนยันลบ {del_user} และข้อมูลทั้งหมด?")
                d1, d2 = st.columns(2)
                with d1:
                    if st.button("✅ ยืนยันลบ", key="confirm_del_yes"):
                        c = get_conn()
                        c.execute("DELETE FROM transactions WHERE user_id=?", (del_user,))
                        c.execute("DELETE FROM consult_requests WHERE user_id=?", (del_user,))
                        try:
                            c.execute("DELETE FROM inventory WHERE user_id=?", (del_user,))
                            c.execute("DELETE FROM feedback WHERE user_id=?", (del_user,))
                        except Exception:
                            pass
                        c.execute("DELETE FROM users WHERE username=?", (del_user,))
                        c.commit(); c.close()
                        st.session_state.confirm_del_user = False
                        st.success(f"✅ ลบผู้ใช้ {del_user} แล้ว")
                        st.rerun()
                with d2:
                    if st.button("ยกเลิก", key="confirm_del_no"):
                        st.session_state.confirm_del_user = False
                        st.rerun()
            else:
                if st.button("🗑️ ลบผู้ใช้นี้", key="req_del_user"):
                    st.session_state.confirm_del_user = True
                    st.rerun()

    st.divider()
    if st.button("← ออกจากโหมดผู้ดูแล กลับหน้าปกติ"):
        st.session_state.is_admin = False
        st.rerun()
    st.stop()

