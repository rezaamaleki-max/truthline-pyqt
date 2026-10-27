"""
افکت Glitch برای انتقال بین فازها
====================================
- چند نوار افقی رنگی که به‌سرعت ظاهر و ناپدید می‌شوند
- بدون تداخل با کلیک
- ۵۰۰ میلی‌ثانیه طول می‌کشد

نسخه: 1.0.0
"""
import random
import math
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer, QRectF
from PyQt6.QtGui import QPainter, QColor, QBrush


class GlitchOverlay(QWidget):
    """لایه‌ی Glitch که به‌طور موقت نمایش داده می‌شود"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents, True
        )
        self.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground, True
        )
        self.setStyleSheet("background: transparent; border: none;")

        self._bands: list = []
        self._elapsed = 0
        self._duration = 500   # ms
        self._active = False
        self._accent = QColor("#4FC3F7")

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)

    def start(self, duration_ms: int = 500,
              color: str = "#4FC3F7"):
        """شروع افکت glitch"""
        self._accent = QColor(color)
        self._duration = duration_ms
        self._elapsed = 0
        self._active = True
        self._bands = []

        # ✅ ساخت نوارهای رنگی
        n_bands = 12
        for i in range(n_bands):
            self._bands.append({
                "y": random.random(),
                "height": random.uniform(2, 8),
                "color": random.choice([
                    self._accent,
                    QColor("#FFFFFF"),
                    QColor(255, 100, 100),
                    QColor(100, 100, 255),
                ]),
                "offset": random.uniform(-0.15, 0.15),
                "alpha": random.randint(80, 200),
            })

        self.show()
        self.raise_()
        self._timer.start(30)

    def _tick(self):
        self._elapsed += 30
        if self._elapsed >= self._duration:
            self._active = False
            self._timer.stop()
            self.hide()
            return
        self.update()

    def paintEvent(self, event):  # type: ignore
        if not self._active:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)

        w = self.width()
        h = self.height()

        # ✅ محاسبه‌ی شدت (fade in/out)
        progress = self._elapsed / self._duration
        if progress < 0.3:
            intensity = progress / 0.3
        elif progress < 0.7:
            intensity = 1.0
        else:
            intensity = 1.0 - (progress - 0.7) / 0.3

        for band in self._bands:
            y = band["y"] * h
            bh = band["height"]
            offset = band["offset"] * w * math.sin(
                self._elapsed * 0.05
            )

            color = QColor(band["color"])
            a = int(band["alpha"] * intensity)
            color.setAlpha(max(0, min(255, a)))

            painter.setBrush(QBrush(color))
            painter.drawRect(
                QRectF(offset, y, w, bh)
            )

        # ✅ نویز نقطه‌ای
        for _ in range(40):
            x = random.random() * w
            y = random.random() * h
            a = int(random.randint(30, 120) * intensity)
            painter.setBrush(QBrush(QColor(255, 255, 255, a)))
            painter.drawRect(int(x), int(y), 2, 2)

        painter.end()