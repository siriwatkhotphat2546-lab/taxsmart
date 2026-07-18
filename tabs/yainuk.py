import streamlit as st
import pandas as pd
from datetime import date, datetime

from core.db import get_conn, read_sql
from core.mascot import get_mascot, get_mascot_mood, OUTFITS


def render(tab, USER):
    with tab:
        st.subheader("👵 ยายนึก — กำลังใจเรื่องเงินของหลาน")

        m = get_mascot(USER)
        mood_emo, mood_name, mood_msg, days_away = get_mascot_mood(USER)
        outfit = m["outfit"] if m is not None else "ธรรมดา"
        coins = int(m["coins"]) if m is not None else 0
        streak = int(m["streak"]) if m is not None else 0

        # URL รูปยายนึก 3D (ผู้ใช้อัปขึ้น GitHub ชื่อ yai_nuk.png)
        YAINUK_IMG = "https://raw.githubusercontent.com/siriwatkhotphat2546-lab/taxsmart/main/yai_nuk.png"

        # ---------- แสดงยายนึก ----------
        mc1, mc2 = st.columns([1, 2])
        with mc1:
            st.markdown(f"""
            <div style="text-align:center;padding:16px;border-radius:20px;
            background:linear-gradient(135deg,rgba(127,119,221,0.15),rgba(29,158,117,0.12));
            border:1px solid rgba(127,119,221,0.3)">
            <img src="{YAINUK_IMG}" style="width:100%;max-width:200px;border-radius:16px;
            box-shadow:0 8px 24px rgba(0,0,0,0.3)"
            onerror="this.style.display='none';this.nextElementSibling.style.display='block'">
            <div style="display:none;font-size:80px">👵{mood_emo}</div>
            <div style="font-size:20px;font-weight:700;margin-top:12px">{mood_emo} {mood_name}</div>
            <div style="font-size:12px;color:#A8A4C8;margin-top:4px">ชุด: {outfit}</div>
            </div>
            """, unsafe_allow_html=True)

        with mc2:
            st.markdown(f"### {mood_msg}")
            s1, s2, s3 = st.columns(3)
            s1.metric("🪙 เหรียญ", f"{coins}")
            s2.metric("🔥 บันทึกต่อเนื่อง", f"{streak} วัน")
            s3.metric("📅 ห่างหายไป", f"{days_away if days_away < 999 else '-'} วัน")

            if days_away == 0:
                st.success("💚 วันนี้หลานบันทึกแล้ว ยายนึกภูมิใจมาก!")
            elif days_away <= 7 and days_away > 2:
                st.info("💡 กลับมาบันทึกวันนี้นะ ยายนึกเป็นห่วง — และหลานจะไม่ลืมว่าเงินไปไหน")
            elif days_away > 7:
                st.warning("🌱 ไม่เป็นไรนะลูก เริ่มใหม่ได้เสมอ — บันทึกวันนี้แค่รายการเดียวก็ยังดี")

            # เรื่องราวแรงบันดาลใจ
            st.markdown("""
            <div style="padding:14px 18px;border-radius:12px;margin-top:8px;
            background:rgba(240,180,41,0.10);border-left:3px solid #F0B429">
            <div style="font-size:13px;color:#E8E6F5;font-style:italic">
            💛 "ยายนึกอยากเห็นเงินล้านจากมือหลาน"</div>
            <div style="font-size:12px;color:#A8A4C8;margin-top:4px">
            แอปนี้สร้างขึ้นเพื่อความฝันนั้น — ทุกบาทที่หลานบันทึก คือก้าวเล็กๆ สู่เงินล้านที่ยายอยากเห็น</div>
            </div>
            """, unsafe_allow_html=True)

        # ---------- ยายนึกพูดข้อมูลจริง ----------
        st.divider()
        st.markdown("##### 💬 ยายนึกมีอะไรจะบอก")
        conn = get_conn()
        df_m = read_sql("SELECT * FROM transactions WHERE user_id=?", conn, params=(USER,))
        conn.close()

        if df_m.empty:
            st.info("🐷 \"เริ่มบันทึกรายการแรกกันเถอะ! แล้วเราจะบอกได้ว่าเงินคุณไปไหนบ้าง\"")
        else:
            df_m["txn_date"] = pd.to_datetime(df_m["txn_date"], errors="coerce")
            inc_m = df_m[df_m.txn_type == "รายรับ"]["amount"].sum()
            exp_m = df_m[df_m.txn_type == "รายจ่าย"]["amount"].sum()
            says = []
            if exp_m > inc_m:
                says.append(f"🐷 \"เดือนนี้จ่ายมากกว่ารับ {exp_m-inc_m:,.0f} บาทนะ ลองดูว่าตัดอะไรได้บ้างไหม\"")
            elif inc_m > 0:
                save_rate = (inc_m - exp_m) / inc_m * 100
                says.append(f"🐷 \"คุณเก็บเงินได้ {save_rate:.0f}% ของรายรับ {'เก่งมาก!' if save_rate >= 20 else 'ลองเพิ่มอีกนิดนะ'}\"")
            exp_only = df_m[df_m.txn_type == "รายจ่าย"]
            if not exp_only.empty:
                top_cat = exp_only.groupby("category")["amount"].sum().idxmax()
                top_amt = exp_only.groupby("category")["amount"].sum().max()
                says.append(f"🐷 \"หมวดที่จ่ายเยอะสุดคือ '{top_cat}' รวม {top_amt:,.0f} บาท\"")
            if streak >= 7:
                says.append(f"🐷 \"คุณบันทึกต่อเนื่อง {streak} วันแล้ว! นิสัยดีมาก 🎉\"")
            for s in says:
                st.markdown(f"> {s}")

        # ---------- ร้านค้าแต่งตัว ----------
        st.divider()
        st.markdown("##### 👕 ร้านแต่งตัวน้อง")
        st.caption(f"คุณมี {coins} เหรียญ — ได้เหรียญจากการบันทึกรายการ (วันละ 10 เหรียญ, ครบ 7 วันติดรับโบนัส 20)")

        ocols = st.columns(4)
        for i, (oname, oinfo) in enumerate(OUTFITS.items()):
            with ocols[i % 4]:
                owned = (oname == outfit)
                can_buy = coins >= oinfo["cost"]
                st.markdown(f"<div style='text-align:center;font-size:36px'>{oinfo['emoji']}</div>", unsafe_allow_html=True)
                st.caption(f"**{oname}**\n\n{oinfo['desc']}")
                if owned:
                    st.success("✅ ใส่อยู่")
                elif oinfo["cost"] == 0 or can_buy:
                    if st.button(f"🪙 {oinfo['cost']}", key=f"buy_{oname}", use_container_width=True):
                        conn = get_conn()
                        new_coins = coins - oinfo["cost"]
                        conn.execute("UPDATE mascot SET outfit=?, coins=? WHERE user_id=?",
                                     (oname, new_coins, USER))
                        conn.commit(); conn.close()
                        get_mascot.clear()
                        st.success(f"เปลี่ยนชุดเป็น {oname} แล้ว!")
                        st.rerun()
                else:
                    st.caption(f"🔒 ต้องมี {oinfo['cost']} เหรียญ")

        st.caption("💡 ยายนึกช่วยให้คุณกลับมาบันทึกทุกวัน — เพราะการเห็นเงินชัดเริ่มจากการจดทุกบาท")

