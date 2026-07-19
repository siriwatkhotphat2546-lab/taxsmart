import streamlit as st
import pandas as pd
from datetime import date, datetime

from core.db import get_conn, read_sql
from core.mascot import feed_mascot
from core.tax import (
    INCOME_SOURCE_OPTIONS, INCOME_SOURCE_HELP,
    EXPENSE_PURPOSE_OPTIONS, DEDUCTION_TYPES,
)


def render(tab, USER):
    with tab:
        st.subheader("💰 รายรับ-รายจ่าย")
        st.caption("บันทึกเงินเข้า-ออกง่ายๆ ระบบสรุปให้เห็นว่าเก็บได้เท่าไหร่ หมดไปกับอะไร")

    with tab:
        st.markdown("---")
        st.subheader("📝 บันทึกรายรับ-รายจ่าย")

        # =========================================================
        #  ตัวเลือก "ประเภท" อยู่นอก form เพื่อให้ช่องด้านล่างเปลี่ยนทันที
        #  (ถ้าอยู่ใน form จะไม่ rerun จนกว่าจะกดบันทึก)
        # =========================================================
        txn_type = st.radio("นี่คือเงินเข้าหรือเงินออก?", ["รายรับ", "รายจ่าย"],
                            horizontal=True, key="mn_txn_type")

        income_code = None       # รหัสมาตราเก็บลง income_type (กรณีรายรับ)
        non_income_type = None   # ประเภทรายจ่ายเก็บลง non_income_type (กรณีรายจ่าย)

        if txn_type == "รายรับ":
            income_label = st.selectbox(
                "💡 เงินนี้ได้มาจากอะไร",
                list(INCOME_SOURCE_OPTIONS.keys()),
                help=INCOME_SOURCE_HELP, key="mn_income_src",
            )
            income_code = INCOME_SOURCE_OPTIONS[income_label]
            if income_code is None:
                st.caption("❓ เลือก 'ไม่แน่ใจ' ไว้ก่อนได้ — ค่อยไประบุประเภทตอนคำนวณภาษีก็ได้")
            else:
                st.caption(f"✅ ระบบจะใช้เงินก้อนนี้เป็นเงินได้ **มาตรา {income_code}** ตอนคำนวณภาษีให้อัตโนมัติ ไม่ต้องกรอกซ้ำ")
        else:
            exp_label = st.radio(
                "💡 จ่ายไปกับอะไร",
                list(EXPENSE_PURPOSE_OPTIONS.keys()),
                key="mn_exp_purpose",
                help="เลือกให้ตรงกับลักษณะการจ่าย ระบบจะดึงไปใช้ตอนคำนวณภาษีให้",
            )
            exp_purpose = EXPENSE_PURPOSE_OPTIONS[exp_label]
            if exp_purpose == "ลดหย่อน":
                # เลือกประเภทลดหย่อนต่อ (ต้องอยู่นอก form ถึงจะโผล่ทันที)
                ded_label = st.selectbox(
                    "🎯 ลดหย่อนประเภทไหน",
                    list(DEDUCTION_TYPES.keys()),
                    key="mn_ded_type",
                    help="เลือกประเภทให้ถูก ระบบจะเอาไปเติมช่องลดหย่อนในแท็บ 🧮 ภาษี ให้อัตโนมัติ",
                )
                non_income_type = ded_label
                st.caption(f"🎯 {DEDUCTION_TYPES[ded_label]}")
                st.caption("✅ ระบบจะเอายอดนี้ไปเติมช่องลดหย่อนในแท็บภาษีให้ แก้ตัวเลขทีหลังได้")
            else:
                non_income_type = exp_purpose  # "ทำมาหากิน" หรือ "ส่วนตัว"
                if exp_purpose == "ทำมาหากิน":
                    st.caption("✅ ระบบจะเก็บไว้เป็น 'ค่าใช้จ่ายตามจริง' ให้เลือกใช้ตอนคำนวณภาษี")
                else:
                    st.caption("ℹ️ รายจ่ายส่วนตัวจะไม่ถูกนำไปหักภาษี (บันทึกไว้ดูเฉยๆ)")

        # =========================================================
        #  ฟอร์มกรอกตัวเลข (เคลียร์หลังบันทึก)
        # =========================================================
        with st.form("txn_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                txn_date = st.date_input("วันที่", value=date.today())
                sel_wallet = st.selectbox("💳 เงินอยู่ที่ไหน", ["🏦 ธนาคาร", "💵 เงินสด"])
            with c2:
                amount = st.number_input("จำนวนเงิน (บาท)", min_value=0.0, step=100.0, format="%.2f")
                cat_choice = st.selectbox("หมวดหมู่ (ตั้งชื่อเองไว้ดูง่าย)", [
                    "ขายของ/รายได้", "เงินเดือน", "รับจ้าง/ฟรีแลนซ์", "รายได้อื่นๆ",
                    "ค่ากิน/ของใช้", "ซื้อของมาขาย/วัตถุดิบ", "ค่าเดินทาง", "ค่าเช่า",
                    "ค่าน้ำ-ไฟ-เน็ต", "ช้อปปิ้ง", "ค่าใช้จ่ายอื่นๆ", "✏️ อื่นๆ (พิมพ์เอง)"
                ])
            with c3:
                custom_cat = st.text_input("ถ้าเลือก 'อื่นๆ' พิมพ์หมวดที่นี่", placeholder="เช่น ค่าหวย, ค่ารักษา")
                description = st.text_input("รายละเอียด (ไม่บังคับ)", placeholder="เช่น ขายหมี่ไก่ฉีก 10 กล่อง")

            if st.form_submit_button("💾 บันทึก", use_container_width=True):
                if amount <= 0:
                    st.error("ใส่จำนวนเงินก่อนนะ")
                else:
                    # หมวด: ถ้าเลือกอื่นๆ ใช้ที่พิมพ์เอง
                    category = custom_cat.strip() if cat_choice.startswith("✏️") and custom_cat.strip() else cat_choice
                    if cat_choice.startswith("✏️") and not custom_cat.strip():
                        category = "อื่นๆ"
                    # รายรับ: เก็บรหัสมาตราลง income_type | รายจ่าย: เก็บประเภทลง non_income_type
                    conn = get_conn()
                    conn.execute(
                        "INSERT INTO transactions (txn_date, txn_type, income_type, category, description, amount, user_id, wallet, is_taxable, non_income_type) VALUES (?,?,?,?,?,?,?,?,?,?)",
                        (txn_date.isoformat(), txn_type,
                         income_code if txn_type == "รายรับ" else None,
                         category, description, amount, USER, sel_wallet, 1,
                         non_income_type if txn_type == "รายจ่าย" else None)
                    )
                    conn.commit(); conn.close()
                    new_coins, new_streak, fed = feed_mascot(USER)
                    st.success(f"✅ บันทึก {txn_type} {amount:,.0f} บาท ({category}) เรียบร้อย!")

                    if fed:
                        if new_streak % 7 == 0 and new_streak > 0:
                            st.balloons()
                            st.success(f"🎉 ยายนึกได้กินแล้ว! บันทึกต่อเนื่อง {new_streak} วัน — รับโบนัส 20 เหรียญ! (รวม {new_coins} เหรียญ)")
                        else:
                            st.info(f"👵 ยายนึกได้กินแล้ว! +10 เหรียญ (รวม {new_coins} เหรียญ) · ต่อเนื่อง {new_streak} วัน")

        conn = get_conn()
        df = read_sql("SELECT * FROM transactions WHERE user_id=? ORDER BY txn_date DESC, id DESC", conn, params=(USER,))
        conn.close()

        st.divider()
        if df.empty:
            st.info("ยังไม่มีรายการ — ลองบันทึกรายการแรกด้านบน")
        else:
            ti = df[df.txn_type=="รายรับ"].amount.sum()
            te = df[df.txn_type=="รายจ่าย"].amount.sum()
            a,b,c = st.columns(3)
            a.metric("💚 รายรับรวม", f"{ti:,.2f} บาท")
            b.metric("💸 รายจ่ายรวม", f"{te:,.2f} บาท")
            c.metric("📊 กำไรสุทธิ", f"{ti-te:,.2f} บาท")

            st.markdown("##### 📋 รายการทั้งหมด (เลือกเพื่อลบรายการที่คีย์ผิด)")
            st.caption("ติ๊กช่อง \'ลบ\' ในรายการที่ต้องการ แล้วกดปุ่มลบด้านล่าง ระบบจะให้ยืนยันก่อนลบจริง")

            df = df.copy()
            # สร้างคอลัมน์ "แยกภาษี": รายรับใช้รหัสมาตรา, รายจ่ายใช้ประเภทรายจ่าย
            if "non_income_type" not in df.columns:
                df["non_income_type"] = None
            def _tax_tag(r):
                if r["txn_type"] == "รายรับ":
                    it = r.get("income_type")
                    return f"เงินได้ ม.{it}" if it else "— (ยังไม่ระบุ)"
                nt = r.get("non_income_type")
                return nt if nt else "—"
            df["แยกภาษี"] = df.apply(_tax_tag, axis=1)

            editor_df = df.rename(columns={
                "txn_date":"วันที่","txn_type":"ประเภท",
                "category":"หมวดหมู่","description":"รายละเอียด","amount":"จำนวนเงิน"
            }).copy()
            # บังคับคอลัมน์วันที่ให้เป็นข้อความ YYYY-MM-DD สะอาด (กันแสดงผลเพี้ยน/มีเวลา 00:00:00)
            editor_df["วันที่"] = pd.to_datetime(editor_df["วันที่"], errors="coerce").dt.strftime("%Y-%m-%d")
            # ป้องกัน KeyError: เติมคอลัมน์ที่อาจหายไปให้ครบก่อนเสมอ
            for col in ["แยกภาษี","รายละเอียด"]:
                if col not in editor_df.columns:
                    editor_df[col] = ""
            editor_df["แยกภาษี"] = editor_df["แยกภาษี"].fillna("")
            editor_df["รายละเอียด"] = editor_df["รายละเอียด"].fillna("")
            editor_df["ลบ"] = False
            view_cols = ["ลบ","วันที่","ประเภท","แยกภาษี","หมวดหมู่","รายละเอียด","จำนวนเงิน"]

            edited = st.data_editor(
                editor_df[["id"] + view_cols],
                use_container_width=True, hide_index=True,
                disabled=["id","วันที่","ประเภท","แยกภาษี","หมวดหมู่","รายละเอียด","จำนวนเงิน"],
                column_config={
                    "id": None,
                    "วันที่": st.column_config.TextColumn("วันที่"),
                    "จำนวนเงิน": st.column_config.NumberColumn("จำนวนเงิน", format="%.2f"),
                },
                key="txn_editor"
            )

            to_delete = edited[edited["ลบ"] == True]
            n_sel = len(to_delete)

            col_del, col_info = st.columns([1, 3])
            with col_del:
                delete_clicked = st.button(
                    f"🗑️ ลบรายการที่เลือก ({n_sel})",
                    disabled=(n_sel == 0),
                    use_container_width=True
                )
            with col_info:
                if n_sel > 0:
                    sum_sel = to_delete["จำนวนเงิน"].sum()
                    st.warning(f"เลือกไว้ {n_sel} รายการ รวม {sum_sel:,.2f} บาท — การลบไม่สามารถย้อนกลับได้")

            if delete_clicked and n_sel > 0:
                st.session_state["confirm_delete_ids"] = to_delete["id"].tolist()

            if st.session_state.get("confirm_delete_ids"):
                ids = st.session_state["confirm_delete_ids"]
                st.error(f"⚠️ ยืนยันการลบ {len(ids)} รายการ? การกระทำนี้ลบข้อมูลออกถาวร")
                cc1, cc2, _ = st.columns([1, 1, 3])
                with cc1:
                    if st.button("✅ ยืนยันลบ", use_container_width=True):
                        conn = get_conn()
                        conn.executemany("DELETE FROM transactions WHERE id = ? AND user_id = ?", [(i, USER) for i in ids])
                        conn.commit(); conn.close()
                        st.session_state.pop("confirm_delete_ids", None)
                        st.success(f"ลบ {len(ids)} รายการเรียบร้อย")
                        st.rerun()
                with cc2:
                    if st.button("❌ ยกเลิก", use_container_width=True):
                        st.session_state.pop("confirm_delete_ids", None)
                        st.rerun()

