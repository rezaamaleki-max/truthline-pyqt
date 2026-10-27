"""
تنظیمات ثابت پروژه Truthline (نسخه PyQt6)
"""
import os

# ==========================================
# مسیرهای پایه پروژه
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
DATA_DIR = os.path.join(BASE_DIR, "data")
SCENARIOS_DIR = os.path.join(DATA_DIR, "scenarios")

# ==========================================
# تنظیمات نمایش پنجره
# ==========================================
# اندازه اولیه پنجره
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720

# ✅ حداقل اندازه قابل تغییر (برای جلوگیری از کوچک شدن بیش از حد)
MIN_WINDOW_WIDTH = 800
MIN_WINDOW_HEIGHT = 600

# ✅ حداکثر اندازه قابل تغییر (برای مانیتورهای بزرگ)
MAX_WINDOW_WIDTH = 1920
MAX_WINDOW_HEIGHT = 1080

# عنوان پنجره
TITLE = "Truthline: Crisis at Caspian Station"

# ==========================================
# پالت رنگی (فرمت HEX برای PyQt6)
# ==========================================
COLORS = {
    "deep_blue": "#0B1D3A",
    "steel_blue": "#2B4A6F",
    "cyan": "#4FC3F7",
    "white": "#FFFFFF",
    "amber": "#FF8F00",
    "red": "#D32F2F",
    "dark_bg": "#212121",
    "black": "#000000",
}

# ==========================================
# تنظیمات فونت و پایگاه داده
# ==========================================
FONT_PATH = os.path.join(ASSETS_DIR, "fonts", "Vazirmatn-Regular.ttf")
DB_PATH = os.path.join(DATA_DIR, "participants.db")

# ==========================================
# تنظیمات ثبت داده (Logging)
# ==========================================
LOGGING_ENABLED = True
LOG_LEVEL = "INFO"

# ==========================================
# تم بصری اختصاصی هر فاز (فضاسازی داستانی)
# ==========================================
# در پایان فایل config.py اضافه کنید:

PHASE_THEMES = {
    1: {
        # روز اول — سرد، بالینی، اتاق کنترل
        "bg_gradient": (
            "qlineargradient(x1:0, y1:0, x2:0.3, y2:1, "
            "stop:0 #0B1D3A, stop:1 #152A45)"
        ),
        "accent": "#4FC3F7",
        "accent_soft": "rgba(79, 195, 247, 0.10)",
        "phase_name": "صداقت و یکپارچگی",
        "phase_color_hud": "#4FC3F7",
    },
    2: {
        # روز دوم — گرم، اضطراری، راهروی قرنطینه
        "bg_gradient": (
            "qlineargradient(x1:0, y1:0, x2:0.3, y2:1, "
            "stop:0 #1A1220, stop:1 #2A1510)"
        ),
        "accent": "#FF8F00",
        "accent_soft": "rgba(255, 143, 0, 0.10)",
        "phase_name": "قابلیت اعتماد",
        "phase_color_hud": "#FF8F00",
    },
    3: {
        # روز سوم — بنفش، تحلیلی، اتاق داده
        "bg_gradient": (
            "qlineargradient(x1:0, y1:0, x2:0.3, y2:1, "
            "stop:0 #150B1D, stop:1 #221535)"
        ),
        "accent": "#9C27B0",
        "accent_soft": "rgba(156, 39, 176, 0.10)",
        "phase_name": "حل مسئله",
        "phase_color_hud": "#9C27B0",
    },
    4: {
        # روز چهارم — قرمز تیره، تشریفاتی، سالن شورا
        "bg_gradient": (
            "qlineargradient(x1:0, y1:0, x2:0.3, y2:1, "
            "stop:0 #1A0B0B, stop:1 #2A1015)"
        ),
        "accent": "#D32F2F",
        "accent_soft": "rgba(211, 47, 47, 0.10)",
        "phase_name": "مسئولیت‌پذیری",
        "phase_color_hud": "#D32F2F",
    },
}

# ==========================================
# فلگ کنترلی: نمایش نقشه‌ی تصمیم در HUD
# ==========================================
# اگر False شود، دایره‌های تصمیم در HUD نمایش داده نمی‌شوند
# (برای جلوگیری از اثر یادگیری در مطالعه‌ی نهایی)
SHOW_DECISION_TRAIL = True

# ==========================================
# فلگ کنترلی: نمایش Toastها به بازیکن
# ==========================================
# در مطالعه‌ی نهایی که نباید هیچ بازخورد فوری داده شود، False کنید
SHOW_TOASTS = True