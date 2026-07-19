import streamlit as st
import pandas as pd
from datetime import date, datetime

from core.db import get_conn, read_sql
from core.mascot import get_mascot_mood, get_mascot_image_b64
from core.tax import calc_progressive_tax, make_excel_report, make_pdf_report


def render(tab_home, tab_analysis, tab_plan, USER):
    with tab_home:
        st.subheader("🏠 ภาพรวมสุขภาพการเงินของคุณ")

        # ===== สถานะยายนึกเล็กๆ ด้านบน (รูปเล็ก ~80px ลอยเบาๆ + เรืองทอง) =====
        _mood_emo, _mood_name, _mood_msg, _days = get_mascot_mood(USER)
        _b64 = get_mascot_image_b64(_mood_name)
        if _b64:
            _yn_visual = (f'<img class="yn-home-img" '
                          f'src="data:image/png;base64,{_b64}" alt="ยายนึก"/>')
        else:
            _yn_visual = f'<div class="yn-home-emoji">👵{_mood_emo}</div>'
        st.markdown(f"""
        <style>
        @keyframes yn-home-float {{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-6px)}}}}
        @keyframes yn-home-glow {{
          0%,100%{{box-shadow:0 0 10px rgba(240,180,41,0.35),0 0 20px rgba(240,180,41,0.15)}}
          50%{{box-shadow:0 0 20px rgba(240,180,41,0.7),0 0 34px rgba(240,180,41,0.35)}}
        }}
        @keyframes yn-home-glow-txt {{
          0%,100%{{filter:drop-shadow(0 0 8px rgba(240,180,41,0.4))}}
          50%{{filter:drop-shadow(0 0 16px rgba(240,180,41,0.8))}}
        }}
        .yn-home-img{{
          width:80px;height:80px;object-fit:contain;border-radius:50%;
          animation:yn-home-float 3s ease-in-out infinite, yn-home-glow 2.5s ease-in-out infinite;
        }}
        .yn-home-emoji{{
          font-size:46px;line-height:1;
          animation:yn-home-float 3s ease-in-out infinite, yn-home-glow-txt 2.5s ease-in-out infinite;
        }}
        </style>
        <div style="display:flex;align-items:center;gap:16px;padding:12px 18px;border-radius:14px;
        background:linear-gradient(135deg,rgba(127,119,221,0.12),rgba(29,158,117,0.10));
        border:1px solid rgba(127,119,221,0.25);margin-bottom:8px">
        {_yn_visual}
        <div>
        <div style="font-size:15px;font-weight:700;color:#E8E6F5">ยายนึก · {_mood_name}</div>
        <div style="font-size:13px;color:#A8A4C8">{_mood_msg}</div>
        </div>
        </div>
        """, unsafe_allow_html=True)
        st.caption("👵 อยากดูยายนึกเต็มๆ + แต่งตัว ไปที่แท็บ 👵 ยายนึก")

        conn = get_conn()
        df_d = read_sql("SELECT * FROM transactions WHERE user_id=?", conn, params=(USER,))
        conn.close()

        if df_d.empty:
            st.info("ยังไม่มีข้อมูล — เริ่มบันทึกที่แท็บ 💰 รายรับ-รายจ่าย แล้วกลับมาดูภาพรวมที่นี่")
        else:
            df_d["txn_date"] = pd.to_datetime(df_d["txn_date"], errors="coerce")
            income = df_d[df_d.txn_type=="รายรับ"].amount.sum()
            expense = df_d[df_d.txn_type=="รายจ่าย"].amount.sum()
            profit = income - expense

            # ===== คะแนนสุขภาพการเงิน (0-100) =====
            # อิงอัตรากำไร (profit margin) เป็นหลัก
            if income > 0:
                margin = profit / income
                if margin >= 0.3: score, grade, color = 90, "ดีเยี่ยม", "🟢"
                elif margin >= 0.15: score, grade, color = 75, "ดี", "🟢"
                elif margin >= 0.05: score, grade, color = 60, "พอใช้", "🟡"
                elif margin >= 0: score, grade, color = 45, "ต้องระวัง", "🟡"
                else: score, grade, color = 25, "เสี่ยง", "🔴"
            else:
                score, grade, color, margin = 0, "ยังไม่มีรายรับ", "⚪", 0

            # ===== แถวคะแนน + ตัวเลขหลัก =====
            st.markdown("##### 💯 คะแนนสุขภาพการเงิน")
            sc1, sc2, sc3, sc4 = st.columns(4)
            sc1.metric("คะแนนรวม", f"{score}/100", grade)
            sc2.metric("💚 รายรับรวม", f"{income:,.0f}")
            sc3.metric("💸 รายจ่ายรวม", f"{expense:,.0f}")
            sc4.metric("📊 กำไรสุทธิ", f"{profit:,.0f}", f"{margin*100:.0f}% ของรายรับ")

            # progress bar คะแนน
            st.progress(score/100)
            st.caption(f"{color} สุขภาพการเงินระดับ: {grade} — คะแนนคำนวณจากอัตรากำไรเทียบกับรายรับ")

            st.divider()

            # ===== กราฟรายรับ-รายจ่ายรายเดือน (Plotly สวย) =====
            import plotly.graph_objects as go
            import plotly.express as px

            cL, cR = st.columns(2)
            with cL:
                st.markdown("##### 📈 รายรับ-รายจ่ายรายเดือน")
                df_d["เดือน"] = df_d["txn_date"].dt.to_period("M").astype(str)
                monthly = df_d.pivot_table(index="เดือน", columns="txn_type",
                                           values="amount", aggfunc="sum", fill_value=0)
                for c in ["รายรับ","รายจ่าย"]:
                    if c not in monthly.columns:
                        monthly[c] = 0
                fig_bar = go.Figure()
                fig_bar.add_trace(go.Bar(x=monthly.index, y=monthly["รายรับ"], name="รายรับ",
                                         marker=dict(color="#1D9E75", line=dict(width=0)), marker_cornerradius=6))
                fig_bar.add_trace(go.Bar(x=monthly.index, y=monthly["รายจ่าย"], name="รายจ่าย",
                                         marker=dict(color="#E8674F", line=dict(width=0)), marker_cornerradius=6))
                fig_bar.update_layout(
                    barmode="group", height=300, margin=dict(l=0,r=0,t=10,b=0),
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#A8A4C8", size=12),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)"),
                )
                st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})

            with cR:
                st.markdown("##### 🍩 เงินหมดไปกับอะไร")
                exp_df = df_d[df_d.txn_type=="รายจ่าย"]
                if exp_df.empty:
                    st.info("ยังไม่มีรายจ่าย")
                else:
                    by_cat = exp_df.groupby("category")["amount"].sum().sort_values(ascending=False)
                    colors = ["#7F77DD","#1D9E75","#E8674F","#F0B429","#5DCAA5","#B57FDD","#4F9EE8","#E85F9E"]
                    fig_donut = go.Figure(data=[go.Pie(
                        labels=by_cat.index, values=by_cat.values, hole=0.55,
                        marker=dict(colors=colors[:len(by_cat)], line=dict(color="#0B0A1F", width=2)),
                        textinfo="percent", textfont=dict(size=12, color="#fff"),
                    )])
                    fig_donut.update_layout(
                        height=300, margin=dict(l=0,r=0,t=10,b=0),
                        paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#A8A4C8", size=11),
                        showlegend=True, legend=dict(orientation="v", x=1, y=0.5, font=dict(size=10)),
                        annotations=[dict(text=f"{expense:,.0f}<br>บาท", x=0.5, y=0.5,
                                          font=dict(size=15, color="#E8E6F5"), showarrow=False)],
                    )
                    st.plotly_chart(fig_donut, use_container_width=True, config={"displayModeBar": False})
                    top_cat = by_cat.index[0]; top_amt = by_cat.iloc[0]
                    st.caption(f"💡 จ่ายเยอะสุด: **{top_cat}** ({top_amt:,.0f} บาท = {top_amt/expense*100:.0f}%)")

            st.divider()

            # ===== คำแนะนำอัตโนมัติ =====
            st.markdown("##### 💡 คำแนะนำสำหรับคุณ")
            tips = []
            if margin < 0:
                tips.append("🔴 ตอนนี้รายจ่ายมากกว่ารายรับ — ควรหาทางลดค่าใช้จ่ายหรือเพิ่มรายได้ด่วน")
            elif margin < 0.05:
                tips.append("🟡 กำไรบางมาก (ต่ำกว่า 5%) — ลองทบทวนต้นทุนและราคาขาย")
            else:
                tips.append(f"🟢 อัตรากำไร {margin*100:.0f}% อยู่ในเกณฑ์ดี รักษาระดับนี้ไว้")

            if not exp_df.empty:
                top_cat = exp_df.groupby("category")["amount"].sum().idxmax()
                top_pct = exp_df.groupby("category")["amount"].sum().max()/expense*100
                if top_pct > 50:
                    tips.append(f"⚠️ ค่าใช้จ่ายกระจุกที่ '{top_cat}' มากถึง {top_pct:.0f}% — ลองหาทางกระจายหรือลดส่วนนี้")

            if income > 1_800_000:
                tips.append("📌 รายรับเกิน 1.8 ล้าน/ปี — อย่าลืมเรื่องจดทะเบียน VAT")

            n_months = df_d["เดือน"].nunique()
            if n_months >= 2:
                avg_profit = profit / n_months
                tips.append(f"📅 เฉลี่ยกำไรเดือนละ {avg_profit:,.0f} บาท — ถ้าเก็บ 6 เดือนจะมีเงินสำรองราว {avg_profit*6:,.0f} บาท")

            for t in tips:
                st.markdown(f"- {t}")

            st.caption("⚠️ คะแนนและคำแนะนำเป็นแนวทางเบื้องต้นจากข้อมูลที่บันทึก ไม่ใช่คำแนะนำทางการเงินอย่างเป็นทางการ")

    with tab_analysis:
        st.subheader("📊 วิเคราะห์รายรับ-รายจ่าย รายเดือนและรายปี")
        conn = get_conn()
        df = read_sql("SELECT * FROM transactions WHERE user_id=?", conn, params=(USER,))
        conn.close()

        if df.empty:
            st.info("ยังไม่มีข้อมูลให้วิเคราะห์")
        else:
            df["txn_date"] = pd.to_datetime(df["txn_date"])
            df["เดือน"] = df["txn_date"].dt.to_period("M").astype(str)

            pivot = df.pivot_table(index="เดือน", columns="txn_type",
                                   values="amount", aggfunc="sum", fill_value=0).reset_index()
            for col in ["รายรับ", "รายจ่าย"]:
                if col not in pivot.columns:
                    pivot[col] = 0
            pivot["กำไรสุทธิ"] = pivot["รายรับ"] - pivot["รายจ่าย"]

            st.markdown("##### 📅 สรุปรายเดือน")
            st.dataframe(pivot, use_container_width=True, hide_index=True)

            st.markdown("##### 📈 กราฟรายรับ-รายจ่ายรายเดือน")
            chart_df = pivot.set_index("เดือน")[["รายรับ", "รายจ่าย"]]
            st.bar_chart(chart_df)

            st.markdown("##### 💹 กราฟกำไรสุทธิสะสม")
            cumulative = pivot.set_index("เดือน")[["กำไรสุทธิ"]].cumsum()
            st.line_chart(cumulative)

            # ----- ปุ่ม Export รายงาน -----
            st.divider()
            st.markdown("##### 📤 ส่งออกรายงาน")
            ex1, ex2, ex3 = st.columns(3)
            with ex1:
                excel_bytes = make_excel_report(df, USER)
                st.download_button(
                    "📊 Excel (มีสรุปรายเดือน)",
                    data=excel_bytes,
                    file_name=f"เงินไทย_{USER}_{date.today().isoformat()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            with ex2:
                csv_df = df.rename(columns={
                    "txn_date":"วันที่","txn_type":"ประเภท","income_type":"เงินได้ ม.40",
                    "category":"หมวดหมู่","description":"รายละเอียด","amount":"จำนวนเงิน"
                })
                csv_cols = [c for c in ["วันที่","ประเภท","เงินได้ ม.40","หมวดหมู่","รายละเอียด","จำนวนเงิน"] if c in csv_df.columns]
                csv_bytes = csv_df[csv_cols].to_csv(index=False).encode("utf-8-sig")
                st.download_button(
                    "📄 CSV (เปิดใน Excel)",
                    data=csv_bytes,
                    file_name=f"เงินไทย_{USER}_{date.today().isoformat()}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            with ex3:
                try:
                    pdf_bytes = make_pdf_report(df, USER)
                    st.download_button(
                        "📕 PDF (รายงานสรุป)",
                        data=pdf_bytes,
                        file_name=f"เงินไทย_{USER}_{date.today().isoformat()}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                except Exception as e:
                    st.button("📕 PDF (ไม่พร้อม)", disabled=True, use_container_width=True)
                    st.caption(f"PDF ต้องมีฟอนต์ไทยในเครื่อง: {e}")
            st.caption("Excel มี 2 ชีต (รายการ + สรุปรายเดือน) | PDF เป็นรายงานสรุปพร้อมพิมพ์ | เปิดได้ทั้ง Excel และ Google Sheets")

    with tab_plan:
        st.subheader("🔮 คาดการณ์และวางแผนการเงินในอนาคต")
        conn = get_conn()
        df = read_sql("SELECT * FROM transactions WHERE user_id=?", conn, params=(USER,))
        conn.close()

        if df.empty:
            st.info("ยังไม่มีข้อมูลให้คาดการณ์ — บันทึกรายการอย่างน้อย 1-2 เดือนเพื่อให้พยากรณ์แม่นขึ้น")
        else:
            df["txn_date"] = pd.to_datetime(df["txn_date"])
            df["เดือน"] = df["txn_date"].dt.to_period("M").astype(str)
            n_months = df["เดือน"].nunique()

            ti = df[df.txn_type=="รายรับ"].amount.sum()
            te = df[df.txn_type=="รายจ่าย"].amount.sum()

            avg_income = ti / n_months
            avg_expense = te / n_months
            avg_profit = avg_income - avg_expense

            st.markdown(f"##### 📌 จากข้อมูล {n_months} เดือนที่ผ่านมา (ค่าเฉลี่ยต่อเดือน)")
            a,b,c = st.columns(3)
            a.metric("รายรับเฉลี่ย/เดือน", f"{avg_income:,.0f} บาท")
            b.metric("รายจ่ายเฉลี่ย/เดือน", f"{avg_expense:,.0f} บาท")
            c.metric("กำไรเฉลี่ย/เดือน", f"{avg_profit:,.0f} บาท")

            st.divider()
            st.markdown("##### 🎯 คาดการณ์สิ้นปี (12 เดือน)")
            proj_income = avg_income * 12
            proj_expense = avg_expense * 12
            proj_profit = proj_income - proj_expense

            # ประมาณภาษีสิ้นปี (สมมติ ม.40(8) หักเหมา 60% + ลดหย่อนส่วนตัว 60k)
            proj_after_exp = proj_income * 0.40
            proj_net = max(0.0, proj_after_exp - 60_000)
            proj_tax, _ = calc_progressive_tax(proj_net)

            p1,p2,p3 = st.columns(3)
            p1.metric("รายรับคาดการณ์ทั้งปี", f"{proj_income:,.0f} บาท")
            p2.metric("กำไรคาดการณ์ทั้งปี", f"{proj_profit:,.0f} บาท")
            p3.metric("ภาษีที่คาดว่าต้องจ่าย", f"{proj_tax:,.0f} บาท")

            st.divider()
            st.markdown("##### 💡 ข้อแนะนำการวางแผน")
            if proj_income > 1_800_000:
                st.warning("• รายรับคาดว่าจะเกิน 1.8 ล้าน/ปี — เตรียมจดทะเบียน VAT และวางแผนภาษีมูลค่าเพิ่ม")
            if proj_tax > 0:
                saving = min(proj_net * 0.30, 500_000)
                st.info(f"• พิจารณาซื้อ RMF/SSF เพื่อลดหย่อนได้สูงสุดราว {saving:,.0f} บาท ช่วยลดภาษีในขั้นบันไดสูงสุดของคุณ")
            if avg_profit < 0:
                st.error("• กำไรเฉลี่ยติดลบ — ควรทบทวนค่าใช้จ่ายที่สูงผิดปกติในแท็บวิเคราะห์")
            else:
                months_to_save = (avg_profit * 6)
                st.success(f"• หากเก็บกำไรไว้ 6 เดือน จะมีเงินสำรองราว {months_to_save:,.0f} บาท เป็นเงินทุนหมุนเวียน")

            st.caption("⚠️ การคาดการณ์ใช้วิธีค่าเฉลี่ยเชิงเส้นจากข้อมูลจริง ยิ่งมีข้อมูลหลายเดือนยิ่งแม่นยำ ไม่ใช่การรับประกันผลในอนาคต")

