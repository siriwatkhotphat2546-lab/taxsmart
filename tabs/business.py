import streamlit as st
import pandas as pd
from datetime import date, datetime

from core.db import get_conn, read_sql
from core.tax import calc_progressive_tax


def render(tab, USER):
    with tab:
        st.divider()
        st.subheader("📅 ภาษีเงินได้ครึ่งปี (ภ.ง.ด.94)")
        st.caption("เฉพาะเงินได้ ม.40(5)-(8) ที่ได้รับ ม.ค.-มิ.ย. | ลดหย่อนใช้ได้ครึ่งเดียว แต่อัตราภาษีเท่าเดิม (ม.56 ทวิ)")

        # เงินได้ที่ต้องยื่น ภ.ง.ด.94 = ม.40(5),(6),(7),(8) เท่านั้น
        HALFYEAR_TYPES = {
            "40(5) ค่าเช่าทรัพย์สิน": 0.30,
            "40(6) วิชาชีพอิสระ": 0.30,
            "40(7) รับเหมา (ค่าแรง+ของ)": 0.60,
            "40(8) ธุรกิจ/ค้าขาย": 0.60,
        }

        conn = get_conn()
        inc_h = read_sql(
            "SELECT * FROM transactions WHERE txn_type='รายรับ' AND user_id=?",
            conn, params=(USER,)
        )
        conn.close()

        # กรองเฉพาะเดือน ม.ค.-มิ.ย.
        if not inc_h.empty:
            inc_h["txn_date"] = pd.to_datetime(inc_h["txn_date"])
            inc_h = inc_h[inc_h["txn_date"].dt.month <= 6]

        # เก็บเฉพาะเงินได้ประเภทที่ต้องยื่น ภ.ง.ด.94
        if not inc_h.empty:
            inc_h = inc_h[inc_h["income_type"].isin(HALFYEAR_TYPES.keys())]

        if inc_h.empty:
            st.info("ยังไม่มีเงินได้ ม.40(5)-(8) ในช่วง ม.ค.-มิ.ย. — บันทึกรายรับและระบุประเภทเงินได้ก่อน")
        else:
            st.markdown("##### 📥 เงินได้ครึ่งปีแรก (ม.ค.-มิ.ย.) แยกตามประเภท")
            grouped_h = inc_h.groupby("income_type")["amount"].sum().reset_index()

            total_after_exp_h = 0.0
            total_income_h = 0.0
            for _, row in grouped_h.iterrows():
                it = row["income_type"]
                amt = row["amount"]
                rate = HALFYEAR_TYPES.get(it, 0.0)
                expense = amt * rate
                after = amt - expense
                total_after_exp_h += after
                total_income_h += amt
                st.markdown(f"**{it}** — รายรับ {amt:,.0f} | หักค่าใช้จ่ายเหมา {rate*100:.0f}% = {expense:,.0f} | เหลือ {after:,.0f} บาท")

            st.divider()
            st.markdown("##### 📋 ค่าลดหย่อน (ภ.ง.ด.94 ใช้ได้ครึ่งเดียวของสิทธิทั้งปี)")
            st.caption("ตามมาตรา 56 ทวิ — ลดหย่อนส่วนตัวครึ่งปี = 30,000 บาท")
            h1, h2 = st.columns(2)
            with h1:
                st.text("ลดหย่อนส่วนตัวครึ่งปี: 30,000 (อัตโนมัติ)")
                h_spouse = st.checkbox("คู่สมรสไม่มีเงินได้ (+30,000)", key="h_spouse")
                h_social = st.number_input("ประกันสังคมครึ่งปี (สูงสุด 4,500)", 0.0, 4_500.0, 0.0, step=100.0, key="h_social")
            with h2:
                h_life = st.number_input("ประกันชีวิตครึ่งปี (สูงสุด 50,000)", 0.0, 50_000.0, 0.0, step=1000.0, key="h_life")
                h_rmf = st.number_input("RMF/กองทุนเกษียณครึ่งปี (สูงสุด 250,000)", 0.0, 250_000.0, 0.0, step=1000.0, key="h_rmf")

            ded_h = 30_000 + (30_000 if h_spouse else 0) + h_social + h_life + h_rmf

            net_h = max(0.0, total_after_exp_h - ded_h)
            tax_h, detail_h = calc_progressive_tax(net_h)

            st.divider()
            mh1, mh2, mh3, mh4 = st.columns(4)
            mh1.metric("เงินได้หลังหักค่าใช้จ่าย", f"{total_after_exp_h:,.0f}")
            mh2.metric("ลดหย่อนครึ่งปี", f"-{ded_h:,.0f}")
            mh3.metric("เงินได้สุทธิครึ่งปี", f"{net_h:,.0f}")
            mh4.metric("ภาษีครึ่งปี", f"{tax_h:,.0f}")

            if detail_h:
                st.markdown("**รายละเอียดขั้นบันได (อัตราเดียวกับทั้งปี ม.48):**")
                st.dataframe(pd.DataFrame(detail_h), use_container_width=True, hide_index=True)

            # เช็คเกณฑ์ต้องยื่น
            if total_income_h > 60_000:
                st.warning(f"📌 เงินได้ครึ่งปีแรก {total_income_h:,.0f} บาท เกิน 60,000 — มีหน้าที่ยื่น ภ.ง.ด.94 ภายใน 30 ก.ย. (ออนไลน์ถึง 8 ต.ค.)")
            else:
                st.info(f"เงินได้ครึ่งปีแรก {total_income_h:,.0f} บาท ไม่เกิน 60,000 — ยังไม่ถึงเกณฑ์ต้องยื่น ภ.ง.ด.94")

            st.success(f"### 💸 ภาษีครึ่งปีโดยประมาณ: {tax_h:,.2f} บาท")
            st.caption("⚠️ ภาษีที่จ่ายตอนครึ่งปีนำไปหักออกจากภาษีทั้งปีได้ (เครดิตภาษี) | ประมาณการเบื้องต้น ควรตรวจสอบกับกรมสรรพากร")

            # ----- ตัวจำลองการกรอกแบบ ภ.ง.ด.94 -----
            st.divider()
            with st.expander("📝 ดูตัวอย่างการกรอกแบบ ภ.ง.ด.94 (สำหรับผู้ไม่เคยยื่น)"):
                st.caption("จำลองว่าตัวเลขที่คำนวณได้ ไปลงช่องไหนในแบบยื่นภาษีครึ่งปีจริง — เป็นแบบจำลองเพื่อการเรียนรู้ ไม่ใช่แบบฟอร์มราชการ")
                st.markdown(f"""
    | ลำดับ | รายการในแบบ ภ.ง.ด.94 | จำนวนเงิน (บาท) |
    |---|---|---|
    | 1 | เงินได้ ม.40(5)-(8) ครึ่งปีแรก (ม.ค.-มิ.ย.) | {total_income_h:,.2f} |
    | 2 | หัก ค่าใช้จ่าย (ตามประเภทเงินได้) | (ตามมาตรา 40 ที่เลือก) |
    | 3 | คงเหลือเงินได้หลังหักค่าใช้จ่าย | {total_after_exp_h:,.2f} |
    | 4 | หัก ค่าลดหย่อนรวม (ใช้ได้ครึ่งเดียว ม.56 ทวิ) | {ded_h:,.2f} |
    | 5 | **เงินได้สุทธิครึ่งปี (นำไปคำนวณภาษี)** | **{net_h:,.2f}** |
    | 6 | ภาษีตามขั้นบันได (อัตราเต็ม ม.48) | {tax_h:,.2f} |
    | 7 | หัก ภาษีที่ถูกหัก ณ ที่จ่าย (ถ้ามี) | (กรอกเอง) |
    | 8 | **ภาษีครึ่งปีที่ต้องชำระ** | **{tax_h:,.2f}** |
                """)
                st.info("💡 ขั้นตอนยื่นจริง: เข้า efiling.rd.go.th → เข้าสู่ระบบด้วยเลขบัตรประชาชน → เลือกแบบ ภ.ง.ด.94 → กรอกตามช่อง 1-8 → ระบบคำนวณให้อัตโนมัติ → ยืนยันและพิมพ์ใบเสร็จ")
                st.caption("กำหนดยื่น: 1 ก.ค. – 30 ก.ย. ของปีภาษี (ยื่นออนไลน์ขยายถึง 8 ต.ค.) | ภาษีนี้นำไปเป็นเครดิตหักออกจาก ภ.ง.ด.90 ตอนสิ้นปีได้")

    with tab:
        st.divider()
        st.subheader("🧾 ภาษีมูลค่าเพิ่ม (ภ.พ.30)")
        st.caption("ภาษีขาย (7% ของรายรับ) − ภาษีซื้อ (7% ของรายจ่าย) | ยื่นทุกเดือน ภายในวันที่ 15 ของเดือนถัดไป")

        VAT_RATE = 0.07

        conn = get_conn()
        df_v = read_sql("SELECT * FROM transactions WHERE user_id=?", conn, params=(USER,))
        conn.close()

        if df_v.empty:
            st.info("ยังไม่มีข้อมูล — บันทึกรายรับ/รายจ่ายก่อน")
        else:
            df_v["txn_date"] = pd.to_datetime(df_v["txn_date"])

            # ===== VAT คิดเฉพาะรายรับที่อยู่ในระบบ VAT เท่านั้น =====
            # ไม่รวม เงินเดือน ม.40(1) และ ดอกเบี้ย/เงินปันผล ม.40(4) เพราะไม่ใช่การขายสินค้า/บริการ
            NON_VAT_INCOME = ["40(1) เงินเดือน ค่าจ้าง", "40(4) ดอกเบี้ย/เงินปันผล"]
            is_income = df_v.txn_type == "รายรับ"
            is_vatable = ~df_v["income_type"].isin(NON_VAT_INCOME)
            # รายรับที่เข้าระบบ VAT (ขาย/บริการ)
            df_v["vat_sale_amt"] = df_v["amount"].where(is_income & is_vatable, 0.0)
            # รายจ่ายถือเป็นภาษีซื้อทั้งหมด
            df_v["vat_purchase_amt"] = df_v["amount"].where(df_v.txn_type == "รายจ่าย", 0.0)

            total_income_y = df_v.loc[is_income & is_vatable, "amount"].sum()

            # แจ้งเตือนถ้ามีเงินเดือน/ดอกเบี้ยที่ถูกตัดออกจาก VAT
            excluded = df_v.loc[is_income & ~is_vatable, "amount"].sum()
            if excluded > 0:
                st.info(f"ℹ️ มีรายรับ {excluded:,.0f} บาท (เงินเดือน/ดอกเบี้ย-เงินปันผล) ที่ไม่นำมาคิด VAT เพราะไม่ใช่การขายสินค้า/บริการ")

            # ตรวจว่าต้องจด VAT หรือไม่ (ใช้เฉพาะรายได้ที่เข้าระบบ VAT)
            if total_income_y > 1_800_000:
                st.error(f"🚨 รายได้จากการขาย/บริการรวม {total_income_y:,.0f} บาท เกิน 1.8 ล้าน/ปี — ต้องจดทะเบียน VAT (มาตรา 85/1)")
            else:
                st.warning(f"ℹ️ รายได้จากการขาย/บริการรวม {total_income_y:,.0f} บาท ยังไม่เกิน 1.8 ล้าน/ปี — ยังไม่บังคับจด VAT (คำนวณเพื่อดูประมาณการได้)")

            st.divider()
            st.markdown("##### 📅 เลือกเดือนที่ต้องการคำนวณ VAT")
            df_v["เดือน"] = df_v["txn_date"].dt.to_period("M").astype(str)
            months = sorted(df_v["เดือน"].unique(), reverse=True)
            sel_month = st.selectbox("เดือนภาษี", months)

            month_data = df_v[df_v["เดือน"] == sel_month]
            sale = month_data["vat_sale_amt"].sum()
            purchase = month_data["vat_purchase_amt"].sum()

            vat_sale = round(sale * VAT_RATE, 2)
            vat_purchase = round(purchase * VAT_RATE, 2)
            vat_payable = round(vat_sale - vat_purchase, 2)

            st.markdown(f"##### 📊 สรุป VAT เดือน {sel_month}")
            v1, v2, v3 = st.columns(3)
            v1.metric("ยอดขายที่เข้า VAT / ภาษีขาย 7%", f"{sale:,.0f}", f"VAT {vat_sale:,.2f}")
            v2.metric("ยอดซื้อ / ภาษีซื้อ 7%", f"{purchase:,.0f}", f"VAT {vat_purchase:,.2f}")
            if vat_payable >= 0:
                v3.metric("ภาษีที่ต้องนำส่ง", f"{vat_payable:,.2f}", "ชำระเพิ่ม", delta_color="inverse")
            else:
                v3.metric("ภาษีชำระเกิน (ยกไปเดือนหน้า)", f"{abs(vat_payable):,.2f}", "เครดิตภาษี")

            st.divider()
            st.markdown("##### 📋 ตาราง VAT ทุกเดือน")
            monthly = df_v.groupby("เดือน").agg(
                ยอดขาย=("vat_sale_amt", "sum"),
                รายจ่าย=("vat_purchase_amt", "sum"),
            ).reset_index()
            monthly["ภาษีขาย 7%"] = (monthly["ยอดขาย"] * VAT_RATE).round(2)
            monthly["ภาษีซื้อ 7%"] = (monthly["รายจ่าย"] * VAT_RATE).round(2)
            monthly["VAT ต้องนำส่ง"] = (monthly["ภาษีขาย 7%"] - monthly["ภาษีซื้อ 7%"]).round(2)
            st.dataframe(monthly[["เดือน","ยอดขาย","ภาษีขาย 7%","รายจ่าย","ภาษีซื้อ 7%","VAT ต้องนำส่ง"]],
                         use_container_width=True, hide_index=True)

            if vat_payable >= 0:
                st.success(f"### 💸 VAT ที่ต้องนำส่งเดือน {sel_month}: {vat_payable:,.2f} บาท")
            else:
                st.info(f"### เดือน {sel_month} ภาษีซื้อมากกว่าภาษีขาย — ไม่ต้องชำระ ยกเครดิต {abs(vat_payable):,.2f} บาทไปเดือนหน้า")
            st.caption("⚠️ ต้องยื่น ภ.พ.30 ทุกเดือนแม้ยอดเป็นศูนย์ | VAT คิดเฉพาะการขายสินค้า/บริการ ไม่รวมเงินเดือนและดอกเบี้ย-เงินปันผล | ควรตรวจสอบรายการยกเว้น VAT กับกรมสรรพากร")

    with tab:
        st.divider()
        st.subheader("✂️ คำนวณภาษีหัก ณ ที่จ่าย (ภ.ง.ด.3)")
        st.caption("ผู้จ่ายเงินหักภาษีไว้ล่วงหน้าจากผู้รับ แล้วนำส่งกรมสรรพากร | อัตราขึ้นกับประเภทเงินได้")

        WHT_RATES = {
            "ค่าจ้างทำของ/รับเหมา (3%)": 0.03,
            "ค่าบริการ/ค่าวิชาชีพ (3%)": 0.03,
            "ค่าจ้างวิทยากร/ที่ปรึกษา (3%)": 0.03,
            "ค่าเช่าอสังหาริมทรัพย์ (5%)": 0.05,
            "ค่าเช่ารถ/ค่าจ้างนักแสดง (5%)": 0.05,
            "ค่าโฆษณา (2%)": 0.02,
            "เงินรางวัล/ชิงโชค (5%)": 0.05,
        }

        st.markdown("##### 🧮 เครื่องคำนวณ")
        wc1, wc2 = st.columns(2)
        with wc1:
            wht_type = st.selectbox("ประเภทเงินที่จ่าย", list(WHT_RATES.keys()))
            pay_amount = st.number_input("จำนวนเงินที่จ่าย (ก่อนหัก)", min_value=0.0, step=1000.0, format="%.2f")
        with wc2:
            gross_up = st.checkbox("ผู้จ่ายออกภาษีให้ (gross-up)",
                                   help="กรณีผู้จ่ายรับภาระภาษีแทนผู้รับ ใช้สูตร เงิน × อัตรา/(1-อัตรา)")

        rate = WHT_RATES[wht_type]
        if pay_amount > 0:
            if gross_up:
                wht = pay_amount * rate / (1 - rate)
                note = "ผู้จ่ายออกภาษีให้ — ผู้รับได้เงินเต็มจำนวน"
            else:
                wht = pay_amount * rate
                note = "หักจากผู้รับ — ผู้รับได้เงินหลังหักภาษี"
            net_paid = pay_amount - (0 if gross_up else wht)

            st.divider()
            wm1, wm2, wm3 = st.columns(3)
            wm1.metric("อัตราหัก ณ ที่จ่าย", f"{rate*100:.0f}%")
            wm2.metric("ภาษีหัก ณ ที่จ่าย", f"{wht:,.2f} บาท")
            if gross_up:
                wm3.metric("ผู้รับได้รับจริง", f"{pay_amount:,.2f} บาท")
            else:
                wm3.metric("ผู้รับได้รับจริง", f"{net_paid:,.2f} บาท")
            st.info(f"📌 {note} | ต้องออกหนังสือรับรองหัก ณ ที่จ่าย (50 ทวิ) ให้ผู้รับ และยื่น ภ.ง.ด.3 ภายในวันที่ 7 ของเดือนถัดไป")

        st.divider()
        st.markdown("##### 📋 ตารางอัตราหัก ณ ที่จ่าย (บุคคลธรรมดา ปี 2568)")
        st.markdown("""
        | ประเภทเงินได้ | อัตรา | มาตรา |
        |---|---|---|
        | ค่าจ้างทำของ / รับเหมา | 3% | ม.3 เตรส |
        | ค่าบริการ / ค่าวิชาชีพอิสระ | 3% | ม.3 เตรส |
        | ค่าเช่าอสังหาริมทรัพย์ | 5% | ม.5 |
        | ค่าเช่ารถ / ค่าจ้างนักแสดง / เงินรางวัล | 5% | ม.3 เตรส |
        | ค่าโฆษณา | 2% | ม.3 เตรส |
        """)
        st.caption("⚠️ อัตราอาจต่างกันตามลักษณะธุรกรรม เช่น ค่าจ้างฟรีแลนซ์ที่เข้าข่ายเงินเดือนต้องหักตามอัตราก้าวหน้า ควรตรวจสอบกับกรมสรรพากร")

    with tab:
        st.subheader("🏪 คำนวณภาษีสำหรับร้านค้า/ร้านอาหาร (บุคคลธรรมดา)")
        st.caption("ออกแบบเฉพาะร้านค้า — รวมรายได้ทุกช่องทาง เทียบวิธีหักค่าใช้จ่าย และเทียบ 2 วิธีคำนวณภาษีตามกฎหมาย")

        # ---------- ขั้น 1: รวมรายได้ทุกช่องทาง ----------
        st.markdown("##### 📥 ขั้นที่ 1 — รายได้ทั้งปี (รวมทุกช่องทาง)")
        st.info("⚠️ สำคัญ: ยอดจากแอป Delivery ให้ใส่**ยอดขายเต็มก่อนหักค่า GP** ไม่ใช่ยอดที่โอนเข้าบัญชี")
        sc1, sc2 = st.columns(2)
        with sc1:
            rev_cash = st.number_input("เงินสดหน้าร้าน (บาท/ปี)", min_value=0.0, step=1000.0, format="%.2f")
            rev_transfer = st.number_input("เงินโอน/PromptPay (บาท/ปี)", min_value=0.0, step=1000.0, format="%.2f")
            rev_gov = st.number_input("โครงการรัฐ เช่น คนละครึ่ง (บาท/ปี)", min_value=0.0, step=1000.0, format="%.2f")
        with sc2:
            rev_delivery = st.number_input("ยอดขายผ่านแอป Delivery — ยอดเต็มก่อนหัก GP (บาท/ปี)", min_value=0.0, step=1000.0, format="%.2f")
            gp_rate = st.slider("ค่า GP ที่แอปหัก (%)", 0, 40, 30, help="เช่น Grab/LINEMAN หักประมาณ 30% — ใช้คำนวณต้นทุนกรณีหักตามจริง")

        total_revenue = rev_cash + rev_transfer + rev_gov + rev_delivery

        if total_revenue <= 0:
            st.info("กรอกรายได้อย่างน้อย 1 ช่องทางเพื่อเริ่มคำนวณ")
        else:
            st.metric("💰 รายได้รวมทั้งปี (ฐานภาษี)", f"{total_revenue:,.2f} บาท")

            # ---------- ขั้น 2: เทียบวิธีหักค่าใช้จ่าย ----------
            st.divider()
            st.markdown("##### 📊 ขั้นที่ 2 — เทียบวิธีหักค่าใช้จ่าย")

            # วิธี A: หักเหมา 60%
            expense_flat = total_revenue * 0.60

            # วิธี B: หักตามจริง (ผู้ใช้กรอก + ค่า GP คำนวณให้)
            st.markdown("**กรอกต้นทุนจริง (ถ้าจะเทียบวิธีหักตามจริง):**")
            rc1, rc2, rc3 = st.columns(3)
            with rc1:
                cost_material = st.number_input("ค่าวัตถุดิบ/ปี", min_value=0.0, step=1000.0, format="%.2f")
            with rc2:
                cost_rent = st.number_input("ค่าเช่า+ค่าจ้าง/ปี", min_value=0.0, step=1000.0, format="%.2f")
            with rc3:
                cost_other = st.number_input("ค่าใช้จ่ายอื่น/ปี", min_value=0.0, step=1000.0, format="%.2f")
            gp_cost = rev_delivery * (gp_rate/100)
            expense_real = cost_material + cost_rent + cost_other + gp_cost

            cmp_exp = pd.DataFrame({
                "วิธีหักค่าใช้จ่าย": ["หักเหมา 60%", "หักตามจริง"],
                "ค่าใช้จ่ายที่หักได้ (บาท)": [f"{expense_flat:,.2f}", f"{expense_real:,.2f}"],
                "หมายเหตุ": [
                    "ไม่ต้องมีใบเสร็จ",
                    f"รวมค่า GP {gp_cost:,.0f} (ต้องมีใบเสร็จครบ)",
                ],
            })
            st.dataframe(cmp_exp, use_container_width=True, hide_index=True)

            # เลือกวิธีหักที่ได้ค่าใช้จ่ายสูงกว่า (เสียภาษีน้อยกว่า)
            if expense_real > expense_flat:
                best_expense = expense_real
                best_exp_method = "หักตามจริง"
                st.success(f"✅ แนะนำ: หักตามจริง ({expense_real:,.0f}) มากกว่าเหมา 60% ({expense_flat:,.0f}) → เสียภาษีน้อยกว่า")
            else:
                best_expense = expense_flat
                best_exp_method = "หักเหมา 60%"
                st.success(f"✅ แนะนำ: หักเหมา 60% ({expense_flat:,.0f}) มากกว่าหรือเท่ากับตามจริง ({expense_real:,.0f}) → ง่ายและคุ้มกว่า")

            # ---------- ค่าลดหย่อน ----------
            st.divider()
            st.markdown("##### 📋 ค่าลดหย่อน")
            dc1, dc2 = st.columns(2)
            with dc1:
                st.text("ลดหย่อนส่วนตัว: 60,000 (อัตโนมัติ)")
                shop_spouse = st.checkbox("คู่สมรสไม่มีเงินได้ (+60,000)", key="shop_spouse")
                shop_children = st.number_input("บุตร (คนละ 30,000)", 0, 15, 0, key="shop_child")
            with dc2:
                shop_social = st.number_input("ประกันสังคม (สูงสุด 9,000)", 0.0, 9_000.0, 0.0, step=100.0, key="shop_social")
                shop_other_ded = st.number_input("ลดหย่อนอื่นๆ (ประกัน/กองทุน/บริจาค)", 0.0, 700_000.0, 0.0, step=1000.0, key="shop_other_ded")
            deduction = 60_000 + (60_000 if shop_spouse else 0) + shop_children*30_000 + shop_social + shop_other_ded

            # ---------- ขั้น 3: เทียบ 2 วิธีคำนวณภาษี ----------
            st.divider()
            st.markdown("##### 🧮 ขั้นที่ 3 — เทียบ 2 วิธีคำนวณภาษี (จ่ายตัวที่สูงกว่า)")

            # วิธีที่ 1: เงินได้สุทธิ × ขั้นบันได
            net_income = max(0.0, total_revenue - best_expense - deduction)
            tax_method1, _ = calc_progressive_tax(net_income)

            # วิธีที่ 2: รายได้รวม × 0.5% (เฉพาะถ้ารายได้ที่ไม่ใช่เงินเดือนเกิน 1 ล้าน)
            method2_exempt = False
            if total_revenue > 1_000_000:
                tax_method2 = total_revenue * 0.005
                # ⚖️ กฎหมาย: ถ้าภาษีวิธีเหมา 0.5% คำนวณได้ไม่เกิน 5,000 บาท → ได้รับยกเว้น
                if tax_method2 <= 5_000:
                    method2_exempt = True
                    tax_method2 = 0
                method2_active = True
            else:
                tax_method2 = 0
                method2_active = False

            final_tax = max(tax_method1, tax_method2)

            if method2_exempt:
                m2_note = "ยกเว้น (ภาษีไม่เกิน 5,000 บาท)"
            elif method2_active:
                m2_note = "ใช้เมื่อรายได้เกิน 1 ล้าน/ปี"
            else:
                m2_note = "รายได้ไม่ถึง 1 ล้าน"

            cmp_tax = pd.DataFrame({
                "วิธีคำนวณภาษี": [
                    "วิธีที่ 1: เงินได้สุทธิ × ขั้นบันได",
                    "วิธีที่ 2: รายได้รวม × 0.5%",
                ],
                "ภาษี (บาท)": [f"{tax_method1:,.2f}", f"{tax_method2:,.2f}" if method2_active else "ไม่เข้าเงื่อนไข"],
                "หมายเหตุ": [
                    f"เงินได้สุทธิ {net_income:,.0f}",
                    m2_note,
                ],
            })
            st.dataframe(cmp_tax, use_container_width=True, hide_index=True)

            if method2_exempt:
                st.info("⚖️ ภาษีวิธีเหมา 0.5% คำนวณได้ไม่เกิน 5,000 บาท จึงได้รับยกเว้นตามกฎหมาย — ใช้วิธีขั้นบันไดแทน")

            # ---------- ผลลัพธ์ ----------
            st.divider()
            rm1, rm2, rm3 = st.columns(3)
            rm1.metric("วิธีหักที่เลือก", best_exp_method)
            rm2.metric("เงินได้สุทธิ", f"{net_income:,.0f}")
            rm3.metric("ภาษีที่ต้องจ่ายจริง", f"{final_tax:,.2f}")

            if method2_active and tax_method2 > tax_method1:
                st.warning(f"📌 ภาษีวิธีที่ 2 (0.5% = {tax_method2:,.0f}) สูงกว่าวิธีที่ 1 ({tax_method1:,.0f}) → ต้องจ่ายตามวิธีที่ 2 ตามกฎหมาย")
            else:
                st.info(f"📌 ภาษีวิธีที่ 1 (ขั้นบันได) สูงกว่าหรือเท่ากับวิธีที่ 2 → จ่ายตามวิธีที่ 1")

            st.success(f"### 💸 ภาษีที่ต้องจ่ายโดยประมาณ: {final_tax:,.2f} บาท")

            # เตือน VAT
            if total_revenue > 1_800_000:
                st.error(f"🚨 รายได้ {total_revenue:,.0f} เกิน 1.8 ล้าน/ปี — ต้องจดทะเบียน VAT! เมื่อจดแล้วต้องแยกยอดขายกับ VAT 7% ที่เก็บจากลูกค้า ระวังกำไรลดลงถ้าไม่บวกราคาเพิ่ม")

            st.info("💼 **ยื่นภาษีไม่เป็น? ให้เราช่วย** — บริการยื่นภาษีโดยผู้เชี่ยวชาญที่จบบัญชี เริ่มต้น 500 บาท · ดูรายละเอียดที่แท็บ **💼 บริการของเรา** หรือ LINE: 0610950531")

            st.caption("⚠️ ประมาณการตามอัตราปีภาษี 2568-2569 | รายได้ต้องใช้ยอดเต็มก่อนหัก GP | ควรเก็บหลักฐานครบถ้วนหากหักตามจริง | ตรวจสอบกับกรมสรรพากรก่อนยื่นจริง")

