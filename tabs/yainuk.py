import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import date, datetime

from core.db import get_conn, read_sql
from core.mascot import get_mascot, get_mascot_mood, get_mascot_image_b64, OUTFITS


def _mascot_effect_html(b64, mood_emo, height=340):
    """สร้าง HTML ยายนึก 2D พร้อมเอฟเฟกต์ CSS: ลอยขึ้นลง + แสงทองเรือง +
    เอียงตามเมาส์ (JS) + เงาใต้ตัว — ถ้าไม่มีรูป fallback เป็น emoji 👵"""
    if b64:
        figure = (f'<img class="yn-img" '
                  f'src="data:image/png;base64,{b64}" alt="ยายนึก"/>')
    else:
        # fallback — ไม่มีไฟล์รูป ใช้ emoji แทน (ห้าม error)
        figure = f'<div class="yn-emoji">👵{mood_emo}</div>'

    return f"""
    <div class="yn-scene">
      <div class="yn-wrap" id="ynWrap">
        <div class="yn-float">
          {figure}
        </div>
        <div class="yn-shadow"></div>
      </div>
    </div>
    <style>
      html,body {{ margin:0; padding:0; background:transparent; overflow:hidden; }}
      .yn-scene {{
        perspective: 800px;
        display:flex; align-items:center; justify-content:center;
        height:{height}px;
      }}
      .yn-wrap {{
        transform-style: preserve-3d;
        transition: transform .15s ease-out;
        display:flex; flex-direction:column; align-items:center;
      }}
      .yn-float {{
        animation: yn-float 3s ease-in-out infinite;
      }}
      .yn-img {{
        width:200px; max-width:70vw; height:auto; display:block;
        border-radius:20px;
        animation: yn-glow 2.5s ease-in-out infinite;
      }}
      .yn-emoji {{
        font-size:120px; line-height:1;
        filter: drop-shadow(0 0 22px rgba(240,180,41,0.7));
        animation: yn-glow-txt 2.5s ease-in-out infinite;
      }}
      .yn-shadow {{
        width:150px; height:26px; margin-top:14px;
        background: radial-gradient(ellipse at center,
                    rgba(0,0,0,0.45) 0%, rgba(0,0,0,0.0) 70%);
        border-radius:50%;
        filter: blur(4px);
        animation: yn-shadow 3s ease-in-out infinite;
      }}
      @keyframes yn-float {{
        0%,100% {{ transform: translateY(0); }}
        50%     {{ transform: translateY(-8px); }}
      }}
      @keyframes yn-glow {{
        0%,100% {{ box-shadow: 0 0 18px rgba(240,180,41,0.35),
                               0 0 36px rgba(240,180,41,0.18); }}
        50%     {{ box-shadow: 0 0 30px rgba(240,180,41,0.75),
                               0 0 60px rgba(240,180,41,0.40),
                               0 0 90px rgba(240,180,41,0.18); }}
      }}
      @keyframes yn-glow-txt {{
        0%,100% {{ filter: drop-shadow(0 0 16px rgba(240,180,41,0.4)); }}
        50%     {{ filter: drop-shadow(0 0 28px rgba(240,180,41,0.8)); }}
      }}
      @keyframes yn-shadow {{
        0%,100% {{ transform: scaleX(1);   opacity:0.40; }}
        50%     {{ transform: scaleX(0.78); opacity:0.22; }}
      }}
    </style>
    <script>
      (function() {{
        var wrap = document.getElementById('ynWrap');
        if (!wrap) return;
        document.addEventListener('mousemove', function(e) {{
          var r = wrap.getBoundingClientRect();
          var cx = r.left + r.width / 2;
          var cy = r.top + r.height / 2;
          var dx = (e.clientX - cx) / (r.width  || 1);
          var dy = (e.clientY - cy) / (r.height || 1);
          var rotY = Math.max(-16, Math.min(16, dx * 22));
          var rotX = Math.max(-16, Math.min(16, -dy * 22));
          wrap.style.transform = 'rotateX(' + rotX + 'deg) rotateY(' + rotY + 'deg)';
        }});
        document.addEventListener('mouseleave', function() {{
          wrap.style.transform = 'rotateX(0deg) rotateY(0deg)';
        }});
      }})();
    </script>
    """


def render(tab, USER):
    with tab:
        st.subheader("👵 ยายนึก — กำลังใจเรื่องเงินของหลาน")

        m = get_mascot(USER)
        mood_emo, mood_name, mood_msg, days_away = get_mascot_mood(USER)
        outfit = m["outfit"] if m is not None else "ธรรมดา"
        coins = int(m["coins"]) if m is not None else 0
        streak = int(m["streak"]) if m is not None else 0

        # เลือกรูปยายนึกตามอารมณ์ (base64 embed จากไฟล์ใน assets/)
        yn_b64 = get_mascot_image_b64(mood_name)

        # ---------- แสดงยายนึก 2D + เอฟเฟกต์ ----------
        mc1, mc2 = st.columns([1, 2])
        with mc1:
            components.html(_mascot_effect_html(yn_b64, mood_emo), height=350)
            st.markdown(f"""
            <div style="text-align:center;margin-top:-8px">
            <div style="font-size:20px;font-weight:700">{mood_emo} {mood_name}</div>
            <div style="font-size:12px;color:#A8A4C8;margin-top:2px">ชุด: {outfit}</div>
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

