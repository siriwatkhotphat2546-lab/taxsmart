import io
import pandas as pd
from datetime import date

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
#  ตัวเชื่อมฟอร์มบันทึกเงิน (money.py) กับการคำนวณภาษี (tax_tab.py)
#  ใช้ภาษาชาวบ้าน + เก็บ "รหัสมาตรา" ลงคอลัมน์ income_type / non_income_type
# =====================================================================

# แหล่งที่มาเงินได้ (ภาษาชาวบ้าน) -> รหัสมาตรา ที่เก็บลง income_type เช่น "40(1)"
INCOME_SOURCE_OPTIONS = {
    "💼 เงินเดือน/โบนัส/ค่าจ้างประจำ (ม.40(1))": "40(1)",
    "🤝 รับจ้างทั่วไป/ฟรีแลนซ์ (ม.40(2))": "40(2)",
    "🏠 ค่าเช่า บ้าน/รถ/ที่ดิน (ม.40(5))": "40(5)",
    "⚕️ วิชาชีพ หมอ/ทนาย/บัญชี/วิศวกร (ม.40(6))": "40(6)",
    "🔨 รับเหมา (ม.40(7))": "40(7)",
    "🛒 ขายของ/ธุรกิจ/ขับรถ/รีวิว (ม.40(8))": "40(8)",
    "💰 ดอกเบี้ย/เงินปันผล (ม.40(4))": "40(4)",
    "❓ ไม่แน่ใจ": None,
}

# คำอธิบายสั้นๆ (tooltip) ของแต่ละแหล่งที่มาเงินได้
INCOME_SOURCE_HELP = (
    "เลือกให้ตรงกับที่มาของเงิน ระบบจะหักค่าใช้จ่ายให้อัตโนมัติตามกฎหมาย · "
    "ม.40(1) เงินเดือนประจำ · ม.40(2) รับจ้าง/ฟรีแลนซ์ · ม.40(5) ค่าเช่า · "
    "ม.40(6) วิชาชีพเฉพาะทาง · ม.40(7) รับเหมา · ม.40(8) ค้าขาย/ธุรกิจทั่วไป · "
    "ม.40(4) ดอกเบี้ย/ปันผล · ถ้าไม่แน่ใจเลือก 'ไม่แน่ใจ' แล้วมาระบุทีหลังได้"
)

# map รหัสมาตรา (เก็บใน income_type) -> key ใน INCOME_TYPES เพื่อดึงวิธีหักค่าใช้จ่าย
INCOME_CODE_MAP = {k.split()[0]: k for k in INCOME_TYPES}

# ประเภทรายจ่าย (เก็บลง non_income_type)
EXPENSE_WORK = "ทำมาหากิน"     # จ่ายเพื่อทำมาหากิน — หักภาษีได้ (ค่าใช้จ่ายตามจริง)
EXPENSE_PERSONAL = "ส่วนตัว"    # ใช้ส่วนตัว — หักไม่ได้

# ประเภทรายจ่ายเพื่อการบันทึก (radio ภาษาชาวบ้าน) -> ค่าที่เก็บ / คำอธิบาย
EXPENSE_PURPOSE_OPTIONS = {
    "💼 จ่ายเพื่อทำมาหากิน — หักภาษีได้": EXPENSE_WORK,
    "🏠 ใช้ส่วนตัว — หักภาษีไม่ได้": EXPENSE_PERSONAL,
    "🎯 ลดหย่อนภาษีได้ (ประกัน กองทุน บริจาค)": "ลดหย่อน",
}

# ประเภทลดหย่อน (เก็บลง non_income_type) -> คำอธิบายสั้นๆ (tooltip)
DEDUCTION_TYPES = {
    "ประกันชีวิต": "เบี้ยประกันชีวิตทั่วไป — ลดหย่อนได้สูงสุด 100,000 (รวมกับประกันสุขภาพ)",
    "ประกันสุขภาพ": "เบี้ยประกันสุขภาพตัวเอง — สูงสุด 25,000",
    "ประกันสุขภาพพ่อแม่": "เบี้ยประกันสุขภาพให้พ่อแม่ — สูงสุด 15,000",
    "RMF": "กองทุนรวมเพื่อการเลี้ยงชีพ — สูงสุด 30% ของเงินได้ (เพดานรวมกลุ่มเกษียณ 500,000)",
    "ThaiESG": "กองทุนไทยเพื่อความยั่งยืน — สูงสุด 300,000",
    "กองทุนสำรองเลี้ยงชีพ": "เงินสะสม PVD ที่หักจากเงินเดือน",
    "เงินบริจาค": "เงินบริจาคทั่วไป — ไม่เกิน 10% ของเงินได้หลังหักลดหย่อน",
    "เงินบริจาคการศึกษา-กีฬา": "บริจาคเพื่อการศึกษา/กีฬา/รพ.รัฐ — หักได้ 2 เท่า",
    "ดอกเบี้ยบ้าน": "ดอกเบี้ยผ่อนบ้าน/ที่อยู่อาศัย — สูงสุด 100,000",
    "ประกันสังคม": "เงินสมทบประกันสังคม — สูงสุด 9,000",
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
    story.append(Paragraph("รายงานสรุปบัญชีและภาษี — เงินไทย", title_style))
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
#  TAB ภาษีตามอาชีพ — คำนวณเฉพาะแต่ละสายอาชีพ
# =====================================================================
CAREERS = {
    "🚗 คนขับ Grab / Bolt / แท็กซี่": {
        "section": "40(8)",
        "expense": "เหมา 60% หรือ ตามจริง",
        "flat_rate": 0.60,
        "income_desc": "ค่าโดยสารทั้งหมด (ยอดเต็มก่อนหักค่า commission)",
        "warn": "⚠️ ใช้ยอดเต็มก่อน Grab หักค่า commission (ไม่ใช่ยอดที่โอนเข้าบัญชี)",
        "expenses": ["ค่าน้ำมัน/ไฟฟ้า", "ค่าผ่อนรถ/ค่าเช่ารถ", "ค่าซ่อมบำรุง", "ค่าประกันรถ", "ค่า commission ที่แอปหัก", "ค่าโทรศัพท์/เน็ต"],
        "tips": ["เก็บใบเสร็จค่าน้ำมันทุกใบ ถ้าจะหักตามจริง", "ถ้าต้นทุนจริงต่ำกว่า 60% ให้หักเหมาดีกว่า", "รายได้เกิน 60,000/ปี ต้องยื่นภาษี"],
    },
    "🍜 คนขับส่งอาหาร (LINE MAN/Foodpanda/Robinhood)": {
        "section": "40(8)",
        "expense": "เหมา 60% หรือ ตามจริง",
        "flat_rate": 0.60,
        "income_desc": "ค่ารอบ + ทิป + โบนัส (ยอดเต็มก่อนหัก)",
        "warn": "⚠️ รวมทั้งค่ารอบ ทิป และโบนัสพิเศษ ต้องใช้ยอดเต็ม",
        "expenses": ["ค่าน้ำมัน", "ค่าซ่อมมอเตอร์ไซค์/รถ", "ค่ากล่องเก็บอาหาร", "ค่าโทรศัพท์/เน็ต", "ค่าประกัน"],
        "tips": ["ทิปก็เป็นเงินได้ ต้องรวมด้วย", "หักเหมา 60% ง่ายที่สุด ไม่ต้องเก็บใบเสร็จ"],
    },
    "🛒 แม่ค้าออนไลน์ (Shopee/Lazada/TikTok)": {
        "section": "40(8)",
        "expense": "เหมา 60% หรือ ตามจริง",
        "flat_rate": 0.60,
        "income_desc": "ยอดขายเต็ม (ก่อนหักค่าธรรมเนียมแพลตฟอร์ม)",
        "warn": "⚠️ สำคัญมาก! ใช้ยอดขายเต็มก่อนแพลตฟอร์มหักค่า GP/ค่าธรรมเนียม ไม่ใช่ยอดที่โอนเข้าบัญชี",
        "expenses": ["ต้นทุนสินค้า", "ค่าธรรมเนียมแพลตฟอร์ม (GP)", "ค่าส่ง/ค่าแพ็ค", "ค่าโฆษณา (Ads)", "ค่ากล่อง/บับเบิล"],
        "tips": ["ยอดขายเกิน 1.8 ล้าน/ปี ต้องจด VAT", "ค่า Ads Facebook/TikTok หักเป็นค่าใช้จ่ายได้", "โหลดรายงานยอดขายจากแอปมาเก็บไว้"],
    },
    "🏠 ผู้ให้เช่า (ห้องเช่า/คอนโด/บ้าน)": {
        "section": "40(5)",
        "expense": "เหมา 30% (บ้าน/โรงเรือน) หรือ ตามจริง",
        "flat_rate": 0.30,
        "income_desc": "ค่าเช่าทั้งหมดที่ได้รับ",
        "warn": "⚠️ ม.40(5) หักเหมาได้แค่ 10-30% ตามประเภททรัพย์สิน (บ้าน/โรงเรือน = 30%)",
        "expenses": ["ค่าซ่อมแซม", "ค่าส่วนกลาง", "ค่าประกันอัคคีภัย", "ดอกเบี้ยเงินกู้", "ค่าเสื่อมราคา"],
        "tips": ["ผู้เช่าที่เป็นนิติบุคคลจะหัก ณ ที่จ่าย 5%", "ถ้าค่าใช้จ่ายจริงเกิน 30% ควรหักตามจริง", "เก็บสัญญาเช่าไว้เป็นหลักฐาน"],
    },
    "🎥 ยูทูบเบอร์ / ครีเอเตอร์ / อินฟลูฯ": {
        "section": "40(8)",
        "expense": "เหมา 60% หรือ ตามจริง",
        "flat_rate": 0.60,
        "income_desc": "AdSense + สปอนเซอร์ + รีวิว + ของที่ได้รับ",
        "warn": "⚠️ ของที่แบรนด์ส่งให้รีวิว ก็ถือเป็นเงินได้ (คิดตามมูลค่า)",
        "expenses": ["ค่าอุปกรณ์ถ่ายทำ", "ค่าตัดต่อ/ซอฟต์แวร์", "ค่าโปรโมท", "ค่าจ้างทีมงาน", "ค่าเน็ต/ไฟ"],
        "tips": ["รายได้จาก AdSense ต่างประเทศก็ต้องเสียภาษีไทย", "สปอนเซอร์ที่เป็นบริษัทจะหัก ณ ที่จ่าย 3%", "อุปกรณ์ราคาสูงหักค่าเสื่อมได้"],
    },
    "💼 ฟรีแลนซ์ / รับจ้างอิสระ": {
        "section": "40(2)",
        "expense": "เหมา 50% (สูงสุด 100,000)",
        "flat_rate": 0.50,
        "income_desc": "ค่าจ้าง/ค่าบริการที่ได้รับทั้งปี",
        "warn": "⚠️ ม.40(2) หักเหมาได้ 50% แต่สูงสุดไม่เกิน 100,000 บาท (ต่างจาก ม.40(8))",
        "expenses": ["(ม.40(2) หักได้เฉพาะเหมา 50% สูงสุด 100,000 — หักตามจริงไม่ได้)"],
        "tips": ["ผู้ว่าจ้างที่เป็นบริษัทจะหัก ณ ที่จ่าย 3% เก็บใบ 50 ทวิไว้", "ถ้ารายได้สูงมาก ลองพิจารณาจดทะเบียนพาณิชย์เป็น ม.40(8) แทน", "รายได้เกิน 60,000/ปี ต้องยื่นภาษี"],
    },
    "⚕️ หมอ/พยาบาล/วิชาชีพอิสระ": {
        "section": "40(6)",
        "expense": "เหมา 60% หรือ ตามจริง",
        "flat_rate": 0.60,
        "income_desc": "ค่าตรวจ/ค่ารักษา/ค่าวิชาชีพ",
        "warn": "⚠️ ม.40(6) ใช้กับวิชาชีพอิสระ (แพทย์ ทนาย วิศวกร สถาปนิก บัญชี ประณีตศิลป์)",
        "expenses": ["ค่าเช่าคลินิก", "ค่ายา/เวชภัณฑ์", "ค่าจ้างผู้ช่วย", "ค่าอุปกรณ์การแพทย์", "ค่าใบอนุญาต"],
        "tips": ["แพทย์หักเหมาได้ 60% (สูงกว่าวิชาชีพอื่นที่ได้ 30%)", "โรงพยาบาลที่จ้างจะหัก ณ ที่จ่าย 3%", "ถ้าเปิดคลินิกเอง ต้องดูเรื่อง VAT ด้วยถ้าเกิน 1.8 ล้าน"],
    },
    "🏪 พ่อค้าแม่ค้า (หน้าร้าน/ตลาด)": {
        "section": "40(8)",
        "expense": "เหมา 60% หรือ ตามจริง",
        "flat_rate": 0.60,
        "income_desc": "ยอดขายทั้งหมด (สด + โอน + คนละครึ่ง)",
        "warn": "⚠️ รวมทุกช่องทาง ทั้งเงินสด เงินโอน และโครงการรัฐ",
        "expenses": ["ต้นทุนสินค้า/วัตถุดิบ", "ค่าเช่าแผง/ร้าน", "ค่าจ้างลูกจ้าง", "ค่าน้ำ/ไฟ", "ค่าขนส่ง"],
        "tips": ["ใช้บัญชีธนาคารแยกสำหรับร้าน จะง่ายตอนสรุปยอด", "ดูรายละเอียดเพิ่มที่แท็บ 🏪 ธุรกิจ"],
    },
    "👨‍💼 พนักงานเอกชน (เงินเดือน)": {
        "section": "40(1)",
        "expense": "เหมา 50% (สูงสุด 100,000)",
        "flat_rate": 0.50,
        "income_desc": "เงินเดือน + โบนัส + ค่าล่วงเวลา + สวัสดิการที่เป็นเงิน",
        "warn": "⚠️ เงินเดือนหักเหมา 50% แต่สูงสุดไม่เกิน 100,000 บาท",
        "expenses": ["(เงินเดือนหักได้เฉพาะเหมา 50% สูงสุด 100,000)"],
        "tips": ["บริษัทหัก ณ ที่จ่ายให้แล้ว ขอใบ 50 ทวิมาเก็บไว้", "ยื่นแบบ ภ.ง.ด.91 (ถ้ามีแค่เงินเดือน)", "ประกันสังคมลดหย่อนได้สูงสุด 9,000"],
    },
    "🎓 ข้าราชการ / ครู / อาจารย์": {
        "section": "40(1)",
        "expense": "เหมา 50% (สูงสุด 100,000)",
        "flat_rate": 0.50,
        "income_desc": "เงินเดือน + เงินประจำตำแหน่ง + ค่าตอบแทนพิเศษ",
        "warn": "⚠️ รายได้จากการสอนพิเศษ/วิทยากร เป็น ม.40(2) แยกต่างหาก",
        "expenses": ["(เงินเดือนหักได้เฉพาะเหมา 50% สูงสุด 100,000)"],
        "tips": ["กบข. ลดหย่อนได้ (รวมเพดานเกษียณ 500,000)", "กองทุนสงเคราะห์ครูเอกชน ลดหย่อนได้", "ค่าสอนพิเศษต้องแยกยื่นเป็น ม.40(2)"],
    },
    "🎓 นักเรียน / นักศึกษา (มีรายได้)": {
        "section": "40(2) หรือ 40(8)",
        "expense": "ขึ้นกับประเภทงาน",
        "flat_rate": 0.50,
        "income_desc": "รายได้จากงานพาร์ทไทม์ / ขายของ / รับจ้าง",
        "warn": "⚠️ แม้เป็นนักศึกษา ถ้ามีรายได้เกินเกณฑ์ก็ต้องยื่นภาษี",
        "expenses": ["ขึ้นกับประเภทงาน (ดูตามอาชีพที่ทำ)"],
        "tips": ["รายได้ไม่เกิน 60,000/ปี (อาชีพอิสระ) ยังไม่ต้องยื่น", "รายได้จากเงินเดือนไม่เกิน 120,000/ปี ยังไม่ต้องยื่น", "ยื่นภาษีไว้ดี ถ้าถูกหัก ณ ที่จ่าย จะขอคืนได้"],
    },
    "🌾 เกษตรกร": {
        "section": "40(8)",
        "expense": "เหมา 60% หรือ ตามจริง",
        "flat_rate": 0.60,
        "income_desc": "รายได้จากการขายผลผลิต",
        "warn": "⚠️ เกษตรกรบางประเภทได้รับยกเว้นภาษี ตรวจสอบกับสรรพากร",
        "expenses": ["ค่าเมล็ดพันธุ์/ปุ๋ย", "ค่ายาฆ่าแมลง", "ค่าน้ำมัน/เครื่องจักร", "ค่าจ้างแรงงาน", "ค่าเช่าที่ดิน"],
        "tips": ["การขายพืชผลบางชนิดได้รับยกเว้น VAT", "เก็บใบเสร็จค่าปุ๋ย/เมล็ดพันธุ์ไว้", "รายได้จากการขายที่ดินเป็นคนละเรื่อง"],
    },
}

