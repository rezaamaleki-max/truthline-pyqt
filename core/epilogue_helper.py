"""
پایان روایی بازی — Epilogue Helper
====================================
منطق پایان بازی بر اساس:
  - روابط با سه شخصیت (li, rahimi, artemis)
  - تصمیم‌های کلیدی در طول مأموریت (choice_memory)

هیچ نمره‌ای در این فایل تولید نمی‌شود — کاملاً لایه‌ی روایی.

نسخه: 1.0.0
"""

# ============================================================
# سطوح پایان روایی
# ============================================================
# آستانه‌ها بر اساس مجموع روابط سه شخصیت (-9 تا +9)
TIERS = [
    {
        "min": 6, "max": 100,
        "code": "belonging",
        "subtitle": "بازگشت",
        "video_path": "interlude_epilogue.png",
    },
    {
        "min": 2, "max": 5,
        "code": "warm_farewell",
        "subtitle": "بدرقه‌ی گرم",
        "video_path": "interlude_epilogue.png",
    },
    {
        "min": -1, "max": 1,
        "code": "neutral",
        "subtitle": "بازنگری",
        "video_path": "interlude_epilogue.png",
    },
    {
        "min": -5, "max": -2,
        "code": "cold_exit",
        "subtitle": "فاصله",
        "video_path": "interlude_epilogue.png",
    },
    {
        "min": -100, "max": -6,
        "code": "exile",
        "subtitle": "خروج",
        "video_path": "interlude_epilogue.png",
    },
]


# ============================================================
# پیام‌های ویژه بر اساس تصمیم‌های کلیدی
# کلید: (scenario_id, choice_id) → {character: text_addon}
# این متن‌ها به پیام اصلی هر شخصیت اضافه می‌شوند
# ============================================================
DECISION_CALLBACKS = {
    # MC-01: واکنش به ماژول حافظه‌ی لی
    ("MC-01", 1): {  # گزارش رسمی
        "li": (
            "لی هنوز گزارش رسمی را فراموش نکرده، ولی "
            "احترامش به انصاف تو را حفظ کرده."
        ),
    },
    ("MC-01", 2): {  # تذکر دوستانه
        "li": (
            "لی همیشه به یاد دارد که تو اولین کسی بودی "
            "که به او فرصت دادی."
        ),
    },
    ("MC-01", 3): {  # چشم‌پوشی
        "li": (
            "لی می‌داند تو از کنار خطایش گذشتی — و این "
            "او را مدیون تو کرده."
        ),
    },

    # TR-01: واکنش به نقص عایق
    ("TR-01", 1): {  # گزارش مستقیم
        "rahimi": (
            "مهندس رحیمی هنوز از این‌که بدون هماهنگی با او "
            "گزارش دادی دلگیر است."
        ),
    },
    ("TR-01", 2): {  # هماهنگی اول
        "rahimi": (
            "مهندس رحیمی از این‌که اول با او مشورت کردی، "
            "احساس اعتماد می‌کند."
        ),
    },
    ("TR-01", 3): {  # سکوت
        "rahimi": (
            "مهندس رحیمی هنوز نفهمیده که تو نقص را دیده "
            "بودی — و همین او را آسوده نگه داشته."
        ),
    },

    # AC-02: اعتراف در برابر شورا
    ("AC-02", 1): {  # اعتراف کامل
        "artemis": (
            "دکتر آرتمیس برای صداقت تو در برابر شورا، "
            "احترام عمیقی قائل است."
        ),
    },
    ("AC-02", 2): {  # اطلاع نداشتن
        "artemis": (
            "دکتر آرتمیس به یاد دارد که چطور در برابر شورا "
            "از پذیرش مسئولیت طفره رفتی."
        ),
    },
    ("AC-02", 3): {  # نقص ساختاری
        "artemis": (
            "دکتر آرتمیس دید که چگونه مسئولیت را به ساختار "
            "منتقل کردی — و این او را نگران کرد."
        ),
    },
}


# ============================================================
# پیام‌های پایه هر شخصیت بر اساس سطح پایان
# ============================================================
BASE_MESSAGES = {
    "belonging": {
        "li": (
            "لی نوشته: «اگه یه روزی برگشتی، من اولین کسی "
            "هستم که بهت سلام می‌کنه.»"
        ),
        "rahimi": (
            "مهندس رحیمی نوشته: «تو متعلق به این ایستگاهی. "
            "این‌جا همیشه جای تو خالیه.»"
        ),
        "artemis": (
            "دکتر آرتمیس نوشته: «روش تحلیل تو رو توی دفترچه‌ی "
            "خودم یادداشت کردم.»"
        ),
        "narrator_close": (
            "شاتل از سکوی پرتاب جدا می‌شود. پشت سرت، "
            "ایستگاه کاسپین مثل یک نقطه‌ی نور گرم در سیاهی "
            "فضا می‌تابد."
        ),
    },
    "warm_farewell": {
        "li": (
            "لی نوشته: «بعضی روزها دلم برات تنگ می‌شه، "
            "ولی می‌دونم که جای دیگه‌ای منتظرته.»"
        ),
        "rahimi": (
            "مهندس رحیمی نوشته: «ایستگاه با تو یه فصل "
            "دیگه‌ای داشت.»"
        ),
        "artemis": (
            "دکتر آرتمیس نوشته: «وقتی برگشتی، یک نسخه از "
            "داده‌های خام تو رو نگه داشتم.»"
        ),
        "narrator_close": (
            "شاتل از سکوی پرتاب جدا می‌شود. سه ماه کار "
            "در کنار سه انسان، به یک خاطره بدل می‌شود."
        ),
    },
    "neutral": {
        "li": (
            "لی نوشته: «بعضی وقتا فکر می‌کنم می‌شد بهتر "
            "باشیم، ولی باز هم ممنونم.»"
        ),
        "rahimi": (
            "مهندس رحیمی نوشته: «تجربه‌ی این چند روز، "
            "تجربه‌ی هر دوی ماست.»"
        ),
        "artemis": (
            "دکتر آرتمیس نوشته: «تحلیلت جای بحث داشت، ولی "
            "هیچ‌وقت متوقف نشد.»"
        ),
        "narrator_close": (
            "شاتل از سکوی پرتاب جدا می‌شود. ایستگاه پشت "
            "سرت به یک رقم در لاگ تبدیل می‌شود."
        ),
    },
    "cold_exit": {
        "li": (
            "لی نوشته: «کاش فرصت بیشتری داشتیم که همدیگه "
            "رو بهتر بشناسیم.»"
        ),
        "rahimi": (
            "مهندس رحیمی پیامی کوتاه فرستاده: «موفق باشی.»"
        ),
        "artemis": (
            "دکتر آرتمیس پیامی نفرستاده."
        ),
        "narrator_close": (
            "شاتل از سکوی پرتاب جدا می‌شود. سه ماه کار، "
            "بدون یک خاطره‌ی گرم."
        ),
    },
    "exile": {
        "li": (
            "لی نوشته: «امیدوارم دفعه‌ی بعد، توی یه تیم "
            "دیگه باشیم.»"
        ),
        "rahimi": (
            "مهندس رحیمی نوشته: «پرونده‌ات کامل است.»"
        ),
        "artemis": (
            "دکتر آرتمیس پیامی نفرستاده."
        ),
        "narrator_close": (
            "شاتل از سکوی پرتاب جدا می‌شود. ایستگاه کاسپین "
            "دیگر خانه‌ی تو نیست."
        ),
    },
}


# ============================================================
# توابع کمکی
# ============================================================
def _find_tier(total: int) -> dict:
    """یافتن سطح پایان بر اساس مجموع روابط"""
    for tier in TIERS:
        if tier["min"] <= total <= tier["max"]:
            return tier
    # fallback
    return TIERS[2]  # neutral


def _collect_callbacks(data_logger) -> dict:
    """
    جمع‌آوری متن‌های ویژه از تصمیم‌های کلیدی.
    Returns: {character: [text1, text2, ...]}
    """
    callbacks: dict = {"li": [], "rahimi": [], "artemis": []}
    for (scenario_id, choice_id), addons in DECISION_CALLBACKS.items():
        actual = data_logger.recall_choice(scenario_id)
        if actual == choice_id:
            for char, text in addons.items():
                if char in callbacks:
                    callbacks[char].append(text)
    return callbacks


# ============================================================
# API عمومی
# ============================================================
def compute_epilogue(data_logger) -> dict:
    """
    محاسبه‌ی پایان روایی بازی.

    Args:
        data_logger: نمونه‌ی DataLogger (برای دسترسی به روابط و
                     حافظه‌ی تصمیم‌ها)

    Returns:
        {
            "code": str,            # کد انگلیسی سطح
            "subtitle": str,        # زیرعنوان فارسی
            "video_path": str,      # نام تصویر/ویدیوی میان‌پرده
            "relationships": dict,  # {li, rahimi, artemis}
            "total": int,           # مجموع روابط
            "dialogues": list,      # لیست دیالوگ‌های آماده
        }
    """
    li_r = data_logger.get_relationship("li")
    rahimi_r = data_logger.get_relationship("rahimi")
    artemis_r = data_logger.get_relationship("artemis")
    total = li_r + rahimi_r + artemis_r

    tier = _find_tier(total)
    code = tier["code"]
    subtitle = tier["subtitle"]
    video_path = tier["video_path"]

    base = BASE_MESSAGES.get(code, BASE_MESSAGES["neutral"])
    callbacks = _collect_callbacks(data_logger)

    # ---- ساخت پیام هر شخصیت ----
    li_msg = base["li"]
    rahimi_msg = base["rahimi"]
    artemis_msg = base["artemis"]

    if callbacks["li"]:
        li_msg += "\n" + "\n".join(callbacks["li"])
    if callbacks["rahimi"]:
        rahimi_msg += "\n" + "\n".join(callbacks["rahimi"])
    if callbacks["artemis"]:
        artemis_msg += "\n" + "\n".join(callbacks["artemis"])

    # ---- ساخت دیالوگ‌ها ----
    dialogues = [
        {
            "speaker": "راوی",
            "text": (
                "شاتل بازگشت به مدار زمین نزدیک می‌شود. "
                "سه ماه بعد از آن چهار روز."
            ),
        },
        {"speaker": "راوی", "text": li_msg},
        {"speaker": "راوی", "text": rahimi_msg},
        {"speaker": "راوی", "text": artemis_msg},
        {
            "speaker": "راوی",
            "text": base["narrator_close"],
        },
    ]

    return {
        "code": code,
        "subtitle": subtitle,
        "video_path": video_path,
        "relationships": {
            "li": li_r,
            "rahimi": rahimi_r,
            "artemis": artemis_r,
        },
        "total": total,
        "dialogues": dialogues,
    }