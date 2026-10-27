"""
سیستم Typography دوسطحی
=========================
دو سبک نوشتاری:
- "interface": برای رابط کاربری — Vazirmatn Normal، اندازه‌های استاندارد
- "narrative": برای متن‌های روایی مهم — Vazirmatn Light/Medium + فاصله‌ی خطی بیشتر

نسخه: 1.0.0
"""
from PyQt6.QtGui import QFont

FONT_FAMILY = "Vazirmatn"


# ====================================================================
# سبک‌های رابط کاربری
# ====================================================================
def make_title(size: int = 28, bold: bool = True) -> QFont:
    """فونت عنوان صفحه"""
    f = QFont(FONT_FAMILY, size)
    f.setBold(bold)
    f.setWeight(QFont.Weight.Bold if bold else QFont.Weight.Normal)
    return f


def make_body(size: int = 12) -> QFont:
    """فونت متن معمولی"""
    f = QFont(FONT_FAMILY, size)
    f.setWeight(QFont.Weight.Normal)
    return f


def make_caption(size: int = 10) -> QFont:
    """فونت متن فرعی"""
    f = QFont(FONT_FAMILY, size)
    f.setWeight(QFont.Weight.Light)
    return f


# ====================================================================
# سبک‌های روایی (برای دیالوگ‌های مهم)
# ====================================================================
def make_narrative(size: int = 15) -> QFont:
    """
    فونت متن روایی — برای دیالوگ اصلی داستان.
    کم‌وزن‌تر، تا حس «ادبی» بدهد.
    """
    f = QFont(FONT_FAMILY, size)
    f.setWeight(QFont.Weight.Light)
    f.setItalic(False)
    return f


def make_narrative_emphasis(size: int = 15) -> QFont:
    """فونت متن روایی تأکیدی — برای بخش‌های کلیدی"""
    f = QFont(FONT_FAMILY, size)
    f.setWeight(QFont.Weight.Medium)
    return f


# ====================================================================
# سبک‌های خاص
# ====================================================================
def make_speaker_name(size: int = 14) -> QFont:
    """فونت نام گوینده"""
    f = QFont(FONT_FAMILY, size)
    f.setWeight(QFont.Weight.Bold)
    return f


def make_system_message(size: int = 11) -> QFont:
    """فونت پیام سیستم — برای متن‌های مونواسپیس"""
    f = QFont("Consolas", size)
    f.setWeight(QFont.Weight.Normal)
    return f