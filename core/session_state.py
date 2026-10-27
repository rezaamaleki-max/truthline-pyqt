"""
مدیریت ذخیره‌ی خودکار جلسه
===========================
- ذخیره‌ی وضعیت در فایل JSON
- بازیابی در شروع بعدی
- فقط در حالت Full و Short فعال است

نسخه: 1.1.0
  - رفع باگ: has_saved_session اکنون session‌های خالی را
    نادیده می‌گیرد تا دکمه‌ی «ادامه» اشتباهاً ظاهر نشود.
  - افزودن ذخیره و بازیابی random_seed (بازتولیدپذیری).
"""
import os
import json
import time

from config import DATA_DIR
from core.app_config import is_theater_mode

SESSION_PATH = os.path.join(DATA_DIR, "session_state.json")

SCHEMA_VERSION = 1


def _empty_state() -> dict:
    return {
        "version": SCHEMA_VERSION,
        "saved_at": 0.0,
        "participant_id": "",
        "current_scene": "",
        "current_scenario_indices": {},
        "flags": {
            "council_prep_shown": False,
            "letter_shown": False,
            "nights_completed": [],
            "phases_completed": [],
        },
        "relationships": {
            "li": 0,
            "rahimi": 0,
            "artemis": 0,
        },
        "choice_memory": {},
        "random_seed": 0,
    }


# ============================================================
# ذخیره
# ============================================================
def save_state(
    participant_id: str,
    current_scene: str,
    scenario_indices: dict,
    flags: dict,
    relationships: dict,
    choice_memory: dict,
    random_seed: int = 0,
):
    """
    ذخیره‌ی وضعیت فعلی بازی.
    در حالت Theater هیچ چیزی ذخیره نمی‌شود.
    """
    if is_theater_mode():
        return

    state = {
        "version": SCHEMA_VERSION,
        "saved_at": time.time(),
        "participant_id": participant_id,
        "current_scene": current_scene,
        "current_scenario_indices": dict(scenario_indices),
        "flags": dict(flags),
        "relationships": dict(relationships),
        "choice_memory": dict(choice_memory),
        "random_seed": int(random_seed),
    }

    try:
        with open(SESSION_PATH, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ خطا در ذخیره‌ی session: {e}")


# ============================================================
# بازیابی
# ============================================================
def load_state() -> dict | None:
    """بارگذاری وضعیت — None اگر وجود نداشت یا نامعتبر بود"""
    if is_theater_mode():
        return None
    if not os.path.exists(SESSION_PATH):
        return None

    try:
        with open(SESSION_PATH, "r", encoding="utf-8") as f:
            state = json.load(f)
        if state.get("version") != SCHEMA_VERSION:
            print(
                f"⚠️ نسخه‌ی session قدیمی است — نادیده گرفته می‌شود"
            )
            return None
        return state
    except Exception as e:
        print(f"⚠️ خطا در بارگذاری session: {e}")
        return None


def has_saved_session() -> bool:
    """
    آیا جلسه‌ی ذخیره‌شده‌ی معناداری وجود دارد؟

    جلسه‌ی خالی (بدون هیچ تصمیم ثبت‌شده) به‌عنوان «موجود» در نظر
    گرفته نمی‌شود تا دکمه‌ی «ادامه» اشتباهاً ظاهر نشود.
    """
    state = load_state()
    if state is None:
        return False

    # ✅ اگر هیچ تصمیمی در choice_memory ثبت نشده، session
    #    معنادار نیست (بازیکن هنوز بازی واقعی را شروع نکرده)
    choice_memory = state.get("choice_memory", {}) or {}
    if not choice_memory:
        return False

    # ✅ اگر صحنه‌ی جاری در مرحله‌ی پیش از بازی است، معنادار نیست
    current_scene = state.get("current_scene", "")
    non_meaningful_scenes = {
        "", "menu", "settings", "splash",
        "demographic", "intro",
    }
    if current_scene in non_meaningful_scenes:
        return False

    return True


def clear_state():
    """پاک کردن وضعیت ذخیره‌شده"""
    if os.path.exists(SESSION_PATH):
        try:
            os.remove(SESSION_PATH)
            print("✓ session ذخیره‌شده پاک شد")
        except Exception as e:
            print(f"⚠️ خطا در پاک کردن session: {e}")