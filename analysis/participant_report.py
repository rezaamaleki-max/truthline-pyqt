"""
گزارش جامع شرکت‌کننده — Truthline
====================================

این اسکریپت داده‌های ذخیره‌شده در دیتابیس را می‌خواند و
به سه شکل گزارش می‌دهد:
  1. گزارش کامل یک شرکت‌کننده (خوانا برای بازبینی)
  2. خلاصه آماری همه شرکت‌کنندگان (برای پایان‌نامه)
  3. صادرات به CSV (برای SPSS/R)

نحوه استفاده:
  python analysis/participant_report.py              → آخرین شرکت‌کننده
  python analysis/participant_report.py <id>         → شرکت‌کننده مشخص
  python analysis/participant_report.py --all        → خلاصه همه
  python analysis/participant_report.py --export     → صادرات CSV
"""
import sys
import os
import json
import sqlite3
from datetime import datetime
from typing import Optional

# مسیر پروژه
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config import DB_PATH

# ✅ اطمینان از UTF-8 در ویندوز
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
    except Exception:
        pass


# ====================================================================
# رنگ‌ها برای خوانایی (اختیاری — در ویندوز ممکن است کار نکند)
# ====================================================================
class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    MAGENTA = "\033[95m"
    DIM = "\033[2m"
    WHITE = "\033[97m"


def banner(title: str, char: str = "═", width: int = 68):
    """چاپ عنوان بخش"""
    print()
    print(char * width)
    print(f"  {C.BOLD}{title}{C.RESET}")
    print(char * width)


def sub_section(title: str):
    """چاپ زیرعنوان"""
    print()
    print(f"{C.CYAN}── {title} ──{C.RESET}")


def fmt_ms(ms: int) -> str:
    """تبدیل میلی‌ثانیه به فرمت خوانا"""
    if ms < 1000:
        return f"{ms}ms"
    sec = ms / 1000
    if sec < 60:
        return f"{sec:.1f}s"
    min_ = int(sec // 60)
    sec = int(sec % 60)
    return f"{min_}m{sec:02d}s"


def fmt_timestamp(ts: float) -> str:
    """تبدیل Unix timestamp به فرمت خوانا"""
    try:
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return str(ts)


# ====================================================================
# تحلیل‌گر اصلی
# ====================================================================
class ParticipantReport:

    def __init__(self, db_path: str = DB_PATH):
        if not os.path.exists(db_path):
            print(f"❌ دیتابیس یافت نشد: {db_path}")
            sys.exit(1)
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

    # ----------------------------------------------------------------
    def close(self):
        self.conn.close()

    # ----------------------------------------------------------------
    def get_all_participants(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT participant_id, session_start, session_end, created_at
            FROM participants
            ORDER BY session_start DESC
        """)
        return [dict(row) for row in cursor.fetchall()]

    # ----------------------------------------------------------------
    def get_last_participant_id(self) -> Optional[str]:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT participant_id FROM participants
            ORDER BY session_start DESC LIMIT 1
        """)
        row = cursor.fetchone()
        return row["participant_id"] if row else None

    # ----------------------------------------------------------------
    def get_participant(self, pid: str):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM participants WHERE participant_id = ?
        """, (pid,))
        row = cursor.fetchone()
        return dict(row) if row else None

    # ----------------------------------------------------------------
    def get_events(self, pid: str):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM events
            WHERE participant_id = ?
            ORDER BY timestamp
        """, (pid,))
        return [dict(row) for row in cursor.fetchall()]

    # ----------------------------------------------------------------
    def get_evidence(self, pid: str):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM evidence
            WHERE participant_id = ?
            ORDER BY competency, evidence_id
        """, (pid,))
        return [dict(row) for row in cursor.fetchall()]

    # ----------------------------------------------------------------
    def get_scores(self, pid: str):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM competency_scores
            WHERE participant_id = ?
        """, (pid,))
        return [dict(row) for row in cursor.fetchall()]

    # ================================================================
    # چاپ گزارش کامل یک شرکت‌کننده
    # ================================================================
    def print_full_report(self, pid: str):
        participant = self.get_participant(pid)
        if not participant:
            print(f"❌ شرکت‌کننده {pid} یافت نشد.")
            return

        banner(f"گزارش کامل شرکت‌کننده: {pid}")

        # ---------- بخش ۱: اطلاعات پایه ----------
        sub_section("۱. اطلاعات پایه")
        ss = participant.get("session_start") or 0
        se = participant.get("session_end") or 0
        duration = (se - ss) / 60 if se > ss else 0
        print(f"  • شروع جلسه:        {fmt_timestamp(ss)}")
        if se > 0:
            print(f"  • پایان جلسه:       {fmt_timestamp(se)}")
            print(f"  • مدت جلسه:         {duration:.1f} دقیقه")
        else:
            print(f"  • وضعیت:            {C.YELLOW}جلسه ناتمام{C.RESET}")

        # ---------- بخش ۲: دموگرافیک ----------
        sub_section("۲. داده‌های دموگرافیک")
        demo = self._parse_json(participant.get("demographic_data"))
        if demo:
            for k, v in demo.items():
                label = self._demo_label(k)
                print(f"  • {label:<32} {v}")
        else:
            print(f"  {C.DIM}(داده‌ای ثبت نشده){C.RESET}")

        # ---------- بخش ۳: HEXACO ----------
        sub_section("۳. نیمرخ HEXACO-24")
        hexaco = self._parse_json(participant.get("hexaco_scores"))
        if hexaco:
            factor_names = {
                "score_H": "صداقت-تواضع (H)",
                "score_E": "هیجان‌پذیری (E)",
                "score_X": "برون‌گرایی (X)",
                "score_A": "خوشایندی (A)",
                "score_C": "وظیفه‌شناسی (C)",
                "score_O": "گشودگی به تجربه (O)",
            }
            for key, label in factor_names.items():
                if key in hexaco:
                    val = hexaco[key]
                    bar = "█" * int(val) + "░" * (5 - int(val))
                    print(f"  • {label:<24} {val:.2f}  {bar}")

        # ---------- بخش ۴: تایم‌لاین رویدادها ----------
        sub_section("۴. تایم‌لاین رویدادها")
        events = self.get_events(pid)
        if not events:
            print(f"  {C.DIM}(رویدادی ثبت نشده){C.RESET}")
        else:
            # فیلتر رویدادهای مهم (نه هر دیالوگ)
            significant = [
                "scene_enter", "scene_exit", "scenario_start",
                "quantum_readings_completed", "calibration_completed",
                "allocation_completed", "diagnosis_completed",
                "pressure_dice_rolled", "choice_made",
                "form_submitted",
            ]
            for ev in events:
                if ev["event_type"] not in significant:
                    continue
                rt = ev.get("reaction_time_ms", 0)
                scene = ev.get("scene_id", "")
                scenario = ev.get("scenario_id", "")
                etype = ev["event_type"]
                meta = self._parse_json(ev.get("metadata"))
                print()
                print(f"  {C.YELLOW}[{fmt_ms(rt):>7}]{C.RESET} "
                      f"{C.BOLD}{etype}{C.RESET}")
                print(f"           {C.DIM}scene={scene} "
                      f"scenario={scenario}{C.RESET}")
                self._print_event_meta(etype, meta, scene)

        # ---------- بخش ۵: شواهد رفتاری ----------
        sub_section("۵. شواهد رفتاری")
        evidence = self.get_evidence(pid)
        if not evidence:
            print(f"  {C.DIM}(شاهدی ثبت نشده){C.RESET}")
        else:
            current_comp = None
            for ev in evidence:
                comp = ev["competency"]
                if comp != current_comp:
                    current_comp = comp
                    comp_fa = {
                        "honesty": "صداقت و یکپارچگی",
                        "trustworthiness": "قابلیت اعتماد",
                        "problem_solving": "حل مسئله",
                        "accountability": "مسئولیت‌پذیری",
                    }.get(comp, comp)
                    print()
                    print(f"  {C.MAGENTA}▸ {comp_fa}{C.RESET}")
                key = ev["evidence_key"]
                val = ev["evidence_value"]
                weight = ev["weight"]
                sub = ev["subcomponent"]
                print(f"      {key:<28} "
                      f"value={val:.2f}  weight={weight:.2f}  "
                      f"{C.DIM}{sub}{C.RESET}")

        # ---------- بخش ۶: نمرات نهایی ----------
        sub_section("۶. نمرات نهایی شایستگی‌ها")
        scores = self.get_scores(pid)
        if not scores:
            print(f"  {C.DIM}(نمره‌ای محاسبه نشده){C.RESET}")
        else:
            order = ["honesty", "trustworthiness",
                     "problem_solving", "accountability"]
            scores_dict = {s["competency"]: s for s in scores}
            for comp in order:
                s = scores_dict.get(comp)
                if not s:
                    continue
                comp_fa = {
                    "honesty": "صداقت و یکپارچگی",
                    "trustworthiness": "قابلیت اعتماد",
                    "problem_solving": "حل مسئله",
                    "accountability": "مسئولیت‌پذیری",
                }[comp]
                score = s["score"]
                conf = s["confidence"]
                count = s["evidence_count"]
                # رنگ بر اساس نمره
                if score >= 70:
                    color = C.GREEN
                elif score >= 40:
                    color = C.YELLOW
                else:
                    color = C.RED
                bar = "█" * int(score / 5) + "░" * (20 - int(score / 5))
                print(f"  • {comp_fa:<22} "
                      f"{color}{score:>6.2f}{C.RESET}  "
                      f"[{bar}]  "
                      f"{C.DIM}({count} شاهد، "
                      f"اعتماد: {conf:.2f}){C.RESET}")

        banner("پایان گزارش", char="═")

    # ----------------------------------------------------------------
    def _print_event_meta(self, etype: str, meta, scene_id: str = ""):
        """چاپ خلاصه اطلاعات هر رویداد"""
        if not meta:
            return
        if etype == "choice_made":
            cid = meta.get("choice_id")
            txt = meta.get("choice_text", "")
            dt = meta.get("decision_time_ms", 0)
            print(f"           انتخاب: {C.GREEN}گزینه {cid}{C.RESET} — "
                  f"{txt}")
            print(f"           زمان تصمیم: {fmt_ms(dt)}")

            # داده‌های ویژه هر سناریو
            if "real_average" in meta:
                print(f"           {C.DIM}میانگین واقعی: "
                      f"{meta['real_average']} | گزارش‌شده: "
                      f"{meta.get('reported_average', '?')}{C.RESET}")
            if "calibration_result" in meta:
                cr = meta["calibration_result"]
                print(f"           {C.DIM}کالیبراسیون: "
                      f"{cr.get('in_zone_count', '?')} از "
                      f"{cr.get('total_count', '?')} | "
                      f"میان‌بر: {cr.get('cheat_used', False)}{C.RESET}")
            if "allocation_result" in meta:
                ar = meta["allocation_result"]
                alloc = ar.get("allocations", {})
                info = ar.get("info_checked", [])
                print(f"           {C.DIM}تخصیص: {alloc}")
                print(f"           اطلاعات بررسی‌شده: {info}"
                      f" ({len(info)}/{len(alloc)}){C.RESET}")
            if "diagnostic_result" in meta:
                dr = meta["diagnostic_result"]
                print(f"           {C.DIM}علت انتخابی: "
                      f"{dr.get('chosen_root_cause', '?')} | "
                      f"بررسی‌شده: {dr.get('total_investigated', 0)}"
                      f"/{dr.get('total_systems', 0)}{C.RESET}")
            if "dice_value" in meta:
                print(f"           {C.DIM}تاس: {meta['dice_value']} | "
                      f"فشار: {meta.get('pressure_level', '?')}{C.RESET}")

        elif etype == "quantum_readings_completed":
            readings = meta.get("readings", [])
            avg = meta.get("average", 0)
            print(f"           قرائت‌ها: {readings} | "
                  f"میانگین: {avg}")

        elif etype == "calibration_completed":
            in_zone = meta.get("in_zone_count", 0)
            total = meta.get("total_count", 0)
            cheat = meta.get("cheat_used", False)
            print(f"           در محدوده: {in_zone}/{total} | "
                  f"میان‌بر: {cheat}")

        elif etype == "allocation_completed":
            alloc = meta.get("allocations", {})
            info = meta.get("info_checked", [])
            timed_out = meta.get("timed_out", False)
            print(f"           تخصیص: {alloc}")
            print(f"           بررسی اطلاعات: {len(info)} بخش | "
                  f"تایم‌اوت: {timed_out}")

        elif etype == "diagnosis_completed":
            print(f"           علت انتخابی: "
                  f"{meta.get('chosen_root_cause', '?')}")
            print(f"           بررسی‌شده: "
                  f"{meta.get('total_investigated', 0)} از "
                  f"{meta.get('total_systems', 0)}")

        elif etype == "pressure_dice_rolled":
            print(f"           تاس: {meta.get('dice_value', '?')} | "
                  f"سطح فشار: {meta.get('pressure_level', '?')}")

        elif etype == "form_submitted":
            if "hexaco" in scene_id.lower():
                print(f"           {C.DIM}پرسشنامه HEXACO ثبت شد{C.RESET}")
            else:
                print(f"           {C.DIM}فرم دموگرافیک ثبت شد{C.RESET}")

    # ----------------------------------------------------------------
    def _parse_json(self, s):
        if not s:
            return {}
        try:
            return json.loads(s)
        except Exception:
            return {}

    def _demo_label(self, key: str) -> str:
        return {
            "age": "سن",
            "gender": "جنسیت",
            "education": "مقطع تحصیلی",
            "field_of_study": "رشته تحصیلی",
            "work_experience": "سابقه کار",
            "gaming_experience": "سابقه بازی",
            "technical_familiarity": "آشنایی فنی",
            "consent": "رضایت‌نامه",
        }.get(key, key)

    # ================================================================
    # خلاصه آماری همه شرکت‌کنندگان
    # ================================================================
    def print_all_summary(self):
        banner("خلاصه آماری همه شرکت‌کنندگان")
        participants = self.get_all_participants()
        if not participants:
            print(f"  {C.YELLOW}هیچ شرکت‌کننده‌ای یافت نشد.{C.RESET}")
            return

        print(f"\n  تعداد کل: {C.BOLD}{len(participants)}{C.RESET}")

        # جدول نمرات
        sub_section("نمرات شایستگی (آخرین اجرا از هر شرکت‌کننده)")
        rows = []
        for p in participants:
            pid = p["participant_id"]
            scores = self.get_scores(pid)
            row = {"participant_id": pid}
            for s in scores:
                row[s["competency"]] = s["score"]
            rows.append(row)

        try:
            import pandas as pd
            df = pd.DataFrame(rows)
        except ImportError:
            print(f"  {C.RED}pandas نصب نیست. نصب کن: pip install pandas{C.RESET}")
            return

        if df.empty:
            print("  داده‌ای برای نمایش نیست.")
            return

        # آمار توصیفی
        cols = ["honesty", "trustworthiness",
                "problem_solving", "accountability"]
        cols = [c for c in cols if c in df.columns]
        print()
        print(f"  {'شایستگی':<25} {'M':>8} {'SD':>8} "
              f"{'Min':>8} {'Max':>8}")
        print(f"  {'-'*25} {'-'*8} {'-'*8} {'-'*8} {'-'*8}")
        for col in cols:
            fa = {
                "honesty": "صداقت و یکپارچگی",
                "trustworthiness": "قابلیت اعتماد",
                "problem_solving": "حل مسئله",
                "accountability": "مسئولیت‌پذیری",
            }[col]
            m = df[col].mean()
            sd = df[col].std() if len(df) > 1 else 0
            mn = df[col].min()
            mx = df[col].max()
            print(f"  {fa:<25} {m:>8.2f} {sd:>8.2f} "
                  f"{mn:>8.2f} {mx:>8.2f}")

        # لیست شرکت‌کنندگان
        sub_section("لیست شرکت‌کنندگان")
        for i, p in enumerate(participants[:20], 1):
            pid = p["participant_id"]
            ss = p.get("session_start") or 0
            scores = self.get_scores(pid)
            score_str = "  ".join([
                f"{s['competency'][:3]}={s['score']:.0f}"
                for s in scores
            ])
            print(f"  {i:>2}. {pid}  "
                  f"{fmt_timestamp(ss):<20}  {score_str}")
        if len(participants) > 20:
            print(f"  {C.DIM}... و {len(participants) - 20} نفر دیگر{C.RESET}")

        banner("پایان خلاصه")

    # ================================================================
    # صادرات به CSV
    # ================================================================
    def export_csv(self, path: str = "participant_data.csv"):
        try:
            import pandas as pd
        except ImportError:
            print(f"❌ pandas نصب نیست. نصب کن: pip install pandas")
            return

        participants = self.get_all_participants()
        rows = []
        for p in participants:
            pid = p["participant_id"]
            row = {"participant_id": pid}
            ss = p.get("session_start") or 0
            se = p.get("session_end") or 0
            row["session_start"] = fmt_timestamp(ss)
            row["session_duration_min"] = round((se - ss) / 60, 1) if se > ss else 0

            # دموگرافیک
            demo = self._parse_json(p.get("demographic_data"))
            for k, v in demo.items():
                row[f"demo_{k}"] = v

            # HEXACO
            hexaco = self._parse_json(p.get("hexaco_scores"))
            for k, v in hexaco.items():
                if k.startswith("score_"):
                    row[f"hexaco_{k[6:]}"] = v

            # نمرات شایستگی
            scores = self.get_scores(pid)
            for s in scores:
                row[f"score_{s['competency']}"] = s["score"]
                row[f"conf_{s['competency']}"] = s["confidence"]
                row[f"count_{s['competency']}"] = s["evidence_count"]

            rows.append(row)

        df = pd.DataFrame(rows)
        df.to_csv(path, index=False, encoding="utf-8-sig")
        print(f"✓ CSV صادر شد: {os.path.abspath(path)}")
        print(f"  تعداد رکورد: {len(df)}")
        print(f"  تعداد ستون: {len(df.columns)}")
        print(f"  ستون‌ها: {', '.join(df.columns.tolist())}")


# ====================================================================
# ورودی اصلی
# ====================================================================
def main():
    args = sys.argv[1:]
    report = ParticipantReport()

    try:
        if not args:
            pid = report.get_last_participant_id()
            if not pid:
                print("هیچ شرکت‌کننده‌ای در دیتابیس نیست.")
                return
            report.print_full_report(pid)

        elif args[0] == "--all":
            report.print_all_summary()

        elif args[0] == "--export":
            out = args[1] if len(args) > 1 else "participant_data.csv"
            report.export_csv(out)

        elif args[0] == "--help" or args[0] == "-h":
            print(__doc__)

        else:
            report.print_full_report(args[0])

    finally:
        report.close()


if __name__ == "__main__":
    main()