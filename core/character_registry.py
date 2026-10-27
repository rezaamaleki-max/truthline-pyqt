"""
فرهنگ شخصیت‌های بازی Truthline

- نگاشت نام گوینده به کلید یکتا، رنگ، حرف اول
- تشخیص خودکار احساس از متن دیالوگ
- حل مسیر پرتره (اگر تصویر موجود باشد)

نسخه: 1.1.0 (افزودن احساسات جدید)
"""
import os
from typing import Optional

from config import ASSETS_DIR


# ============================================================
# تعریف شخصیت‌ها
# ============================================================
CHARACTERS = {
    "راوی": {
        "key": "narrator",
        "name_fa": "راوی",
        "color": "#B0BEC5",
        "initial": "ن",
        "portrait_dir": None,
    },
    "مهندس رحیمی": {
        "key": "rahimi",
        "name_fa": "مهندس رحیمی",
        "color": "#4FC3F7",
        "initial": "ر",
        "portrait_dir": "rahimi",
    },
    "دکتر آرتمیس": {
        "key": "artemis",
        "name_fa": "دکتر آرتمیس",
        "color": "#9C27B0",
        "initial": "آ",
        "portrait_dir": "artemis",
    },
    "لی": {
        "key": "lee",
        "name_fa": "لی",
        "color": "#4CAF50",
        "initial": "ل",
        "portrait_dir": "lee",
    },
    "سیستم": {
        "key": "os_caspian",
        "name_fa": "OS-CASPIAN",
        "color": "#4FC3F7",
        "initial": "◈",
        "portrait_dir": "os_caspian",
    },
    "فرزین": {
        "key": "farzin",
        "name_fa": "فرزین",
        "color": "#FF8F00",
        "initial": "ف",
        "portrait_dir": "farzin",
    },
    "فرزین (تکنسین فنی)": {
        "key": "farzin",
        "name_fa": "فرزین",
        "color": "#FF8F00",
        "initial": "ف",
        "portrait_dir": "farzin",
    },
    "جناب آقای پرویز کیانی": {
        "key": "council_chair",
        "name_fa": "پرویز کیانی",
        "color": "#FFD700",
        "initial": "پ",
        "portrait_dir": "council_chair",
    },
    "دکتر فربد مهرانی": {
        "key": "council_science",
        "name_fa": "دکتر مهرانی",
        "color": "#FFD700",
        "initial": "م",
        "portrait_dir": "council_science",
    },
    "خانم سارا آذری": {
        "key": "council_ethics",
        "name_fa": "سارا آذری",
        "color": "#FFD700",
        "initial": "س",
        "portrait_dir": "council_ethics",
    },
    "کارمند اداری": {
        "key": "clerk",
        "name_fa": "کارمند اداری",
        "color": "#90A4AE",
        "initial": "ک",
        "portrait_dir": None,
    },
    "تکنسین جانشین": {
        "key": "tech_deputy",
        "name_fa": "تکنسین جانشین",
        "color": "#90A4AE",
        "initial": "ت",
        "portrait_dir": None,
    },
    "افسر ارتباطات": {
        "key": "comm_officer",
        "name_fa": "افسر ارتباطات",
        "color": "#90A4AE",
        "initial": "ا",
        "portrait_dir": None,
    },
}


# ============================================================
# تشخیص احساس از متن — نسخه گسترش‌یافته
# ترتیب مهم است: از شدیدترین/خاص‌ترین به عمومی‌ترین
# ============================================================
EMOTION_KEYWORDS = [
    # 1. وضعیت‌های بحرانی
    ("stress",    ["وحشت", "فاجعه", "فرار", "دستپاچه",
                   "با وحشت", "نگرانی شدید", "با استرس",
                   "رگولاتور اصلی داره می‌سوزه",
                   "صدای خش‌دار"]),
    ("anger",     ["خشم", "با لحن سرد", "با لحن تند", "عصبان",
                   "با عصبانیت", "خشمگین"]),
    ("cold",      ["با لحن خشک", "با لحن رسمی", "با لحن سرد",
                   "خشک و بی‌احساس", "با لحن محکم"]),
    ("flustered", ["رنگ می‌پراند", "دستپاچه", "گیج شد",
                   "جا خورد"]),
    ("satisfied", ["با رضایت", "با خرسندی", "رضایت‌بخش",
                   "با لبخند کم‌رنگ"]),
    ("urgent",    ["فوری", "سریع", "باید همین الان",
                   "اضطرار", "با عجله", "زود باش"]),

    # 2. واکنش‌های احساسی
    ("surprised", ["متعجب", "شوکه", "غافلگیر", "با تعجب",
                   "چی؟", "باورم نمی‌شه"]),
    ("sad",       ["متأسف", "افسوس", "متأسفانه", "دلگیر",
                   "با ناراحتی"]),
    ("worried",   ["دلواپس", "خیلی نگرانم", "بیمناک"]),
    ("concern",   ["نگران", "هشدار", "خطرناک", "مشکل",
                   "با نگرانی", "احتیاط"]),

    # 3. حالت‌های فکری
    ("thinking",  ["فکر می‌کنم", "بررسی", "تحلیل", "شاید",
                   "به نظرم", "باید ببینم"]),
    ("attentive", ["گوش می‌دم", "دقت می‌کنم", "متوجهم"]),
    ("serious",   ["جدی", "رسمی", "قاطع", "با صدای جدی",
                   "با لحن جدی"]),

    # 4. حالت‌های مثبت (آخر، چون ممکن است اشتباه match شوند)
    ("grateful",  ["ممنون", "سپاسگزار", "لطف کردی",
                   "قدرت رو می‌دونم"]),
    ("relief",    ["آسودگی", "خوب شد", "راحت شدم",
                   "با آسودگی", "خدا رو شکر"]),
    ("warm",      ["خوش آمد", "با لبخند", "خوشحال",
                   "با احترام", "صمیمانه"]),
]


# ============================================================
# زنجیره‌ی fallback احساسات
# وقتی تصویرِ احساسِ دقیق وجود ندارد، به ترتیب این‌ها را امتحان کن
# مثال: "satisfied" → اگر نبود → "warm" → اگر نبود → "neutral"
# ============================================================
EMOTION_FALLBACK_CHAIN = {
    # احساسات مثبت
    "warm":      ["warm", "neutral"],
    "satisfied": ["satisfied", "warm", "neutral"],
    "grateful":  ["grateful", "warm", "neutral"],
    "relief":    ["relief", "warm", "neutral"],

    # احساسات منفی ملایم
    "concern":   ["concern", "neutral"],
    "worried":   ["worried", "concern", "neutral"],
    "sad":       ["sad", "concern", "neutral"],

    # احساسات منفی شدید
    "stress":    ["stress", "concern", "neutral"],
    "anger":     ["anger", "stress", "concern", "neutral"],
    "urgent":    ["urgent", "stress", "neutral"],
    "flustered": ["flustered", "stress", "neutral"],

    # احساسات فکری و جدی
    "cold":      ["cold", "concern", "neutral"],
    "serious":   ["serious", "cold", "concern", "neutral"],
    "thinking":  ["thinking", "neutral"],
    "attentive": ["attentive", "neutral"],

    # سایر
    "surprised": ["surprised", "stress", "neutral"],
    "neutral":   ["neutral"],
}


def detect_emotion(text: str) -> str:
    """تشخیص احساس از متن دیالوگ (بر پایه کلواژه)"""
    if not text:
        return "neutral"
    for emotion, keywords in EMOTION_KEYWORDS:
        for kw in keywords:
            if kw in text:
                return emotion
    return "neutral"


# ============================================================
# API عمومی
# ============================================================
def get_character(speaker_name: str) -> dict:
    """دریافت اطلاعات شخصیت بر اساس نام گوینده"""
    if not speaker_name:
        return _default_character("نامشخص")
    if speaker_name in CHARACTERS:
        return CHARACTERS[speaker_name]
    for known_name, char in CHARACTERS.items():
        if known_name in speaker_name or speaker_name in known_name:
            return char
    return _default_character(speaker_name)


def _default_character(name: str) -> dict:
    """شخصیت پیش‌فرض برای گوینده‌های ناشناخته"""
    return {
        "key": "unknown",
        "name_fa": name,
        "color": "#607D8B",
        "initial": name[0] if name else "؟",
        "portrait_dir": None,
    }


def get_character_by_key(key: str) -> dict | None:
    """
    دریافت شخصیت بر اساس کلید یکتا (مثل 'council_chair').
    Returns: dict یا None اگر پیدا نشد.
    """
    if not key:
        return None
    for char in CHARACTERS.values():
        if char.get("key") == key:
            return char
    return None


def resolve_portrait_path(character: dict,
                           emotion: str) -> Optional[str]:
    """
    تلاش برای یافتن مسیر تصویر پرتره واقعی.
    الگو: assets/characters/{dir}/portraits/{dir}_{emotion}_v01.{ext}

    منطق: اول از زنجیره‌ی fallback احساسات استفاده می‌کند.
    مثال: "satisfied" → "warm" → "neutral"
    """
    pdir = character.get("portrait_dir")
    if not pdir:
        return None

    # ✅ فرمت‌های پشتیبانی‌شده
    extensions = ["png", "jpg", "jpeg"]

    # ✅ استفاده از زنجیره‌ی fallback — نه فقط [emotion, neutral]
    emotion_chain = EMOTION_FALLBACK_CHAIN.get(
        emotion, [emotion, "neutral"]
    )

    # حذف تکراری‌ها با حفظ ترتیب
    seen: set = set()
    unique_chain: list = []
    for emo in emotion_chain:
        if emo not in seen:
            seen.add(emo)
            unique_chain.append(emo)

    base = os.path.join(ASSETS_DIR, "characters", pdir, "portraits")

    for emo in unique_chain:
        for ext in extensions:
            fname = f"{pdir}_{emo}_v01.{ext}"
            path = os.path.join(base, fname)
            if os.path.exists(path):
                return path

    # ✅ جستجوی آخرین راه: هر فایل png/jpg که با نام پوشه شروع شود
    if os.path.isdir(base):
        try:
            for fname in sorted(os.listdir(base)):
                lower = fname.lower()
                if lower.startswith(pdir.lower() + "_"):
                    if lower.endswith((".png", ".jpg", ".jpeg")):
                        return os.path.join(base, fname)
        except Exception:
            pass

    return None


def resolve_portrait_auto(speaker_name: str, text: str):
    """
    یکپارچه: از speaker + text، پرتره و احساس را استخراج می‌کند.
    Returns: (character_dict, emotion, portrait_path_or_None)
    """
    char = get_character(speaker_name)
    emotion = detect_emotion(text)
    path = resolve_portrait_path(char, emotion)
    return char, emotion, path