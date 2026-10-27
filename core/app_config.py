"""
مدیریت تنظیمات سراسری برنامه
ذخیره‌سازی در data/app_config.json
"""
import os
import json
from typing import Optional

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(PROJECT_ROOT, "data", "app_config.json")

# ============================================================
# پیش‌فرض‌ها — همه چیز روشن
# ============================================================
DEFAULT_CONFIG = {
    "mode": "full",
    "fast_mode": False,  # ✅ حالت سریع (بدون انیمیشن)
    "sections": {
        "prologue": True,
        "interludes_extended": True,
        "nights": True,
        "flashbacks": True,
        "multilayer_memory": True,
        "council_prep": True,
        "council_outro": True,
        "epilogue": True,
        "letter_to_self": True,
    },
    "phases": {
        "phase1": True,
        "phase2": True,
        "phase3": True,
        "phase4": True,
        "hexaco": True,
    },
    "audio": {
        "enabled": True,
        "volume": 0.4,
    },
    "auto_resume": True,
    "inner_dialogue": "off",
    "accessibility": {
        "large_fonts": False,
        "high_contrast": False,
        "reduce_motion": False,
    },
}

# پیش‌تنظیم حالت «استخدام»
PRESET_SHORT = {
    "mode": "short",
    "fast_mode": True,
    "sections": {
        "prologue": False,
        "interludes_extended": False,
        "nights": False,
        "flashbacks": False,
        "multilayer_memory": False,
        "council_prep": False,
        "council_outro": False,
        "epilogue": True,
        "letter_to_self": False,
    },
    "phases": {
        "phase1": True,
        "phase2": True,
        "phase3": True,
        "phase4": True,
        "hexaco": True,
    },
    "audio": {
        "enabled": True,
        "volume": 0.4,
    },
    "auto_resume": True,
    # ✅ افزودن تنظیم دیالوگ درونی به حالت سریع
    "inner_dialogue": "on", # یا "on" اگر می‌خواهید همیشه باشد
}

PRESET_FULL = dict(DEFAULT_CONFIG)

# پیش‌تنظیم حالت نمایش (برای جذب و مصاحبه)
PRESET_THEATER = {
    "mode": "theater",
    "sections": {
        "prologue": True,
        "interludes_extended": True,
        "nights": False,
        "flashbacks": False,
        "multilayer_memory": False,
        "council_prep": False,
        "council_outro": False,
        "epilogue": False,
        "letter_to_self": False,
    },
    "phases": {
        "phase1": True,
        "phase2": True,
        "phase3": True,
        "phase4": True,
        "hexaco": False,
    },
    "audio": {
        "enabled": True,
        "volume": 0.4,
    },
    "auto_resume": False,
}


# ============================================================
# Cache
# ============================================================
_config_cache: Optional[dict] = None


def _deep_merge(base: dict, override: dict) -> dict:
    """ادغام ساده‌ی دو دیکشنری تودرتو"""
    result = dict(base)
    for key, value in override.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config() -> dict:
    """بارگذاری تنظیمات — از فایل اگر باشد، وگرنه پیش‌فرض"""
    global _config_cache
    if _config_cache is not None:
        return _config_cache

    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                user_cfg = json.load(f)
            _config_cache = _deep_merge(DEFAULT_CONFIG, user_cfg)
        except Exception as e:
            print(f"⚠️ خطا در بارگذاری app_config: {e}")
            _config_cache = dict(DEFAULT_CONFIG)
    else:
        _config_cache = dict(DEFAULT_CONFIG)

    return _config_cache


def save_config(cfg: dict):
    """ذخیره‌ی تنظیمات در فایل"""
    global _config_cache
    _config_cache = cfg
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    print(f"✓ تنظیمات ذخیره شد: {CONFIG_PATH}")


def apply_preset(preset_name: str):
    """اعمال یکی از پیش‌تنظیم‌ها"""
    if preset_name == "full":
        save_config(dict(PRESET_FULL))
    elif preset_name == "short":
        save_config(dict(PRESET_SHORT))
    elif preset_name == "theater":
        save_config(dict(PRESET_THEATER))
    else:
        print(f"⚠️ پیش‌تنظیم ناشناخته: {preset_name}")


# ============================================================
# توابع کمکی — این‌ها در سراسر برنامه صدا زده می‌شوند
# ============================================================
def is_section_enabled(section_name: str) -> bool:
    """آیا یک بخش روایی فعال است؟"""
    cfg = load_config()
    return cfg.get("sections", {}).get(section_name, True)


# ============================================================
# ابزارهای ارزیابی — HEXACO، CRT، SD3 و ...
# ============================================================
ASSESSMENT_TOOL_NAMES = {
    "hexaco": "HEXACO-24 (شخصیت)",
    "crt": "CRT7 (تأمل شناختی)",
    "tower_of_hanoi": "برج هانوی (برنامه‌ریزی)",
    "sd3": "SD3 (مثلث تاریک)",
    "social_desirability": "SD (مطلوبیت اجتماعی)",
    "postgame_feedback": "بازخورد پس از بازی",
    "sme_review": "ارزیابی متخصصان (SME)",
}


def is_assessment_tool_enabled(tool_name: str) -> bool:
    """آیا یک ابزار ارزیابی فعال است؟"""
    cfg = load_config()
    return cfg.get("assessment_tools", {}).get(
        tool_name, True
    )


def set_assessment_tool_enabled(tool_name: str, enabled: bool):
    """فعال/غیرفعال کردن یک ابزار ارزیابی"""
    cfg = load_config()
    if "assessment_tools" not in cfg:
        cfg["assessment_tools"] = {}
    cfg["assessment_tools"][tool_name] = bool(enabled)
    save_config(cfg)


def get_enabled_assessment_tools() -> list:
    """لیست ابزارهای فعال"""
    cfg = load_config()
    tools = cfg.get("assessment_tools", {})
    return [k for k, v in tools.items() if v]


def is_phase_enabled(phase_name: str) -> bool:
    """آیا یک فاز فعال است؟"""
    cfg = load_config()
    return cfg.get("phases", {}).get(phase_name, True)


def next_enabled_phase_after(phase_name: str) -> Optional[str]:
    """
    فاز بعدی فعال را برمی‌گرداند.
    اگر فاز فعلی، آخرین فاز فعال باشد، None برمی‌گرداند.
    """
    order = ["phase1", "phase2", "phase3", "phase4", "hexaco"]
    if phase_name not in order:
        return None
    idx = order.index(phase_name)
    for candidate in order[idx + 1:]:
        if is_phase_enabled(candidate):
            return candidate
    return None


# ============================================================
# حالت نمایش (Theater Mode)
# ============================================================
def is_theater_mode() -> bool:
    """آیا حالت نمایش فعال است؟"""
    cfg = load_config()
    return cfg.get("mode", "") == "theater"


# لیست سناریوهای منتخب برای هر فاز در حالت نمایش
THEATER_SCENARIOS = {
    "phase1": ["VH-01.json", "MC-01.json"],
    "phase2": ["TR-01.json", "BC-01.json"],
    "phase3": ["MC-02.json", "MR-02.json"],
    "phase4": ["PI-01.json", "AC-02.json"],
}


def theater_scenarios_for_phase(phase_key: str) -> Optional[list]:
    """
    لیست فایل‌های سناریو برای حالت نمایش.
    اگر phase_key نامعتبر باشد یا حالت theater فعال نباشد، None.
    """
    if not is_theater_mode():
        return None
    return THEATER_SCENARIOS.get(phase_key)


# ============================================================
# تنظیمات صدا
# ============================================================
def get_audio_settings() -> dict:
    """دریافت تنظیمات صدا"""
    cfg = load_config()
    audio = cfg.get("audio", {})
    return {
        "enabled": bool(audio.get("enabled", True)),
        "volume": float(audio.get("volume", 0.4)),
    }


def set_audio_settings(enabled: bool, volume: float):
    """ذخیره‌ی تنظیمات صدا"""
    cfg = load_config()
    cfg["audio"] = {
        "enabled": bool(enabled),
        "volume": max(0.0, min(1.0, float(volume))),
    }
    save_config(cfg)


def is_auto_resume_enabled() -> bool:
    """آیا ذخیره‌ی خودکار فعال است؟"""
    cfg = load_config()
    return bool(cfg.get("auto_resume", True))

def set_auto_resume(enabled: bool):
    """روشن/خاموش کردن ذخیره‌ی خودکار"""
    cfg = load_config()
    cfg["auto_resume"] = bool(enabled)
    save_config(cfg)

def get_inner_dialogue_mode() -> str:
    """حالت دیالوگ درونی: off / on / random"""
    cfg = load_config()
    mode = cfg.get("inner_dialogue", "off")
    if mode not in ("off", "on", "random"):
        return "off"
    return mode


def set_inner_dialogue_mode(mode: str):
    """ذخیره‌ی حالت دیالوگ درونی"""
    if mode not in ("off", "on", "random"):
        return
    cfg = load_config()
    cfg["inner_dialogue"] = mode
    save_config(cfg)


def should_use_inner_dialogue(random_seed: int = 0) -> bool:
    """
    آیا از نسخه‌ی با توجیه استفاده شود؟
    - "off" → False
    - "on" → True
    - "random" → بر اساس بذر بازیکن (نیمه‌نیمه)
    """
    mode = get_inner_dialogue_mode()
    if mode == "off":
        return False
    if mode == "on":
        return True
    if mode == "random":
        # ✅ نیمه‌نیمه بر اساس بذر
        return (int(random_seed) % 2) == 0
    return False

def get_accessibility_settings() -> dict:
    """دریافت تنظیمات دسترس‌پذیری"""
    cfg = load_config()
    acc = cfg.get("accessibility", {})
    return {
        "large_fonts": bool(acc.get("large_fonts", False)),
        "high_contrast": bool(acc.get("high_contrast", False)),
        "reduce_motion": bool(acc.get("reduce_motion", False)),
    }


def set_accessibility_settings(large_fonts: bool,
                                high_contrast: bool,
                                reduce_motion: bool):
    """ذخیره‌ی تنظیمات دسترس‌پذیری"""
    cfg = load_config()
    cfg["accessibility"] = {
        "large_fonts": bool(large_fonts),
        "high_contrast": bool(high_contrast),
        "reduce_motion": bool(reduce_motion),
    }
    save_config(cfg)

def get_fast_mode() -> bool:
    """آیا حالت سریع (بدون انیمیشن) فعال است؟"""
    cfg = load_config()
    return bool(cfg.get("fast_mode", False))

def set_fast_mode(enabled: bool):
    """تنظیم حالت سریع"""
    cfg = load_config()
    cfg["fast_mode"] = bool(enabled)
    save_config(cfg)
