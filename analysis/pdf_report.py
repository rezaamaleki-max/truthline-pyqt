"""
گزارش PDF چندصفحه‌ای — Truthline
====================================
نسخه: 2.1.0 — رفع خطاهای Pylance (typing & possibly-unbound)
"""
import os
import json
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable, cast


# ============================================================
# ✅ Persian text shaping — با fallback امن
# ============================================================
_arabic_reshape_fn: Optional[Callable[[str], str]] = None
_bidi_get_display_fn: Optional[Callable[[str], str]] = None

try:
    import arabic_reshaper as _ar  # type: ignore
    from bidi.algorithm import get_display as _gd  # type: ignore

    def _wrap_reshape(text: str) -> str:
        return str(_ar.reshape(text))

    def _wrap_bidi(text: str) -> str:
        # get_display می‌تواند str یا bytes برگرداند — صریحاً str می‌کنیم
        return str(_gd(text))

    _arabic_reshape_fn = _wrap_reshape
    _bidi_get_display_fn = _wrap_bidi
except Exception as _e:
    print(f"⚠️ کتابخانه‌ی RTL در دسترس نیست: {_e}")


# ============================================================
# ✅ PDF imports
# ============================================================
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing, String
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie

from config import DB_PATH, ASSETS_DIR


# ============================================================
# ابزارهای متن فارسی
# ============================================================
def _fa(text: Optional[str]) -> str:
    """شکل‌دهی و RTL کردن متن فارسی — همیشه str برمی‌گرداند."""
    if not text:
        return ""
    s = str(text)
    if _arabic_reshape_fn is None or _bidi_get_display_fn is None:
        return s
    try:
        reshaped = _arabic_reshape_fn(s)
        return _bidi_get_display_fn(reshaped)
    except Exception:
        return s


# ============================================================
# فونت
# ============================================================
_FONT_REGISTERED: bool = False
_FONT_NAME: str = "Helvetica"


def _register_font() -> str:
    global _FONT_REGISTERED, _FONT_NAME
    if _FONT_REGISTERED:
        return _FONT_NAME

    candidates = [
        os.path.join(ASSETS_DIR, "fonts", "Vazirmatn-Regular.ttf"),
        os.path.join(ASSETS_DIR, "fonts", "Vazirmatn-Medium.ttf"),
        os.path.join(ASSETS_DIR, "fonts", "Vazir.ttf"),
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont("Vazir", path))
                _FONT_NAME = "Vazir"
                _FONT_REGISTERED = True
                print(f"✓ فونت گزارش PDF ثبت شد: {path}")
                return _FONT_NAME
            except Exception as e:
                print(f"⚠️ خطا در ثبت فونت {path}: {e}")

    print("⚠️ فونت فارسی یافت نشد — از Helvetica استفاده می‌شود")
    _FONT_REGISTERED = True
    return _FONT_NAME


# ============================================================
# استایل‌ها
# ============================================================
def _build_styles() -> Dict[str, ParagraphStyle]:
    font = _register_font()
    ss = getSampleStyleSheet()

    styles: Dict[str, ParagraphStyle] = {
        "title": ParagraphStyle(
            "Title", parent=ss["Title"],
            fontName=font, fontSize=22, leading=28,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#0B1D3A"),
            spaceAfter=20,
        ),
        "h1": ParagraphStyle(
            "H1", parent=ss["Heading1"],
            fontName=font, fontSize=16, leading=22,
            alignment=TA_RIGHT,
            textColor=colors.HexColor("#0B1D3A"),
            spaceBefore=12, spaceAfter=8,
        ),
        "h2": ParagraphStyle(
            "H2", parent=ss["Heading2"],
            fontName=font, fontSize=13, leading=18,
            alignment=TA_RIGHT,
            textColor=colors.HexColor("#2B4A6F"),
            spaceBefore=8, spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "Body", parent=ss["BodyText"],
            fontName=font, fontSize=11, leading=17,
            alignment=TA_RIGHT,
            textColor=colors.HexColor("#212121"),
        ),
        "small": ParagraphStyle(
            "Small", parent=ss["BodyText"],
            fontName=font, fontSize=9, leading=13,
            alignment=TA_RIGHT,
            textColor=colors.HexColor("#555555"),
        ),
        "center": ParagraphStyle(
            "Center", parent=ss["BodyText"],
            fontName=font, fontSize=11, leading=16,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#212121"),
        ),
    }
    return styles


# ============================================================
# داده‌کاوی
# ============================================================
def _fetch_all(cur, query: str, params: tuple = ()) -> List[Any]:
    try:
        cur.execute(query, params)
        return cur.fetchall()
    except Exception as e:
        print(f"⚠️ خطا در اجرای کوئری: {e}")
        return []


def _gather_participant_data(participant_id: str) -> Dict[str, Any]:
    """جمع‌آوری همه‌ی داده‌های شرکت‌کننده به‌صورت dict[str, Any]"""
    data: Dict[str, Any] = {
        "participant_id": participant_id,
        "participant": {},
        "competency_scores": [],
        "sub_scores": [],
        "schema_dist": {},
        "schema_list": [],
        "evidence_raw": [],
        "hexaco": {},
        "extended": {},
        "postgame": {},
        "letters": [],
    }

    if not os.path.exists(DB_PATH):
        return data

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # participants
    rows = _fetch_all(
        cur,
        "SELECT * FROM participants WHERE participant_id = ?",
        (participant_id,),
    )
    if rows:
        data["participant"] = dict(rows[0])

    # competency_scores
    rows = _fetch_all(
        cur,
        "SELECT competency, score, confidence, evidence_count "
        "FROM competency_scores WHERE participant_id = ?",
        (participant_id,),
    )
    data["competency_scores"] = [dict(r) for r in rows]

    # sub_competency_scores
    rows = _fetch_all(
        cur,
        "SELECT competency, sub_competency, score, evidence_count "
        "FROM sub_competency_scores WHERE participant_id = ? "
        "ORDER BY competency, score DESC",
        (participant_id,),
    )
    data["sub_scores"] = [dict(r) for r in rows]

    # schema distribution
    rows = _fetch_all(
        cur,
        "SELECT schema_primary, COUNT(*) as cnt "
        "FROM schema_evidence WHERE participant_id = ? "
        "GROUP BY schema_primary",
        (participant_id,),
    )
    schema_dist = {
        "personal_interest": 0,
        "maintaining_norms": 0,
        "postconventional": 0,
    }
    for r in rows:
        key = r["schema_primary"]
        if key in schema_dist:
            schema_dist[key] = r["cnt"]
    data["schema_dist"] = schema_dist

    # schema list
    rows = _fetch_all(
        cur,
        "SELECT scenario_id, choice_id, schema_primary, schema_secondary "
        "FROM schema_evidence WHERE participant_id = ? ORDER BY created_at",
        (participant_id,),
    )
    data["schema_list"] = [dict(r) for r in rows]

    # evidence raw
    rows = _fetch_all(
        cur,
        "SELECT scenario_id, competency, evidence_key, "
        "evidence_value, weight FROM evidence "
        "WHERE participant_id = ? ORDER BY evidence_id",
        (participant_id,),
    )
    data["evidence_raw"] = [dict(r) for r in rows]

    # hexaco
    rows = _fetch_all(
        cur,
        "SELECT hexaco_scores FROM participants WHERE participant_id = ?",
        (participant_id,),
    )
    if rows and rows[0]["hexaco_scores"]:
        try:
            data["hexaco"] = json.loads(rows[0]["hexaco_scores"])
        except Exception:
            data["hexaco"] = {}

    # extended
    rows = _fetch_all(
        cur,
        "SELECT crt_data, sd3_scores, social_desirability "
        "FROM extended_questionnaires WHERE participant_id = ?",
        (participant_id,),
    )
    data["extended"] = dict(rows[0]) if rows else {}

    # postgame
    rows = _fetch_all(
        cur,
        "SELECT * FROM postgame_feedback WHERE participant_id = ?",
        (participant_id,),
    )
    data["postgame"] = dict(rows[0]) if rows else {}

    # letters
    rows = _fetch_all(
        cur,
        "SELECT content, word_count FROM self_letters "
        "WHERE participant_id = ? ORDER BY letter_id",
        (participant_id,),
    )
    data["letters"] = [dict(r) for r in rows]

    conn.close()
    return data


# ============================================================
# کمک‌کننده‌ها
# ============================================================
def _score_level(score: float) -> str:
    if score >= 85:
        return "بسیار خوب"
    if score >= 70:
        return "خوب"
    if score >= 50:
        return "متوسط"
    return "نیاز به توسعه"


def _compute_typology(data: Dict[str, Any]) -> str:
    scores: Dict[str, float] = {
        str(r["competency"]): float(r["score"])
        for r in data.get("competency_scores", [])
    }
    if not scores:
        return "داده‌ی کافی برای تعیین تایپولوژی وجود ندارد."

    high: List[str] = [k for k, v in scores.items() if v >= 75]
    low: List[str] = [k for k, v in scores.items() if v < 50]

    fa_map: Dict[str, str] = {
        "honesty": "صداقت",
        "trustworthiness": "قابلیت اعتماد",
        "problem_solving": "حل مسئله",
        "accountability": "مسئولیت‌پذیری",
    }

    parts: List[str] = []

    if high:
        # ✅ صریحاً str بساز تا Pylance راضی شود
        high_names: List[str] = [str(fa_map.get(k, k)) for k in high]
        parts.append("نقاط قوت: " + "، ".join(high_names))

    if low:
        low_names: List[str] = [str(fa_map.get(k, k)) for k in low]
        parts.append("نقاط قابل بهبود: " + "، ".join(low_names))

    if not parts:
        parts.append("پروفایل متعادل در همه‌ی شایستگی‌ها")

    return " | ".join(parts)


# ============================================================
# نمودارها
# ============================================================
def _competency_bar_chart(comp_scores: List[Dict[str, Any]]) -> Drawing:
    fa_map = {
        "honesty": "صداقت",
        "trustworthiness": "اعتماد",
        "problem_solving": "حل مسئله",
        "accountability": "مسئولیت",
    }
    order = [
        "honesty", "trustworthiness",
        "problem_solving", "accountability",
    ]
    by_key = {r["competency"]: r["score"] for r in comp_scores}
    values = [by_key.get(k, 0) for k in order]
    labels = [fa_map.get(k, k) for k in order]

    d = Drawing(400, 180)
    chart = VerticalBarChart()
    chart.x = 30
    chart.y = 25
    chart.height = 130
    chart.width = 340
    chart.data = [values]
    chart.valueAxis.valueMin = 0
    chart.valueAxis.valueMax = 100
    chart.valueAxis.valueStep = 25
    chart.categoryAxis.categoryNames = [_fa(x) for x in labels]
    chart.categoryAxis.labels.fontName = _register_font()
    chart.categoryAxis.labels.fontSize = 9
    chart.valueAxis.labels.fontName = _register_font()
    chart.valueAxis.labels.fontSize = 8
    chart.bars[0].fillColor = colors.HexColor("#4FC3F7")
    chart.bars[0].strokeColor = colors.HexColor("#0B1D3A")
    d.add(chart)
    return d


def _schema_pie_chart(schema_dist: Dict[str, int]) -> Drawing:
    pi = schema_dist.get("personal_interest", 0)
    mn = schema_dist.get("maintaining_norms", 0)
    pc = schema_dist.get("postconventional", 0)
    total = pi + mn + pc

    d = Drawing(300, 200)
    if total == 0:
        d.add(String(
            100, 100,
            _fa("داده‌ای موجود نیست"),
            fontName=_register_font(),
            fontSize=10,
        ))
        return d

    pie = Pie()
    pie.x = 60
    pie.y = 20
    pie.width = 160
    pie.height = 160
    pie.data = [pi, mn, pc]
    pie.labels = [
        _fa(f"منفعت‌شخصی {pi}"),
        _fa(f"هنجار {mn}"),
        _fa(f"پساعرفی {pc}"),
    ]
    pie.slices.strokeWidth = 1
    pie.slices[0].fillColor = colors.HexColor("#D32F2F")
    pie.slices[1].fillColor = colors.HexColor("#FF8F00")
    pie.slices[2].fillColor = colors.HexColor("#4CAF50")
    pie.slices.fontName = _register_font()
    pie.slices.fontSize = 8
    d.add(pie)
    return d


# ============================================================
# جدول‌ها
# ============================================================
def _competency_table(
    comp_scores: List[Dict[str, Any]]
) -> Table:
    header = [
        _fa("شایستگی"), _fa("نمره"), _fa("سطح"),
        _fa("اعتماد"), _fa("تعداد شواهد"),
    ]
    fa_map = {
        "honesty": "صداقت",
        "trustworthiness": "قابلیت اعتماد",
        "problem_solving": "حل مسئله",
        "accountability": "مسئولیت‌پذیری",
    }
    rows: List[List[str]] = [header]
    for r in sorted(comp_scores, key=lambda x: -x["score"]):
        rows.append([
            _fa(fa_map.get(r["competency"], r["competency"])),
            f"{r['score']:.1f}",
            _fa(_score_level(r["score"])),
            f"{r['confidence']:.2f}",
            str(r["evidence_count"]),
        ])

    t = Table(rows, colWidths=[4*cm, 2*cm, 3*cm, 2.2*cm, 2.5*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0B1D3A")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTNAME", (0, 0), (-1, -1), _register_font()),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#F2F7FA")]),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def _sub_competency_table(
    sub_scores: List[Dict[str, Any]]
) -> Table:
    header = [
        _fa("شایستگی"), _fa("زیرمؤلفه"), _fa("نمره"), _fa("تعداد")
    ]
    rows: List[List[str]] = [header]
    for r in sub_scores[:30]:
        rows.append([
            _fa(r["competency"]),
            _fa(r["sub_competency"]),
            f"{r['score']:.1f}",
            str(r["evidence_count"]),
        ])
    t = Table(rows, colWidths=[3.5*cm, 5.5*cm, 2.2*cm, 2*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2B4A6F")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, -1), _register_font()),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#F7F7F7")]),
    ]))
    return t


def _schema_table(schema_list: List[Dict[str, Any]]) -> Table:
    header = [
        _fa("سناریو"), _fa("گزینه"),
        _fa("طرح‌واره اصلی"), _fa("طرح‌واره فرعی"),
    ]
    rows: List[List[str]] = [header]
    fa_schema = {
        "personal_interest": "منفعت شخصی",
        "maintaining_norms": "حفظ هنجارها",
        "postconventional": "پساعرفی",
    }
    for r in schema_list:
        primary = r.get("schema_primary") or ""
        secondary = r.get("schema_secondary") or ""
        rows.append([
            str(r.get("scenario_id", "")),
            str(r.get("choice_id", "")),
            _fa(fa_schema.get(primary, primary)),
            _fa(fa_schema.get(secondary, "")) if secondary else "-",
        ])
    t = Table(rows, colWidths=[3*cm, 2*cm, 4.5*cm, 4.5*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4A148C")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, -1), _register_font()),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#F3E5F5")]),
    ]))
    return t


def _hexaco_table(hexaco: Dict[str, Any]) -> Optional[Table]:
    """اگر HEXACO داده باشد Table برمی‌گرداند، وگرنه None."""
    if not hexaco:
        return None

    fa_map = {
        "score_H": "صداقت-فروتنی",
        "score_E": "هیجان‌خواهی",
        "score_X": "برون‌گرایی",
        "score_A": "توافق‌پذیری",
        "score_C": "وجدان‌گرایی",
        "score_O": "تجربه‌پذیری",
    }
    rows: List[List[str]] = [[_fa("عامل"), _fa("نمره (۱ تا ۵)")]]
    for k, label in fa_map.items():
        v = hexaco.get(k)
        if v is not None:
            rows.append([_fa(label), f"{float(v):.2f}"])

    if len(rows) == 1:
        return None

    t = Table(rows, colWidths=[5*cm, 4*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#00838F")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, -1), _register_font()),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
    ]))
    return t


# ============================================================
# سربرگ/پاصفحه
# ============================================================
def _on_page(canvas, doc):
    canvas.saveState()
    canvas.setFont(_register_font(), 8)
    canvas.setFillColor(colors.HexColor("#555555"))
    canvas.drawString(
        1.5*cm, 1.2*cm,
        _fa(f"Truthline Report — {datetime.now().strftime('%Y-%m-%d')}"),
    )
    canvas.drawRightString(
        A4[0] - 1.5*cm, 1.2*cm,
        _fa(f"صفحه {doc.page}"),
    )
    canvas.setStrokeColor(colors.HexColor("#CFD8DC"))
    canvas.line(1.5*cm, 1.6*cm, A4[0] - 1.5*cm, 1.6*cm)
    canvas.restoreState()


# ============================================================
# API اصلی
# ============================================================
def generate_pdf_report(
    participant_id: str,
    output_path: Optional[str] = None,
) -> Optional[str]:
    """تولید گزارش PDF کامل."""
    data = _gather_participant_data(participant_id)
    if not data:
        print(f"❌ داده‌ای برای {participant_id} یافت نشد")
        return None

    # ✅ تعیین مسیر خروجی
    final_output: str
    if output_path is None:
        reports_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "reports",
        )
        os.makedirs(reports_dir, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        final_output = os.path.join(
            reports_dir, f"{participant_id}_report_{ts}.pdf"
        )
    else:
        final_output = output_path
        parent = os.path.dirname(final_output)
        if parent:
            os.makedirs(parent, exist_ok=True)

    styles = _build_styles()

    doc = SimpleDocTemplate(
        final_output,
        pagesize=A4,
        rightMargin=1.5*cm, leftMargin=1.5*cm,
        topMargin=2*cm, bottomMargin=2*cm,
        title=f"Truthline Report — {participant_id}",
        author="Truthline Assessment",
    )

    story: List[Any] = []

    # ------- صفحه ۱ — جلد -------
    story.append(Spacer(1, 3*cm))
    story.append(Paragraph(
        _fa("گزارش ارزیابی شایستگی‌ها"), styles["title"]
    ))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph(
        _fa("Truthline: Crisis at Caspian Station"), styles["center"]
    ))
    story.append(Spacer(1, 3*cm))

    meta_rows: List[List[str]] = [
        [_fa("شناسه‌ی شرکت‌کننده"), participant_id],
        [_fa("تاریخ گزارش"), _fa(datetime.now().strftime("%Y-%m-%d %H:%M"))],
    ]
    p = data.get("participant", {})
    if p.get("created_at"):
        meta_rows.append([
            _fa("تاریخ شروع"), str(p["created_at"])[:19]
        ])

    meta_table = Table(meta_rows, colWidths=[5*cm, 7*cm])
    meta_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), _register_font()),
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F2F7FA")),
    ]))
    story.append(meta_table)
    story.append(PageBreak())

    # ------- صفحه ۲ — خلاصه‌ی اجرایی -------
    story.append(Paragraph(_fa("خلاصه‌ی اجرایی"), styles["h1"]))
    story.append(Spacer(1, 0.3*cm))

    comp_scores = data.get("competency_scores", [])
    if comp_scores:
        story.append(_competency_table(comp_scores))
        story.append(Spacer(1, 0.4*cm))
        story.append(_competency_bar_chart(comp_scores))
        story.append(Spacer(1, 0.4*cm))
        story.append(Paragraph(_fa("پروفایل کلی"), styles["h2"]))
        story.append(Paragraph(
            _fa(_compute_typology(data)), styles["body"]
        ))
    else:
        story.append(Paragraph(
            _fa("نمرات شایستگی ثبت نشده است."), styles["body"]
        ))
    story.append(PageBreak())

    # ------- صفحه ۳ — زیرمؤلفه‌ای -------
    sub_scores = data.get("sub_scores", [])
    if sub_scores:
        story.append(Paragraph(
            _fa("نمرات زیرمؤلفه‌ای"), styles["h1"]
        ))
        story.append(Spacer(1, 0.3*cm))
        story.append(Paragraph(
            _fa("نمرات تفصیلی بر اساس شواهد رفتاری در هر زیرمؤلفه."),
            styles["small"],
        ))
        story.append(Spacer(1, 0.3*cm))
        story.append(_sub_competency_table(sub_scores))
        story.append(PageBreak())

    # ------- صفحه ۴ — طرح‌واره‌ها -------
    schema_dist = data.get("schema_dist", {})
    story.append(Paragraph(
        _fa("طرح‌واره‌های استدلال اخلاقی (کلبرگ)"), styles["h1"]
    ))
    story.append(Spacer(1, 0.3*cm))

    total_schema = sum(schema_dist.values()) if schema_dist else 0
    if total_schema > 0:
        story.append(Paragraph(
            _fa(f"تعداد کل تصمیم‌های ثبت‌شده: {total_schema}"),
            styles["body"],
        ))
        story.append(Spacer(1, 0.3*cm))
        story.append(_schema_pie_chart(schema_dist))
        story.append(Spacer(1, 0.5*cm))
        story.append(Paragraph(
            _fa("جزئیات طرح‌واره‌ها"), styles["h2"]
        ))
        story.append(_schema_table(data.get("schema_list", [])))
    else:
        story.append(Paragraph(
            _fa("طرح‌واره‌ای ثبت نشده است."), styles["body"]
        ))
    story.append(PageBreak())

    # ------- صفحه ۵ — HEXACO -------
    hexaco = data.get("hexaco", {})
    ht = _hexaco_table(hexaco)
    if ht is not None:
        story.append(Paragraph(
            _fa("پرسشنامه‌ی HEXACO-24"), styles["h1"]
        ))
        story.append(Spacer(1, 0.3*cm))
        story.append(ht)
        story.append(PageBreak())

    # ------- صفحه ۶ — پرسشنامه‌های تکمیلی -------
    ext = data.get("extended", {})
    if ext:
        story.append(Paragraph(
            _fa("پرسشنامه‌های تکمیلی"), styles["h1"]
        ))
        story.append(Spacer(1, 0.3*cm))
        for key, label in [
            ("crt_data", "CRT7 — تأمل شناختی"),
            ("sd3_scores", "SD3 — مثلث تاریک"),
            ("social_desirability", "SD — مطلوبیت اجتماعی"),
        ]:
            raw = ext.get(key)
            if not raw:
                continue
            story.append(Paragraph(_fa(label), styles["h2"]))
            try:
                parsed = json.loads(raw) if isinstance(raw, str) else raw
                pretty = json.dumps(parsed, ensure_ascii=False, indent=2)
            except Exception:
                pretty = str(raw)
            story.append(Paragraph(
                _fa(pretty[:600]), styles["small"]
            ))
            story.append(Spacer(1, 0.2*cm))
        story.append(PageBreak())

    # ------- صفحه ۷ — نامه به خود -------
    letters = data.get("letters", [])
    if letters:
        story.append(Paragraph(_fa("نامه به خود"), styles["h1"]))
        story.append(Spacer(1, 0.3*cm))
        for i, letter in enumerate(letters, 1):
            story.append(Paragraph(
                _fa(
                    f"نامه‌ی {i} "
                    f"({letter.get('word_count', 0)} کلمه)"
                ),
                styles["h2"],
            ))
            content = (letter.get("content") or "").strip()
            if content:
                story.append(Paragraph(
                    _fa(content[:1500]), styles["body"]
                ))
            else:
                story.append(Paragraph(
                    _fa("(بازیکن از نوشتن نامه صرف‌نظر کرده)"),
                    styles["small"],
                ))
            story.append(Spacer(1, 0.3*cm))
        story.append(PageBreak())

    # ------- صفحه ۸ — شواهد خام -------
    ev = data.get("evidence_raw", [])
    if ev:
        story.append(Paragraph(
            _fa("فهرست شواهد خام"), styles["h1"]
        ))
        story.append(Spacer(1, 0.3*cm))
        story.append(Paragraph(
            _fa(f"تعداد کل شواهد: {len(ev)}"), styles["small"]
        ))
        story.append(Spacer(1, 0.2*cm))

        header = [
            _fa("سناریو"), _fa("شایستگی"), _fa("کلید شاهد"),
            _fa("مقدار"), _fa("وزن"),
        ]
        rows: List[List[str]] = [header]
        for r in ev[:40]:
            key = str(r.get("evidence_key", ""))[:35]
            rows.append([
                str(r.get("scenario_id", "")),
                _fa(r.get("competency", "")),
                _fa(key),
                f"{float(r.get('evidence_value', 0)):.2f}",
                f"{float(r.get('weight', 1.0)):.2f}",
            ])
        t = Table(
            rows, colWidths=[2.2*cm, 2.5*cm, 6*cm, 1.8*cm, 1.5*cm]
        )
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0),
             colors.HexColor("#0B1D3A")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, -1), _register_font()),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.white, colors.HexColor("#F2F7FA")]),
        ]))
        story.append(t)

    # ------- ساخت -------
    try:
        doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
        print(f"✓ گزارش PDF ساخته شد: {final_output}")
        return final_output
    except Exception as e:
        print(f"❌ خطا در ساخت PDF: {e}")
        import traceback
        traceback.print_exc()
        return None


# ✅ ============================================================
# ✅ Wrapper سازگار با فراخوانی قدیمی (results_scene.py)
# ============================================================
def generate_report(
    participant_id: str,
    output_dir: Optional[str] = None,
) -> bool:
    """
    نسخه‌ی سازگار با فراخوانی قبلی که فقط bool برمی‌گرداند.

    Args:
        participant_id: شناسه‌ی شرکت‌کننده
        output_dir: پوشه‌ی خروجی (پیش‌فرض: reports/)

    Returns:
        True اگر موفق، False اگر ناموفق
    """
    try:
        # ✅ تعیین مسیر خروجی
        if output_dir is None:
            output_dir = os.path.join(
                os.path.dirname(
                    os.path.dirname(os.path.abspath(__file__))
                ),
                "reports",
            )
        os.makedirs(output_dir, exist_ok=True)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = os.path.join(
            output_dir, f"{participant_id}_report_{ts}.pdf"
        )

        result = generate_pdf_report(participant_id, out_path)
        return result is not None
    except Exception as e:
        print(f"❌ خطا در generate_report: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================================
# CLI
# ============================================================
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("استفاده: python -m analysis.pdf_report <participant_id> [output.pdf]")
        sys.exit(1)
    pid = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else None
    result = generate_pdf_report(pid, out)
    if result:
        print(f"OK: {result}")