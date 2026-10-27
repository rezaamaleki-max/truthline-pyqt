"""
ویجت پرتره شخصیت — نسخه 2.0

- پشتیبانی از تصاویر full-body مستطیلی
- fallback به آواتار دایره‌ای
- حاشیه احساسی رنگ‌شده
- گوشه‌های گرد به جای دایره کامل
"""
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont, QPixmap,
    QRadialGradient
)

FONT_FAMILY = "Vazirmatn"


# رنگ حاشیه بر اساس احساس
EMOTION_BORDER = {
    "neutral":   "#4FC3F7",
    "warm":      "#4CAF50",
    "grateful":  "#66BB6A",
    "relief":    "#4CAF50",
    "concern":   "#FF8F00",
    "worried":   "#FF8F00",
    "stress":    "#D32F2F",
    "anger":     "#D32F2F",
    "cold":      "#546E7A",
    "flustered": "#FFB300",
    "satisfied": "#4CAF50",
    "urgent":    "#FF5722",
    "surprised": "#FFB300",
    "sad":       "#5C6BC0",
    "thinking":  "#9C27B0",
    "attentive": "#4FC3F7",
    "serious":   "#546E7A",
}


class PortraitWidget(QWidget):
    """نمایش پرتره یا آواتار شخصیت — پشتیبانی از ابعاد مستطیلی"""

    def __init__(self, width: int = 180, height: int = 180,
                 parent=None):
        super().__init__(parent)
        self._w = width
        self._h = height
        self.setFixedSize(width, height)

        # ✅ تعریف صریح برای Pylance
        self._character: dict = {}
        self._emotion: str = "neutral"
        self._pixmap: QPixmap | None = None

    # ----------------------------------------------------------
    def set_character(self, character: dict, emotion: str,
                      portrait_path: str | None = None):
        """تنظیم شخصیت و احساس برای نمایش"""
        old_emotion = self._emotion
        self._character = character or {}
        self._emotion = emotion or "neutral"
        self._pixmap = None

        if portrait_path:
            pm = QPixmap(portrait_path)
            if not pm.isNull():
                self._pixmap = pm

        # ✅ اگر احساس تغییر کرد، افکت flash
        if old_emotion != self._emotion:
            self._emotion_flash = 1.0
            if not hasattr(self, "_emotion_timer"):
                from PyQt6.QtCore import QTimer
                self._emotion_timer = QTimer(self)
                self._emotion_timer.timeout.connect(
                    self._decay_flash
                )
            self._emotion_timer.start(50)

        self.update()

    def _decay_flash(self):
        """کاهش شدت flash احساسی"""
        if not hasattr(self, "_emotion_flash"):
            self._emotion_flash = 0.0
        self._emotion_flash = max(0.0, self._emotion_flash - 0.08)
        if self._emotion_flash <= 0.01:
            if hasattr(self, "_emotion_timer"):
                self._emotion_timer.stop()
        self.update()

    # ----------------------------------------------------------
    def paintEvent(self, event):  # type: ignore[reportIncompatibleMethodOverride]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        w = self.width()
        h = self.height()
        border_color = QColor(
            EMOTION_BORDER.get(self._emotion, "#4FC3F7")
        )

        # ========================================================
        # حالت ۱: تصویر full-body موجود است
        # ========================================================
        if self._pixmap is not None:
            # پس‌زمینه با گوشه‌های گرد
            painter.setBrush(QColor(11, 29, 58, 220))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(
                QRectF(0, 0, w, h), 10, 10
            )

            # ✅ KeepAspectRatioByExpanding — تصویر بزرگ می‌شود
            #    تا کل باکس را پر کند و لبه‌های اضافی با clip
            #    بریده می‌شوند (مثل پروفایل مربعی)
            scaled = self._pixmap.scaled(
                w - 4, h - 4,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            x = int((w - scaled.width()) / 2)
            y = int((h - scaled.height()) / 2)

            # کلیپ گرد
            from PyQt6.QtGui import QPainterPath
            path = QPainterPath()
            path.addRoundedRect(QRectF(0, 0, w, h), 10, 10)
            painter.setClipPath(path)
            painter.drawPixmap(x, y, scaled)
            painter.setClipping(False)

            # حاشیه احساسی
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(border_color, 3))
            painter.drawRoundedRect(
                QRectF(1.5, 1.5, w - 3, h - 3), 10, 10
            )

            # ✅ افکت flash احساسی
            if getattr(self, "_emotion_flash", 0) > 0:
                flash_alpha = int(120 * self._emotion_flash)
                flash_color = QColor(border_color)
                flash_color.setAlpha(flash_alpha)
                painter.setPen(QPen(flash_color, 4))
                inset = int(2 * self._emotion_flash)
                painter.drawRoundedRect(
                    QRectF(inset, inset, w - inset * 2, h - inset * 2),
                    12, 12
                )

            painter.end()
            return

        # ========================================================
        # حالت ۲: آواتار fallback (دایره + حرف اول)
        # ========================================================
        cx = w / 2.0
        cy = h / 2.0
        radius = min(w, h) / 2.0 - 4

        grad = QRadialGradient(QPointF(cx, cy), radius)
        grad.setColorAt(0.0, QColor(26, 42, 74, 240))
        grad.setColorAt(1.0, QColor(11, 29, 58, 240))
        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(cx, cy), radius, radius)

        initial = self._character.get("initial", "؟")
        color_hex = self._character.get("color", "#4FC3F7")

        painter.setPen(QColor(color_hex))
        font = QFont(FONT_FAMILY, int(radius * 0.9))
        font.setBold(True)
        painter.setFont(font)
        rect = QRectF(cx - radius, cy - radius, radius * 2, radius * 2)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, initial)

        painter.setPen(QPen(border_color, 3))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPointF(cx, cy), radius, radius)

        # ✅ افکت flash احساسی (بعد از تغییر احساس)
        if getattr(self, "_emotion_flash", 0) > 0:
            flash_alpha = int(120 * self._emotion_flash)
            flash_color = QColor(border_color)
            flash_color.setAlpha(flash_alpha)

            # حلقه‌ی نورانی گشاد
            painter.setPen(QPen(flash_color, 4))
            extra = int(
                radius * (1.0 + 0.15 * self._emotion_flash)
            )
            painter.drawEllipse(QPointF(cx, cy), extra, extra)

        painter.end()