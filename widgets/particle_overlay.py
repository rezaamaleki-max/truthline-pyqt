"""
لایه‌ی ذرات رویه‌ای (Procedural Particles)
==========================================
- ذرات کوچک شناور روی پس‌زمینه
- بدون نیاز به کلیک (transparent for mouse events)
- تم اختصاصی برای هر فاز
- کارایی بالا با QTimer

نسخه: 1.0.0
"""
import random
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer, QPointF
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen


# ============================================================
# تم ذرات برای هر صحنه
# ============================================================
PARTICLE_THEMES = {
    "phase1": {
        "color": "#4FC3F7",
        "count": 40,
        "speed": 0.35,
        "size_range": (1.5, 3.5),
        "alpha_range": (60, 160),
        "shape": "circle",
    },
    "phase2": {
        "color": "#FF8F00",
        "count": 35,
        "speed": 0.5,
        "size_range": (1.0, 2.8),
        "alpha_range": (70, 180),
        "shape": "circle",
    },
    "phase3": {
        "color": "#9C27B0",
        "count": 50,
        "speed": 0.25,
        "size_range": (1.2, 3.0),
        "alpha_range": (60, 150),
        "shape": "square",
    },
    "phase4": {
        "color": "#D32F2F",
        "count": 20,
        "speed": 0.15,
        "size_range": (1.8, 3.5),
        "alpha_range": (50, 130),
        "shape": "circle",
    },
    "night": {
        "color": "#B0BEC5",
        "count": 15,
        "speed": 0.08,
        "size_range": (1.0, 2.5),
        "alpha_range": (80, 200),
        "shape": "circle",
    },
    "default": {
        "color": "#4FC3F7",
        "count": 25,
        "speed": 0.25,
        "size_range": (1.5, 3.0),
        "alpha_range": (60, 150),
        "shape": "circle",
    },
}


class ParticleOverlay(QWidget):
    """لایه‌ی ذرات — روی پس‌زمینه، بدون مسدود کردن کلیک"""

    def __init__(self, theme_key: str = "default", parent=None):
        super().__init__(parent)

        # ✅ ذرات نباید کلیک را مسدود کنند
        self.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents, True
        )
        self.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground, True
        )
        self.setAttribute(
            Qt.WidgetAttribute.WA_StyledBackground, False
        )
        self.setStyleSheet("background: transparent; border: none;")

        self._theme = PARTICLE_THEMES.get(
            theme_key, PARTICLE_THEMES["default"]
        )
        self._particles: list = []
        self._generate_particles()

        # ✅ تایمر برای به‌روزرسانی موقعیت
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(60)  # ~16 FPS — کارایی بهتر

        # ✅ اگر ویجت خالی بود، یک‌بار resize کنیم
        self.resize(800, 600)

    # ----------------------------------------------------------
    def _generate_particles(self):
        """تولید ذرات با ویژگی‌های تصادفی"""
        self._particles.clear()
        count = self._theme["count"]
        size_min, size_max = self._theme["size_range"]
        alpha_min, alpha_max = self._theme["alpha_range"]

        for _ in range(count):
            self._particles.append({
                "x": random.random(),
                "y": random.random(),
                "size": random.uniform(size_min, size_max),
                "alpha": random.randint(alpha_min, alpha_max),
                "vx": random.uniform(-0.2, 0.2),
                "vy": random.uniform(-0.4, -0.05),
                "phase": random.uniform(0, 6.28),  # برای موج
            })

    # ----------------------------------------------------------
    def _tick(self):
        """به‌روزرسانی موقعیت ذرات"""
        speed = self._theme["speed"]
        for p in self._particles:
            p["x"] += p["vx"] * speed * 0.01
            p["y"] += p["vy"] * speed * 0.01
            p["phase"] += 0.05

            # wrap
            if p["y"] < -0.05:
                p["y"] = 1.05
                p["x"] = random.random()
            if p["y"] > 1.05:
                p["y"] = -0.05
            if p["x"] < -0.05:
                p["x"] = 1.05
            if p["x"] > 1.05:
                p["x"] = -0.05

        self.update()

    # ----------------------------------------------------------
    def paintEvent(self, event):  # type: ignore
        if not self._particles:
            return

        painter = QPainter(self)
        if not painter.isActive():
            return

        try:
            painter.setRenderHint(
                QPainter.RenderHint.Antialiasing
            )
            painter.setPen(Qt.PenStyle.NoPen)

            w = self.width()
            h = self.height()
            if w < 10 or h < 10:
                return

            base_color = QColor(self._theme["color"])
            shape = self._theme["shape"]

            for p in self._particles:
                x = p["x"] * w
                y = p["y"] * h
                size = p["size"]

                import math
                pulse = (math.sin(p["phase"]) + 1.0) * 0.5
                alpha = int(
                    p["alpha"] * (0.7 + 0.3 * pulse)
                )
                alpha = max(0, min(255, alpha))

                c = QColor(
                    base_color.red(),
                    base_color.green(),
                    base_color.blue(),
                    alpha,
                )
                painter.setBrush(QBrush(c))

                if shape == "square":
                    painter.drawRect(
                        int(x - size / 2),
                        int(y - size / 2),
                        int(size),
                        int(size),
                    )
                else:
                    painter.drawEllipse(
                        QPointF(x, y), size, size
                    )
        finally:
            try:
                painter.end()
            except Exception:
                pass

    # ----------------------------------------------------------
    def set_theme(self, theme_key: str):
        """تغییر تم ذرات"""
        self._theme = PARTICLE_THEMES.get(
            theme_key, PARTICLE_THEMES["default"]
        )
        self._generate_particles()
        self.update()

    # ----------------------------------------------------------
    def stop(self):
        """توقف تایمر — هنگام پنهان شدن"""
        self._timer.stop()

    def start(self):
        """شروع مجدد تایمر"""
        if not self._timer.isActive():
            self._timer.start(60)

    # ✅ مدیریت خودکار تایمر بر اساس نمایش/پنهان شدن
    def showEvent(self, event):  # type: ignore
        super().showEvent(event)
        if not self._timer.isActive():
            self._timer.start(60)

    def hideEvent(self, event):  # type: ignore
        super().hideEvent(event)
        if self._timer.isActive():
            self._timer.stop()