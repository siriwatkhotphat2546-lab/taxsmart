import streamlit as st
import pandas as pd
from datetime import date, datetime

from core.db import get_conn, read_sql
from core.tax import calc_fifo, calc_weighted_avg


def render(tab, USER):
    with tab:
        st.subheader("📦 คำนวณต้นทุนสินค้า (FIFO / ถัวเฉลี่ยถ่วงน้ำหนัก)")
        st.caption("อ้างอิงมาตรฐานการบัญชี TAS 2 สินค้าคงเหลือ | บันทึกการซื้อเข้า-ขายออก ระบบคำนวณต้นทุนขาย (COGS) และสินค้าคงเหลือให้")

        # ฟอร์มบันทึกการเคลื่อนไหวสินค้า
        with st.form("inv_form", clear_on_submit=True):
            st.markdown("##### ➕ บันทึกการเคลื่อนไหวสินค้า")
            ic1, ic2, ic3, ic4 = st.columns(4)
            with ic1:
                inv_date = st.date_input("วันที่", value=date.today(), key="inv_date")
            with ic2:
                product = st.text_input("ชื่อสินค้า", placeholder="เช่น ปลาทู")
            with ic3:
                move_type = st.selectbox("ประเภท", ["ซื้อเข้า", "ขายออก"])
                qty = st.number_input("จำนวน", min_value=0.0, step=1.0)
            with ic4:
                unit_cost = st.number_input("ต้นทุน/หน่วย (เฉพาะซื้อเข้า)", min_value=0.0, step=1.0,
                                            help="ใส่เฉพาะตอนซื้อเข้า ตอนขายออกไม่ต้องใส่")
            if st.form_submit_button("💾 บันทึก", use_container_width=True):
                if not product.strip() or qty <= 0:
                    st.error("กรุณากรอกชื่อสินค้าและจำนวนให้ครบ")
                else:
                    conn = get_conn()
                    conn.execute(
                        "INSERT INTO inventory (user_id, move_date, product, move_type, qty, unit_cost) VALUES (?,?,?,?,?,?)",
                        (USER, inv_date.isoformat(), product.strip(), move_type, qty, unit_cost if move_type=="ซื้อเข้า" else None)
                    )
                    conn.commit(); conn.close()
                    st.success(f"✅ บันทึก {move_type} {product} จำนวน {qty:,.0f} เรียบร้อย")

        conn = get_conn()
        inv_df = read_sql(
            "SELECT * FROM inventory WHERE user_id=? ORDER BY move_date, id", conn, params=(USER,)
        )
        conn.close()

        if inv_df.empty:
            st.info("ยังไม่มีข้อมูลสินค้า — บันทึกการซื้อเข้า/ขายออกด้านบนก่อน")
        else:
            st.divider()
            products = sorted(inv_df["product"].unique())
            sel_product = st.selectbox("เลือกสินค้าที่ต้องการคำนวณต้นทุน", products)
            method = st.radio("วิธีคำนวณต้นทุน (TAS 2)", ["FIFO (เข้าก่อนออกก่อน)", "Weighted Average (ถัวเฉลี่ย)"], horizontal=True)

            prod_moves = inv_df[inv_df["product"] == sel_product].to_dict("records")

            if "FIFO" in method:
                cogs, ending_value, ending_qty = calc_fifo(prod_moves)
            else:
                cogs, ending_value, ending_qty = calc_weighted_avg(prod_moves)

            st.markdown(f"##### 📊 ผลการคำนวณ — {sel_product}")
            cc1, cc2, cc3 = st.columns(3)
            cc1.metric("ต้นทุนขายรวม (COGS)", f"{cogs:,.2f} บาท")
            cc2.metric("มูลค่าสินค้าคงเหลือ", f"{ending_value:,.2f} บาท")
            cc3.metric("จำนวนคงเหลือ", f"{ending_qty:,.0f} หน่วย")

            st.markdown("##### 📋 ประวัติการเคลื่อนไหว")
            show_inv = prod_moves
            inv_show_df = pd.DataFrame(show_inv).rename(columns={
                "move_date":"วันที่","move_type":"ประเภท","qty":"จำนวน","unit_cost":"ต้นทุน/หน่วย"
            })
            st.dataframe(inv_show_df[["วันที่","ประเภท","จำนวน","ต้นทุน/หน่วย"]],
                         use_container_width=True, hide_index=True)

            st.info("💡 FIFO เหมาะกับสินค้าที่มีวันหมดอายุ (ขายของเก่าก่อน) | Weighted Average เหมาะกับสินค้าที่คละกันได้ เช่น วัตถุดิบ")
            st.caption("⚠️ ตาม TAS 2 ใช้ได้ทั้ง FIFO และ Weighted Average (ห้ามใช้ LIFO) ควรใช้วิธีเดียวสม่ำเสมอตามมาตรา TAS 8")

    with tab:
        st.subheader("💲 คำนวณราคาขายจากวัตถุดิบ")
        st.caption("กรอกวัตถุดิบทีละอย่าง → ระบบรวมต้นทุน หารต่อกล่อง แล้วแนะนำราคาขายตามกำไรที่อยากได้")

        st.markdown("##### 1️⃣ ใส่ชื่อสินค้าและจำนวนที่ทำได้")
        rc1, rc2, rc3 = st.columns(3)
        with rc1:
            recipe_name = st.text_input("ชื่อสินค้า", placeholder="เช่น หมี่ไก่ฉีก")
        with rc2:
            batch_yield = st.number_input("ทำได้กี่กล่อง/ชิ้น ต่อ 1 รอบ", min_value=1, value=10, step=1,
                                          help="วัตถุดิบที่กรอกทั้งหมด ทำได้ทั้งหมดกี่กล่อง")
        with rc3:
            yield_unit = st.text_input("หน่วย", value="กล่อง")

        st.markdown("##### 2️⃣ ใส่วัตถุดิบทีละอย่าง")
        st.caption("กรอกชื่อวัตถุดิบ + ราคาที่ซื้อมา (ต่อรอบการทำ) เช่น หมี่ 1 ห่อ 25 บาท, ไก่ 1 กก. 80 บาท")

        # ใช้ session state เก็บรายการวัตถุดิบ
        if "recipe_ingredients" not in st.session_state:
            st.session_state.recipe_ingredients = [
                {"name": "", "price": 0.0},
                {"name": "", "price": 0.0},
                {"name": "", "price": 0.0},
            ]

        ing_cols = st.columns([3, 2, 1])
        ing_cols[0].markdown("**วัตถุดิบ**")
        ing_cols[1].markdown("**ราคาที่ซื้อมา (บาท)**")
        ing_cols[2].markdown("**ลบ**")

        total_ingredient_cost = 0.0
        for i, ing in enumerate(st.session_state.recipe_ingredients):
            c1, c2, c3 = st.columns([3, 2, 1])
            with c1:
                ing["name"] = st.text_input(f"ing_name_{i}", value=ing["name"],
                                            placeholder="เช่น หมี่, ไก่, น้ำมัน", label_visibility="collapsed", key=f"ing_n_{i}")
            with c2:
                ing["price"] = st.number_input(f"ing_price_{i}", value=float(ing["price"]), min_value=0.0, step=5.0,
                                               format="%.2f", label_visibility="collapsed", key=f"ing_p_{i}")
            with c3:
                if len(st.session_state.recipe_ingredients) > 1:
                    if st.button("🗑️", key=f"del_ing_{i}"):
                        st.session_state.recipe_ingredients.pop(i)
                        st.rerun()
            total_ingredient_cost += ing["price"]

        ac1, ac2 = st.columns(2)
        with ac1:
            if st.button("➕ เพิ่มวัตถุดิบ", use_container_width=True):
                st.session_state.recipe_ingredients.append({"name": "", "price": 0.0})
                st.rerun()
        with ac2:
            if st.button("🔄 ล้างทั้งหมด", use_container_width=True):
                st.session_state.recipe_ingredients = [{"name": "", "price": 0.0}]
                st.rerun()

        # ต้นทุนแฝงเพิ่มเติม
        st.markdown("##### 3️⃣ ต้นทุนแฝง (ต่อรอบการทำ)")
        hc1, hc2, hc3 = st.columns(3)
        with hc1:
            packaging_cost = st.number_input("ค่าบรรจุภัณฑ์รวม (กล่อง/ถุง/ช้อน)", min_value=0.0, step=5.0, format="%.2f")
        with hc2:
            gas_cost = st.number_input("ค่าแก๊ส/ไฟ/น้ำ (ต่อรอบ)", min_value=0.0, step=5.0, format="%.2f")
        with hc3:
            labor_cost = st.number_input("ค่าแรงตัวเอง (ต่อรอบ)", min_value=0.0, step=10.0, format="%.2f",
                                         help="ตีราคาเวลาที่ใช้ทำ เช่น ทำ 2 ชม. คิด 100 บาท")

        # ===== คำนวณ =====
        total_batch_cost = total_ingredient_cost + packaging_cost + gas_cost + labor_cost
        cost_per_unit = total_batch_cost / batch_yield if batch_yield > 0 else 0

        if total_batch_cost <= 0:
            st.info("👆 กรอกวัตถุดิบและราคาก่อน เพื่อให้ระบบคำนวณต้นทุนและราคาขาย")
        else:
            st.divider()
            st.markdown(f"##### 📊 ต้นทุน{' — ' + recipe_name if recipe_name else ''}")
            tc1, tc2, tc3 = st.columns(3)
            tc1.metric("ต้นทุนรวมทั้งรอบ", f"{total_batch_cost:,.2f} บาท")
            tc2.metric(f"ทำได้", f"{batch_yield} {yield_unit}")
            tc3.metric(f"ต้นทุนต่อ{yield_unit}", f"{cost_per_unit:,.2f} บาท")

            # แยกให้เห็นว่าต้นทุนมาจากไหน
            with st.expander("ดูรายละเอียดต้นทุน"):
                breakdown = []
                for ing in st.session_state.recipe_ingredients:
                    if ing["name"] and ing["price"] > 0:
                        breakdown.append({"รายการ": ing["name"], "ราคา (บาท)": f"{ing['price']:,.2f}"})
                if packaging_cost > 0:
                    breakdown.append({"รายการ": "ค่าบรรจุภัณฑ์", "ราคา (บาท)": f"{packaging_cost:,.2f}"})
                if gas_cost > 0:
                    breakdown.append({"รายการ": "ค่าแก๊ส/ไฟ/น้ำ", "ราคา (บาท)": f"{gas_cost:,.2f}"})
                if labor_cost > 0:
                    breakdown.append({"รายการ": "ค่าแรง", "ราคา (บาท)": f"{labor_cost:,.2f}"})
                st.dataframe(pd.DataFrame(breakdown), use_container_width=True, hide_index=True)

            # ===== ตั้งราคาขาย =====
            st.divider()
            st.markdown("##### 4️⃣ อยากได้กำไรกี่ %")
            mg1, mg2 = st.columns(2)
            with mg1:
                profit_pct = st.slider("กำไรที่ต้องการ (% ของราคาขาย)", 0, 80, 40,
                                       help="เช่น 40% หมายถึง ในราคาขาย 100 บาท เป็นกำไร 40 บาท")
            with mg2:
                round_price = st.checkbox("ปัดราคาให้สวย (ลงท้าย 0 หรือ 5)", value=True)

            # ราคาขาย = ต้นทุน / (1 - กำไr%)
            if profit_pct < 100:
                suggested_price = cost_per_unit / (1 - profit_pct/100)
            else:
                suggested_price = cost_per_unit

            # ปัดราคาให้สวย
            import math
            display_price = suggested_price
            if round_price:
                display_price = math.ceil(suggested_price / 5) * 5  # ปัดขึ้นเป็นหลัก 5

            actual_profit = display_price - cost_per_unit
            actual_margin = (actual_profit / display_price * 100) if display_price > 0 else 0

            st.divider()
            st.markdown("##### 💰 ราคาขายแนะนำ")
            pr1, pr2, pr3 = st.columns(3)
            pr1.metric(f"ราคาขายต่อ{yield_unit}", f"{display_price:,.0f} บาท")
            pr2.metric(f"กำไรต่อ{yield_unit}", f"{actual_profit:,.2f} บาท")
            pr3.metric("อัตรากำไรจริง", f"{actual_margin:.0f}%")

            # กำไรถ้าขายหมดทั้งรอบ
            total_revenue = display_price * batch_yield
            total_profit = total_revenue - total_batch_cost
            st.success(f"💡 ถ้าขายหมด {batch_yield} {yield_unit} → รายได้ {total_revenue:,.0f} บาท, กำไร {total_profit:,.0f} บาท")

            # ===== เทียบราคาตลาด (แบบ B: แนะนำช่วง + เตือนเช็คเอง) =====
            st.divider()
            st.markdown("##### 🔍 เทียบกับราคาตลาด")
            st.caption("ระบบแนะนำช่วงราคาตามต้นทุน — ควรไปเช็คราคาคู่แข่งจริงใน Grab/Shopee/ตลาดแถวบ้านประกอบ")

            # ช่วงราคาแนะนำ (กำไร 30-50%)
            price_low = cost_per_unit / (1 - 0.30)   # กำไร 30%
            price_high = cost_per_unit / (1 - 0.50)  # กำไร 50%
            if round_price:
                price_low = math.ceil(price_low / 5) * 5
                price_high = math.ceil(price_high / 5) * 5

            rng1, rng2, rng3 = st.columns(3)
            rng1.metric("💚 ราคาแข่งขันได้ (กำไร 30%)", f"{price_low:,.0f} บาท")
            rng2.metric("⭐ ราคาแนะนำ (กำไร 40%)", f"{display_price:,.0f} บาท")
            rng3.metric("💎 ราคาพรีเมียม (กำไร 50%)", f"{price_high:,.0f} บาท")

            st.warning(f"""
    📌 **ก่อนตั้งราคาจริง ลองเช็คตลาด:**
    - เปิด **Grab Food / LINE MAN** ค้นหา "{recipe_name or 'สินค้าคล้ายกัน'}" ดูว่าร้านอื่นขายกี่บาท
    - เปิด **Shopee / Lazada** ดูราคาสินค้าใกล้เคียง
    - ถ้าราคาแนะนำ **สูงกว่าตลาดมาก** → ลดกำไร หรือหาวิธีลดต้นทุน
    - ถ้าราคาแนะนำ **ต่ำกว่าตลาด** → คุณตั้งราคาสูงขึ้นได้ กำไรเพิ่ม!
    """)

            # ===== ขายผ่าน Delivery ต้องบวกค่า GP =====
            st.divider()
            st.markdown("##### 🛵 ถ้าขายผ่าน Grab/LINE MAN (มีค่า GP)")
            st.caption("แพลตฟอร์มเดลิเวอรีหักค่าคอมมิชชั่น (GP) ประมาณ 30-35% ต้องบวกในราคาขายเพื่อไม่ให้ขาดทุน")
            gp1, gp2 = st.columns(2)
            with gp1:
                gp_pct = st.slider("ค่า GP ที่แพลตฟอร์มหัก (%)", 0, 40, 30)
            with gp2:
                # ราคาบนแอป = ราคาที่อยากได้ / (1 - GP%)
                if gp_pct < 100:
                    delivery_price = display_price / (1 - gp_pct/100)
                    if round_price:
                        delivery_price = math.ceil(delivery_price / 5) * 5
                    st.metric("ราคาที่ควรตั้งบนแอป", f"{delivery_price:,.0f} บาท",
                              help="ตั้งราคานี้บนแอป เพื่อให้หลังหัก GP แล้วยังได้กำไรเท่าที่ต้องการ")

            st.info(f"💡 ขายหน้าร้าน {display_price:,.0f} บาท แต่บน Grab ควรตั้ง {delivery_price:,.0f} บาท (เพราะโดนหัก GP {gp_pct}%) — ลูกค้าจ่ายแพงขึ้น แต่คุณได้กำไรเท่าเดิม")

            st.caption("⚠️ ราคาแนะนำเป็นแนวทางจากต้นทุน ควรพิจารณาราคาตลาดและกำลังซื้อของลูกค้าประกอบเสมอ")

