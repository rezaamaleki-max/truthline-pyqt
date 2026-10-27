"""
تحلیل گروهی داده‌های Truthline
===============================
خواندن دیتابیس و تولید گزارش گروهی از N شرکت‌کننده.

Usage:
    python -m analysis.aggregate_report
    python -m analysis.aggregate_report --csv out.csv
"""
import os
import sys
import sqlite3
import json
from datetime import datetime
from statistics import mean, stdev


PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from config import DB_PATH
except ImportError:
    DB_PATH = os.path.join(
        PROJECT_ROOT, "data", "participants.db"
    )


def fetch_all_data() -> dict:
    """خواندن همه‌ی داده‌های موردنیاز از دیتابیس"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # شرکت‌کنندگان
    cur.execute("""
        SELECT participant_id, session_start, session_end,
               demographic_data, hexaco_scores
        FROM participants
        WHERE participant_id NOT LIKE 'THEATER_%'
          AND participant_id NOT LIKE 'TEST_%'
    """)
    participants = [dict(r) for r in cur.fetchall()]

    # نمرات شایستگی
    cur.execute("""
        SELECT participant_id, competency, score, confidence,
               evidence_count
        FROM competency_scores
    """)
    scores = [dict(r) for r in cur.fetchall()]

    # زیرمؤلفه‌ها
    cur.execute("""
        SELECT participant_id, competency, sub_competency, score
        FROM sub_competency_scores
    """)
    subs = [dict(r) for r in cur.fetchall()]

    # طرح‌واره‌ها
    cur.execute("""
        SELECT participant_id, schema_primary, COUNT(*) as cnt
        FROM schema_evidence
        GROUP BY participant_id, schema_primary
    """)
    schemas = [dict(r) for r in cur.fetchall()]

    # پرسشنامه‌های تکمیلی
    cur.execute("""
        SELECT participant_id, hexaco_scores, crt_data,
               sd3_scores, social_desirability
        FROM extended_questionnaires
    """)
    questionnaires = [dict(r) for r in cur.fetchall()]

    conn.close()

    return {
        "participants": participants,
        "scores": scores,
        "subs": subs,
        "schemas": schemas,
        "questionnaires": questionnaires,
    }


def compute_stats(values: list) -> dict:
    """آمار توصیفی"""
    clean = [v for v in values if v is not None]
    if not clean:
        return {"n": 0}
    return {
        "n": len(clean),
        "mean": round(mean(clean), 2),
        "sd": round(stdev(clean), 2) if len(clean) > 1 else 0.0,
        "min": round(min(clean), 2),
        "max": round(max(clean), 2),
    }


def main():
    print("=" * 70)
    print("تحلیل گروهی Truthline")
    print("=" * 70)

    data = fetch_all_data()

    n_part = len(data["participants"])
    print(f"\nتعداد شرکت‌کنندگان (بدون theater و test): {n_part}")

    if n_part == 0:
        print("داده‌ای برای تحلیل وجود ندارد.")
        return

    # ============================================================
    # ۱. نمرات شایستگی
    # ============================================================
    print("\n--- نمرات شایستگی (۰ تا ۱۰۰) ---")
    competencies = [
        "honesty", "trustworthiness",
        "problem_solving", "accountability",
    ]
    comp_fa = {
        "honesty": "صداقت",
        "trustworthiness": "قابلیت اعتماد",
        "problem_solving": "حل مسئله",
        "accountability": "مسئولیت‌پذیری",
    }
    for comp in competencies:
        values = [
            s["score"] for s in data["scores"]
            if s["competency"] == comp
        ]
        st = compute_stats(values)
        if st["n"] > 0:
            print(
                f"  {comp_fa[comp]:15s}  "
                f"n={st['n']:3d}  "
                f"mean={st['mean']:5.1f}  "
                f"sd={st['sd']:4.1f}  "
                f"[{st['min']:.0f}–{st['max']:.0f}]"
            )
        else:
            print(f"  {comp_fa[comp]:15s}  داده‌ای نیست")

    # ============================================================
    # ۲. زیرمؤلفه‌های کلیدی
    # ============================================================
    print("\n--- زیرمؤلفه‌های کلیدی ---")
    key_subs = [
        ("honesty", "transparency"),
        ("honesty", "data_integrity"),
        ("honesty", "moral_consistency"),
        ("trustworthiness", "commitment_keeping"),
        ("trustworthiness", "autonomous_quality"),
        ("problem_solving", "root_cause_analysis"),
        ("problem_solving", "sequence_planning"),
        ("problem_solving", "creative_thinking"),
        ("accountability", "formal_accountability"),
        ("accountability", "proactive_improvement"),
        ("accountability", "resistance_to_temptation"),
        ("accountability", "growth_mindset"),
    ]
    for comp, sub in key_subs:
        values = [
            s["score"] for s in data["subs"]
            if s["competency"] == comp
            and s["sub_competency"] == sub
        ]
        st = compute_stats(values)
        if st["n"] > 0:
            print(
                f"  {comp}/{sub:30s}  "
                f"n={st['n']:3d}  mean={st['mean']:5.1f}"
            )

    # ============================================================
    # ۳. توزیع طرح‌واره‌ها
    # ============================================================
    print("\n--- توزیع طرح‌واره‌های کلبرگ ---")
    schema_totals = {
        "personal_interest": 0,
        "maintaining_norms": 0,
        "postconventional": 0,
    }
    for s in data["schemas"]:
        if s["schema_primary"] in schema_totals:
            schema_totals[s["schema_primary"]] += s["cnt"]
    total = sum(schema_totals.values())
    if total > 0:
        for key, val in schema_totals.items():
            pct = 100 * val / total
            print(f"  {key:25s}  {val:4d}  ({pct:.1f}%)")
    else:
        print("  داده‌ای نیست")

    # ============================================================
    # ۴. همبستگی‌ها (اختیاری)
    # ============================================================
    print("\n--- همبستگی طرح‌واره با نمرات (پیش‌نمایش) ---")
    # ساخت دیکشنری per-participant
    by_pid = {}
    for s in data["scores"]:
        by_pid.setdefault(s["participant_id"], {})[s["competency"]] = s["score"]
    schema_by_pid = {}
    for s in data["schemas"]:
        schema_by_pid.setdefault(
            s["participant_id"], {}
        )[s["schema_primary"]] = s["cnt"]

    # همبستگی PI با نمره‌ی صداقت
    pi_vals, honesty_vals = [], []
    for pid, sc in by_pid.items():
        pi = schema_by_pid.get(pid, {}).get("personal_interest", 0)
        h = sc.get("honesty")
        if h is not None:
            pi_vals.append(pi)
            honesty_vals.append(h)

    if len(pi_vals) >= 3:
        r = pearson(pi_vals, honesty_vals)
        print(f"  r(PI_count, honesty) = {r:+.3f}  (n={len(pi_vals)})")
    else:
        print("  برای همبستگی، حداقل ۳ شرکت‌کننده لازم است")

    print("\n" + "=" * 70)


def pearson(xs: list, ys: list) -> float:
    """ضریب همبستگی Pearson"""
    n = len(xs)
    if n < 2:
        return 0.0
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = sum((x - mx) ** 2 for x in xs) ** 0.5
    dy = sum((y - my) ** 2 for y in ys) ** 0.5
    if dx == 0 or dy == 0:
        return 0.0
    return num / (dx * dy)


if __name__ == "__main__":
    main()