import streamlit as st

from core.db import get_conn
from core.auth import login_user, register_user, reset_password_by_email
from tabs import home, money, tax_tab, pricing, business, yainuk, settings, services, admin

st.set_page_config(page_title="เงินไทย", page_icon="💰", layout="wide")

# ===== Modern Slate — CSS แต่งเพิ่มให้เข้าธีม landing =====
st.markdown("""
<style>
:root{
  --violet:#7F77DD; --violet-deep:#534AB7; --mint:#1D9E75;
  --mint-soft:#5DCAA5; --ink:#0B0A1F; --slate:#16142E;
  --paper:#F4F3FB; --muted:#A8A4C8; --line:rgba(255,255,255,0.08);
}
/* พื้นหลังไล่เฉดนุ่มๆ */
.stApp{
  background:
    radial-gradient(1100px 700px at 15% -5%, rgba(127,119,221,0.12), transparent 55%),
    radial-gradient(900px 600px at 95% 0%, rgba(29,158,117,0.10), transparent 55%),
    var(--ink);
}
/* หัวข้อใหญ่ไล่เฉดม่วง-เขียว */
h1{
  font-weight:800 !important; letter-spacing:-0.5px;
  background:linear-gradient(120deg,#7F77DD 10%,#5DCAA5 90%);
  -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent;
}
h2,h3{color:var(--paper) !important; font-weight:700 !important;}
/* แท็บ */
.stTabs [data-baseweb="tab-list"]{gap:4px; border-bottom:1px solid var(--line);}
.stTabs [data-baseweb="tab"]{
  border-radius:10px 10px 0 0; padding:8px 14px; color:var(--muted);
}
.stTabs [aria-selected="true"]{
  background:rgba(127,119,221,0.14) !important; color:var(--paper) !important;
}
/* การ์ด metric — มุมมน เงานุ่ม ขอบเรืองแสง */
[data-testid="stMetric"]{
  background:rgba(255,255,255,0.03);
  border:1px solid var(--line);
  border-radius:16px; padding:16px 18px;
  transition:transform .2s, border-color .2s;
}
[data-testid="stMetric"]:hover{
  transform:translateY(-3px); border-color:rgba(127,119,221,0.4);
}
[data-testid="stMetricValue"]{
  font-weight:800 !important;
  background:linear-gradient(120deg,#7F77DD,#5DCAA5);
  -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent;
}
/* ปุ่ม */
.stButton>button, .stDownloadButton>button, .stFormSubmitButton>button{
  border-radius:12px; font-weight:600; border:1px solid var(--line);
  background:linear-gradient(135deg,var(--violet),var(--violet-deep));
  color:#fff; transition:transform .2s, box-shadow .2s;
}
.stButton>button:hover, .stDownloadButton>button:hover, .stFormSubmitButton>button:hover{
  transform:translateY(-2px); box-shadow:0 8px 24px rgba(83,74,183,0.4);
  border-color:transparent; color:#fff;
}
/* กล่อง input / selectbox มุมมน */
.stTextInput input, .stNumberInput input, .stDateInput input,
[data-baseweb="select"]>div{
  border-radius:10px !important;
}
/* expander */
.streamlit-expanderHeader, [data-testid="stExpander"]{
  border-radius:12px; border:1px solid var(--line);
}
/* ตาราง dataframe มุมมน */
[data-testid="stDataFrame"]{border-radius:12px; overflow:hidden;}
/* เส้นคั่น */
hr{border-color:var(--line) !important;}
/* sidebar */
[data-testid="stSidebar"]{
  background:var(--slate); border-right:1px solid var(--line);
}
/* ===== แก้ปัญหาตัวหนังสือกลืนพื้นหลัง — บังคับให้สว่างพออ่านได้ ===== */
/* ข้อความทั่วไป ป้ายกำกับ */
.stApp, .stApp p, .stApp span, .stApp label, .stApp li,
[data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] *,
.stMarkdown, .stMarkdown *{
  color:var(--paper);
}
/* caption / ข้อความช่วยเหลือ — สีเทาอ่อนพออ่านได้ */
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] *,
.stCaption, small{
  color:var(--muted) !important;
}
/* sidebar ทุกข้อความให้สว่าง */
[data-testid="stSidebar"] *, [data-testid="stSidebar"] p,
[data-testid="stSidebar"] span, [data-testid="stSidebar"] label{
  color:var(--paper) !important;
}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] *{
  color:var(--mint-soft) !important;
}
/* ลิงก์ */
.stApp a, [data-testid="stSidebar"] a{
  color:var(--mint-soft) !important; text-decoration:none;
}
.stApp a:hover{text-decoration:underline;}
/* ตัวเลข metric label และ caption ใต้ metric */
[data-testid="stMetricLabel"], [data-testid="stMetricLabel"] *{
  color:var(--muted) !important;
}
/* ตัวอักษรในช่องกรอก (input) ให้เข้ม อ่านบนพื้นอ่อน */
.stTextInput input, .stNumberInput input, .stDateInput input,
.stTextArea textarea{
  color:var(--paper) !important;
  background:var(--slate) !important;
}
/* พื้นหลังช่องกรอกทั้งหมดให้เข้มเข้าธีม (กันพื้นขาว ตัวขาว) */
.stTextInput>div>div, .stNumberInput>div>div, .stDateInput>div>div,
.stTextArea>div>div, [data-baseweb="input"], [data-baseweb="textarea"]{
  background:var(--slate) !important;
  border:1px solid var(--line) !important;
}
/* selectbox พื้นเข้ม */
[data-baseweb="select"]>div{
  background:var(--slate) !important;
  border:1px solid var(--line) !important;
}
/* dropdown selectbox text */
[data-baseweb="select"]{color:var(--paper) !important;}
/* ปุ่ม +/- ของ number_input ให้เข้ากับพื้นเข้ม */
.stNumberInput button{
  background:var(--slate) !important;
  color:var(--paper) !important;
  border:1px solid var(--line) !important;
}
/* เมนู dropdown ที่เปิดออกมา (ตัวเลือก) พื้นเข้ม ตัวสว่าง */
[data-baseweb="popover"] *, [data-baseweb="menu"] *{
  background:var(--slate) !important;
  color:var(--paper) !important;
}
/* กล่อง st.json / st.code / โค้ด — พื้นเข้ม ตัวสว่าง อ่านชัด */
[data-testid="stJson"], .stJson, pre, code,
[data-testid="stJson"] *{
  background:var(--slate) !important;
  color:var(--paper) !important;
}
[data-testid="stJson"]{
  border:1px solid var(--line) !important;
  border-radius:12px !important;
  padding:12px !important;
}
/* ตาราง dataframe ข้อความ */
[data-testid="stDataFrame"] *{color:var(--paper);}
/* แก้ JSON / code block ที่ตัวหนังสือจาง */
[data-testid="stJson"], [data-testid="stJson"] *,
.stJson, pre, code{
  color:var(--paper) !important;
}
[data-testid="stJson"]{
  background:var(--slate) !important; border-radius:10px;
}
</style>
""", unsafe_allow_html=True)

# =====================================================================
#  HEADER
# =====================================================================
# ===== PDPA: หน้าขอความยินยอม (แสดงก่อนเข้าใช้ครั้งแรก) =====
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "pdpa_consent" not in st.session_state:
    st.session_state.pdpa_consent = False

if not st.session_state.pdpa_consent:
    st.title("💰 เงินไทย")
    st.markdown("#### 🔒 นโยบายความเป็นส่วนตัว และการขอความยินยอม")
    st.markdown("""
    ก่อนเริ่มใช้งาน กรุณาอ่านและยอมรับนโยบายความเป็นส่วนตัว ตามพระราชบัญญัติคุ้มครองข้อมูลส่วนบุคคล พ.ศ. 2562 (PDPA)
    """)
    with st.expander("📋 อ่านนโยบายความเป็นส่วนตัวฉบับเต็ม", expanded=True):
        st.markdown("""
**1. ข้อมูลที่เราเก็บ**
เราเก็บข้อมูลที่คุณกรอกเข้าระบบ ได้แก่ ชื่อผู้ใช้ที่คุณตั้ง, รายการรายรับ-รายจ่าย, ข้อมูลภาษีและบัญชี, และข้อมูลที่คุณกรอกในฟอร์มต่างๆ

**2. วัตถุประสงค์การเก็บข้อมูล**
เพื่อใช้ในการคำนวณภาษี บันทึกบัญชี วิเคราะห์การเงิน และแสดงผลย้อนหลังให้คุณเท่านั้น เราไม่นำข้อมูลไปขายหรือเปิดเผยต่อบุคคลภายนอกโดยไม่ได้รับความยินยอม

**3. ระยะเวลาการเก็บข้อมูล**
เราเก็บข้อมูลไว้ตราบเท่าที่คุณยังใช้งาน คุณสามารถขอลบข้อมูลของตัวเองได้ตลอดเวลาผ่านเมนูในระบบ

**4. สิทธิของคุณ (เจ้าของข้อมูล)**
คุณมีสิทธิขอดู แก้ไข ดาวน์โหลด หรือลบข้อมูลส่วนบุคคลของคุณได้ตลอดเวลา ผ่านเมนู "ข้อมูลส่วนตัว/PDPA" ในระบบ

**5. มาตรการความปลอดภัย**
เราจัดให้มีมาตรการรักษาความปลอดภัยตามสมควรเพื่อป้องกันการเข้าถึงข้อมูลโดยไม่ได้รับอนุญาต อย่างไรก็ตาม ระบบนี้อยู่ในช่วงทดสอบ แนะนำไม่ให้กรอกข้อมูลที่เป็นความลับสูงสุด

**6. การติดต่อผู้ควบคุมข้อมูล**
หากมีข้อสงสัยเรื่องข้อมูลส่วนบุคคล ติดต่อได้ที่ LINE: 0610950531 หรือโทร 098-667-3680

**7. หมายเหตุ**
เงินไทย เป็นเครื่องมือช่วยคำนวณเบื้องต้น ไม่ใช่คำแนะนำทางกฎหมายหรือการเงินอย่างเป็นทางการ ควรตรวจสอบกับกรมสรรพากรก่อนยื่นจริง
        """)

    agree = st.checkbox("ฉันได้อ่านและยอมรับนโยบายความเป็นส่วนตัว และยินยอมให้เก็บรวบรวมและใช้ข้อมูลตามวัตถุประสงค์ข้างต้น")
    if st.button("ยอมรับและเริ่มใช้งาน →", use_container_width=True, disabled=not agree):
        if agree:
            st.session_state.pdpa_consent = True
            st.rerun()
    st.caption("การกดยอมรับถือว่าคุณให้ความยินยอมตาม PDPA — คุณสามารถถอนความยินยอมและลบข้อมูลได้ภายหลัง")
    st.stop()

# ===== ระบบเข้าสู่ระบบ / สมัครสมาชิก (มีรหัสผ่าน) =====
if not st.session_state.user_id:
    st.title("💰 เงินไทย")
    st.markdown("#### ยินดีต้อนรับ — เข้าสู่ระบบหรือสมัครสมาชิก")
    st.caption("🔒 ข้อมูลของคุณปลอดภัย รหัสผ่านถูกเข้ารหัส และแต่ละคนเห็นเฉพาะข้อมูลของตัวเอง")

    login_tab, reg_tab, forgot_tab = st.tabs(["🔑 เข้าสู่ระบบ", "✨ สมัครสมาชิกใหม่", "🔓 ลืมรหัสผ่าน"])

    with login_tab:
        with st.form("login_form"):
            li_user = st.text_input("ชื่อผู้ใช้", max_chars=30, key="li_user")
            li_pw = st.text_input("รหัสผ่าน", type="password", key="li_pw")
            if st.form_submit_button("เข้าสู่ระบบ", use_container_width=True):
                ok, msg = login_user(li_user, li_pw)
                if ok:
                    st.session_state.user_id = li_user.strip()
                    st.rerun()
                else:
                    st.error(msg)

    with reg_tab:
        with st.form("register_form"):
            rg_user = st.text_input("ตั้งชื่อผู้ใช้ (เช่น somchai)", max_chars=30, key="rg_user")
            rg_email = st.text_input("อีเมล (สำหรับกู้รหัสผ่าน + รับแจ้งเตือนภาษี)", key="rg_email",
                                     placeholder="your@email.com")
            rg_pw = st.text_input("ตั้งรหัสผ่าน (อย่างน้อย 6 ตัว)", type="password", key="rg_pw")
            rg_pw2 = st.text_input("ยืนยันรหัสผ่านอีกครั้ง", type="password", key="rg_pw2")
            if st.form_submit_button("สมัครสมาชิก", use_container_width=True):
                if rg_pw != rg_pw2:
                    st.error("รหัสผ่านทั้งสองช่องไม่ตรงกัน")
                else:
                    ok, msg = register_user(rg_user, rg_pw, rg_email)
                    if ok:
                        st.success(msg + " กำลังเข้าสู่ระบบ...")
                        st.session_state.user_id = rg_user.strip()
                        st.rerun()
                    else:
                        st.error(msg)
        st.caption("💡 แนะนำให้ใส่อีเมล เพื่อกู้รหัสผ่านได้เองและรับแจ้งเตือนกำหนดยื่นภาษี")

    with forgot_tab:
        st.markdown("**ลืมรหัสผ่าน?** กรอกชื่อผู้ใช้ ระบบจะส่งรหัสใหม่ไปที่อีเมลที่ผูกไว้")
        with st.form("forgot_form"):
            fg_user = st.text_input("ชื่อผู้ใช้", max_chars=30, key="fg_user")
            if st.form_submit_button("ส่งรหัสผ่านใหม่เข้าอีเมล", use_container_width=True):
                ok, msg = reset_password_by_email(fg_user)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)
        st.caption("📮 ถ้าไม่ได้ผูกอีเมลไว้ ติดต่อผู้ดูแล LINE: 0610950531")

    st.stop()

USER = st.session_state.user_id

# ===== ตรวจว่า user นี้เป็นผู้ดูแลระบบหรือไม่ (ระบุชื่อ admin ใน Secrets) =====
try:
    _admin_users = st.secrets.get("ADMIN_USERS", "")
except Exception:
    _admin_users = ""
# รองรับหลายคน คั่นด้วย comma เช่น "AdminSiri,siriwat"
ADMIN_LIST = [u.strip() for u in str(_admin_users).split(",") if u.strip()]
IS_ADMIN_USER = USER in ADMIN_LIST

# ===== หน้าต้อนรับ + คู่มือ (แสดงครั้งแรกหลังเข้าใช้) =====
if not st.session_state.get("seen_welcome"):
    st.title(f"👋 ยินดีต้อนรับสู่ เงินไทย, คุณ {USER}")
    st.markdown("#### แพลตฟอร์มบัญชี-ภาษี-วางแผนการเงิน ครบจบในที่เดียว")
    st.markdown("""
    **เริ่มต้นใช้งานง่ายๆ 3 ขั้น:**

    1. **📒 บันทึกบัญชี** — บันทึกรายรับรายจ่าย ติ๊กประเภทเงินได้ (เงินเดือน/ค้าขาย/ฯลฯ)
    2. **🧮 คำนวณภาษี** — ระบบคำนวณภาษีให้อัตโนมัติตามที่บันทึก พร้อมลดหย่อนครบ 26 รายการ
    3. **🏠 ภาพรวม** — ดูสุขภาพการเงิน กราฟ และคำแนะนำ
    """)

    st.markdown("**เลือกว่าคุณเป็นแบบไหน? (ระบบจะแนะนำโมดูลที่เหมาะกับคุณ)**")
    wc1, wc2, wc3 = st.columns(3)
    with wc1:
        if st.button("🧑 บุคคลทั่วไป/มนุษย์เงินเดือน", use_container_width=True):
            st.session_state.user_type = "บุคคลทั่วไป"
            st.session_state.seen_welcome = True
            st.rerun()
    with wc2:
        if st.button("🏪 ร้านค้า/ร้านอาหาร", use_container_width=True):
            st.session_state.user_type = "ร้านค้า"
            st.session_state.seen_welcome = True
            st.rerun()
    with wc3:
        if st.button("💼 ฟรีแลนซ์/รับจ้างอิสระ", use_container_width=True):
            st.session_state.user_type = "ฟรีแลนซ์"
            st.session_state.seen_welcome = True
            st.rerun()

    st.divider()
    if st.button("ข้ามไปเลย →"):
        st.session_state.user_type = "ทั่วไป"
        st.session_state.seen_welcome = True
        st.rerun()
    st.caption("💡 ผลการคำนวณเป็นการประมาณการเบื้องต้น ควรตรวจสอบกับกรมสรรพากรหรือผู้เชี่ยวชาญก่อนยื่นจริง")
    st.stop()

col_t, col_u = st.columns([4, 1])
with col_t:
    st.title("💰 เงินไทย")
    st.caption("แพลตฟอร์มบัญชี-ภาษี-วางแผนการเงิน สำหรับบุคคลธรรมดา | อ้างอิงประมวลรัษฎากร ปีภาษี 2568-2569")
with col_u:
    st.markdown(f"**ผู้ใช้:** {USER}")
    if st.button("ออกจากระบบ"):
        st.session_state.user_id = None
        st.rerun()

# ===== แบนเนอร์แนะนำโมดูลตามประเภทผู้ใช้ =====
_utype = st.session_state.get("user_type", "ทั่วไป")
_rec = {
    "บุคคลทั่วไป": "🧑 สำหรับคุณ: เริ่มที่ **📒 บันทึกบัญชี** → **🧮 คำนวณภาษี** เพื่อดูภาษีเงินเดือนของคุณ พร้อมลดหย่อน",
    "ร้านค้า": "🏪 สำหรับร้านค้า: ลองใช้ **🏪 ร้านค้า/ร้านอาหาร** ที่เทียบวิธีหักค่าใช้จ่ายและคำนวณภาษีให้ครบ + **💲 คำนวณราคาขาย**",
    "ฟรีแลนซ์": "💼 สำหรับฟรีแลนซ์: เริ่มที่ **📒 บันทึกบัญชี** (เลือกเงินได้ ม.40(2)) → **🧮 คำนวณภาษี** และดู **✂️ หัก ณ ที่จ่าย**",
}
if _utype in _rec:
    st.info(_rec[_utype])

# ===== Sidebar: ติดต่อผู้สร้าง / แจ้งปัญหา =====
with st.sidebar:
    st.markdown("### 📨 ติดต่อ / แจ้งปัญหา")
    st.caption("พบข้อผิดพลาดหรือมีข้อเสนอแนะ? แจ้งได้ที่นี่")
    with st.form("feedback_form", clear_on_submit=True):
        fb_type = st.selectbox("ประเภท", ["แจ้งบั๊ก/ข้อผิดพลาด", "เสนอฟีเจอร์ใหม่", "สอบถามการใช้งาน", "อื่นๆ"])
        fb_msg = st.text_area("รายละเอียด", height=100, placeholder="พิมพ์ข้อความของคุณ...")
        if st.form_submit_button("ส่งข้อความ", use_container_width=True):
            if fb_msg.strip():
                conn = get_conn()
                conn.execute(
                    "INSERT INTO feedback (user_id, fb_type, message) VALUES (?,?,?)",
                    (USER, fb_type, fb_msg.strip())
                )
                conn.commit(); conn.close()
                st.success("✅ ส่งข้อความเรียบร้อย ขอบคุณสำหรับข้อเสนอแนะ")
            else:
                st.error("กรุณาพิมพ์รายละเอียดก่อนส่ง")
    st.divider()
    st.markdown("**ช่องทางติดต่อ**")
    st.markdown("[💬 Facebook: Siriwat Khotphat](https://www.facebook.com/siriwat.khotphat.2024/?locale=th_TH)")
    st.caption("📱 LINE ID: 0610950531")
    st.caption("☎️ โทร: 098-667-3680")
    st.divider()
    with st.expander("📋 ข้อจำกัดความรับผิด"):
        st.caption(
            "เงินไทย เป็นเครื่องมือช่วยคำนวณและบันทึกข้อมูลเบื้องต้นเท่านั้น "
            "ผลการคำนวณภาษีเป็นการประมาณการ ไม่ใช่คำแนะนำทางกฎหมายหรือการเงินอย่างเป็นทางการ "
            "ผู้ใช้ควรตรวจสอบกับกรมสรรพากรหรือผู้เชี่ยวชาญก่อนยื่นภาษีจริงเสมอ "
            "ผู้พัฒนาไม่รับผิดชอบต่อความเสียหายที่เกิดจากการนำผลไปใช้โดยไม่ตรวจสอบ"
        )

    # ===== Admin Panel — แสดงเฉพาะ user ที่เป็น admin (ไม่ต้องใส่รหัสซ้ำ) =====
    if IS_ADMIN_USER:
        st.divider()
        st.markdown("**🛠️ โหมดผู้ดูแลระบบ**")
        st.caption(f"คุณ ({USER}) มีสิทธิ์ผู้ดูแล")
        if st.button("เปิดแดชบอร์ดผู้ดูแล", use_container_width=True):
            st.session_state.is_admin = True
            st.rerun()


if st.session_state.get("is_admin") and IS_ADMIN_USER:
    admin.render(USER)

tabD, tabMoney, tabTax, tabPrice, tabShop, tabAnalysis, tabPlan, tabLaw, tabMascot, tabPartner, tabConsult, tabService, tabUpgrade, tabPDPA = st.tabs([
    "🏠 หน้าหลัก", "💰 รายรับ-รายจ่าย", "🧮 คำนวณภาษี", "💲 ต้นทุน+ราคาขาย", "🏪 ร้านค้า/ร้านอาหาร",
    "📊 วิเคราะห์", "🔮 วางแผนการเงิน", "📖 คลังความรู้ภาษี",
    "🐷 ยายนึก", "💞 ออมด้วยกัน", "🤝 ปรึกษาผู้เชี่ยวชาญ", "💼 บริการของเรา", "⭐ อัปเกรด", "🔒 ข้อมูล/PDPA"
])

home.render(tabD, tabAnalysis, tabPlan, USER)
money.render(tabMoney, USER)
tax_tab.render(tabTax, tabLaw, USER)
pricing.render(tabPrice, USER)
business.render(tabShop, USER)
yainuk.render(tabMascot, USER)
settings.render(tabConsult, tabPDPA, tabPartner, USER)
services.render(tabUpgrade, tabService, USER)
