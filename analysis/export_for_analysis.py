"""
تحلیل‌گر نهایی برای SPSS / R / Excel
====================================

این اسکریپت داده‌های خام بازی را از پایگاه داده می‌خواند و
آن‌ها را به فرمت‌های آماده‌ی تحلیل صادر می‌کند.

نحوه استفاده:
    python analysis/export_for_analysis.py

خروجی‌ها در پوشه‌ی analysis_output/ ذخیره می‌شوند.
"""
import os
import sys
import json
import sqlite3
from datetime import datetime

import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from config import DB_PATH
except ImportError:
    # fallback اگر config در دسترس نبود
    DB_PATH = os.path.join(PROJECT_ROOT, "data", "participants.db")

OUTPUT_DIR = os.path.join(PROJECT_ROOT, "analysis_output")


# ============================================================
# ابزار کمکی
# ============================================================
def _parse_json(value) -> dict:
    """تبدیل رشته‌ی JSON به دیکشنری"""
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    try:
        return json.loads(value)
    except Exception:
        return {}


def _ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# خواندن از دیتابیس
# ============================================================
def _read_participants(conn: sqlite3.Connection) -> pd.DataFrame:
    query = """
        SELECT participant_id,
               session_start,
               session_end,
               demographic_data,
               hexaco_scores,
               created_at,
               random_seed
        FROM participants
        WHERE participant_id NOT LIKE 'THEATER_%'
        ORDER BY session_start
    """
    return pd.read_sql_query(query, conn)


def _read_competency_scores(conn: sqlite3.Connection) -> pd.DataFrame:
    query = """
        SELECT participant_id, competency, score, confidence,
               evidence_count
        FROM competency_scores
        WHERE participant_id NOT LIKE 'THEATER_%'
    """
    return pd.read_sql_query(query, conn)


def _read_evidence(conn: sqlite3.Connection) -> pd.DataFrame:
    query = """
        SELECT evidence_id, participant_id, scenario_id, competency,
               subcomponent, evidence_key, evidence_value, weight
        FROM evidence
        WHERE participant_id NOT LIKE 'THEATER_%'
        ORDER BY participant_id, evidence_id
    """
    return pd.read_sql_query(query, conn)


def _read_events(conn: sqlite3.Connection) -> pd.DataFrame:
    query = """
        SELECT event_id, participant_id, scene_id, scenario_id,
               event_type, timestamp, reaction_time_ms, metadata
        FROM events
        WHERE participant_id NOT LIKE 'THEATER_%'
        ORDER BY participant_id, event_id
    """
    return pd.read_sql_query(query, conn)


def _read_self_letters(conn: sqlite3.Connection) -> pd.DataFrame:
    try:
        query = """
            SELECT letter_id, participant_id, content, word_count,
                   created_at
            FROM self_letters
            WHERE participant_id NOT LIKE 'THEATER_%'
            ORDER BY participant_id, letter_id
        """
        return pd.read_sql_query(query, conn)
    except sqlite3.OperationalError:
        # اگر جدول هنوز ساخته نشده باشد
        return pd.DataFrame(
            columns=["letter_id", "participant_id", "content",
                     "word_count", "created_at"]
        )


# ============================================================
# ساخت جدول خلاصه (wide format)
# ============================================================
COMPETENCY_CODES = [
    "honesty",
    "trustworthiness",
    "problem_solving",
    "accountability",
]

DEMO_FIELDS = [
    "age", "gender", "education", "field_of_study",
    "work_experience", "gaming_experience", "technical_familiarity",
    "consent",
]

HEXACO_CODES = ["H", "E", "X", "A", "C", "O"]


def build_summary(
    participants: pd.DataFrame,
    scores: pd.DataFrame,
) -> pd.DataFrame:
    """ساخت یک ردیف per participant"""
    rows: list = []

    for _, p in participants.iterrows():
        pid = p["participant_id"]
        row: dict = {"participant_id": pid}

        # ---------------- زمان جلسه ----------------
        ss = p.get("session_start")
        se = p.get("session_end")
        row["session_start"] = (
            datetime.fromtimestamp(ss).isoformat()
            if pd.notna(ss) else None
        )
        row["session_end"] = (
            datetime.fromtimestamp(se).isoformat()
            if pd.notna(se) else None
        )
        if pd.notna(ss) and pd.notna(se) and se > ss:
            row["session_duration_min"] = round((se - ss) / 60, 2)
        else:
            row["session_duration_min"] = 0

        row["random_seed"] = p.get("random_seed")

        # ---------------- دموگرافیک ----------------
        demo = _parse_json(p.get("demographic_data"))
        for field in DEMO_FIELDS:
            row[f"demo_{field}"] = demo.get(field)

        # ---------------- HEXACO ----------------
        hexaco = _parse_json(p.get("hexaco_scores"))
        for code in HEXACO_CODES:
            row[f"hexaco_{code}"] = hexaco.get(f"score_{code}")

        # ---------------- نمرات شایستگی ----------------
        p_scores = scores[scores["participant_id"] == pid]
        for comp in COMPETENCY_CODES:
            comp_row = p_scores[p_scores["competency"] == comp]
            if len(comp_row) > 0:
                row[f"score_{comp}"] = float(comp_row.iloc[0]["score"])
                row[f"conf_{comp}"] = float(
                    comp_row.iloc[0]["confidence"]
                )
                row[f"count_{comp}"] = int(
                    comp_row.iloc[0]["evidence_count"]
                )
            else:
                row[f"score_{comp}"] = None
                row[f"conf_{comp}"] = None
                row[f"count_{comp}"] = 0

        # ---------------- نمره‌ی کل ----------------
        score_values = [
            row.get(f"score_{c}") for c in COMPETENCY_CODES
        ]
        valid = [v for v in score_values if v is not None]
        row["score_mean_all"] = (
            round(sum(valid) / len(valid), 2) if valid else None
        )

        # ---------------- همگرایی با HEXACO ----------------
        # همبستگی ساده بین honesty و HEXACO_H (اگر هر دو موجود)
        hex_h = hexaco.get("score_H")
        honesty_score = row.get("score_honesty")
        if hex_h is not None and honesty_score is not None:
            row["alignment_H_honesty"] = round(
                abs(hex_h / 5.0 - honesty_score / 100.0), 3
            )
        else:
            row["alignment_H_honesty"] = None

        rows.append(row)

    return pd.DataFrame(rows)


# ============================================================
# افزودن ستون‌های استخراجی به evidence_long
# ============================================================
PHASE_MAP = {
    "VH-01": 1, "DA-01": 1, "DA-02": 1, "MC-01": 1,
    "VH-02": 1, "F-02": 1,
    "CF-01": 2, "TR-01": 2, "TR-02": 2, "BC-01": 2,
    "BC-02": 2, "CF-02": 2,
    "PID-01": 3, "MC-02": 3, "PID-02": 3, "SPA-01": 3,
    "CFI-01": 3, "MR-01": 3, "SPA-02": 3, "MR-02": 3,
    "PI-01": 4, "TC-01": 4, "TC-02": 4, "PI-02": 4,
    "RG-01": 4, "RG-02": 4, "AC-02": 4, "AC-01": 4,
    "CO-computed": 0,
}


def enrich_evidence(evidence: pd.DataFrame) -> pd.DataFrame:
    """افزودن ستون‌های phase و weighted_value"""
    if evidence.empty:
        return evidence
    evidence = evidence.copy()
    evidence["phase"] = evidence["scenario_id"].map(PHASE_MAP)
    evidence["weighted_value"] = (
        evidence["evidence_value"] * evidence["weight"]
    )
    return evidence


# ============================================================
# نوشتن فایل‌های خروجی
# ============================================================
def _write_csv(df: pd.DataFrame, filename: str, label: str):
    path = os.path.join(OUTPUT_DIR, filename)
    df.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"✓ {label}: {filename} "
          f"({len(df)} ردیف × {len(df.columns)} ستون)")


def _write_excel(
    summary: pd.DataFrame,
    evidence: pd.DataFrame,
    events: pd.DataFrame,
    letters: pd.DataFrame,
):
    path = os.path.join(OUTPUT_DIR, "participants_summary.xlsx")
    try:
        with pd.ExcelWriter(path, engine="openpyxl") as writer:
            summary.to_excel(writer, sheet_name="summary", index=False)
            if not evidence.empty:
                evidence.to_excel(
                    writer, sheet_name="evidence_long", index=False
                )
            if not events.empty:
                # برای Excel محدودیت ردیف داریم — نمونه می‌گیریم
                events_sample = events.head(50000)
                events_sample.to_excel(
                    writer, sheet_name="events_sample", index=False
                )
            if not letters.empty:
                letters.to_excel(
                    writer, sheet_name="self_letters", index=False
                )
        print(f"✓ Excel: participants_summary.xlsx")
    except Exception as e:
        print(f"⚠️ خطا در ساخت Excel: {e}")


# ============================================================
# README
# ============================================================
def _write_readme(
    summary: pd.DataFrame,
    evidence: pd.DataFrame,
    events: pd.DataFrame,
):
    path = os.path.join(OUTPUT_DIR, "README.txt")
    lines = []
    lines.append("راهنمای فایل‌های تحلیلی Truthline")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"تاریخ تولید: {datetime.now().isoformat()}")
    lines.append(f"تعداد شرکت‌کنندگان: {len(summary)}")
    lines.append(f"تعداد رکورد شواهد: {len(evidence)}")
    lines.append(f"تعداد رویداد خام: {len(events)}")
    lines.append("")
    lines.append("توجه: رکوردهای THEATER_ به‌طور خودکار حذف شده‌اند.")
    lines.append("")
    lines.append("-" * 60)
    lines.append("۱. participants_summary.csv / .xlsx")
    lines.append("-" * 60)
    lines.append("یک ردیف per participant. ستون‌ها:")
    lines.append("")
    lines.append("  participant_id        شناسه یکتای شرکت‌کننده")
    lines.append("  session_start         زمان شروع (ISO 8601)")
    lines.append("  session_end           زمان پایان")
    lines.append("  session_duration_min  مدت جلسه (دقیقه)")
    lines.append("  random_seed           بذر تصادفی (برای بازتولیدپذیری)")
    lines.append("")
    lines.append("  دموگرافیک:")
    for field in DEMO_FIELDS:
        lines.append(f"    demo_{field}")
    lines.append("")
    lines.append("  HEXACO-24 (میانگین ۱ تا ۵):")
    for code in HEXACO_CODES:
        lines.append(f"    hexaco_{code}")
    lines.append("")
    lines.append("  نمرات شایستگی (۰ تا ۱۰۰):")
    for comp in COMPETENCY_CODES:
        lines.append(f"    score_{comp}")
        lines.append(f"    conf_{comp}       (اطمینان ۰ تا ۱)")
        lines.append(f"    count_{comp}      (تعداد شواهد)")
    lines.append("")
    lines.append("  score_mean_all        میانگین چهار شایستگی")
    lines.append("  alignment_H_honesty   شاخص همگرایی (پایین‌تر = همگراتر)")
    lines.append("")
    lines.append("-" * 60)
    lines.append("۲. evidence_long.csv")
    lines.append("-" * 60)
    lines.append("فرمت long — یک ردیف per شاهد. مناسب برای:")
    lines.append("  • تحلیل چندسطحی (HLM) در R با lme4")
    lines.append("  • Mplus / AMOS")
    lines.append("")
    lines.append("  participant_id, scenario_id, phase, competency,")
    lines.append("  subcomponent, evidence_key, evidence_value, weight,")
    lines.append("  weighted_value")
    lines.append("")
    lines.append("-" * 60)
    lines.append("۳. events_raw.csv")
    lines.append("-" * 60)
    lines.append("رویدادهای خام. مناسب برای:")
    lines.append("  • تحلیل فرآیند (process mining)")
    lines.append("  • محاسبه‌ی reaction_time_ms")
    lines.append("  • بازسازی دقیق جریان بازی")
    lines.append("")
    lines.append("-" * 60)
    lines.append("۴. self_letters.csv")
    lines.append("-" * 60)
    lines.append("نامه‌های به خود (تحلیل کیفی). ستون content متن کامل است.")
    lines.append("")
    lines.append("-" * 60)
    lines.append("نمونه‌ی کد R برای شروع")
    lines.append("-" * 60)
    lines.append("")
    lines.append("  library(tidyverse)")
    lines.append("  df <- read_csv('participants_summary.csv')")
    lines.append("")
    lines.append("  # توصیفی")
    lines.append("  df %>% summarise(across(starts_with('score_'), ")
    lines.append("       list(m = mean, sd = sd)))")
    lines.append("")
    lines.append("  # همبستگی HEXACO ↔ شایستگی")
    lines.append("  cor.test(df$hexaco_H, df$score_honesty)")
    lines.append("")
    lines.append("  # رگرسیون چندگانه")
    lines.append("  lm(score_honesty ~ hexaco_H + demo_age + demo_gender,")
    lines.append("     data = df)")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"✓ README: README.txt")


# ============================================================
# main
# ============================================================
def main():
    print("=" * 60)
    print("  تحلیل‌گر داده‌های Truthline")
    print("=" * 60)

    if not os.path.exists(DB_PATH):
        print(f"❌ پایگاه داده یافت نشد: {DB_PATH}")
        return

    _ensure_output_dir()
    print(f"✓ پوشه‌ی خروجی: {OUTPUT_DIR}")
    print()

    # اتصال
    conn = sqlite3.connect(DB_PATH)
    try:
        participants = _read_participants(conn)
        scores = _read_competency_scores(conn)
        evidence = _read_evidence(conn)
        events = _read_events(conn)
        letters = _read_self_letters(conn)
    finally:
        conn.close()

    if participants.empty:
        print("⚠️ هیچ شرکت‌کننده‌ای در پایگاه داده یافت نشد.")
        print("   (یا همه‌ی رکوردها با پیشوند THEATER_ هستند)")
        return

    print(f"✓ شرکت‌کنندگان: {len(participants)}")
    print(f"✓ رکورد نمرات: {len(scores)}")
    print(f"✓ شواهد: {len(evidence)}")
    print(f"✓ رویدادها: {len(events)}")
    print(f"✓ نامه‌ها: {len(letters)}")
    print()

    # ساخت جدول خلاصه
    summary = build_summary(participants, scores)
    evidence_enriched = enrich_evidence(evidence)

    # ذخیره
    _write_csv(summary, "participants_summary.csv", "خلاصه")
    _write_csv(evidence_enriched, "evidence_long.csv", "شواهد (long)")
    _write_csv(events, "events_raw.csv", "رویدادهای خام")
    _write_csv(letters, "self_letters.csv", "نامه‌ها")

    _write_excel(summary, evidence_enriched, events, letters)
    _write_readme(summary, evidence_enriched, events)

    print()
    print("=" * 60)
    print(f"  ✓ صادرات کامل شد — {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()