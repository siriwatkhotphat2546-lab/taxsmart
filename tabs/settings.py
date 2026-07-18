import streamlit as st
import pandas as pd
from datetime import date, datetime

from core.db import get_conn, read_sql


def render(tab_consult, tab_pdpa, tab_partner, USER):
    with tab_consult:
        st.subheader("🤝 ปรึกษาผู้เชี่ยวชาญด้านภาษีและการเงิน")
        st.markdown("""
        ต้องการคำปรึกษาเฉพาะทางจากผู้เชี่ยวชาญที่จบด้านบัญชีโดยตรง? เรารับให้คำปรึกษาและบริการดังนี้:
        """)

        cs1, cs2, cs3 = st.columns(3)
        with cs1:
            st.markdown("##### 📊 วางแผนภาษี")
            st.caption("วางแผนภาษีให้ประหยัดและถูกกฎหมาย เลือกวิธีหักค่าใช้จ่าย จัดการลดหย่อน")
        with cs2:
            st.markdown("##### 💰 วางแผนการเงิน")
            st.caption("วางแผนการเงินส่วนบุคคลและธุรกิจ จัดสรรงบ ตั้งเป้าหมายการออม")
        with cs3:
            st.markdown("##### 📈 บริหารการเงิน")
            st.caption("ดูแลกระแสเงินสด วิเคราะห์กำไรขาดทุน ให้คำแนะนำการเติบโต")

        st.divider()
        st.markdown("##### 📮 ส่งเรื่องที่ต้องการปรึกษา")
        st.caption("กรอกเรื่องที่อยากปรึกษา แล้วเราจะติดต่อกลับผ่านช่องทางที่คุณสะดวก")
        with st.form("consult_form", clear_on_submit=True):
            cf1, cf2 = st.columns(2)
            with cf1:
                c_service = st.selectbox("บริการที่สนใจ", ["วางแผนภาษี", "วางแผนการเงิน", "บริหารการเงิน", "อื่นๆ"])
            with cf2:
                c_contact = st.text_input("ช่องทางติดต่อกลับ (เบอร์/LINE/อีเมล)")
            c_detail = st.text_area("รายละเอียดเรื่องที่ต้องการปรึกษา", height=120,
                                    placeholder="เช่น ร้านอาหารรายได้ปีละ 2 ล้าน อยากวางแผนภาษีให้ประหยัด...")
            if st.form_submit_button("📨 ส่งคำขอปรึกษา", use_container_width=True):
                if c_detail.strip() and c_contact.strip():
                    conn = get_conn()
                    conn.execute(
                        "INSERT INTO consult_requests (user_id, service, contact, detail) VALUES (?,?,?,?)",
                        (USER, c_service, c_contact.strip(), c_detail.strip())
                    )
                    conn.commit(); conn.close()
                    st.success("✅ ส่งคำขอเรียบร้อย! เราจะติดต่อกลับโดยเร็วที่สุด ขอบคุณที่ไว้วางใจ")
                else:
                    st.error("กรุณากรอกช่องทางติดต่อและรายละเอียดก่อนส่ง")

        st.divider()
        st.markdown("##### 📞 ติดต่อโดยตรง")
        dc1, dc2, dc3 = st.columns(3)
        with dc1:
            st.markdown("[💬 Facebook](https://www.facebook.com/siriwat.khotphat.2024/?locale=th_TH)")
        with dc2:
            st.markdown("**📱 LINE:** 0610950531")
        with dc3:
            st.markdown("**☎️ โทร:** 098-667-3680")

        st.caption("⚠️ บริการให้คำปรึกษาเป็นบริการเสริมนอกเหนือจากเครื่องมือคำนวณในระบบ")

    with tab_pdpa:
        st.subheader("🔒 ข้อมูลส่วนตัวและสิทธิของคุณ (PDPA)")
        st.markdown("""
        ตามพระราชบัญญัติคุ้มครองข้อมูลส่วนบุคคล พ.ศ. 2562 คุณมีสิทธิเหนือข้อมูลของตัวเอง
        ที่นี่คุณสามารถ **ดู ดาวน์โหลด หรือลบ** ข้อมูลทั้งหมดของคุณได้
        """)

        conn = get_conn()
        my_txn = read_sql("SELECT * FROM transactions WHERE user_id=?", conn, params=(USER,))
        my_consult = read_sql("SELECT * FROM consult_requests WHERE user_id=?", conn, params=(USER,))
        try:
            my_inv = read_sql("SELECT * FROM inventory WHERE user_id=?", conn, params=(USER,))
        except Exception:
            my_inv = pd.DataFrame()
        conn.close()

        st.divider()
        st.markdown("##### 📊 ข้อมูลที่ระบบเก็บของคุณ")
        pc1, pc2, pc3 = st.columns(3)
        pc1.metric("รายการบัญชี", f"{len(my_txn)} รายการ")
        pc2.metric("คำขอปรึกษา", f"{len(my_consult)} รายการ")
        pc3.metric("รายการสินค้า", f"{len(my_inv)} รายการ")

        # ===== สิทธิที่ 1: ดูข้อมูล =====
        with st.expander("👁️ ดูข้อมูลทั้งหมดของฉัน"):
            st.markdown("**รายการบัญชี**")
            st.dataframe(my_txn, use_container_width=True, hide_index=True) if not my_txn.empty else st.caption("ยังไม่มีข้อมูล")
            if not my_consult.empty:
                st.markdown("**คำขอปรึกษา**")
                st.dataframe(my_consult, use_container_width=True, hide_index=True)

        # ===== สิทธิที่ 2: ดาวน์โหลดข้อมูล =====
        st.markdown("##### 📥 ดาวน์โหลดข้อมูลของคุณ (สิทธิในการเข้าถึงข้อมูล)")
        if not my_txn.empty:
            csv_data = my_txn.to_csv(index=False).encode("utf-8-sig")
            st.download_button("⬇️ ดาวน์โหลดข้อมูลบัญชี (CSV)", csv_data,
                              file_name=f"taxsmart_data_{USER}.csv", mime="text/csv")
        else:
            st.caption("ยังไม่มีข้อมูลให้ดาวน์โหลด")

        # ===== สิทธิที่ 3: ลบข้อมูล =====
        st.divider()
        st.markdown("##### 🗑️ ลบข้อมูลของฉัน (สิทธิในการลบข้อมูล)")
        st.warning("⚠️ การลบข้อมูลจะลบถาวร ไม่สามารถกู้คืนได้ กรุณาดาวน์โหลดเก็บไว้ก่อนถ้าต้องการ")

        if st.session_state.get("confirm_delete_pdpa"):
            st.error("ยืนยันการลบข้อมูลทั้งหมดของคุณ? การกระทำนี้ย้อนกลับไม่ได้")
            dc1, dc2 = st.columns(2)
            with dc1:
                if st.button("✅ ยืนยันลบข้อมูลทั้งหมด", use_container_width=True):
                    conn = get_conn()
                    conn.execute("DELETE FROM transactions WHERE user_id=?", (USER,))
                    conn.execute("DELETE FROM consult_requests WHERE user_id=?", (USER,))
                    try:
                        conn.execute("DELETE FROM inventory WHERE user_id=?", (USER,))
                    except Exception:
                        pass
                    conn.commit(); conn.close()
                    st.session_state.confirm_delete_pdpa = False
                    st.success("✅ ลบข้อมูลทั้งหมดของคุณเรียบร้อยแล้ว")
                    st.rerun()
            with dc2:
                if st.button("ยกเลิก", use_container_width=True):
                    st.session_state.confirm_delete_pdpa = False
                    st.rerun()
        else:
            if st.button("🗑️ ขอลบข้อมูลทั้งหมดของฉัน"):
                st.session_state.confirm_delete_pdpa = True
                st.rerun()

        st.divider()
        st.caption("📖 อ่านนโยบายความเป็นส่วนตัวฉบับเต็มได้ที่หน้าแรกก่อนเข้าใช้งาน | ติดต่อผู้ควบคุมข้อมูล: LINE 0610950531")

    with tab_partner:
        st.subheader("💞 ออมด้วยกัน")
        st.caption("ตั้งเป้าหมายการเงินร่วมกับคนที่คุณไว้ใจ — คู่รัก คู่ชีวิต เพื่อน หรือครอบครัว")

        conn = get_conn()
        my_partners = read_sql("SELECT * FROM partners WHERE owner=? OR partner=?", conn, params=(USER, USER))
        my_goals = read_sql("SELECT * FROM shared_goals WHERE owner=? OR partner=?", conn, params=(USER, USER))
        conn.close()

        # ---------- เชิญคู่ ----------
        with st.expander("➕ เชิญคนมาออมด้วยกัน", expanded=my_partners.empty):
            st.info("💡 อีกฝ่ายต้องสมัครสมาชิกในระบบก่อน แล้วคุณใส่ชื่อผู้ใช้ของเขา")
            with st.form("partner_form", clear_on_submit=True):
                pf1, pf2 = st.columns(2)
                with pf1:
                    p_user = st.text_input("ชื่อผู้ใช้ของอีกฝ่าย")
                with pf2:
                    p_nick = st.text_input("เรียกเขาว่าอะไร", placeholder="เช่น ที่รัก, เพื่อนซี้")
                if st.form_submit_button("ส่งคำเชิญ", use_container_width=True):
                    if p_user.strip() == USER:
                        st.error("เชิญตัวเองไม่ได้นะ 😅")
                    elif p_user.strip():
                        conn = get_conn()
                        chk = read_sql("SELECT username FROM users WHERE username=?", conn, params=(p_user.strip(),))
                        if chk.empty:
                            st.error("ไม่พบชื่อผู้ใช้นี้ — ให้เขาสมัครสมาชิกก่อน")
                        else:
                            conn.execute("INSERT INTO partners (owner, partner, nickname, status) VALUES (?,?,?,?)",
                                         (USER, p_user.strip(), p_nick.strip() or p_user.strip(), "active"))
                            conn.commit()
                            st.success(f"✅ เชื่อมกับ {p_user} แล้ว! ตอนนี้ตั้งเป้าหมายร่วมกันได้")
                            st.rerun()
                        conn.close()
                    else:
                        st.error("กรุณากรอกชื่อผู้ใช้")

        if my_partners.empty:
            st.info("ยังไม่มีคู่ออม — เชิญคนที่คุณไว้ใจมาตั้งเป้าหมายด้วยกัน")
        else:
            st.markdown("##### 👥 คู่ออมของคุณ")
            for _, p in my_partners.iterrows():
                other = p["partner"] if p["owner"] == USER else p["owner"]
                nick = p["nickname"] or other
                st.markdown(f"- 💞 **{nick}** ({other})")

        # ---------- เป้าหมายร่วม ----------
        st.divider()
        st.markdown("##### 🎯 เป้าหมายร่วม")

        with st.expander("➕ ตั้งเป้าหมายใหม่"):
            with st.form("goal_form", clear_on_submit=True):
                gf1, gf2 = st.columns(2)
                with gf1:
                    g_name = st.text_input("ชื่อเป้าหมาย", placeholder="เช่น เก็บเงินแต่งงาน, ดาวน์บ้าน")
                    g_target = st.number_input("เป้าหมาย (บาท)", min_value=0.0, step=10000.0, format="%.2f")
                with gf2:
                    partner_opts = ["(ออมคนเดียว)"]
                    if not my_partners.empty:
                        for _, p in my_partners.iterrows():
                            other = p["partner"] if p["owner"] == USER else p["owner"]
                            partner_opts.append(other)
                    g_partner = st.selectbox("ออมกับใคร", partner_opts)
                    g_deadline = st.text_input("กำหนดถึงเมื่อไหร่ (YYYY-MM-DD)", placeholder="2027-12-31")
                if st.form_submit_button("สร้างเป้าหมาย", use_container_width=True):
                    if g_name.strip() and g_target > 0:
                        conn = get_conn()
                        conn.execute(
                            "INSERT INTO shared_goals (owner, partner, goal_name, target_amount, deadline) VALUES (?,?,?,?,?)",
                            (USER, None if g_partner == "(ออมคนเดียว)" else g_partner,
                             g_name.strip(), float(g_target), g_deadline.strip() or None)
                        )
                        conn.commit(); conn.close()
                        st.success("✅ สร้างเป้าหมายแล้ว!")
                        st.rerun()
                    else:
                        st.error("กรุณากรอกชื่อเป้าหมายและจำนวนเงิน")

        if my_goals.empty:
            st.info("ยังไม่มีเป้าหมาย — ตั้งเป้าหมายแรกกันเถอะ")
        else:
            for _, g in my_goals.iterrows():
                saved = float(g["saved_amount"] or 0)
                target = float(g["target_amount"])
                pct = min(saved / target * 100, 100) if target > 0 else 0
                with st.container():
                    gc1, gc2 = st.columns([3, 1])
                    with gc1:
                        partner_txt = f" (ร่วมกับ {g['partner']})" if g["partner"] else " (คนเดียว)"
                        st.markdown(f"**🎯 {g['goal_name']}**{partner_txt}")
                        st.progress(pct / 100)
                        st.caption(f"{saved:,.0f} / {target:,.0f} บาท ({pct:.0f}%)" +
                                   (f" · ถึง {g['deadline']}" if g["deadline"] else ""))
                    with gc2:
                        add_amt = st.number_input("เพิ่มเงินออม", min_value=0.0, step=500.0,
                                                  key=f"add_{g['id']}", format="%.0f", label_visibility="collapsed")
                        if st.button("💰 ออมเพิ่ม", key=f"save_{g['id']}", use_container_width=True):
                            if add_amt > 0:
                                conn = get_conn()
                                conn.execute("UPDATE shared_goals SET saved_amount=? WHERE id=?",
                                             (saved + add_amt, int(g["id"])))
                                conn.commit(); conn.close()
                                st.success(f"ออมเพิ่ม {add_amt:,.0f} บาท!")
                                st.rerun()
                    if pct >= 100:
                        st.success("🎉 ถึงเป้าหมายแล้ว! ยินดีด้วย")
                    st.divider()

        st.caption("🔒 ความเป็นส่วนตัว: ระบบแชร์เฉพาะเป้าหมายร่วม ไม่แชร์รายการส่วนตัวของคุณ")

