"""
لایه‌ی پارالاکس برای منو
==========================
- چند لایه‌ی دکوراتیو که با سرعت‌های متفاوت حرکت می‌کنند
- بدون تداخل با کلیک (transparent for mouse)
- کاملاً رویه‌ای — بدون تصویر

نسخه: 1.0.0
"""
import random
import math
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer, QPointF
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen


class ParallaxLayer(QWidget):
    """لایه‌ی پارالاکس با اشیاء شناور"""

    def __init__(self, depth: int = 1, parent=None):
        """
        depth: 1 = نزدیک (سریع، بزرگ)، 3 = دور (کند، کوچک)
        """
        super().__init__(parent)
        self.depth = max(1, min(3, depth))

        self.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents, True
        )
        self.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground, True
        )
        self.setStyleSheet("background: transparent; border: none;")

        # ✅ پارامترها بر اساس عمق
        self.speed = 0.6 / self.depth
        self.opacity = {1: 90, 2: 60, 3: 35}[self.depth]
        self.size_min = {1: 2.0, 2: 1.2, 3: 0.8}[self.depth]
        self.size_max = {1: 3.5, 2: 2.2, 3: 1.4}[self.depth]
        self.count = {1: 12, 2: 20, 3: 30}[self.depth]

        self._phase = 0.0
        self._shapes: list = []
        self._regenerate()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(70)

    def _regenerate(self):
        self._shapes = []
        for _ in range(self.count):
            self._shapes.append({
                "x": random.random(),
                "y": random.random(),
                "size": random.uniform(
                    self.size_min, self.size_max
                ),
                "vx": random.uniform(-0.15, 0.15),
                "vy": random.uniform(-0.25, -0.05),
                "phase": random.uniform(0, 6.28),
                "shape": random.choice(
                    ["circle", "circle", "square"]
                ),
            })

    def _tick(self):
        self._phase += 0.03
        if self._phase > 2 * math.pi:
            self._phase -= 2 * math.pi
        for s in self._shapes:
            s["x"] += s["vx"] * self.speed * 0.008
            s["y"] += s["vy"] * self.speed * 0.008
            # wrap
            if s["y"] < -0.05:
                s["y"] = 1.05
                s["x"] = random.random()
            if s["y"] > 1.05:
                s["y"] = -0.05
            if s["x"] < -0.05:
                s["x"] = 1.05
            if s["x"] > 1.05:
                s["x"] = -0.05
        self.update()

    def paintEvent(self, event):  # type: ignore
        if not self._shapes:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)

        w = self.width()
        h = self.height()

        for s in self._shapes:
            x = s["x"] * w
            y = s["y"] * h
            size = s["size"]

            # ✅ ضربان شفافیت
            pulse = (math.sin(
                s["phase"] + self._phase * 0.5
            ) + 1) * 0.5
            alpha = int(self.opacity * (0.6 + 0.4 * pulse))

            color = QColor(79, 195, 247, alpha)
            painter.setBrush(QBrush(color))

            if s["shape"] == "square":
                painter.drawRect(
                    int(x - size), int(y - size),
                    int(size * 2), int(size * 2)
                )
            else:
                painter.drawEllipse(QPointF(x, y), size, size)

        painter.end()