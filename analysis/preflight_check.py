"""
پیش‌بازرسی سیستم (Pre-flight Check)
=====================================
این اسکریپت را پیش از شروع هر جلسه‌ی پژوهشی اجرا کنید تا
مطمئن شوید همه‌ی اجزای سیستم سالم هستند.

نحوه استفاده:
    python analysis/preflight_check.py

خروجی:
    گزارش رنگی با ✓ یا ✗ برای هر مورد
    کد خروج 0 = همه چیز سالم
    کد خروج 1 = مشکلات بحرانی
"""
import os
import sys
import json
import sqlite3
import re
from datetime import datetime

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from config import DB_PATH, DATA_DIR, ASSETS_DIR, SCENARIOS_DIR
except ImportError:
    DB_PATH = os.path.join(PROJECT_ROOT, "data", "participants.db")
    DATA_DIR = os.path.join(PROJECT_ROOT, "data")
    ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")
    SCENARIOS_DIR = os.path.join(DATA_DIR, "scenarios")


# ====================================================================
# رنگ‌ها
# ====================================================================
class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    MAGENTA = "\033[95m"
    DIM = "\033[2m"


def _ok(msg: str):
    print(f"  {C.GREEN}✓{C.RESET}  {msg}")


def _warn(msg: str):
    print(f"  {C.YELLOW}⚠{C.RESET}  {msg}")


def _err(msg: str):
    print(f"  {C.RED}✗{C.RESET}  {msg}")


def _info(msg: str):
    print(f"     {C.DIM}{msg}{C.RESET}")


def _section(title: str):
    print()
    print(f"{C.CYAN}{C.BOLD}─── {title} ───{C.RESET}")


# ====================================================================
# فرمول‌های شناخته‌شده
# ====================================================================
KNOWN_FORMULAS = {
    "decision_time",
    "consistency_computed",
    "deferred",
    "deferred_consistency",
    # Semantic formulas
    "allocation_score",
    "info_check_score",
    "fairness_under_pressure",
    "investigation_depth",
    "investigation_count",
    "time_to_first_action",
    "correct_root_cause",
    "perseveration_score",
    "exploration_score",
    # Mechanic-specific
    "sequence_score",
    "planning_time",
    "efficiency_score",
    "old_attempts_penalty",
    "unique_combinations",
    "solution_time",
    "completion_rate",
    "cheat_penalty",
    "rejected_temptation",
}

# الگوهای regex فرمول‌های choice_id
CHOICE_FORMULA_PATTERNS = [
    re.compile(
        r"^1 if choice_id == \d+ "
        r"else \((\d+(?:\.\d+)?) if choice_id == \d+ "
        r"else (\d+(?:\.\d+)?)\)$"
    ),
    re.compile(r"^1 if choice_id == \d+ else \d+(?:\.\d+)?$"),
    re.compile(
        r"^1 if choice_id in \(\d+,\s*\d+\) "
        r"else \d+(?:\.\d+)?$"
    ),
]


def _is_known_formula(formula: str) -> bool:
    if formula in KNOWN_FORMULAS:
        return True
    for pat in CHOICE_FORMULA_PATTERNS:
        if pat.match(formula.strip()):
            return True
    return False


# ====================================================================
# بررسی‌ها
# ====================================================================
class PreflightChecker:
    def __init__(self):
        self.errors = 0
        self.warnings = 0
        self.scenario_count = 0
        self.formula_errors = []

    # ================================================================
    def run(self) -> int:
        print("=" * 70)
        print(f"  {C.BOLD}Truthline — پیش‌بازرسی سیستم{C.RESET}")
        print(f"  {C.DIM}{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{C.RESET}")
        print("=" * 70)

        self._check_config()
        self._check_database()
        self._check_scenarios()
        self._check_spa_01()
        self._check_spa_02()
        self._check_assets()
        self._check_other_data_files()

        self._print_summary()

        return 1 if self.errors > 0 else 0

    # ================================================================
    def _check_config(self):
        _section("۱. تنظیمات و مسیرها")

        if os.path.exists(DB_PATH):
            _ok(f"DB_PATH موجود است: {C.DIM}{DB_PATH}{C.RESET}")
        else:
            _warn(f"DB_PATH وجود ندارد (اولین اجرا): {DB_PATH}")

        if os.path.isdir(SCENARIOS_DIR):
            _ok(f"پوشه سناریوها: {SCENARIOS_DIR}")
        else:
            _err(f"پوشه سناریوها یافت نشد: {SCENARIOS_DIR}")
            self.errors += 1

    # ================================================================
    def _check_database(self):
        _section("۲. پایگاه داده")

        if not os.path.exists(DB_PATH):
            _warn("پایگاه داده هنوز ساخته نشده — با اولین اجرا ساخته می‌شود")
            return

        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()

            required_tables = {
                "participants", "events", "evidence",
                "competency_scores",
            }

            cur.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='table'"
            )
            existing = {row[0] for row in cur.fetchall()}

            missing = required_tables - existing
            if missing:
                _err(f"جدول‌های غایب: {missing}")
                self.errors += 1
            else:
                _ok(f"همه‌ی جدول‌های اصلی موجودند "
                    f"({len(existing)} جدول)")

            # اختیاری: self_letters
            if "self_letters" in existing:
                _ok("جدول self_letters موجود است")
            else:
                _warn("جدول self_letters موجود نیست "
                      "(در اولین استفاده ساخته می‌شود)")

            # تعداد شرکت‌کنندگان
            cur.execute("SELECT COUNT(*) FROM participants")
            n = cur.fetchone()[0]
            _info(f"تعداد شرکت‌کنندگان: {n}")

            conn.close()

        except Exception as e:
            _err(f"خطا در باز کردن DB: {e}")
            self.errors += 1

    # ================================================================
    def _check_scenarios(self):
        _section("۳. فایل‌های سناریو")

        if not os.path.isdir(SCENARIOS_DIR):
            return

        # نگاشت: scenario_id → لیست فایل‌های آن
        # (چون ممکن است دو نسخه داشته باشیم: ساده و _inner)
        id_to_files: dict = {}
        inner_pairs_ok: int = 0
        inner_pairs_missing: list = []

        for phase_name in sorted(os.listdir(SCENARIOS_DIR)):
            phase_dir = os.path.join(SCENARIOS_DIR, phase_name)
            if not os.path.isdir(phase_dir):
                continue

            json_files = [
                f for f in sorted(os.listdir(phase_dir))
                if f.endswith(".json")
            ]

            phase_ok = 0
            phase_inner = 0

            for fname in json_files:
                path = os.path.join(phase_dir, fname)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        scen = json.load(f)
                except json.JSONDecodeError as e:
                    _err(f"{phase_name}/{fname}: JSON خراب — {e}")
                    self.errors += 1
                    continue
                except Exception as e:
                    _err(f"{phase_name}/{fname}: خطا — {e}")
                    self.errors += 1
                    continue

                sid = scen.get("scenario_id", "")
                if not sid:
                    _err(f"{phase_name}/{fname}: بدون scenario_id")
                    self.errors += 1
                    continue

                is_inner = fname.endswith("_inner.json")

                # ثبت فایل زیر همان scenario_id
                id_to_files.setdefault(sid, []).append({
                    "phase": phase_name,
                    "file": fname,
                    "is_inner": is_inner,
                })

                # بررسی choices — id یکتا
                choice_ids = []
                for c in scen.get("choices", []):
                    cid = c.get("id")
                    if cid is None:
                        _warn(f"{fname}: گزینه بدون id")
                        continue
                    choice_ids.append(cid)
                if len(choice_ids) != len(set(choice_ids)):
                    _err(f"{phase_name}/{fname}: "
                         "choice_id تکراری")
                    self.errors += 1

                # بررسی evidence_model
                em = scen.get("evidence_model", {})
                for ev_id, ev_def in em.items():
                    formula = ev_def.get("formula", "")
                    if not formula:
                        continue
                    if not _is_known_formula(formula):
                        self.formula_errors.append(
                            (f"{phase_name}/{fname}", ev_id,
                             formula)
                        )

                if is_inner:
                    phase_inner += 1
                else:
                    phase_ok += 1

            if phase_ok > 0:
                msg = f"{phase_name}: {phase_ok} سناریوی پایه"
                if phase_inner > 0:
                    msg += f" + {phase_inner} نسخه‌ی inner"
                _ok(msg)

        # ✅ بررسی جفت بودن _inner با نسخه‌ی ساده
        for sid, files in id_to_files.items():
            inners = [f for f in files if f["is_inner"]]
            bases = [f for f in files if not f["is_inner"]]

            for inner in inners:
                # آیا نسخه‌ی ساده‌ی متناظر وجود دارد؟
                base_exists = any(
                    b["phase"] == inner["phase"]
                    for b in bases
                )
                if base_exists:
                    inner_pairs_ok += 1
                else:
                    inner_pairs_missing.append(
                        f"{inner['phase']}/{inner['file']}"
                    )

        _info(
            f"مجموع شناسه‌های یکتا: {len(id_to_files)}"
        )

        if inner_pairs_ok > 0:
            _ok(
                f"{inner_pairs_ok} جفت ساده + inner "
                "سالم هستند"
            )

        if inner_pairs_missing:
            _warn(
                f"{len(inner_pairs_missing)} فایل inner بدون "
                "نسخه‌ی ساده:"
            )
            for item in inner_pairs_missing[:5]:
                _info(item)
            self.warnings += len(inner_pairs_missing)

        if self.formula_errors:
            _warn(
                f"{len(self.formula_errors)} فرمول ناشناخته "
                f"(غیر بحرانی)"
            )
            for path, ev_id, formula in self.formula_errors[:5]:
                _info(f"{path} → {ev_id}: {formula[:40]}")
            if len(self.formula_errors) > 5:
                _info(
                    f"... و {len(self.formula_errors) - 5} مورد "
                    "دیگر"
                )
            self.warnings += len(self.formula_errors)

    # ================================================================
    def _check_spa_01(self):
        _section("۴. هم‌خوانی SPA-01 (زنجیره نجات)")

        path = os.path.join(
            SCENARIOS_DIR, "phase3", "SPA-01.json"
        )
        if not os.path.exists(path):
            _warn("SPA-01.json یافت نشد")
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                scen = json.load(f)

            cfg = scen.get("dependency_config", {})
            actions = cfg.get("actions", [])
            correct = cfg.get("correct_order", [])

            action_ids = {a["id"] for a in actions}
            if len(action_ids) != len(actions):
                _err("SPA-01: action_id تکراری")
                self.errors += 1

            missing = set(correct) - action_ids
            if missing:
                _err(
                    f"SPA-01: این idها در correct_order هستند "
                    f"ولی در actions نیستند: {missing}"
                )
                self.errors += 1
            else:
                _ok(
                    f"SPA-01: {len(actions)} action، "
                    f"{len(correct)} در ترتیب صحیح"
                )

            distractors = [
                a["id"] for a in actions
                if a.get("is_distractor", False)
            ]
            if distractors:
                _info(f"گزینه‌های بی‌ربط: {distractors}")

        except Exception as e:
            _err(f"SPA-01: خطا — {e}")
            self.errors += 1

    # ================================================================
    def _check_spa_02(self):
        _section("۵. هم‌خوانی SPA-02 (تخصیص منابع)")

        path = os.path.join(
            SCENARIOS_DIR, "phase3", "SPA-02.json"
        )
        if not os.path.exists(path):
            _warn("SPA-02.json یافت نشد")
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                scen = json.load(f)

            cfg = scen.get("allocation_config", {})
            sections = cfg.get("sections", [])
            resources = cfg.get("resources", [])
            optimal = cfg.get("optimal_allocation", {})

            section_ids = {s["id"] for s in sections}
            resource_ids = {r["id"] for r in resources}

            missing_sec = set(optimal.keys()) - section_ids
            if missing_sec:
                _err(
                    f"SPA-02: بخش‌های غایب در optimal: "
                    f"{missing_sec}"
                )
                self.errors += 1

            missing_res = (
                set(optimal.values()) - resource_ids
            )
            if missing_res:
                _err(
                    f"SPA-02: منابع غایب در optimal: "
                    f"{missing_res}"
                )
                self.errors += 1

            if not missing_sec and not missing_res:
                _ok(
                    f"SPA-02: {len(sections)} بخش، "
                    f"{len(resources)} منبع، "
                    f"optimal سازگار"
                )

        except Exception as e:
            _err(f"SPA-02: خطا — {e}")
            self.errors += 1

    # ================================================================
    def _check_assets(self):
        _section("۶. پوشه‌های دارایی")

        for sub in ["audio", "characters", "backgrounds"]:
            path = os.path.join(ASSETS_DIR, sub)
            if os.path.isdir(path):
                files = os.listdir(path)
                _ok(f"assets/{sub}: {len(files)} مورد")
            else:
                _warn(f"assets/{sub} موجود نیست")

    # ================================================================
    def _check_other_data_files(self):
        _section("۷. فایل‌های داده‌ی دیگر")

        checks = [
            ("night_dialogues.json",
             "دیالوگ‌های شب"),
            ("mission_log_reflections.json",
             "بازتاب‌های دفترچه"),
            ("app_config.json",
             "تنظیمات"),
        ]

        for fname, label in checks:
            path = os.path.join(DATA_DIR, fname)
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        json.load(f)
                    _ok(f"{label}: {fname}")
                except Exception as e:
                    _err(f"{label}: JSON خراب — {e}")
                    self.errors += 1
            else:
                _warn(f"{label}: یافت نشد ({fname})")

    # ================================================================
    def _print_summary(self):
        print()
        print("=" * 70)
        if self.errors == 0 and self.warnings == 0:
            print(f"  {C.GREEN}{C.BOLD}✓ همه چیز سالم است{C.RESET}")
        elif self.errors == 0:
            print(
                f"  {C.YELLOW}{C.BOLD}⚠ "
                f"{self.warnings} هشدار — قابل قبول{C.RESET}"
            )
        else:
            print(
                f"  {C.RED}{C.BOLD}✗ "
                f"{self.errors} خطا و {self.warnings} هشدار"
                f"{C.RESET}"
            )
            print(
                f"  {C.DIM}پیش از شروع جلسه‌ی پژوهشی "
                f"این خطاها را رفع کنید.{C.RESET}"
            )
        print("=" * 70)


def main():
    checker = PreflightChecker()
    exit_code = checker.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()