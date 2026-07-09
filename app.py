import streamlit as st
import sqlite3
import pandas as pd
from datetime import date, datetime
import io

st.set_page_config(page_title="TaxSmart", page_icon="💰", layout="wide")

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
#  ฐานข้อมูลกลาง (Single Source of Truth)
# =====================================================================
DB = "taxsmart.db"

def get_conn():
    conn = sqlite3.connect(DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            txn_date TEXT NOT NULL,
            txn_type TEXT NOT NULL,          -- รายรับ / รายจ่าย
            income_type TEXT,                -- ประเภทเงินได้ ม.40(x) (เฉพาะรายรับ)
            category TEXT NOT NULL,
            description TEXT,
            amount REAL NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # ----- Auto-migration: เพิ่มคอลัมน์ที่ขาดให้ตารางเก่า โดยไม่ลบข้อมูลเดิม -----
    existing = [r[1] for r in conn.execute("PRAGMA table_info(transactions)").fetchall()]
    migrations = {
        "income_type": "ALTER TABLE transactions ADD COLUMN income_type TEXT",
        "description": "ALTER TABLE transactions ADD COLUMN description TEXT",
        "created_at": "ALTER TABLE transactions ADD COLUMN created_at TEXT",
        "user_id": "ALTER TABLE transactions ADD COLUMN user_id TEXT",
    }
    for col, sql in migrations.items():
        if col not in existing:
            conn.execute(sql)
    # ตารางเก็บข้อความติดต่อ/แจ้งปัญหา
    conn.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            fb_type TEXT,
            message TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # ตารางเคลื่อนไหวสินค้า (ซื้อเข้า/ขายออก) สำหรับคำนวณต้นทุน
    conn.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            move_date TEXT NOT NULL,
            product TEXT NOT NULL,
            move_type TEXT NOT NULL,
            qty REAL NOT NULL,
            unit_cost REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # ตารางคำขอปรึกษาผู้เชี่ยวชาญ
    conn.execute("""
        CREATE TABLE IF NOT EXISTS consult_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            service TEXT,
            contact TEXT,
            detail TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn

# =====================================================================
#  คลังความรู้กฎหมายภาษี — ประเภทเงินได้ ม.40 และวิธีหักค่าใช้จ่าย
#  อ้างอิงประมวลรัษฎากร หมวด 3 (ปีภาษี 2568-2569)
# =====================================================================
INCOME_TYPES = {
    "40(1) เงินเดือน ค่าจ้าง": {
        "section": "มาตรา 40(1)",
        "expense_rule": "หักเหมา 50% สูงสุด 100,000 บาท (รวมกับ 40(2))",
        "expense_rate": 0.50,
        "expense_cap": 100_000,
        "note": "เงินได้จากการจ้างแรงงาน เช่น เงินเดือน โบนัส เบี้ยเลี้ยง",
    },
    "40(2) รับจ้างทำงาน/ฟรีแลนซ์": {
        "section": "มาตรา 40(2)",
        "expense_rule": "หักเหมา 50% สูงสุด 100,000 บาท (รวมกับ 40(1))",
        "expense_rate": 0.50,
        "expense_cap": 100_000,
        "note": "ค่านายหน้า ค่าจ้างทั่วไปที่ไม่ใช่ลูกจ้างประจำ",
    },
    "40(3) ค่าลิขสิทธิ์/goodwill": {
        "section": "มาตรา 40(3)",
        "expense_rule": "หักตามจริง หรือเหมา 50% สูงสุด 100,000 (เฉพาะบางกรณี)",
        "expense_rate": 0.50,
        "expense_cap": 100_000,
        "note": "ค่าแห่งกู๊ดวิลล์ ลิขสิทธิ์ สิทธิอย่างอื่น",
    },
    "40(4) ดอกเบี้ย/เงินปันผล": {
        "section": "มาตรา 40(4)",
        "expense_rule": "หักค่าใช้จ่ายไม่ได้",
        "expense_rate": 0.0,
        "expense_cap": 0,
        "note": "ดอกเบี้ยเงินฝาก เงินปันผล (มักถูกหัก ณ ที่จ่ายแล้ว)",
    },
    "40(5) ค่าเช่าทรัพย์สิน": {
        "section": "มาตรา 40(5)",
        "expense_rule": "หักเหมา 10-30% ตามประเภททรัพย์ หรือหักตามจริง",
        "expense_rate": 0.30,
        "expense_cap": None,
        "note": "ค่าเช่าบ้าน ที่ดิน ยานพาหนะ (เหมาตามชนิดทรัพย์สิน)",
    },
    "40(6) วิชาชีพอิสระ": {
        "section": "มาตรา 40(6)",
        "expense_rule": "หักเหมา 30-60% ตามวิชาชีพ หรือหักตามจริง",
        "expense_rate": 0.30,
        "expense_cap": None,
        "note": "แพทย์ ทนาย วิศวกร สถาปนิก บัญชี ประณีตศิลป์",
    },
    "40(7) รับเหมา (ค่าแรง+ของ)": {
        "section": "มาตรา 40(7)",
        "expense_rule": "หักเหมา 60% หรือหักตามจริง",
        "expense_rate": 0.60,
        "expense_cap": None,
        "note": "รับเหมาที่ผู้รับเหมาจัดหาสัมภาระสำคัญนอกจากเครื่องมือ",
    },
    "40(8) ธุรกิจ/ค้าขาย": {
        "section": "มาตรา 40(8)",
        "expense_rule": "หักเหมา 60% หรือหักตามจริง (ม.65 ทวิ)",
        "expense_rate": 0.60,
        "expense_cap": None,
        "note": "ค้าขาย ขายของออนไลน์ ร้านอาหาร ขนส่ง ฯลฯ",
    },
}

# =====================================================================
#  ฟังก์ชันคำนวณภาษีขั้นบันได (มาตรา 48) ปีภาษี 2568-2569
# =====================================================================
def calc_progressive_tax(net_income):
    brackets = [
        (150_000, 0.00), (300_000, 0.05), (500_000, 0.10), (750_000, 0.15),
        (1_000_000, 0.20), (2_000_000, 0.25), (5_000_000, 0.30), (float("inf"), 0.35),
    ]
    tax, prev, detail = 0.0, 0, []
    for limit, rate in brackets:
        if net_income > prev:
            taxable = min(net_income, limit) - prev
            t = taxable * rate
            tax += t
            if taxable > 0:
                detail.append({
                    "ช่วงเงินได้สุทธิ": f"{prev:,.0f} - {min(net_income, limit):,.0f}",
                    "อัตรา": f"{rate*100:.0f}%",
                    "ภาษี (บาท)": round(t, 2),
                })
        prev = limit
        if net_income <= limit:
            break
    return round(tax, 2), detail

# =====================================================================
#  ฟังก์ชัน Export รายงานเป็น Excel
# =====================================================================
def make_excel_report(df, user):
    """สร้างไฟล์ Excel มี 2 sheet: รายการทั้งหมด + สรุปรายเดือน"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        # Sheet 1: รายการทั้งหมด
        export_df = df.rename(columns={
            "txn_date":"วันที่","txn_type":"ประเภท","income_type":"เงินได้ ม.40",
            "category":"หมวดหมู่","description":"รายละเอียด","amount":"จำนวนเงิน"
        })
        cols = ["วันที่","ประเภท","เงินได้ ม.40","หมวดหมู่","รายละเอียด","จำนวนเงิน"]
        cols = [c for c in cols if c in export_df.columns]
        export_df[cols].to_excel(writer, sheet_name="รายการทั้งหมด", index=False)

        # Sheet 2: สรุปรายเดือน
        tmp = df.copy()
        tmp["txn_date"] = pd.to_datetime(tmp["txn_date"])
        tmp["เดือน"] = tmp["txn_date"].dt.to_period("M").astype(str)
        summary = tmp.pivot_table(index="เดือน", columns="txn_type",
                                   values="amount", aggfunc="sum", fill_value=0).reset_index()
        for c in ["รายรับ","รายจ่าย"]:
            if c not in summary.columns:
                summary[c] = 0
        summary["กำไรสุทธิ"] = summary["รายรับ"] - summary["รายจ่าย"]
        summary.to_excel(writer, sheet_name="สรุปรายเดือน", index=False)

        # จัดความกว้างคอลัมน์ให้อ่านง่าย
        for sheet in writer.sheets.values():
            for col in sheet.columns:
                width = max((len(str(c.value)) for c in col if c.value), default=10)
                sheet.column_dimensions[col[0].column_letter].width = min(width + 4, 40)

    output.seek(0)
    return output.getvalue()

# =====================================================================
#  ฟังก์ชัน Export รายงานสรุปภาษีเป็น PDF (รองรับภาษาไทย)
# =====================================================================
def make_pdf_report(df, user, tax_summary=None):
    """สร้างรายงาน PDF สรุปบัญชีและภาษี — โหลดฟอนต์ไทยจากระบบ Windows อัตโนมัติ"""
    import os
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

    # หาฟอนต์ไทยจากระบบ (Windows / macOS / Linux)
    thai_font_paths = [
        r"C:\Windows\Fonts\tahoma.ttf",
        r"C:\Windows\Fonts\leelawui.ttf",
        r"C:\Windows\Fonts\leelawad.ttf",
        r"C:\Windows\Fonts\angsau.ttf",
        r"C:\Windows\Fonts\cordia.ttf",
        "/Library/Fonts/Thonburi.ttf",
        "/usr/share/fonts/truetype/tlwg/Sarabun.ttf",
        "/usr/share/fonts/truetype/thai/Sarabun.ttf",
    ]
    font_name = "Helvetica"  # fallback
    for fp in thai_font_paths:
        if os.path.exists(fp):
            try:
                pdfmetrics.registerFont(TTFont("ThaiFont", fp))
                font_name = "ThaiFont"
                break
            except Exception:
                continue

    output = io.BytesIO()
    doc = SimpleDocTemplate(output, pagesize=A4,
                            topMargin=20*mm, bottomMargin=20*mm,
                            leftMargin=18*mm, rightMargin=18*mm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("ThaiTitle", parent=styles["Title"], fontName=font_name, fontSize=18)
    head_style = ParagraphStyle("ThaiHead", parent=styles["Heading2"], fontName=font_name, fontSize=13)
    normal_style = ParagraphStyle("ThaiNormal", parent=styles["Normal"], fontName=font_name, fontSize=10)

    story = []
    story.append(Paragraph("รายงานสรุปบัญชีและภาษี — TaxSmart", title_style))
    story.append(Paragraph(f"ผู้ใช้: {user} | วันที่ออกรายงาน: {date.today().isoformat()}", normal_style))
    story.append(Spacer(1, 10))

    # สรุปยอด
    ti = df[df.txn_type=="รายรับ"].amount.sum()
    te = df[df.txn_type=="รายจ่าย"].amount.sum()
    story.append(Paragraph("สรุปภาพรวม", head_style))
    summary_data = [
        ["รายการ", "จำนวนเงิน (บาท)"],
        ["รายรับรวม", f"{ti:,.2f}"],
        ["รายจ่ายรวม", f"{te:,.2f}"],
        ["กำไรสุทธิ", f"{ti-te:,.2f}"],
    ]
    if tax_summary:
        summary_data.append(["ภาษีโดยประมาณ", f"{tax_summary:,.2f}"])
    t = Table(summary_data, colWidths=[90*mm, 70*mm])
    t.setStyle(TableStyle([
        ("FONTNAME", (0,0), (-1,-1), font_name),
        ("FONTSIZE", (0,0), (-1,-1), 10),
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#1D9E75")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("ALIGN", (1,0), (1,-1), "RIGHT"),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#F1EFE8")]),
    ]))
    story.append(t)
    story.append(Spacer(1, 14))

    # รายการล่าสุด (สูงสุด 30 รายการ)
    story.append(Paragraph("รายการทั้งหมด (แสดงสูงสุด 30 รายการล่าสุด)", head_style))
    rows = [["วันที่", "ประเภท", "หมวดหมู่", "จำนวนเงิน"]]
    for _, r in df.head(30).iterrows():
        d = pd.to_datetime(r["txn_date"], errors="coerce")
        d_str = d.strftime("%Y-%m-%d") if pd.notna(d) else str(r["txn_date"])
        rows.append([d_str, r["txn_type"], r["category"], f"{r['amount']:,.2f}"])
    t2 = Table(rows, colWidths=[35*mm, 30*mm, 60*mm, 35*mm])
    t2.setStyle(TableStyle([
        ("FONTNAME", (0,0), (-1,-1), font_name),
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#378ADD")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("ALIGN", (3,0), (3,-1), "RIGHT"),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#F1EFE8")]),
    ]))
    story.append(t2)
    story.append(Spacer(1, 14))
    story.append(Paragraph("⚠️ รายงานนี้เป็นการประมาณการเบื้องต้นตามอัตราปีภาษี 2568-2569 "
                           "ควรตรวจสอบกับกรมสรรพากรหรือผู้เชี่ยวชาญก่อนยื่นจริง", normal_style))

    doc.build(story)
    output.seek(0)
    return output.getvalue()

# =====================================================================
#  ฟังก์ชันคำนวณต้นทุนสินค้า — FIFO และ Weighted Average (TAS 2)
# =====================================================================
def calc_fifo(movements):
    """คำนวณต้นทุนแบบ FIFO. movements = list ของ dict {move_type, qty, unit_cost}
    คืนค่า: ต้นทุนขายรวม (COGS), มูลค่าคงเหลือ, จำนวนคงเหลือ"""
    lots = []  # คิว [qty, unit_cost]
    cogs = 0.0
    for m in movements:
        if m["move_type"] == "ซื้อเข้า":
            lots.append([m["qty"], m["unit_cost"]])
        else:  # ขายออก
            remain = m["qty"]
            while remain > 0 and lots:
                lot = lots[0]
                take = min(remain, lot[0])
                cogs += take * lot[1]
                lot[0] -= take
                remain -= take
                if lot[0] <= 0:
                    lots.pop(0)
    ending_qty = sum(l[0] for l in lots)
    ending_value = sum(l[0]*l[1] for l in lots)
    return round(cogs, 2), round(ending_value, 2), round(ending_qty, 2)

def calc_weighted_avg(movements):
    """คำนวณต้นทุนแบบถัวเฉลี่ยถ่วงน้ำหนัก (Weighted Average)"""
    total_qty = 0.0
    total_value = 0.0
    cogs = 0.0
    for m in movements:
        if m["move_type"] == "ซื้อเข้า":
            total_qty += m["qty"]
            total_value += m["qty"] * m["unit_cost"]
        else:  # ขายออก
            avg_cost = (total_value / total_qty) if total_qty > 0 else 0.0
            sold = min(m["qty"], total_qty)
            cogs += sold * avg_cost
            total_value -= sold * avg_cost
            total_qty -= sold
    return round(cogs, 2), round(total_value, 2), round(total_qty, 2)

# =====================================================================
#  HEADER
# =====================================================================
# ===== ระบบแยกผู้ใช้ ระดับ 1 (พิมพ์ชื่อเข้าใช้) =====
if "user_id" not in st.session_state:
    st.session_state.user_id = None

if not st.session_state.user_id:
    st.title("💰 TaxSmart")
    st.markdown("#### เข้าใช้งาน — กรุณาพิมพ์ชื่อผู้ใช้ของคุณ")
    st.caption("แต่ละชื่อจะเห็นเฉพาะข้อมูลของตัวเอง (ระบบทดสอบ ยังไม่มีรหัสผ่าน)")
    with st.form("login_form"):
        uid = st.text_input("ชื่อผู้ใช้ (เช่น somchai หรือ user01)", max_chars=30)
        if st.form_submit_button("เข้าใช้งาน", use_container_width=True):
            cleaned = uid.strip()
            if cleaned:
                st.session_state.user_id = cleaned
                st.rerun()
            else:
                st.error("กรุณาพิมพ์ชื่อผู้ใช้ก่อนเข้าใช้งาน")
    st.stop()

USER = st.session_state.user_id

# ===== หน้าต้อนรับ + คู่มือ (แสดงครั้งแรกหลังเข้าใช้) =====
if not st.session_state.get("seen_welcome"):
    st.title(f"👋 ยินดีต้อนรับสู่ TaxSmart, คุณ {USER}")
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
    st.title("💰 TaxSmart")
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
            "TaxSmart เป็นเครื่องมือช่วยคำนวณและบันทึกข้อมูลเบื้องต้นเท่านั้น "
            "ผลการคำนวณภาษีเป็นการประมาณการ ไม่ใช่คำแนะนำทางกฎหมายหรือการเงินอย่างเป็นทางการ "
            "ผู้ใช้ควรตรวจสอบกับกรมสรรพากรหรือผู้เชี่ยวชาญก่อนยื่นภาษีจริงเสมอ "
            "ผู้พัฒนาไม่รับผิดชอบต่อความเสียหายที่เกิดจากการนำผลไปใช้โดยไม่ตรวจสอบ"
        )

tabD, tab1, tab2, tabShop, tab6, tab7, tab8, tab9, tab10, tab3, tab4, tab5, tabConsult = st.tabs([
    "🏠 ภาพรวม (Dashboard)", "📒 บันทึกบัญชี", "🧮 คำนวณภาษี", "🏪 ร้านค้า/ร้านอาหาร",
    "📅 ภาษีครึ่งปี (ภ.ง.ด.94)", "🧾 VAT (ภ.พ.30)", "✂️ หัก ณ ที่จ่าย", "📦 ต้นทุนสินค้า",
    "💲 คำนวณราคาขาย", "📊 วิเคราะห์รายเดือน-ปี", "🔮 วางแผนการเงิน", "📖 คลังกฎหมายภาษี",
    "🤝 ปรึกษาผู้เชี่ยวชาญ"
])

# =====================================================================
#  TAB DASHBOARD — ภาพรวมสุขภาพการเงิน
# =====================================================================
with tabD:
    st.subheader("🏠 ภาพรวมสุขภาพการเงินของคุณ")
    conn = get_conn()
    df_d = pd.read_sql_query("SELECT * FROM transactions WHERE user_id=?", conn, params=(USER,))
    conn.close()

    if df_d.empty:
        st.info("ยังไม่มีข้อมูล — เริ่มบันทึกรายรับรายจ่ายที่แท็บ 'บันทึกบัญชี' แล้วกลับมาดูภาพรวมที่นี่")
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

        # ===== กราฟรายรับ-รายจ่ายรายเดือน =====
        cL, cR = st.columns(2)
        with cL:
            st.markdown("##### 📈 รายรับ-รายจ่ายรายเดือน")
            df_d["เดือน"] = df_d["txn_date"].dt.to_period("M").astype(str)
            monthly = df_d.pivot_table(index="เดือน", columns="txn_type",
                                       values="amount", aggfunc="sum", fill_value=0)
            for c in ["รายรับ","รายจ่าย"]:
                if c not in monthly.columns:
                    monthly[c] = 0
            st.bar_chart(monthly[["รายรับ","รายจ่าย"]])

        with cR:
            st.markdown("##### 🍩 หมวดค่าใช้จ่ายสูงสุด")
            exp_df = df_d[df_d.txn_type=="รายจ่าย"]
            if exp_df.empty:
                st.info("ยังไม่มีรายจ่าย")
            else:
                by_cat = exp_df.groupby("category")["amount"].sum().sort_values(ascending=False)
                st.bar_chart(by_cat)
                top_cat = by_cat.index[0]
                top_amt = by_cat.iloc[0]
                st.caption(f"💡 หมวดที่จ่ายมากสุด: **{top_cat}** ({top_amt:,.0f} บาท = {top_amt/expense*100:.0f}% ของรายจ่าย)")

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



# =====================================================================
#  TAB 1 — บันทึกบัญชี (มีติ๊กเลือกประเภทเงินได้)
# =====================================================================
with tab1:
    with st.form("txn_form", clear_on_submit=True):
        st.subheader("📝 บันทึกรายการใหม่")
        c1, c2, c3 = st.columns(3)
        with c1:
            txn_date = st.date_input("วันที่", value=date.today())
            txn_type = st.selectbox("ประเภท", ["รายรับ", "รายจ่าย"])
        with c2:
            # ติ๊กเลือกประเภทเงินได้ (เฉพาะรายรับ)
            income_type = st.selectbox(
                "ประเภทเงินได้ (ตามมาตรา 40) — เลือกถ้าเป็นรายรับ",
                ["— ไม่ระบุ —"] + list(INCOME_TYPES.keys()),
                help="ระบบจะใช้ข้อมูลนี้เติมช่องภาษีให้อัตโนมัติในแท็บคำนวณภาษี"
            )
            amount = st.number_input("จำนวนเงิน (บาท)", min_value=0.0, step=100.0, format="%.2f")
        with c3:
            category = st.selectbox("หมวดหมู่บัญชี", [
                "ขายสินค้า", "ค่าบริการ", "รายได้อื่นๆ",
                "ซื้อสินค้า/วัตถุดิบ", "ค่าขนส่ง", "ค่าเช่า",
                "ค่าน้ำค่าไฟ", "ค่าโฆษณา", "เงินเดือนพนักงาน", "ค่าใช้จ่ายอื่นๆ"
            ])
            description = st.text_input("รายละเอียด (ไม่บังคับ)")

        if st.form_submit_button("💾 บันทึกรายการ", use_container_width=True):
            if amount <= 0:
                st.error("กรุณากรอกจำนวนเงินมากกว่า 0")
            else:
                it = None if income_type == "— ไม่ระบุ —" else income_type
                conn = get_conn()
                conn.execute(
                    "INSERT INTO transactions (txn_date, txn_type, income_type, category, description, amount, user_id) VALUES (?,?,?,?,?,?,?)",
                    (txn_date.isoformat(), txn_type, it, category, description, amount, USER)
                )
                conn.commit(); conn.close()
                st.success(f"✅ บันทึก {txn_type} {amount:,.2f} บาท เรียบร้อย!")

    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM transactions WHERE user_id=? ORDER BY txn_date DESC, id DESC", conn, params=(USER,))
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

        editor_df = df.rename(columns={
            "txn_date":"วันที่","txn_type":"ประเภท","income_type":"เงินได้ ม.40",
            "category":"หมวดหมู่","description":"รายละเอียด","amount":"จำนวนเงิน"
        }).copy()
        # บังคับคอลัมน์วันที่ให้เป็นข้อความ YYYY-MM-DD สะอาด (กันแสดงผลเพี้ยน/มีเวลา 00:00:00)
        editor_df["วันที่"] = pd.to_datetime(editor_df["วันที่"], errors="coerce").dt.strftime("%Y-%m-%d")
        # ป้องกัน KeyError: เติมคอลัมน์ที่อาจหายไปให้ครบก่อนเสมอ
        for col in ["เงินได้ ม.40","รายละเอียด"]:
            if col not in editor_df.columns:
                editor_df[col] = ""
        editor_df["เงินได้ ม.40"] = editor_df["เงินได้ ม.40"].fillna("")
        editor_df["รายละเอียด"] = editor_df["รายละเอียด"].fillna("")
        editor_df["ลบ"] = False
        view_cols = ["ลบ","วันที่","ประเภท","เงินได้ ม.40","หมวดหมู่","รายละเอียด","จำนวนเงิน"]

        edited = st.data_editor(
            editor_df[["id"] + view_cols],
            use_container_width=True, hide_index=True,
            disabled=["id","วันที่","ประเภท","เงินได้ ม.40","หมวดหมู่","รายละเอียด","จำนวนเงิน"],
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

# =====================================================================
#  TAB 2 — คำนวณภาษี (เติมช่องอัตโนมัติจากประเภทเงินได้ที่ติ๊กไว้)
# =====================================================================
with tab2:
    st.subheader("🧮 คำนวณภาษีเงินได้บุคคลธรรมดา")

    conn = get_conn()
    inc = pd.read_sql_query("SELECT * FROM transactions WHERE txn_type='รายรับ' AND user_id=?", conn, params=(USER,))
    conn.close()

    if inc.empty:
        st.info("ยังไม่มีรายรับในระบบ — ไปบันทึกที่แท็บ  'บันทึกบัญชี' ก่อน")
    else:
        # จัดกลุ่มรายรับตามประเภทเงินได้ที่ติ๊กไว้
        st.markdown("##### 📥 รายรับแยกตามประเภทเงินได้ (ดึงจากที่คุณติ๊กไว้)")
        grouped = inc.groupby("income_type", dropna=False)["amount"].sum().reset_index()

        total_after_expense = 0.0
        used_sections = []
        for _, row in grouped.iterrows():
            it = row["income_type"]
            amt = row["amount"]
            if it is None or it not in INCOME_TYPES:
                st.warning(f"⚠️ รายรับ {amt:,.0f} บาท ยังไม่ได้ระบุประเภทเงินได้ — หักค่าใช้จ่ายไม่ได้จนกว่าจะระบุ")
                total_after_expense += amt
                continue
            info = INCOME_TYPES[it]
            rate = info["expense_rate"]; cap = info["expense_cap"]
            expense = amt * rate
            if cap is not None:
                expense = min(expense, cap)
            after = amt - expense
            total_after_expense += after
            used_sections.append(info["section"])
            st.markdown(
                f"**{it}** — รายรับ {amt:,.0f} | หักค่าใช้จ่าย "
                f"({info['expense_rule']}) = {expense:,.0f} | เหลือ {after:,.0f} บาท"
            )

        st.divider()
        st.markdown("##### 📋 ค่าลดหย่อน ปีภาษี 2568 — ครบทุกรายการ (อ้างอิง ภ.ง.ด.90/91)")
        st.caption("เปิดเฉพาะกลุ่มที่คุณใช้สิทธิ์ — ส่วนที่ไม่ได้กรอกระบบจะถือเป็น 0")

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
                social = st.number_input("ประกันสังคม (สูงสุด 9,000)", 0.0, 9_000.0, 0.0, step=100.0)
                life_ins = st.number_input("ประกันชีวิตทั่วไป", 0.0, 100_000.0, 0.0, step=1000.0)
                health_ins = st.number_input("ประกันสุขภาพตัวเอง (สูงสุด 25,000)", 0.0, 25_000.0, 0.0, step=1000.0)
                health_parents = st.number_input("ประกันสุขภาพบิดามารดา (สูงสุด 15,000)", 0.0, 15_000.0, 0.0, step=1000.0)
                thai_esg = st.number_input("กองทุน Thai ESG/ESGX (สูงสุด 300,000)", 0.0, 300_000.0, 0.0, step=1000.0)
            with g2b:
                st.markdown("**กลุ่มเกษียณ (เพดานรวม 500,000):**")
                pension_ins = st.number_input("ประกันชีวิตแบบบำนาญ", 0.0, 200_000.0, 0.0, step=1000.0)
                rmf = st.number_input("กองทุน RMF", 0.0, 500_000.0, 0.0, step=1000.0)
                pvd = st.number_input("กองทุนสำรองเลี้ยงชีพ (PVD)", 0.0, 500_000.0, 0.0, step=1000.0)
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
                home_interest = st.number_input("ดอกเบี้ยที่อยู่อาศัย (สูงสุด 100,000)", 0.0, 100_000.0, 0.0, step=1000.0)
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
                donate_general = st.number_input("บริจาคทั่วไป (ไม่เกิน 10% ของเงินได้)", 0.0, 1_000_000.0, 0.0, step=500.0)
                donate_edu = st.number_input("บริจาคการศึกษา/กีฬา/รพ.รัฐ/สังคม (หัก 2 เท่า)", 0.0, 500_000.0, 0.0, step=500.0)
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

# =====================================================================
#  TAB 3 — วิเคราะห์รายเดือน-รายปี
# =====================================================================
with tab3:
    st.subheader("📊 วิเคราะห์รายรับ-รายจ่าย รายเดือนและรายปี")
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM transactions WHERE user_id=?", conn, params=(USER,))
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
                file_name=f"TaxSmart_{USER}_{date.today().isoformat()}.xlsx",
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
                file_name=f"TaxSmart_{USER}_{date.today().isoformat()}.csv",
                mime="text/csv",
                use_container_width=True
            )
        with ex3:
            try:
                pdf_bytes = make_pdf_report(df, USER)
                st.download_button(
                    "📕 PDF (รายงานสรุป)",
                    data=pdf_bytes,
                    file_name=f"TaxSmart_{USER}_{date.today().isoformat()}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e:
                st.button("📕 PDF (ไม่พร้อม)", disabled=True, use_container_width=True)
                st.caption(f"PDF ต้องมีฟอนต์ไทยในเครื่อง: {e}")
        st.caption("Excel มี 2 ชีต (รายการ + สรุปรายเดือน) | PDF เป็นรายงานสรุปพร้อมพิมพ์ | เปิดได้ทั้ง Excel และ Google Sheets")

# =====================================================================
#  TAB 4 — วางแผนการเงิน (คาดการณ์อนาคต)
# =====================================================================
with tab4:
    st.subheader("🔮 คาดการณ์และวางแผนการเงินในอนาคต")
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM transactions WHERE user_id=?", conn, params=(USER,))
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

# =====================================================================
#  TAB 6 — ภาษีครึ่งปี (ภ.ง.ด.94) มาตรา 56 ทวิ
# =====================================================================
with tab6:
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
    inc_h = pd.read_sql_query(
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

# =====================================================================
#  TAB 7 — VAT (ภ.พ.30) ภาษีมูลค่าเพิ่ม
# =====================================================================
with tab7:
    st.subheader("🧾 ภาษีมูลค่าเพิ่ม (ภ.พ.30)")
    st.caption("ภาษีขาย (7% ของรายรับ) − ภาษีซื้อ (7% ของรายจ่าย) | ยื่นทุกเดือน ภายในวันที่ 15 ของเดือนถัดไป")

    VAT_RATE = 0.07

    conn = get_conn()
    df_v = pd.read_sql_query("SELECT * FROM transactions WHERE user_id=?", conn, params=(USER,))
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

# =====================================================================
#  TAB 8 — ภาษีหัก ณ ที่จ่าย (Withholding Tax)
# =====================================================================
with tab8:
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

# =====================================================================
#  TAB 9 — โมดูลคำนวณต้นทุนสินค้า (FIFO / Weighted Average) ตาม TAS 2
# =====================================================================
with tab9:
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
    inv_df = pd.read_sql_query(
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

# =====================================================================
#  TAB 10 — คำนวณราคาขาย + เทียบราคา (ช่วยพ่อค้าแม่ค้าตั้งราคา)
# =====================================================================
with tab10:
    st.subheader("💲 คำนวณราคาขายและเทียบราคา")
    st.caption("ใส่ต้นทุน แล้วระบบช่วยตั้งราคาขายตามกำไรที่ต้องการ + เทียบหลายวิธีให้ตัดสินใจ")

    st.markdown("##### 📥 ใส่ข้อมูลต้นทุน")
    pc1, pc2 = st.columns(2)
    with pc1:
        product_name = st.text_input("ชื่อสินค้า (ไม่บังคับ)", placeholder="เช่น เสื้อยืด")
        cost = st.number_input("ต้นทุนสินค้า/หน่วย (บาท)", min_value=0.0, step=10.0, format="%.2f")
        other_cost = st.number_input("ต้นทุนแฝงต่อหน่วย (ค่าส่ง/แพ็ค/ค่าธรรมเนียม)", min_value=0.0, step=5.0, format="%.2f",
                                     help="ค่าใช้จ่ายอื่นต่อชิ้น เช่น ค่ากล่อง ค่าส่ง ค่าธรรมเนียมแพลตฟอร์ม")
    with pc2:
        target_margin = st.slider("กำไรที่ต้องการ (% ของราคาขาย)", 0, 90, 30,
                                  help="กำไรขั้นต้นคิดเป็น % ของราคาขาย")
        vat_included = st.checkbox("บวก VAT 7% ในราคาขาย", value=False)

    total_cost = cost + other_cost

    if total_cost <= 0:
        st.info("กรอกต้นทุนสินค้าก่อน เพื่อให้ระบบคำนวณราคาขายแนะนำ")
    else:
        # ===== วิธีที่ 1: ตั้งราคาจาก % กำไรของราคาขาย (margin) =====
        # ราคาขาย = ต้นทุน / (1 - margin%)
        if target_margin < 100:
            price_margin = total_cost / (1 - target_margin/100)
        else:
            price_margin = total_cost

        # ===== วิธีที่ 2: ตั้งราคาจาก % บวกเพิ่มจากต้นทุน (markup) =====
        # ใช้ markup เท่ากับ target ที่ผู้ใช้ตั้ง เพื่อเทียบให้เห็นต่าง
        price_markup = total_cost * (1 + target_margin/100)

        # ===== วิธีที่ 3: ราคาที่นิยม (ลงท้าย 9) =====
        import math
        price_psych = math.ceil(price_margin/10)*10 - 1
        if price_psych < total_cost:
            price_psych = math.ceil(price_margin)

        def add_vat(p):
            return p * 1.07 if vat_included else p

        rows = []
        for name, p, desc in [
            ("ตั้งจากกำไร % ของราคาขาย (Margin)", price_margin, f"กำไร {target_margin}% ของราคาขาย"),
            ("ตั้งจากบวกเพิ่มจากต้นทุน (Markup)", price_markup, f"บวก {target_margin}% จากต้นทุน"),
            ("ราคาจูงใจ (ลงท้าย 9)", add_vat(price_psych)/1.07 if vat_included else price_psych, "ปัดให้ลงท้าย 9 ดึงดูดลูกค้า"),
        ]:
            final_price = add_vat(p)
            profit = final_price/(1.07 if vat_included else 1) - total_cost
            margin_pct = (profit / (final_price/(1.07 if vat_included else 1))) * 100 if final_price > 0 else 0
            rows.append({
                "วิธีตั้งราคา": name,
                "ราคาขาย (บาท)": f"{final_price:,.2f}",
                "กำไร/ชิ้น (บาท)": f"{profit:,.2f}",
                "อัตรากำไร": f"{margin_pct:.1f}%",
                "หมายเหตุ": desc,
            })

        st.divider()
        st.markdown(f"##### 📊 ราคาขายแนะนำ" + (f" — {product_name}" if product_name else ""))
        m1, m2, m3 = st.columns(3)
        m1.metric("ต้นทุนรวม/ชิ้น", f"{total_cost:,.2f}")
        m2.metric("ราคาขายแนะนำ", f"{add_vat(price_margin):,.2f}")
        m3.metric("กำไร/ชิ้น", f"{add_vat(price_margin)/(1.07 if vat_included else 1) - total_cost:,.2f}")

        st.markdown("##### 🔍 เทียบหลายวิธีตั้งราคา")
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        # จุดคุ้มทุน
        st.divider()
        st.markdown("##### 🎯 วิเคราะห์เพิ่มเติม")
        bep1, bep2 = st.columns(2)
        with bep1:
            fixed_cost = st.number_input("ค่าใช้จ่ายคงที่ต่อเดือน (ค่าเช่า/เงินเดือน)", min_value=0.0, step=500.0, format="%.2f",
                                         help="ใส่เพื่อคำนวณว่าต้องขายกี่ชิ้นถึงคุ้มทุน")
        with bep2:
            if fixed_cost > 0:
                profit_per_unit = add_vat(price_margin)/(1.07 if vat_included else 1) - total_cost
                if profit_per_unit > 0:
                    bep_units = fixed_cost / profit_per_unit
                    st.metric("ต้องขายกี่ชิ้น/เดือนถึงคุ้มทุน", f"{bep_units:,.0f} ชิ้น")
                else:
                    st.warning("กำไรต่อชิ้นเป็น 0 หรือติดลบ — ตั้งราคาใหม่")

        st.info("💡 Margin (กำไรจากราคาขาย) กับ Markup (บวกจากต้นทุน) ต่างกัน! เช่น ต้นทุน 100 บวก markup 30% = ขาย 130 แต่กำไรจริงแค่ 23% ของราคาขาย ระบบคำนวณให้เห็นชัดทั้งสองแบบ")
        st.caption("⚠️ ราคาแนะนำเป็นแนวทาง ควรพิจารณาราคาตลาดและคู่แข่งประกอบ")

# =====================================================================
#  TAB ร้านค้า/ร้านอาหาร — คำนวณภาษีเฉพาะร้านค้า (เทียบวิธีหัก + เทียบ 2 วิธีภาษี)
# =====================================================================
with tabShop:
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
        if total_revenue > 1_000_000:
            tax_method2 = total_revenue * 0.005
            method2_active = True
        else:
            tax_method2 = 0
            method2_active = False

        final_tax = max(tax_method1, tax_method2)

        cmp_tax = pd.DataFrame({
            "วิธีคำนวณภาษี": [
                "วิธีที่ 1: เงินได้สุทธิ × ขั้นบันได",
                "วิธีที่ 2: รายได้รวม × 0.5%",
            ],
            "ภาษี (บาท)": [f"{tax_method1:,.2f}", f"{tax_method2:,.2f}" if method2_active else "ไม่เข้าเงื่อนไข"],
            "หมายเหตุ": [
                f"เงินได้สุทธิ {net_income:,.0f}",
                "ใช้เมื่อรายได้เกิน 1 ล้าน/ปี" if method2_active else "รายได้ไม่ถึง 1 ล้าน",
            ],
        })
        st.dataframe(cmp_tax, use_container_width=True, hide_index=True)

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

        st.caption("⚠️ ประมาณการตามอัตราปีภาษี 2568-2569 | รายได้ต้องใช้ยอดเต็มก่อนหัก GP | ควรเก็บหลักฐานครบถ้วนหากหักตามจริง | ตรวจสอบกับกรมสรรพากรก่อนยื่นจริง")

# =====================================================================
#  TAB ปรึกษาผู้เชี่ยวชาญ — รับงานที่ปรึกษาภาษี/การเงิน
# =====================================================================
with tabConsult:
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

# =====================================================================
#  TAB 5 — คลังกฎหมายภาษี
# =====================================================================
with tab5:
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
