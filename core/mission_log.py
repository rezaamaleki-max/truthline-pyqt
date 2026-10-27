"""
ساخت ورودی‌های دفترچه‌ی مأموریت
- از choice_memory بازیکن می‌خواند
- با سناریوهای JSON تطبیق می‌دهد
- لیست آماده برای نمایش برمی‌گرداند

هیچ نمره‌ای در آن نیست — کاملاً لایه‌ی روایی
"""
import os
import json
from config import DATA_DIR


# نگاشت شماره‌ی فاز به برچسب روز
PHASE_DAYS = {
    "1": "روز اول",
    "2": "روز دوم",
    "3": "روز سوم",
    "4": "روز چهارم",
}

# مسیر فایل بازتاب‌ها
REFLECTIONS_PATH = os.path.join(
    DATA_DIR, "mission_log_reflections.json"
)

# ✅ cache — یک بار ساخته می‌شود
_SCENARIO_MAP: dict = {}
_REFLECTIONS_CACHE: dict = {}


def _build_scenario_map() -> dict:
    """بارگذاری همه‌ی سناریوها و ساخت نگاشت scenario_id → اطلاعات"""
    global _SCENARIO_MAP
    if _SCENARIO_MAP:
        return _SCENARIO_MAP

    for phase_num in ["1", "2", "3", "4"]:
        phase_dir = os.path.join(
            DATA_DIR, "scenarios", f"phase{phase_num}"
        )
        if not os.path.isdir(phase_dir):
            continue

        for fname in sorted(os.listdir(phase_dir)):
            if not fname.endswith(".json"):
                continue
            path = os.path.join(phase_dir, fname)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    scen = json.load(f)
            except Exception as e:
                print(f"⚠️ خطا در بارگذاری {fname}: {e}")
                continue

            sid = scen.get("scenario_id", "")
            if not sid:
                continue

            choices = {
                c.get("id"): c.get("text_fa", c.get("text", ""))
                for c in scen.get("choices", [])
            }

            _SCENARIO_MAP[sid] = {
                "phase": PHASE_DAYS.get(phase_num, ""),
                "phase_num": int(phase_num),
                "title": scen.get("title_fa", sid),
                "choices": choices,
            }

    print(f"✓ دفترچه: {len(_SCENARIO_MAP)} سناریو ایندکس شد")
    return _SCENARIO_MAP


def _load_reflections() -> dict:
    """بارگذاری بازتاب‌های بی‌طرف از فایل JSON"""
    global _REFLECTIONS_CACHE
    if _REFLECTIONS_CACHE:
        return _REFLECTIONS_CACHE

    if not os.path.exists(REFLECTIONS_PATH):
        print(
            f"⚠️ فایل بازتاب‌ها یافت نشد: {REFLECTIONS_PATH}"
        )
        _REFLECTIONS_CACHE = {}
        return _REFLECTIONS_CACHE

    try:
        with open(REFLECTIONS_PATH, "r", encoding="utf-8") as f:
            raw = json.load(f)
        # حذف کلید _readme که توضیحی است
        raw.pop("_readme", None)
        _REFLECTIONS_CACHE = raw
        print(
            f"✓ دفترچه: {len(_REFLECTIONS_CACHE)} سناریو "
            "بازتاب دارد"
        )
    except Exception as e:
        print(f"⚠️ خطا در بارگذاری بازتاب‌ها: {e}")
        _REFLECTIONS_CACHE = {}

    return _REFLECTIONS_CACHE


def get_mission_log_entries(data_logger) -> list:
    """
    ساخت لیست ورودی‌های دفترچه.

    Returns:
        لیست دیکشنری‌هایی با کلیدهای:
            - phase: برچسب روز
            - phase_num: شماره‌ی فاز
            - title: عنوان سناریو
            - choice_text: متن انتخاب بازیکن
            - reflection: بازتاب بی‌طرف (یا رشته‌ی خالی)
    """
    scenario_map = _build_scenario_map()
    reflections = _load_reflections()
    entries: list = []

    for scenario_id, choice_id in data_logger.choice_memory.items():
        # رد کردن پرچم‌های داخلی (که با _ شروع می‌شوند)
        if scenario_id.startswith("_"):
            continue

        info = scenario_map.get(scenario_id)
        if not info:
            continue

        choice_text = info["choices"].get(choice_id, "")
        if not choice_text:
            continue

        # ✅ بازتاب بی‌طرف — اگر موجود باشد
        reflection = ""
        refl_block = reflections.get(scenario_id, {})
        if isinstance(refl_block, dict):
            reflection = refl_block.get(str(choice_id), "")

        entries.append({
            "phase": info["phase"],
            "phase_num": info["phase_num"],
            "title": info["title"],
            "choice_text": choice_text,
            "reflection": reflection,
        })

    return entries