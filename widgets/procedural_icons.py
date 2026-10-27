"""
آیکون‌های رویه‌ای — رسم با QPainter
=====================================
سیستم آیکون کامل، بدون نیاز به فایل SVG یا PNG.

هر تابع یک QIcon یا QPixmap برمی‌گرداند که قابل استفاده
در QPushButton, QLabel, QAction و... است.

نسخه: 1.0.0
"""
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QRectF, QPointF, QSize
from PyQt6.QtGui import (
    QPixmap, QIcon, QPainter, QPen, QBrush, QColor,
    QPainterPath, QPolygonF, QFont,
)
import math


# ====================================================================
# تابع کمکی: ساخت QPixmap با اندازه و رنگ
# ====================================================================
def _make_pixmap(size: int = 32) -> QPixmap:
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    return pm


def _pen(color: str, width: float = 2.0) -> QPen:
    pen = QPen(QColor(color), width)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    return pen


# ====================================================================
# ۱. چرخ‌دنده (تنظیمات)
# ====================================================================
def gear_icon(size: int = 32, color: str = "#4FC3F7") -> QIcon:
    pm = _make_pixmap(size)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    cx = size / 2
    cy = size / 2
    outer_r = size * 0.42
    inner_r = size * 0.32
    hole_r = size * 0.12
    teeth = 8

    # ساخت پولیگان دندانه‌دار
    points = []
    for i in range(teeth * 2):
        angle = (i / (teeth * 2)) * 2 * math.pi - math.pi / 2
        r = outer_r if i % 2 == 0 else inner_r
        points.append(QPointF(
            cx + r * math.cos(angle),
            cy + r * math.sin(angle),
        ))

    poly = QPolygonF(points)
    p.setPen(_pen(color, max(1.5, size * 0.06)))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawPolygon(poly)

    # سوراخ مرکزی
    p.drawEllipse(QPointF(cx, cy), hole_r, hole_r)

    p.end()
    return QIcon(pm)


# ====================================================================
# ۲. خانه (منو)
# ====================================================================
def home_icon(size: int = 32, color: str = "#4FC3F7") -> QIcon:
    pm = _make_pixmap(size)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    s = size
    w = s * 0.06

    p.setPen(_pen(color, max(1.5, w)))
    p.setBrush(Qt.BrushStyle.NoBrush)

    # سقف
    roof = QPolygonF([
        QPointF(s * 0.1, s * 0.5),
        QPointF(s * 0.5, s * 0.15),
        QPointF(s * 0.9, s * 0.5),
    ])
    p.drawPolyline(roof)

    # بدنه
    p.drawLine(
        QPointF(s * 0.2, s * 0.5),
        QPointF(s * 0.2, s * 0.85),
    )
    p.drawLine(
        QPointF(s * 0.8, s * 0.5),
        QPointF(s * 0.8, s * 0.85),
    )
    p.drawLine(
        QPointF(s * 0.2, s * 0.85),
        QPointF(s * 0.8, s * 0.85),
    )

    # در
    p.drawRect(QRectF(
        s * 0.42, s * 0.62, s * 0.16, s * 0.23
    ))

    p.end()
    return QIcon(pm)


# ====================================================================
# ۳. دفترچه (Mission Log)
# ====================================================================
def notebook_icon(size: int = 32, color: str = "#FF8F00") -> QIcon:
    pm = _make_pixmap(size)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    s = size
    w = max(1.5, s * 0.05)

    p.setPen(_pen(color, w))
    p.setBrush(Qt.BrushStyle.NoBrush)

    # بدنه دفتر
    p.drawRect(QRectF(s * 0.2, s * 0.15, s * 0.6, s * 0.7))

    # خطوط داخلی (شبیه نوشته)
    for i in range(3):
        y = s * (0.3 + i * 0.15)
        p.drawLine(
            QPointF(s * 0.3, y),
            QPointF(s * 0.7, y),
        )

    # شییره (ستون کنار)
    p.drawLine(
        QPointF(s * 0.32, s * 0.15),
        QPointF(s * 0.32, s * 0.85),
    )

    p.end()
    return QIcon(pm)


# ====================================================================
# ۴. پرونده‌ی شخصیت‌ها (دو نفر)
# ====================================================================
def dossier_icon(size: int = 32, color: str = "#4FC3F7") -> QIcon:
    pm = _make_pixmap(size)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    s = size
    w = max(1.5, s * 0.05)

    p.setPen(_pen(color, w))
    p.setBrush(Qt.BrushStyle.NoBrush)

    # نفر عقب
    p.drawEllipse(
        QPointF(s * 0.35, s * 0.32),
        s * 0.12, s * 0.12,
    )
    arc1 = QPainterPath()
    arc1.moveTo(s * 0.15, s * 0.75)
    arc1.quadTo(s * 0.35, s * 0.5, s * 0.55, s * 0.75)
    p.drawPath(arc1)

    # نفر جلو
    p.drawEllipse(
        QPointF(s * 0.68, s * 0.4),
        s * 0.13, s * 0.13,
    )
    arc2 = QPainterPath()
    arc2.moveTo(s * 0.45, s * 0.85)
    arc2.quadTo(s * 0.68, s * 0.55, s * 0.9, s * 0.85)
    p.drawPath(arc2)

    p.end()
    return QIcon(pm)


# ====================================================================
# ۵. ذخیره (دیسکت)
# ====================================================================
def save_icon(size: int = 32, color: str = "#4CAF50") -> QIcon:
    pm = _make_pixmap(size)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    s = size
    w = max(1.5, s * 0.05)

    p.setPen(_pen(color, w))
    p.setBrush(Qt.BrushStyle.NoBrush)

    # بدنه دیسکت
    body = QPainterPath()
    body.moveTo(s * 0.15, s * 0.15)
    body.lineTo(s * 0.7, s * 0.15)
    body.lineTo(s * 0.85, s * 0.3)
    body.lineTo(s * 0.85, s * 0.85)
    body.lineTo(s * 0.15, s * 0.85)
    body.closeSubpath()
    p.drawPath(body)

    # نوار بالایی
    p.drawRect(QRectF(
        s * 0.32, s * 0.15, s * 0.36, s * 0.18
    ))

    # برچسب پایین
    p.drawRect(QRectF(
        s * 0.28, s * 0.55, s * 0.44, s * 0.3
    ))

    p.end()
    return QIcon(pm)


# ====================================================================
# ۶. خروج (درب)
# ====================================================================
def exit_icon(size: int = 32, color: str = "#D32F2F") -> QIcon:
    pm = _make_pixmap(size)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    s = size
    w = max(1.5, s * 0.05)

    p.setPen(_pen(color, w))
    p.setBrush(Qt.BrushStyle.NoBrush)

    # در
    p.drawRect(QRectF(s * 0.15, s * 0.15, s * 0.45, s * 0.7))

    # دستگیره
    p.drawEllipse(
        QPointF(s * 0.5, s * 0.5),
        s * 0.03, s * 0.03,
    )

    # فلش خروج
    p.drawLine(
        QPointF(s * 0.65, s * 0.5),
        QPointF(s * 0.9, s * 0.5),
    )
    p.drawLine(
        QPointF(s * 0.82, s * 0.42),
        QPointF(s * 0.9, s * 0.5),
    )
    p.drawLine(
        QPointF(s * 0.82, s * 0.58),
        QPointF(s * 0.9, s * 0.5),
    )

    p.end()
    return QIcon(pm)


# ====================================================================
# ۷. میانبر (کیبورد)
# ====================================================================
def keyboard_icon(size: int = 32, color: str = "#4FC3F7") -> QIcon:
    pm = _make_pixmap(size)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    s = size
    w = max(1.5, s * 0.05)

    p.setPen(_pen(color, w))
    p.setBrush(Qt.BrushStyle.NoBrush)

    # بدنه کیبورد
    p.drawRect(QRectF(s * 0.1, s * 0.3, s * 0.8, s * 0.4))

    # دکمه‌ها
    for row in range(2):
        for col in range(4):
            x = s * (0.16 + col * 0.18)
            y = s * (0.4 + row * 0.1)
            p.drawRect(QRectF(x, y, s * 0.12, s * 0.06))

    p.end()
    return QIcon(pm)


# ====================================================================
# ۸. شروع (مثلث Play)
# ====================================================================
def play_icon(size: int = 32, color: str = "#4CAF50") -> QIcon:
    pm = _make_pixmap(size)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    s = size
    poly = QPolygonF([
        QPointF(s * 0.3, s * 0.2),
        QPointF(s * 0.8, s * 0.5),
        QPointF(s * 0.3, s * 0.8),
    ])

    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(QColor(color)))
    p.drawPolygon(poly)

    p.end()
    return QIcon(pm)


# ====================================================================
# ۹. تیک (تأیید)
# ====================================================================
def check_icon(size: int = 32, color: str = "#4CAF50") -> QIcon:
    pm = _make_pixmap(size)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    s = size
    p.setPen(_pen(color, max(2.0, s * 0.12)))
    p.setBrush(Qt.BrushStyle.NoBrush)

    path = QPainterPath()
    path.moveTo(s * 0.2, s * 0.55)
    path.lineTo(s * 0.42, s * 0.75)
    path.lineTo(s * 0.8, s * 0.28)
    p.drawPath(path)

    p.end()
    return QIcon(pm)


# ====================================================================
# ۱۰. ضربدر (بستن)
# ====================================================================
def close_icon(size: int = 32, color: str = "#D32F2F") -> QIcon:
    pm = _make_pixmap(size)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    s = size
    p.setPen(_pen(color, max(2.0, s * 0.12)))
    p.setBrush(Qt.BrushStyle.NoBrush)

    p.drawLine(
        QPointF(s * 0.25, s * 0.25),
        QPointF(s * 0.75, s * 0.75),
    )
    p.drawLine(
        QPointF(s * 0.75, s * 0.25),
        QPointF(s * 0.25, s * 0.75),
    )

    p.end()
    return QIcon(pm)


# ====================================================================
# ۱۱. ذره‌بین (بررسی/جستجو)
# ====================================================================
def search_icon(size: int = 32, color: str = "#4FC3F7") -> QIcon:
    pm = _make_pixmap(size)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    s = size
    p.setPen(_pen(color, max(1.5, s * 0.08)))
    p.setBrush(Qt.BrushStyle.NoBrush)

    # دایره‌ی ذره‌بین
    p.drawEllipse(
        QPointF(s * 0.42, s * 0.42),
        s * 0.22, s * 0.22,
    )

    # دسته
    p.drawLine(
        QPointF(s * 0.58, s * 0.58),
        QPointF(s * 0.82, s * 0.82),
    )

    p.end()
    return QIcon(pm)


# ====================================================================
# ۱۲. چرخ‌دنده (نام دیگر برای سازگاری)
# ====================================================================
settings_icon = gear_icon


# ====================================================================
# ۱۳. زبان (کره‌ی جهانی)
# ====================================================================
def language_icon(size: int = 32, color: str = "#4FC3F7") -> QIcon:
    pm = _make_pixmap(size)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    s = size
    p.setPen(_pen(color, max(1.5, s * 0.05)))
    p.setBrush(Qt.BrushStyle.NoBrush)

    # دایره
    p.drawEllipse(
        QPointF(s * 0.5, s * 0.5),
        s * 0.35, s * 0.35,
    )

    # نصف‌النهار
    p.drawEllipse(
        QPointF(s * 0.5, s * 0.5),
        s * 0.15, s * 0.35,
    )

    # مدار
    p.drawLine(
        QPointF(s * 0.15, s * 0.5),
        QPointF(s * 0.85, s * 0.5),
    )

    p.end()
    return QIcon(pm)


# ====================================================================
# ۱۴. صدا (بلندگو)
# ====================================================================
def sound_icon(size: int = 32, color: str = "#4FC3F7") -> QIcon:
    pm = _make_pixmap(size)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    s = size
    p.setPen(_pen(color, max(1.5, s * 0.06)))
    p.setBrush(Qt.BrushStyle.NoBrush)

    # بدنه بلندگو
    poly = QPolygonF([
        QPointF(s * 0.2, s * 0.4),
        QPointF(s * 0.35, s * 0.4),
        QPointF(s * 0.55, s * 0.25),
        QPointF(s * 0.55, s * 0.75),
        QPointF(s * 0.35, s * 0.6),
        QPointF(s * 0.2, s * 0.6),
    ])
    p.drawPolygon(poly)

    # امواج
    for i in range(2):
        r = s * (0.15 + i * 0.1)
        p.drawArc(
            int(s * 0.5 - r), int(s * 0.5 - r),
            int(2 * r), int(2 * r),
            -45 * 16, 90 * 16,
        )

    p.end()
    return QIcon(pm)


# ====================================================================
# ۱۵. بازگشت (فلش به چپ)
# ====================================================================
def back_icon(size: int = 32, color: str = "#4FC3F7") -> QIcon:
    pm = _make_pixmap(size)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    s = size
    p.setPen(_pen(color, max(2.0, s * 0.08)))
    p.setBrush(Qt.BrushStyle.NoBrush)

    path = QPainterPath()
    path.moveTo(s * 0.8, s * 0.5)
    path.lineTo(s * 0.2, s * 0.5)
    p.drawPath(path)

    p.drawLine(
        QPointF(s * 0.4, s * 0.3),
        QPointF(s * 0.2, s * 0.5),
    )
    p.drawLine(
        QPointF(s * 0.4, s * 0.7),
        QPointF(s * 0.2, s * 0.5),
    )

    p.end()
    return QIcon(pm)


# ====================================================================
# تابع عمومی برای دریافت آیکون با نام
# ====================================================================
_ICON_REGISTRY = {
    "gear": gear_icon,
    "settings": gear_icon,
    "home": home_icon,
    "menu": home_icon,
    "notebook": notebook_icon,
    "log": notebook_icon,
    "dossier": dossier_icon,
    "users": dossier_icon,
    "save": save_icon,
    "exit": exit_icon,
    "quit": exit_icon,
    "keyboard": keyboard_icon,
    "shortcuts": keyboard_icon,
    "play": play_icon,
    "start": play_icon,
    "check": check_icon,
    "close": close_icon,
    "x": close_icon,
    "search": search_icon,
    "language": language_icon,
    "sound": sound_icon,
    "back": back_icon,
}


def get_icon(name: str, size: int = 32,
              color: str = "#4FC3F7") -> QIcon:
    """دریافت آیکون با نام"""
    func = _ICON_REGISTRY.get(name.lower())
    if func is None:
        return QIcon()
    return func(size, color)