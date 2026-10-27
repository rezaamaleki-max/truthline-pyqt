"""
افکت‌های بصری مشترک — سایه و درخشش
====================================
توابع کمکی برای اعمال سایه/درخشش روی ویجت‌ها با یک فراخوانی.

نسخه: 1.0.0
"""
from PyQt6.QtWidgets import (
    QGraphicsDropShadowEffect, QWidget
)
from PyQt6.QtGui import QColor


def add_shadow(
    widget: QWidget,
    blur: int = 20,
    offset_x: int = 0,
    offset_y: int = 4,
    color: str = "#000000",
    alpha: int = 100,
) -> QGraphicsDropShadowEffect | None:
    """
    اعمال سایه‌ی نرم روی یک ویجت.

    Args:
        widget: ویجت هدف
        blur: میزان محو شدن سایه
        offset_x / offset_y: جابجایی سایه
        color: رنگ سایه (hex)
        alpha: شفافیت (0 تا 255)

    Returns:
        QGraphicsDropShadowEffect یا None اگر خطا
    """
    try:
        shadow = QGraphicsDropShadowEffect(widget)
        shadow.setBlurRadius(blur)
        shadow.setOffset(offset_x, offset_y)
        c = QColor(color)
        c.setAlpha(alpha)
        shadow.setColor(c)
        widget.setGraphicsEffect(shadow)
        return shadow
    except Exception as e:
        print(f"⚠️ خطا در اعمال سایه: {e}")
        return None


def add_glow(
    widget: QWidget,
    color: str = "#4FC3F7",
    blur: int = 24,
    alpha: int = 120,
) -> QGraphicsDropShadowEffect | None:
    """
    اعمال درخشش رنگی (سایه‌ی بدون offset).
    مناسب برای دکمه‌های فعال و عناصر برجسته.
    """
    return add_shadow(
        widget,
        blur=blur,
        offset_x=0,
        offset_y=0,
        color=color,
        alpha=alpha,
    )