"""
نمایشگر بارگذاری (Loading Overlay)
=====================================
- یک دایره‌ی چرخان در وسط صفحه
- لایه‌ی نیمه‌شفاف روی پس‌زمینه
- بدون مسدود کردن کلیک (اختیاری: مسدودکننده)

نسخه: 1.0.0
"""
import math
from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QGraphicsOpacityEffect
)
from PyQt6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve
)
from PyQt6.QtGui import (
    QPainter, QPen, QColor, QFont, QBrush
)

FONT_FAMILY = "Vazirmatn"


class LoadingOverlay(QWidget):
    """
    لایه‌ی بارگذاری — روی parent قرار می‌گیرد و چرخاننده
    نشان می‌دهد.
    """

    def __init__(self, parent=None, message: str = "لطفاً صبر کنید..."):
        super().__init__(parent)
        self._message = message
        self._angle = 0.0
        self._active = False

        # ✅ تنظیمات ظاهری
        self.setAttribute(
            Qt.WidgetAttribute.WA_StyledBackground, False
        )
        self.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground, True
        )
        self.setStyleSheet(
            "background: transparent; border: none;"
        )
        self.hide()

        # ✅ تایمر انیمیشن
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.setInterval(40)

        # ✅ اگر parent یک QWidget است، هم‌اندازه شو
        parent_widget = self.parentWidget()
        if parent_widget is not None:
            self.setGeometry(parent_widget.rect())
            self.raise_()

    # ----------------------------------------------------------------
    def start(self, message: str | None = None):
        """شروع نمایش"""
        if message is not None:
            self._message = message
        self._active = True
        parent_widget = self.parentWidget()
        if parent_widget is not None:
            self.setGeometry(parent_widget.rect())
        self.show()
        self.raise_()
        self._timer.start()

    def stop(self):
        """پایان نمایش"""
        self._active = False
        self._timer.stop()
        self.hide()

    def set_message(self, text: str):
        self._message = text
        self.update()

    # ----------------------------------------------------------------
    def _tick(self):
        self._angle = (self._angle + 8) % 360
        self.update()

    # ----------------------------------------------------------------
    def paintEvent(self, event):  # type: ignore
        if not self._active:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        cx = w / 2
        cy = h / 2

        # پس‌زمینه‌ی نیمه‌شفاف
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(11, 29, 58, 200)))
        painter.drawRect(0, 0, w, h)

        # حلقه‌ی چرخان
        radius = 36
        pen_width = 6

        # حلقه‌ی پس‌زمینه
        painter.setPen(QPen(
            QColor(43, 74, 111, 180), pen_width
        ))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(
            int(cx - radius), int(cy - radius),
            radius * 2, radius * 2,
        )

        # قوس چرخان
        painter.setPen(QPen(
            QColor("#4FC3F7"), pen_width,
            Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
        ))
        start_angle = int(self._angle * 16)
        span_angle = int(90 * 16)  # ۹۰ درجه
        rect = (
            int(cx - radius), int(cy - radius),
            radius * 2, radius * 2,
        )
        painter.drawArc(*rect, start_angle, span_angle)

        # متن
        painter.setPen(QColor("#FFFFFF"))
        painter.setFont(QFont(FONT_FAMILY, 13, QFont.Weight.Bold))
        text_rect = (
            int(cx - 200), int(cy + radius + 20),
            400, 30,
        )
        painter.drawText(
            text_rect[0], text_rect[1],
            text_rect[2], text_rect[3],
            int(Qt.AlignmentFlag.AlignCenter),
            self._message,
        )

        painter.end()

    # ----------------------------------------------------------------
    def mousePressEvent(self, event):  # type: ignore
        # جلوگیری از کلیک‌های ناخواسته در حین بارگذاری
        if self._active:
            event.accept()
            return
        super().mousePressEvent(event)