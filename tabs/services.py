import streamlit as st
import pandas as pd
from datetime import date, datetime

from core.db import get_conn, read_sql
from core.plans import PLANS, FREE_TXN_LIMIT, get_user_plan


def render(tab_upgrade, tab_service, USER):
    with tab_upgrade:
        st.subheader("⭐ อัปเกรดแพ็กเกจ")

        cur_plan, cur_expiry = get_user_plan(USER)
        pinfo = PLANS.get(cur_plan, PLANS["free"])

        # แสดงแพ็กปัจจุบัน
        pc1, pc2 = st.columns([2,1])
        with pc1:
            st.info(f"แพ็กเกจปัจจุบันของคุณ: **{pinfo['name']}**" +
                    (f" (หมดอายุ {cur_expiry})" if cur_expiry and cur_plan != "free" else ""))
        with pc2:
            if cur_plan == "free":
                conn = get_conn()
                my_cnt = read_sql("SELECT COUNT(*) as c FROM transactions WHERE user_id=?", conn, params=(USER,))
                conn.close()
                used = int(my_cnt.iloc[0]["c"]) if not my_cnt.empty else 0
                st.metric("รายการที่ใช้", f"{used}/{FREE_TXN_LIMIT}")

        st.divider()
        st.markdown("##### 📦 เลือกแพ็กเกจ")

        p1, p2, p3 = st.columns(3)
        with p1:
            st.markdown("### 🆓 ฟรี")
            st.markdown("# 0 ฿")
            st.caption("ต่อเดือน")
            st.markdown("""
            - บันทึกบัญชี + คำนวณภาษี
            - ลดหย่อน 26 รายการ
            - Dashboard พื้นฐาน
            - จำกัด 50 รายการ/เดือน
            """)
        with p2:
            st.markdown("### ⭐ พรีเมียม")
            st.markdown("# 199 ฿")
            st.caption("ต่อเดือน")
            st.markdown("""
            - **บันทึกไม่จำกัด**
            - Export Excel/PDF ไม่จำกัด
            - พยากรณ์กระแสเงินสด
            - แจ้งเตือนกำหนดยื่นภาษี
            """)
        with p3:
            st.markdown("### 👑 ที่ปรึกษาส่วนตัว")
            st.markdown("# 999 ฿")
            st.caption("ต่อเดือน")
            st.markdown("""
            - **ทุกอย่างในพรีเมียม**
            - ปรึกษาผู้เชี่ยวชาญตลอดเดือน
            - วิเคราะห์กระแสเงินสดให้
            - วางแผนภาษีเฉพาะราย
            """)

        st.success("🎁 **โปรเปิดเว็บ:** ผู้ใช้ใหม่สมัครแพ็ก 999 รับสิทธิ์ใช้งาน **3 เดือน** ครอบคลุมถึงไตรมาสที่ต้องยื่นภาษี!")

        st.divider()
        st.markdown("##### 💳 ชำระเงิน")

        if cur_plan != "free":
            st.info("คุณมีแพ็กเกจอยู่แล้ว สามารถต่ออายุหรืออัปเกรดได้")

        pay_col1, pay_col2 = st.columns([1,1])

        with pay_col1:
            st.markdown("**1️⃣ เลือกแพ็กและระยะเวลา**")
            sel_plan = st.selectbox("แพ็กเกจ", ["premium", "consult"],
                                    format_func=lambda x: f"{PLANS[x]['name']} — {PLANS[x]['price']} บาท/เดือน")
            # โปรผู้ใช้ใหม่ 3 เดือน สำหรับแพ็ก consult
            if sel_plan == "consult":
                months = st.selectbox("ระยะเวลา", [3, 1, 6, 12],
                                      format_func=lambda m: f"{m} เดือน" + (" 🎁 โปรเปิดเว็บ!" if m == 3 else ""))
            else:
                months = st.selectbox("ระยะเวลา", [1, 3, 6, 12], format_func=lambda m: f"{m} เดือน")

            total = PLANS[sel_plan]["price"] * months
            st.metric("ยอดที่ต้องชำระ", f"{total:,.0f} บาท")

        with pay_col2:
            st.markdown("**2️⃣ โอนเงินผ่าน PromptPay**")
            st.markdown(f"""
            <div style="background:rgba(29,158,117,0.12);border:1px solid rgba(29,158,117,0.35);
            border-radius:12px;padding:16px;text-align:center">
            <div style="font-size:13px;color:#A8A4C8">พร้อมเพย์ (PromptPay)</div>
            <div style="font-size:24px;font-weight:700;color:#5DCAA5;margin:6px 0">098-667-3680</div>
            <div style="font-size:13px;color:#A8A4C8">ชื่อบัญชี: Siriwat Khotphat</div>
            <div style="font-size:20px;font-weight:700;margin-top:8px">ยอด: {total:,.0f} บาท</div>
            </div>
            """, unsafe_allow_html=True)
            st.caption("📱 เปิดแอปธนาคาร → สแกน/โอนพร้อมเพย์ → ใส่เบอร์และยอดข้างบน")

        st.markdown("**3️⃣ แจ้งการชำระเงิน**")
        with st.form("payment_form", clear_on_submit=True):
            pf1, pf2 = st.columns(2)
            with pf1:
                ref_code = st.text_input("เลขอ้างอิงการโอน / 4 ตัวท้ายบัญชี", placeholder="เช่น 1234")
            with pf2:
                pay_time = st.text_input("วันเวลาที่โอน", placeholder="เช่น 12/07/2569 14:30")
            slip_note = st.text_area("หมายเหตุเพิ่มเติม (ไม่บังคับ)", height=70,
                                     placeholder="เช่น โอนจากบัญชีกสิกร ชื่อ...")
            if st.form_submit_button("📨 แจ้งชำระเงิน", use_container_width=True):
                if not ref_code.strip():
                    st.error("กรุณากรอกเลขอ้างอิงหรือ 4 ตัวท้ายบัญชี")
                else:
                    note = f"เวลาโอน: {pay_time} | {slip_note}".strip()
                    conn = get_conn()
                    conn.execute(
                        "INSERT INTO payments (user_id, plan, amount, months, ref_code, slip_note, status) VALUES (?,?,?,?,?,?,?)",
                        (USER, sel_plan, float(total), int(months), ref_code.strip(), note, "pending")
                    )
                    conn.commit(); conn.close()
                    st.success("✅ แจ้งชำระเงินเรียบร้อย! เราจะตรวจสอบและเปิดสิทธิ์ให้ภายใน 24 ชม.")
                    st.info("💡 หากต้องการให้เปิดสิทธิ์เร็วขึ้น ส่งสลิปมาที่ LINE: 0610950531")

        # ประวัติการชำระเงินของผู้ใช้
        conn = get_conn()
        my_pays = read_sql("SELECT plan, amount, months, status, created_at FROM payments WHERE user_id=? ORDER BY id DESC", conn, params=(USER,))
        conn.close()
        if not my_pays.empty:
            st.divider()
            st.markdown("##### 📜 ประวัติการชำระเงินของคุณ")
            show_p = my_pays.copy()
            show_p["plan"] = show_p["plan"].map(lambda p: PLANS.get(p, {}).get("name", p))
            show_p["status"] = show_p["status"].map({"pending": "⏳ รอตรวจสอบ", "approved": "✅ อนุมัติแล้ว", "rejected": "❌ ไม่อนุมัติ"})
            st.dataframe(show_p, use_container_width=True, hide_index=True)

        st.caption("⚠️ การชำระเงินตรวจสอบด้วยตนเอง อาจใช้เวลาไม่เกิน 24 ชม. | ติดต่อ LINE: 0610950531")

    with tab_service:
        st.subheader("💼 บริการของเรา")
        st.markdown("นอกจากเครื่องมือในระบบ เรายังรับงานบริการด้านบัญชี ภาษี และวางระบบ โดยผู้เชี่ยวชาญที่จบบัญชีโดยตรง")

        st.divider()
        st.markdown("##### 📋 บริการที่รับ")

        sv1, sv2 = st.columns(2)
        with sv1:
            st.markdown("""
            **🧾 ยื่นภาษีให้**
            - ภ.ง.ด.94 (ภาษีครึ่งปี) — เริ่มต้น 500 บาท
            - ภ.ง.ด.90/91 (ภาษีประจำปี) — เริ่มต้น 800 บาท
            - ภ.พ.30 (VAT รายเดือน) — เริ่มต้น 500 บาท/เดือน

            **📊 ทำบัญชีรายเดือน**
            - บุคคลธรรมดา/ร้านค้า — เริ่มต้น 2,000 บาท/เดือน
            - นิติบุคคล — เริ่มต้น 4,000 บาท/เดือน
            """)
        with sv2:
            st.markdown("""
            **⚙️ วางระบบบัญชี (ERP)**
            - SAP Business One — ประเมินตามขอบเขตงาน
            - PEAK / FlowAccount — เริ่มต้น 8,000 บาท
            - Express — เริ่มต้น 5,000 บาท
            - ย้ายข้อมูลระบบเก่า → ใหม่ — ประเมินตามปริมาณ

            **🎓 สอน/เทรนนิ่ง**
            - สอนใช้โปรแกรมบัญชี — 2,000 บาท/วัน
            """)

        st.info("💡 **ประสบการณ์:** วางระบบ SAP Business One, PEAK, FlowAccount, Express มาแล้ว พร้อมความรู้บัญชีและภาษีเชิงลึก")

        st.divider()
        st.markdown("##### 📮 สนใจบริการ — ติดต่อเรา")

        with st.form("service_form", clear_on_submit=True):
            sf1, sf2 = st.columns(2)
            with sf1:
                sv_type = st.selectbox("บริการที่สนใจ", [
                    "ยื่นภาษี ภ.ง.ด.94 (ครึ่งปี)",
                    "ยื่นภาษีประจำปี ภ.ง.ด.90/91",
                    "ยื่น VAT ภ.พ.30",
                    "ทำบัญชีรายเดือน",
                    "วางระบบ SAP Business One",
                    "วางระบบ PEAK / FlowAccount",
                    "วางระบบ Express",
                    "ย้ายข้อมูลระบบบัญชี",
                    "สอนใช้โปรแกรมบัญชี",
                    "อื่นๆ",
                ])
            with sf2:
                sv_contact = st.text_input("ช่องทางติดต่อกลับ (เบอร์/LINE/อีเมล)")
            sv_detail = st.text_area("รายละเอียดงาน", height=100,
                                     placeholder="เช่น ร้านอาหาร 2 สาขา อยากวางระบบ PEAK และให้ทำบัญชีรายเดือน")
            if st.form_submit_button("📨 ส่งคำขอ", use_container_width=True):
                if sv_contact.strip() and sv_detail.strip():
                    conn = get_conn()
                    conn.execute(
                        "INSERT INTO consult_requests (user_id, service, contact, detail) VALUES (?,?,?,?)",
                        (USER, sv_type, sv_contact.strip(), sv_detail.strip())
                    )
                    conn.commit(); conn.close()
                    st.success("✅ ส่งคำขอเรียบร้อย! เราจะติดต่อกลับภายใน 24 ชม.")
                else:
                    st.error("กรุณากรอกช่องทางติดต่อและรายละเอียด")

        st.divider()
        sc1, sc2, sc3 = st.columns(3)
        with sc1:
            st.markdown("[💬 Facebook](https://www.facebook.com/siriwat.khotphat.2024/?locale=th_TH)")
        with sc2:
            st.markdown("**📱 LINE:** 0610950531")
        with sc3:
            st.markdown("**☎️ โทร:** 098-667-3680")

        st.caption("⚠️ ราคาเป็นราคาเริ่มต้น อาจปรับตามความซับซ้อนของงาน — ปรึกษาฟรี ไม่มีค่าใช้จ่าย")

