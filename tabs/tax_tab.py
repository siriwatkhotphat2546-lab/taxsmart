import streamlit as st
import pandas as pd
from datetime import date, datetime

from core.db import get_conn, read_sql
from core.tax import (
    calc_progressive_tax, INCOME_TYPES, CAREERS,
    INCOME_CODE_MAP, DEDUCTION_TYPES, EXPENSE_WORK,
)


def render(tab_tax, tab_law, USER):
    with tab_tax:
        st.subheader("🧮 คำนวณภาษีเงินได้บุคคลธรรมดา")

        conn = get_conn()
        inc = read_sql("SELECT * FROM transactions WHERE txn_type='รายรับ' AND user_id=?", conn, params=(USER,))
        exp = read_sql("SELECT * FROM transactions WHERE txn_type='รายจ่าย' AND user_id=?", conn, params=(USER,))
        conn.close()

        # ===== ดึงข้อมูลจากรายจ่ายที่บันทึกไว้ (เชื่อมกับแท็บบันทึกเงิน) =====
        # 1) ค่าลดหย่อน: รวมยอดตามประเภทที่ผู้ใช้ติ๊ก "ลดหย่อนภาษีได้"
        ded_prefill = {}      # {ประเภทลดหย่อน: ยอดรวม}
        biz_actual = 0.0      # ค่าใช้จ่าย "ทำมาหากิน" รวม (ไว้เลือกหักตามจริง)
        if not exp.empty and "non_income_type" in exp.columns:
            for _dtype in DEDUCTION_TYPES:
                ded_prefill[_dtype] = float(exp[exp["non_income_type"] == _dtype]["amount"].sum())
            biz_actual = float(exp[exp["non_income_type"] == EXPENSE_WORK]["amount"].sum())

        def _pf(dtype, cap=None):
            """ยอดลดหย่อนที่ดึงมาให้ (clamp ไม่ให้เกินเพดานของช่อง)"""
            v = ded_prefill.get(dtype, 0.0)
            return float(min(v, cap)) if cap is not None else float(v)

        # ===== ให้ผู้ใช้เลือกว่ารายรับไหน "ไม่ต้องเสียภาษี" (ย้ายมาจากตอนบันทึก) =====
        if not inc.empty:
            with st.expander("💡 เงินแบบไหนไม่ต้องเสียภาษี? (กดดูก่อนคำนวณ)", expanded=False):
                st.markdown("""
    **เงินที่เข้าบัญชี ไม่ใช่ว่าต้องเสียภาษีทุกบาท** เงินพวกนี้ **ไม่ต้องเสียภาษี**:
    - 💝 **เงินที่คนอื่นให้/โอนให้** — พ่อแม่ ญาติ แฟนโอนมาให้ใช้
    - 🤝 **เงินยืม/เงินกู้** — เป็นหนี้ ต้องคืน ไม่ใช่รายได้
    - 🔄 **ย้ายเงินตัวเอง** — โอนจากบัญชีนึงไปอีกบัญชี
    - ↩️ **เงินคืน** — เงินทอน คืนของ คืนภาษี
    - 💰 **เงินลงทุนตัวเอง** — เงินก้อนที่เอามาลงทุนในร้าน

    **เงินที่ต้องเสียภาษี** = เงินที่หามาได้จากการทำงาน/ขายของ/ให้บริการ
                """)
            st.caption("👇 ติ๊กเอารายการที่ **ไม่ต้องเสียภาษี** ออก (ถ้ามี) แล้วระบบจะคำนวณจากเงินได้จริงเท่านั้น")

            inc = inc.reset_index(drop=True)
            inc["ตัดออก"] = False
            # แสดงเฉพาะรายรับให้เลือกตัด
            show_inc = inc[["txn_date", "category", "description", "amount"]].copy()
            show_inc.columns = ["วันที่", "หมวด", "รายละเอียด", "จำนวนเงิน"]
            show_inc["ไม่เสียภาษี (ติ๊ก)"] = False
            edited = st.data_editor(
                show_inc, use_container_width=True, hide_index=True,
                column_config={"ไม่เสียภาษี (ติ๊ก)": st.column_config.CheckboxColumn(help="ติ๊กถ้าเงินนี้ไม่ใช่รายได้ เช่น เงินแม่โอนมา")},
                disabled=["วันที่", "หมวด", "รายละเอียด", "จำนวนเงิน"], key="tax_income_editor"
            )
            # ตัดรายการที่ติ๊ก
            mask_exclude = edited["ไม่เสียภาษี (ติ๊ก)"].values
            excluded_amt = inc[mask_exclude]["amount"].sum()
            inc = inc[~mask_exclude]
            if excluded_amt > 0:
                st.success(f"✅ ตัดเงิน {excluded_amt:,.0f} บาท (ที่ไม่ใช่รายได้) ออกจากการคิดภาษีแล้ว — เหลือเงินได้จริง {inc['amount'].sum():,.0f} บาท")

        if inc.empty:
            st.info("ยังไม่มีรายได้ในระบบ — ไปบันทึกที่แท็บ 💰 รายรับ-รายจ่าย ก่อน")
        else:
            # จัดกลุ่มรายรับตามประเภทเงินได้ที่ติ๊กไว้ (income_type เก็บรหัสมาตรา เช่น "40(1)")
            st.markdown("##### 📥 รายรับแยกตามประเภทเงินได้ (ดึงจากที่คุณติ๊กไว้ตอนบันทึก — ไม่ต้องกรอกซ้ำ)")
            grouped = inc.groupby("income_type", dropna=False)["amount"].sum().reset_index()

            total_after_expense = 0.0     # เงินได้หลังหักค่าใช้จ่ายแบบเหมา (ค่าตั้งต้น)
            eligible_income = 0.0         # รายรับที่หัก "ตามจริง" ได้ (ม.40(5)-(8))
            eligible_flat_after = 0.0     # เงินคงเหลือ (เหมา) เฉพาะกลุ่มที่หักตามจริงได้
            noneligible_after = 0.0       # เงินคงเหลือของกลุ่มที่หักตามจริงไม่ได้ (40(1)(2)(4))
            used_sections = []
            for _, row in grouped.iterrows():
                code = row["income_type"]
                amt = row["amount"]
                # แปลงรหัสมาตรา -> key ใน INCOME_TYPES
                it = INCOME_CODE_MAP.get(code) if code is not None else None
                if it is None or it not in INCOME_TYPES:
                    st.warning(f"⚠️ รายรับ {amt:,.0f} บาท ยังไม่ได้ระบุประเภทเงินได้ (ติ๊ก 'ไม่แน่ใจ' ไว้) — หักค่าใช้จ่ายไม่ได้จนกว่าจะระบุที่แท็บ 💰 รายรับ-รายจ่าย")
                    total_after_expense += amt
                    noneligible_after += amt
                    continue
                info = INCOME_TYPES[it]
                rate = info["expense_rate"]; cap = info["expense_cap"]
                expense = amt * rate
                if cap is not None:
                    expense = min(expense, cap)
                after = amt - expense
                total_after_expense += after
                used_sections.append(info["section"])
                # กลุ่มที่หักตามจริงได้ = ไม่มีเพดาน (cap is None) => ม.40(5)-(8)
                if cap is None:
                    eligible_income += amt
                    eligible_flat_after += after
                else:
                    noneligible_after += after
                st.markdown(
                    f"**{it}** — รายรับ {amt:,.0f} | หักค่าใช้จ่าย "
                    f"({info['expense_rule']}) = {expense:,.0f} | เหลือ {after:,.0f} บาท"
                )

            # ===== ตัวเลือกหักค่าใช้จ่าย "ตามจริง" จากรายจ่ายที่ติ๊ก "ทำมาหากิน" =====
            if biz_actual > 0 and eligible_income > 0:
                st.info(f"💼 ระบบดึง **ค่าใช้จ่ายทำมาหากิน** ที่คุณบันทึกไว้ = **{biz_actual:,.0f} บาท** (จากแท็บ 💰 รายรับ-รายจ่าย)")
                use_actual = st.checkbox(
                    f"ใช้ค่าใช้จ่ายตามจริง {biz_actual:,.0f} บาท แทนแบบเหมา (เฉพาะเงินได้ ม.40(5)-(8) ที่หักตามจริงได้)",
                    help="ถ้ามีใบเสร็จครบและค่าใช้จ่ายจริงมากกว่าแบบเหมา การหักตามจริงจะเสียภาษีน้อยกว่า",
                )
                if use_actual:
                    eligible_after_actual = max(0.0, eligible_income - biz_actual)
                    total_after_expense = noneligible_after + eligible_after_actual
                    st.success(
                        f"✅ ใช้แบบตามจริง: รายรับกลุ่มหักตามจริงได้ {eligible_income:,.0f} − ค่าใช้จ่ายจริง {biz_actual:,.0f} "
                        f"= {eligible_after_actual:,.0f} บาท (เทียบแบบเหมาเหลือ {eligible_flat_after:,.0f})"
                    )

            st.divider()
            st.markdown("##### 📋 ค่าลดหย่อน ปีภาษี 2568 — ครบทุกรายการ (อ้างอิง ภ.ง.ด.90/91)")
            st.caption("เปิดเฉพาะกลุ่มที่คุณใช้สิทธิ์ — ส่วนที่ไม่ได้กรอกระบบจะถือเป็น 0")

            # แจ้งผู้ใช้ว่าระบบดึงยอดลดหย่อนจากที่บันทึกไว้มาเติมให้แล้ว
            _pulled = {k: v for k, v in ded_prefill.items() if v > 0}
            if _pulled:
                _lines = " · ".join(f"{k} {v:,.0f}" for k, v in _pulled.items())
                st.success(f"✅ ดึงค่าลดหย่อนที่คุณติ๊กไว้ตอนบันทึกมาเติมให้แล้ว: {_lines} — แก้ตัวเลขในช่องด้านล่างได้")

            # ===== กลุ่ม 1: ส่วนตัวและครอบครัว =====
            with st.expander("👤 กลุ่ม 1 — ส่วนตัวและครอบครัว", expanded=True):
                g1a, g1b = st.columns(2)
                with g1a:
                    st.text("ลดหย่อนส่วนตัว: 60,000 (อัตโนมัติ ม.47(1)(ก))")
                    spouse = st.checkbox("คู่สมรสไม่มีเงินได้ (+60,000)")
                    children = st.number_input("บุตร (คนละ 30,000)", 0, 15, 0)
                    children2 = st.number_input("บุตรคนที่ 2+ เกิดปี 2561 ขึ้นไป (คนละ 60,000)", 0, 15, 0)
                with g1b:
                    parents = st.number_input("อุปการะบิดามารดา (คนละ 30,000, สูงสุด 4)", 0, 4, 0)
                    disabled_care = st.number_input("ผู้พิการ/ทุพพลภาพในอุปการะ (คนละ 60,000)", 0, 10, 0)
                    maternity = st.number_input("ค่าฝากครรภ์-คลอดบุตร (สูงสุด 60,000)", 0.0, 60_000.0, 0.0, step=1000.0)

            ded_g1 = (60_000 + (60_000 if spouse else 0) + children*30_000 + children2*60_000
                      + parents*30_000 + disabled_care*60_000 + min(maternity, 60_000))

            # ===== กลุ่ม 2: ประกัน การออม และการลงทุน =====
            with st.expander("🛡️ กลุ่ม 2 — ประกัน การออม และการลงทุน (มีเพดานรวม)"):
                g2a, g2b = st.columns(2)
                with g2a:
                    social = st.number_input("ประกันสังคม (สูงสุด 9,000)", 0.0, 9_000.0, _pf("ประกันสังคม", 9_000.0), step=100.0)
                    life_ins = st.number_input("ประกันชีวิตทั่วไป", 0.0, 100_000.0, _pf("ประกันชีวิต", 100_000.0), step=1000.0)
                    health_ins = st.number_input("ประกันสุขภาพตัวเอง (สูงสุด 25,000)", 0.0, 25_000.0, _pf("ประกันสุขภาพ", 25_000.0), step=1000.0)
                    health_parents = st.number_input("ประกันสุขภาพบิดามารดา (สูงสุด 15,000)", 0.0, 15_000.0, _pf("ประกันสุขภาพพ่อแม่", 15_000.0), step=1000.0)
                    thai_esg = st.number_input("กองทุน Thai ESG/ESGX (สูงสุด 300,000)", 0.0, 300_000.0, _pf("ThaiESG", 300_000.0), step=1000.0)
                with g2b:
                    st.markdown("**กลุ่มเกษียณ (เพดานรวม 500,000):**")
                    pension_ins = st.number_input("ประกันชีวิตแบบบำนาญ", 0.0, 200_000.0, 0.0, step=1000.0)
                    rmf = st.number_input("กองทุน RMF", 0.0, 500_000.0, _pf("RMF", 500_000.0), step=1000.0)
                    pvd = st.number_input("กองทุนสำรองเลี้ยงชีพ (PVD)", 0.0, 500_000.0, _pf("กองทุนสำรองเลี้ยงชีพ", 500_000.0), step=1000.0)
                    gpf = st.number_input("กบข. (ข้าราชการ)", 0.0, 500_000.0, 0.0, step=1000.0)
                    teacher_fund = st.number_input("กองทุนสงเคราะห์ครูเอกชน", 0.0, 500_000.0, 0.0, step=1000.0)
                    nsf = st.number_input("กองทุนการออมแห่งชาติ กอช. (สูงสุด 30,000)", 0.0, 30_000.0, 0.0, step=1000.0)

                life_health = life_ins + health_ins
                if life_health > 100_000:
                    st.warning(f"⚠️ ประกันชีวิต + สุขภาพตัวเอง รวม {life_health:,.0f} เกินเพดาน 100,000 — ระบบจะใช้ 100,000")
                    life_health = 100_000

                retire_sum = pension_ins + rmf + pvd + gpf + teacher_fund + nsf
                if retire_sum > 500_000:
                    st.error(f"🚫 กลุ่มเกษียณรวม {retire_sum:,.0f} เกินเพดาน 500,000 — ระบบจะจำกัดที่ 500,000")
                    retire_sum = 500_000

            ded_g2 = social + life_health + health_parents + retire_sum + thai_esg

            # ===== กลุ่ม 3: อสังหาฯ และมาตรการกระตุ้นเศรษฐกิจ =====
            with st.expander("🏠 กลุ่ม 3 — อสังหาฯ และมาตรการรัฐ"):
                g3a, g3b = st.columns(2)
                with g3a:
                    home_interest = st.number_input("ดอกเบี้ยที่อยู่อาศัย (สูงสุด 100,000)", 0.0, 100_000.0, _pf("ดอกเบี้ยบ้าน", 100_000.0), step=1000.0)
                    easy_ereceipt = st.number_input("Easy E-Receipt 2.0 (สูงสุด 50,000)", 0.0, 50_000.0, 0.0, step=1000.0)
                    new_home = st.number_input("ค่าก่อสร้างบ้านใหม่ (สูงสุด 100,000)", 0.0, 100_000.0, 0.0, step=1000.0)
                with g3b:
                    travel_main = st.number_input("เที่ยวเมืองหลัก 1 เท่า (สูงสุด 20,000)", 0.0, 20_000.0, 0.0, step=1000.0)
                    travel_minor = st.number_input("เที่ยวเมืองรอง 1.5 เท่า (สูงสุด 30,000)", 0.0, 20_000.0, 0.0, step=1000.0)
                    cctv = st.number_input("CCTV ชายแดนใต้ (ม.40(5)-(8) ตามจริง)", 0.0, 1_000_000.0, 0.0, step=1000.0)

            # เที่ยวเมืองรองหักได้ 1.5 เท่า สูงสุด 30,000
            travel_minor_x = min(travel_minor * 1.5, 30_000)
            ded_g3 = home_interest + easy_ereceipt + new_home + travel_main + travel_minor_x + cctv

            # ===== กลุ่ม 4: เงินบริจาค =====
            with st.expander("💝 กลุ่ม 4 — เงินบริจาค"):
                g4a, g4b = st.columns(2)
                with g4a:
                    donate_general = st.number_input("บริจาคทั่วไป (ไม่เกิน 10% ของเงินได้)", 0.0, 1_000_000.0, _pf("เงินบริจาค", 1_000_000.0), step=500.0)
                    donate_edu = st.number_input("บริจาคการศึกษา/กีฬา/รพ.รัฐ/สังคม (หัก 2 เท่า)", 0.0, 500_000.0, _pf("เงินบริจาคการศึกษา-กีฬา", 500_000.0), step=500.0)
                with g4b:
                    donate_party = st.number_input("บริจาคพรรคการเมือง (สูงสุด 10,000)", 0.0, 10_000.0, 0.0, step=500.0)

            donate_edu_x2 = donate_edu * 2
            ded_before_donate = ded_g1 + ded_g2 + ded_g3
            income_for_donate_cap = max(0.0, total_after_expense - ded_before_donate)
            donate_cap = income_for_donate_cap * 0.10
            donate_total = donate_general + donate_edu_x2
            if donate_total > donate_cap:
                st.info(f"ℹ️ เงินบริจาครวม {donate_total:,.0f} เกิน 10% ของเงินได้ ({donate_cap:,.0f}) — ระบบจะใช้เพดาน 10%")
                donate_total = donate_cap
            ded_g4 = donate_total + min(donate_party, 10_000)

            ded = ded_g1 + ded_g2 + ded_g3 + ded_g4

            with st.expander("🧾 ดูสรุปค่าลดหย่อนแต่ละกลุ่ม"):
                summary_ded = pd.DataFrame({
                    "กลุ่มค่าลดหย่อน": [
                        "กลุ่ม 1 — ส่วนตัว/ครอบครัว",
                        "กลุ่ม 2 — ประกัน/ออม/ลงทุน",
                        "กลุ่ม 3 — อสังหาฯ/มาตรการรัฐ",
                        "กลุ่ม 4 — เงินบริจาค",
                        "รวมทั้งหมด",
                    ],
                    "จำนวนเงิน (บาท)": [
                        f"{ded_g1:,.0f}", f"{ded_g2:,.0f}", f"{ded_g3:,.0f}",
                        f"{ded_g4:,.0f}", f"{ded:,.0f}",
                    ],
                })
                st.dataframe(summary_ded, use_container_width=True, hide_index=True)

            net = max(0.0, total_after_expense - ded)
            tax, detail = calc_progressive_tax(net)

            st.divider()
            m1,m2,m3,m4 = st.columns(4)
            m1.metric("เงินได้หลังหักค่าใช้จ่าย", f"{total_after_expense:,.0f}")
            m2.metric("ค่าลดหย่อนรวม", f"-{ded:,.0f}")
            m3.metric("เงินได้สุทธิ", f"{net:,.0f}")
            m4.metric("ภาษีที่ต้องชำระ", f"{tax:,.0f}")

            if detail:
                st.markdown("**รายละเอียดการคำนวณขั้นบันได (มาตรา 48):**")
                st.dataframe(pd.DataFrame(detail), use_container_width=True, hide_index=True)

            if used_sections:
                st.info("📑 มาตราที่ใช้ในการคำนวณ: " + ", ".join(sorted(set(used_sections))) + ", มาตรา 47 (ลดหย่อน), มาตรา 48 (อัตราภาษี)")

            total_income = inc.amount.sum()
            if total_income > 1_800_000:
                st.error("🚨 รายรับเกิน 1.8 ล้านบาท/ปี — ต้องจดทะเบียน VAT (มาตรา 85/1)")

            st.success(f"### 💸 ภาษีโดยประมาณ: {tax:,.2f} บาท")
            st.caption("⚠️ เป็นการประมาณการเบื้องต้นตามอัตราปีภาษี 2568-2569 ควรตรวจสอบกับกรมสรรพากรหรือผู้เชี่ยวชาญก่อนยื่นจริง")

            # ----- ตัวจำลองการกรอกแบบ ภ.ง.ด.90 -----
            st.divider()
            with st.expander("📝 ดูตัวอย่างการกรอกแบบ ภ.ง.ด.90 (สำหรับผู้ไม่เคยยื่น)"):
                st.caption("จำลองว่าตัวเลขที่คำนวณได้ ไปลงช่องไหนในแบบยื่นภาษีจริง — เป็นแบบจำลองเพื่อการเรียนรู้ ไม่ใช่แบบฟอร์มราชการ")
                st.markdown(f"""
    | ลำดับ | รายการในแบบ ภ.ง.ด.90 | จำนวนเงิน (บาท) |
    |---|---|---|
    | 1 | เงินได้พึงประเมินทั้งปี | {inc.amount.sum():,.2f} |
    | 2 | หัก ค่าใช้จ่าย (ตามประเภทเงินได้) | (ตามมาตรา 40 ที่เลือก) |
    | 3 | คงเหลือเงินได้หลังหักค่าใช้จ่าย | {total_after_expense:,.2f} |
    | 4 | หัก ค่าลดหย่อนรวม | {ded:,.2f} |
    | 5 | **เงินได้สุทธิ (นำไปคำนวณภาษี)** | **{net:,.2f}** |
    | 6 | ภาษีตามขั้นบันได (มาตรา 48) | {tax:,.2f} |
    | 7 | หัก ภาษีที่ถูกหัก ณ ที่จ่าย/ชำระล่วงหน้า | (ถ้ามี — กรอกเอง) |
    | 8 | **ภาษีที่ต้องชำระเพิ่ม / ขอคืน** | **{tax:,.2f}** |
                """)
                st.info("💡 ขั้นตอนยื่นจริง: เข้า efiling.rd.go.th → เข้าสู่ระบบด้วยเลขบัตรประชาชน → เลือกแบบ ภ.ง.ด.90 → กรอกตามช่อง 1-8 → ระบบคำนวณให้อัตโนมัติ → ยืนยันและพิมพ์ใบเสร็จ")
                st.caption("กำหนดยื่น: 1 ม.ค. – 31 มี.ค. ปีถัดไป (ยื่นออนไลน์ขยายถึง 8 เม.ย.)")

    with tab_tax:
        st.subheader("👔 คำนวณภาษีตามอาชีพของคุณ")
        st.caption("เลือกอาชีพ แล้วระบบจะบอกว่าใช้เงินได้ประเภทไหน หักค่าใช้จ่ายอย่างไร และมีอะไรต้องระวัง")

        sel_career = st.selectbox("เลือกอาชีพของคุณ", list(CAREERS.keys()))
        ci = CAREERS[sel_career]

        # แสดงข้อมูลอาชีพ
        st.divider()
        ic1, ic2, ic3 = st.columns(3)
        ic1.metric("ประเภทเงินได้", f"มาตรา {ci['section']}")
        ic2.metric("วิธีหักค่าใช้จ่าย", ci["expense"])
        ic3.metric("อัตราหักเหมา", f"{ci['flat_rate']*100:.0f}%")

        st.warning(ci["warn"])

        st.markdown(f"**💰 รายได้ที่ต้องนำมาคำนวณ:** {ci['income_desc']}")

        # ---------- คำนวณภาษี ----------
        st.divider()
        st.markdown("##### 🧮 คำนวณภาษีของคุณ")

        cc1, cc2 = st.columns(2)
        with cc1:
            c_income = st.number_input("รายได้ทั้งปี (บาท)", min_value=0.0, step=10000.0, format="%.2f", key="career_income")
            use_real = st.checkbox("หักค่าใช้จ่ายตามจริง (แทนเหมา)", key="career_real",
                                   help="ต้องมีใบเสร็จครบถ้วน" if ci["section"] not in ("40(1)", "40(2)") else "ม.40(1) และ ม.40(2) หักตามจริงไม่ได้")
        with cc2:
            if use_real and ci["section"] not in ("40(1)", "40(2)"):
                c_real_exp = st.number_input("ค่าใช้จ่ายจริงทั้งปี (บาท)", min_value=0.0, step=10000.0, format="%.2f", key="career_real_exp")
            else:
                c_real_exp = 0.0
                if use_real:
                    st.error("⚠️ มาตรา 40(1) และ 40(2) หักตามจริงไม่ได้ตามกฎหมาย — ใช้เหมาเท่านั้น")
            c_ded = st.number_input("ค่าลดหย่อนรวม (ส่วนตัว 60,000 + อื่นๆ)", min_value=0.0, value=60000.0, step=10000.0, format="%.2f", key="career_ded")

        if c_income > 0:
            # คำนวณค่าใช้จ่าย
            flat_exp = c_income * ci["flat_rate"]
            # ม.40(1) และ 40(2) มีเพดาน 100,000
            if ci["section"] in ("40(1)", "40(2)"):
                flat_exp = min(flat_exp, 100_000)

            if use_real and ci["section"] not in ("40(1)", "40(2)") and c_real_exp > 0:
                chosen_exp = c_real_exp
                exp_method = "ตามจริง"
            else:
                chosen_exp = flat_exp
                exp_method = f"เหมา {ci['flat_rate']*100:.0f}%"

            # เทียบให้เห็นว่าแบบไหนดีกว่า
            if c_real_exp > 0 and ci["section"] not in ("40(1)", "40(2)"):
                better = "ตามจริง" if c_real_exp > flat_exp else "เหมา"
                st.info(f"💡 เทียบ: หักเหมา = {flat_exp:,.0f} | หักตามจริง = {c_real_exp:,.0f} → **หัก{better}คุ้มกว่า** (เสียภาษีน้อยกว่า)")

            c_net = max(0.0, c_income - chosen_exp - c_ded)
            c_tax, c_detail = calc_progressive_tax(c_net)

            st.divider()
            r1, r2, r3, r4 = st.columns(4)
            r1.metric("รายได้", f"{c_income:,.0f}")
            r2.metric(f"หักค่าใช้จ่าย ({exp_method})", f"{chosen_exp:,.0f}")
            r3.metric("เงินได้สุทธิ", f"{c_net:,.0f}")
            r4.metric("💸 ภาษีที่ต้องจ่าย", f"{c_tax:,.2f}")

            if c_tax == 0:
                st.success("🎉 เงินได้สุทธิไม่เกิน 150,000 บาท — ไม่ต้องเสียภาษี! (แต่ยังต้องยื่นแบบถ้าเข้าเกณฑ์)")

            # เตือนเกณฑ์ยื่นภาษี
            threshold = 120_000 if ci["section"] == "40(1)" else 60_000
            if c_income >= threshold:
                st.info(f"📌 รายได้ {c_income:,.0f} เกินเกณฑ์ {threshold:,.0f} บาท/ปี — **ต้องยื่นแบบภาษี** แม้ไม่ต้องเสียภาษีก็ตาม")

        # ---------- ค่าใช้จ่ายที่หักได้ ----------
        st.divider()
        st.markdown("##### 📋 ค่าใช้จ่ายที่หักได้ (กรณีหักตามจริง)")
        for e in ci["expenses"]:
            st.markdown(f"- {e}")

        # ---------- เคล็ดลับ ----------
        st.markdown("##### 💡 เคล็ดลับสำหรับอาชีพนี้")
        for t in ci["tips"]:
            st.markdown(f"- {t}")

        st.caption("⚠️ ประมาณการตามกฎหมายปีภาษี 2568 | ควรตรวจสอบกับกรมสรรพากรก่อนยื่นจริง")

    with tab_law:
        st.subheader("📖 คลังความรู้ประเภทเงินได้ตามมาตรา 40")
        st.caption("อ้างอิงประมวลรัษฎากร หมวด 3 ภาษีเงินได้")
        for name, info in INCOME_TYPES.items():
            with st.expander(f"📑 {name}  ({info['section']})"):
                st.markdown(f"**คำอธิบาย:** {info['note']}")
                st.markdown(f"**วิธีหักค่าใช้จ่าย:** {info['expense_rule']}")
        st.divider()
        st.markdown("""
        **มาตราสำคัญอื่นๆ ที่ระบบใช้อ้างอิง:**
        - **มาตรา 39** — นิยาม "เงินได้พึงประเมิน"
        - **มาตรา 42** — เงินได้ที่ยกเว้นภาษี (25 รายการ)
        - **มาตรา 47** — ค่าลดหย่อนทุกประเภท
        - **มาตรา 48** — อัตราภาษีขั้นบันได 5-35%
        - **มาตรา 48(2)** — ภาษีขั้นต่ำ 0.5% ของเงินได้
        - **มาตรา 56 / 56 ทวิ** — การยื่นแบบ ภ.ง.ด.90/94
        - **มาตรา 85/1** — เกณฑ์จดทะเบียน VAT (รายได้เกิน 1.8 ล้าน/ปี)
        """)

        st.divider()
        st.markdown("##### 📋 รายการลดหย่อน ปีภาษี 2568 (อ้างอิง ภ.ง.ด.90/91)")
        with st.expander("👤 กลุ่ม 1 — ส่วนตัวและครอบครัว"):
            st.markdown("""
            - ลดหย่อนส่วนตัว: 60,000 | คู่สมรสไม่มีเงินได้: 60,000
            - บุตร: 30,000/คน (คนที่ 2 ที่เกิดปี 2561+ ได้ 60,000)
            - บิดามารดา (อายุ 60+ รายได้ไม่เกิน 30,000): 30,000/คน สูงสุด 4 คน
            - ผู้พิการ/ทุพพลภาพในอุปการะ: 60,000/คน
            - ค่าฝากครรภ์-คลอดบุตร: ตามจ่ายจริง สูงสุด 60,000
            """)
        with st.expander("🛡️ กลุ่ม 2 — ประกันและการลงทุน"):
            st.markdown("""
            - ประกันสังคม: สูงสุด 9,000
            - ประกันชีวิต + สุขภาพตัวเอง: **รวมไม่เกิน 100,000** (สุขภาพแยกไม่เกิน 25,000)
            - ประกันสุขภาพบิดามารดา: สูงสุด 15,000
            - ประกันชีวิตแบบบำนาญ: 15% ของเงินได้ สูงสุด 200,000
            - กองทุน RMF: 30% ของเงินได้ สูงสุด 500,000
            - กองทุน Thai ESG: 30% ของเงินได้ สูงสุด 300,000 (แยกวงเงิน)
            - **เพดานรวมกลุ่มเกษียณ (บำนาญ+RMF+สำรองเลี้ยงชีพ+Thai ESG) ไม่เกิน 500,000**
            - หมายเหตุ: SSF ยกเลิกสิทธิแล้วในปี 2568
            """)
        with st.expander("🏠 กลุ่ม 3 — อสังหาฯ และมาตรการรัฐ"):
            st.markdown("""
            - ดอกเบี้ยที่อยู่อาศัย: สูงสุด 100,000
            - Easy E-Receipt 2.0: สูงสุด 50,000 (ซื้อ 16 ม.ค.–28 ก.พ. 2568)
            - ค่าก่อสร้างบ้านใหม่: 10,000 ต่อค่าก่อสร้าง 1 ล้าน สูงสุด 100,000
            - ค่าท่องเที่ยวเมืองหลัก/รอง: ตามประกาศกรมสรรพากร
            """)
        with st.expander("💝 กลุ่ม 4 — เงินบริจาค"):
            st.markdown("""
            - บริจาคทั่วไป: ตามจริง ไม่เกิน 10% ของเงินได้หลังหักลดหย่อน
            - บริจาคการศึกษา/กีฬา/รพ.รัฐ: หักได้ 2 เท่า (รวมไม่เกิน 10%)
            - บริจาคพรรคการเมือง: สูงสุด 10,000
            """)

