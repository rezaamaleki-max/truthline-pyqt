"""
پس‌زمینه‌های رویه‌ای — نسخه 2.0
====================================
رسم کامل پس‌زمینه با QPainter — بدون تصویر خارجی.
۶ تم اختصاصی + ۳ لایه عمق (عمق دور، میانی، جلو).

نسخه: 2.0.0
"""
import random
import math
import time
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer, QPointF, QRectF
from PyQt6.QtGui import (
    QPainter, QLinearGradient, QRadialGradient,
    QColor, QBrush, QPen, QPolygonF,
)


THEMES = {
    "control_room": {
        "bg_top": "#050A18",
        "bg_mid": "#0F2035",
        "bg_bottom": "#152A45",
        "accent": "#4FC3F7",
        "secondary": "#4CAF50",
    },
    "corridor": {
        "bg_top": "#1A0A05",
        "bg_mid": "#251210",
        "bg_bottom": "#2A1510",
        "accent": "#FF8F00",
        "secondary": "#FFB74D",
    },
    "data_lab": {
        "bg_top": "#100518",
        "bg_mid": "#1A0F28",
        "bg_bottom": "#221535",
        "accent": "#9C27B0",
        "secondary": "#CE93D8",
    },
    "council_hall": {
        "bg_top": "#150505",
        "bg_mid": "#200A0A",
        "bg_bottom": "#2A1015",
        "accent": "#D32F2F",
        "secondary": "#FFB74D",
    },
    "space": {
        "bg_top": "#010308",
        "bg_mid": "#050E1F",
        "bg_bottom": "#0A1830",
        "accent": "#4FC3F7",
        "secondary": "#FFFFFF",
    },
    "night": {
        "bg_top": "#03060F",
        "bg_mid": "#070F20",
        "bg_bottom": "#0B1D3A",
        "accent": "#B0BEC5",
        "secondary": "#4FC3F7",
    },
    "default": {
        "bg_top": "#0B1D3A",
        "bg_mid": "#102542",
        "bg_bottom": "#152A45",
        "accent": "#4FC3F7",
        "secondary": "#4CAF50",
    },
}


class ProceduralBackground(QWidget):
    """
    پس‌زمینه‌ی رویه‌ای با سه لایه‌ی عمق.
    """

    def __init__(self, theme_key: str = "default", parent=None):
        super().__init__(parent)
        self._theme_key = theme_key
        self._theme = THEMES.get(theme_key, THEMES["default"])

        self._phase = 0.0

        # داده‌های هر سه لایه
        self._back_data: dict = {}
        self._mid_data: dict = {}
        self._near_data: dict = {}

        # ✅ رویدادهای بصری
        self._event_active = False
        self._event_progress = 0.0     # 0.0 تا 1.0
        self._event_duration_ms = 1500
        self._event_kind = ""           # "wave" | "flash" | "spike" |
                                        # "pulse" | "shooting_star"
        self._event_data: dict = {}
        self._event_start_time = 0

        self._regenerate_static()

        self.setAttribute(
            Qt.WidgetAttribute.WA_StyledBackground, True
        )
        self.setStyleSheet(
            "ProceduralBackground { background: transparent; "
            "border: none; }"
        )

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(80)

        # ✅ تایمر رویداد — با وقفه‌ی تصادفی ۱۸-۳۰ ثانیه
        self._event_schedule_timer = QTimer(self)
        self._event_schedule_timer.setSingleShot(True)
        self._event_schedule_timer.timeout.connect(
            self._trigger_random_event
        )
        # شروع اولین رویداد پس از ۱۰ ثانیه (تا کاربر فرصت کند)
        self._event_schedule_timer.start(10000)

        # ✅ تایمر انیمیشن رویداد
        self._event_anim_timer = QTimer(self)
        self._event_anim_timer.timeout.connect(self._tick_event)

    # ----------------------------------------------------------
    def _tick(self):
        self._phase += 0.04
        if self._phase > 2 * math.pi:
            self._phase -= 2 * math.pi
        self.update()

    def set_theme(self, theme_key: str):
        if theme_key == self._theme_key:
            return
        self._theme_key = theme_key
        self._theme = THEMES.get(theme_key, THEMES["default"])
        self._regenerate_static()
        # بازنشانی رویداد
        self._event_active = False
        self._event_anim_timer.stop()
        self._event_schedule_timer.start(8000)
        self.update()

    def stop_animation(self):
        self._timer.stop()

    def start_animation(self):
        if not self._timer.isActive():
            self._timer.start(80)

    # ✅ مدیریت خودکار تایمرها بر اساس نمایش/پنهان شدن
    def showEvent(self, event):  # type: ignore
        super().showEvent(event)
        if not self._timer.isActive():
            self._timer.start(80)
        if not self._event_schedule_timer.isActive():
            self._event_schedule_timer.start(10000)

    def hideEvent(self, event):  # type: ignore
        super().hideEvent(event)
        if self._timer.isActive():
            self._timer.stop()
        if self._event_schedule_timer.isActive():
            self._event_schedule_timer.stop()
        if self._event_anim_timer.isActive():
            self._event_anim_timer.stop()

    # ==========================================================
    def _regenerate_static(self):
        self._back_data = {}
        self._mid_data = {}
        self._near_data = {}
        key = self._theme_key

        # ---------------- لایه‌ی دور (Back) ----------------
        if key in ("space", "night"):
            self._back_data["stars"] = [
                {
                    "x": random.random(),
                    "y": random.random(),
                    "size": random.uniform(0.5, 1.4),
                    "bright": random.uniform(0.3, 0.85),
                    "twinkle": random.uniform(0, 6.28),
                }
                for _ in range(120)
            ]
        elif key == "control_room":
            self._back_data["distant_monitors"] = [
                {
                    "x": 0.02 + i * 0.05,
                    "y": 0.06 + random.uniform(-0.02, 0.02),
                    "w": 0.035,
                    "h": 0.045,
                    "hue": random.choice(
                        ["#4FC3F7", "#4CAF50"]
                    ),
                }
                for i in range(18)
            ]
        elif key == "corridor":
            self._back_data["distant_arcs"] = [
                {"t": i / 12.0} for i in range(12)
            ]
        elif key == "data_lab":
            self._back_data["grid_nodes"] = [
                {
                    "x": random.random(),
                    "y": random.random(),
                    "r": random.uniform(1.0, 2.0),
                }
                for _ in range(50)
            ]
        elif key == "council_hall":
            self._back_data["distant_seats"] = [
                {"x": 0.1 + i * 0.1, "y": 0.08}
                for i in range(9)
            ]

        # ---------------- لایه‌ی میانی (Mid) — همان محتوای قبلی ----------------
        if key == "control_room":
            self._mid_data["screens"] = [
                {
                    "x": 0.12 + i * 0.18,
                    "y": 0.15 + random.uniform(-0.03, 0.03),
                    "w": 0.14,
                    "h": 0.16,
                    "hue": random.choice(
                        ["#4FC3F7", "#4CAF50", "#FF8F00", "#4FC3F7"]
                    ),
                    "seed": random.uniform(0, 10),
                }
                for i in range(4)
            ]
            self._mid_data["lights"] = [
                {"x": 0.15 + i * 0.2, "y": 0.05}
                for i in range(5)
            ]
        elif key == "data_lab":
            self._mid_data["charts"] = [
                {
                    "x": 0.08 + i * 0.3,
                    "y": 0.5 + random.uniform(-0.02, 0.02),
                    "w": 0.24,
                    "h": 0.18,
                    "seed": random.uniform(0, 10),
                    "hue": random.choice(
                        ["#9C27B0", "#CE93D8", "#4FC3F7"]
                    ),
                }
                for i in range(3)
            ]
            self._mid_data["nodes"] = [
                {
                    "x": random.random(),
                    "y": random.random(),
                    "r": random.uniform(1.5, 3.0),
                    "phase": random.uniform(0, 6.28),
                }
                for _ in range(25)
            ]
        elif key == "council_hall":
            self._mid_data["seats"] = [
                {"angle": math.pi * 0.15 +
                          i * (math.pi * 0.7 / 8)}
                for i in range(9)
            ]
            self._mid_data["chandeliers"] = [
                {"x": 0.25 + i * 0.25, "y": 0.1}
                for i in range(3)
            ]

        # ---------------- لایه‌ی نزدیک (Near) — عناصر تار در گوشه‌ها ----------------
        if key == "control_room":
            # کنسول تار در پایین
            self._near_data["console"] = {
                "x": 0.0,
                "y": 0.78,
                "w": 1.0,
                "h": 0.22,
            }
            self._near_data["side_panels"] = [
                {"x": 0.0, "y": 0.0, "w": 0.08, "h": 1.0},
                {"x": 0.92, "y": 0.0, "w": 0.08, "h": 1.0},
            ]
        elif key == "corridor":
            self._near_data["front_pillars"] = [
                {"x": 0.02, "y": 0.0, "w": 0.06, "h": 1.0},
                {"x": 0.92, "y": 0.0, "w": 0.06, "h": 1.0},
            ]
            self._near_data["ceiling_arch"] = {
                "x": 0.0, "y": 0.0, "w": 1.0, "h": 0.08,
            }
        elif key == "data_lab":
            self._near_data["terminal"] = {
                "x": 0.0, "y": 0.82, "w": 1.0, "h": 0.18,
            }
        elif key == "council_hall":
            self._near_data["table_edge"] = {
                "x": 0.1, "y": 0.85, "w": 0.8, "h": 0.15,
            }
        elif key in ("space", "night"):
            self._near_data["vignette"] = True

    # ==========================================================
    # رویدادهای بصری
    # ==========================================================
    def _trigger_random_event(self):
        """انتخاب و شروع یک رویداد تصادفی بر اساس تم"""
        if self._event_active:
            return

        key = self._theme_key
        kind = ""
        data = {}

        if key == "control_room":
            kind = "wave"
            # موج از چپ به راست
            data = {"direction": 1}
        elif key == "corridor":
            kind = "flash"
            data = {"x": 0.5, "y": 0.45}
        elif key == "data_lab":
            kind = "spike"
            charts = self._mid_data.get("charts", [])
            if charts:
                chart_idx = random.randint(0, len(charts) - 1)
                data = {"chart_idx": chart_idx}
            else:
                return
        elif key == "council_hall":
            kind = "pulse"
            chandeliers = self._mid_data.get("chandeliers", [])
            if chandeliers:
                idx = random.randint(0, len(chandeliers) - 1)
                data = {"chandelier_idx": idx}
            else:
                return
        elif key in ("space", "night"):
            kind = "shooting_star"
            # نقطه‌ی شروع تصادفی در نیمه‌ی بالا
            data = {
                "start_x": random.uniform(0.1, 0.7),
                "start_y": random.uniform(0.05, 0.3),
                "end_x": random.uniform(0.5, 0.95),
                "end_y": random.uniform(0.4, 0.8),
            }
        else:
            # default: بدون رویداد
            return

        self._event_kind = kind
        self._event_data = data
        self._event_progress = 0.0
        self._event_active = True
        self._event_start_time = int(time.time() * 1000)

        # ✅ شروع انیمیشن رویداد
        self._event_anim_timer.start(30)

    def _tick_event(self):
        """پیشرفت انیمیشن رویداد"""
        elapsed = int(time.time() * 1000) - self._event_start_time
        self._event_progress = min(
            1.0, elapsed / self._event_duration_ms
        )

        if self._event_progress >= 1.0:
            # پایان رویداد
            self._event_active = False
            self._event_anim_timer.stop()
            self.update()

            # ✅ زمان‌بندی رویداد بعدی (۱۸ تا ۳۰ ثانیه)
            next_delay = random.randint(18000, 30000)
            self._event_schedule_timer.start(next_delay)
            return

        self.update()

    def _paint_event(self, painter, w, h):
        """رسم رویداد فعال"""
        if not self._event_active:
            return

        kind = self._event_kind
        t = self._event_progress  # 0.0 تا 1.0

        if kind == "wave":
            # موج نوری افقی روی اتاق کنترل
            wave_x = t * w  # از چپ به راست
            # شدت: در وسط مسیر بیشتر
            intensity = math.sin(t * math.pi)
            alpha = int(120 * intensity)

            # گرادیانت عمودی برای موج
            grad = QLinearGradient(wave_x - 80, 0, wave_x + 80, 0)
            c1 = QColor(79, 195, 247, 0)
            c2 = QColor(79, 195, 247, alpha)
            c3 = QColor(79, 195, 247, 0)
            grad.setColorAt(0.0, c1)
            grad.setColorAt(0.5, c2)
            grad.setColorAt(1.0, c3)

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(grad))
            # فقط روی نیمه‌ی بالای صفحه (نزدیک مانیتورها)
            painter.drawRect(
                QRectF(wave_x - 80, 0, 160, h * 0.55)
            )

        elif kind == "flash":
            # فلاش قرمز در مرکز تونل
            cx = self._event_data.get("x", 0.5) * w
            cy = self._event_data.get("y", 0.45) * h

            intensity = math.sin(t * math.pi)
            radius = 100 + 150 * intensity

            glow = QRadialGradient(QPointF(cx, cy), radius)
            c1 = QColor(255, 80, 40, int(180 * intensity))
            c2 = QColor(255, 80, 40, int(80 * intensity))
            c3 = QColor(255, 80, 40, 0)
            glow.setColorAt(0.0, c1)
            glow.setColorAt(0.4, c2)
            glow.setColorAt(1.0, c3)

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(glow))
            painter.drawEllipse(QPointF(cx, cy), radius, radius)

        elif kind == "spike":
            # اسپایک در یکی از نمودارها
            idx = self._event_data.get("chart_idx", 0)
            charts = self._mid_data.get("charts", [])
            if idx >= len(charts):
                return
            chart = charts[idx]
            x = chart["x"] * w
            y = chart["y"] * h
            cw = chart["w"] * w
            ch = chart["h"] * h

            # اسپایک قرمز روی نمودار
            intensity = math.sin(t * math.pi)
            spike_color = QColor(255, 80, 80, int(220 * intensity))
            painter.setPen(QPen(spike_color, 2))

            # خط اسپایک عمودی در وسط نمودار
            spike_x = x + cw * 0.5
            spike_h = ch * 0.9 * intensity
            painter.drawLine(
                QPointF(spike_x, y + ch),
                QPointF(spike_x, y + ch - spike_h),
            )

            # هاله
            halo = QRadialGradient(
                QPointF(spike_x, y + ch - spike_h), 40
            )
            c1 = QColor(255, 80, 80, int(100 * intensity))
            c2 = QColor(255, 80, 80, 0)
            halo.setColorAt(0.0, c1)
            halo.setColorAt(1.0, c2)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(halo))
            painter.drawEllipse(
                QPointF(spike_x, y + ch - spike_h), 40, 40
            )

        elif kind == "pulse":
            # درخشش در یکی از چراغ‌های آویز
            idx = self._event_data.get("chandelier_idx", 0)
            chandeliers = self._mid_data.get("chandeliers", [])
            if idx >= len(chandeliers):
                return
            ch = chandeliers[idx]
            x = ch["x"] * w
            y = ch["y"] * h

            intensity = math.sin(t * math.pi)
            radius = 90 + 90 * intensity

            glow = QRadialGradient(QPointF(x, y), radius)
            c1 = QColor(255, 220, 100, int(180 * intensity))
            c2 = QColor(255, 220, 100, int(60 * intensity))
            c3 = QColor(255, 220, 100, 0)
            glow.setColorAt(0.0, c1)
            glow.setColorAt(0.5, c2)
            glow.setColorAt(1.0, c3)

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(glow))
            painter.drawEllipse(QPointF(x, y), radius, radius)

        elif kind == "shooting_star":
            # شهاب سنگ از یک نقطه به نقطه‌ی دیگر
            sx = self._event_data.get("start_x", 0.2) * w
            sy = self._event_data.get("start_y", 0.1) * h
            ex = self._event_data.get("end_x", 0.8) * w
            ey = self._event_data.get("end_y", 0.6) * h

            # موقعیت فعلی
            px = sx + (ex - sx) * t
            py = sy + (ey - sy) * t

            # شدت (در ابتدا و انتها کمتر)
            intensity = math.sin(t * math.pi)

            # دنباله
            trail_len = 80
            trail_dx = (ex - sx) / max(1, math.hypot(
                ex - sx, ey - sy
            )) * trail_len
            trail_dy = (ey - sy) / max(1, math.hypot(
                ex - sx, ey - sy
            )) * trail_len

            # خط دنباله
            pen = QPen(
                QColor(255, 255, 255, int(220 * intensity)),
                2,
            )
            painter.setPen(pen)
            painter.drawLine(
                QPointF(px, py),
                QPointF(px - trail_dx, py - trail_dy),
            )

            # سر شهاب درخشان
            glow = QRadialGradient(QPointF(px, py), 12)
            c1 = QColor(255, 255, 255, int(255 * intensity))
            c2 = QColor(255, 255, 200, 0)
            glow.setColorAt(0.0, c1)
            glow.setColorAt(1.0, c2)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(glow))
            painter.drawEllipse(QPointF(px, py), 12, 12)

    # ==========================================================
    def paintEvent(self, event):  # type: ignore
        painter = QPainter(self)
        if not painter.isActive():
            return

        try:
            painter.setRenderHint(
                QPainter.RenderHint.Antialiasing
            )

            w = self.width()
            h = self.height()
            if w < 20 or h < 20:
                return

            # ---------------- گرادیانت پس‌زمینه ----------------
            grad = QLinearGradient(0, 0, 0, h)
            grad.setColorAt(
                0.0, QColor(self._theme["bg_top"])
            )
            grad.setColorAt(
                0.5, QColor(self._theme["bg_mid"])
            )
            grad.setColorAt(
                1.0, QColor(self._theme["bg_bottom"])
            )
            painter.fillRect(self.rect(), grad)

            # ---------------- لایه‌ی دور ----------------
            self._paint_back_layer(painter, w, h)

            # ---------------- لایه‌ی میانی ----------------
            key = self._theme_key
            if key == "control_room":
                self._paint_control_room_mid(painter, w, h)
            elif key == "corridor":
                self._paint_corridor_mid(painter, w, h)
            elif key == "data_lab":
                self._paint_data_lab_mid(painter, w, h)
            elif key == "council_hall":
                self._paint_council_hall_mid(painter, w, h)
            elif key in ("space", "night"):
                self._paint_space_mid(painter, w, h, key)

            # ---------------- لایه‌ی نزدیک ----------------
            self._paint_near_layer(painter, w, h)

            # ---------------- رویداد فعال ----------------
            self._paint_event(painter, w, h)
        finally:
            try:
                painter.end()
            except Exception:
                pass

    # ==========================================================
    # لایه‌ی دور (Back)
    # ==========================================================
    def _paint_back_layer(self, painter, w, h):
        key = self._theme_key
        accent = QColor(self._theme["accent"])

        if key in ("space", "night"):
            for star in self._back_data.get("stars", []):
                x = star["x"] * w
                y = star["y"] * h
                twinkle = (
                    star["bright"]
                    * (0.7 + 0.3 * math.sin(
                        self._phase + star["twinkle"]
                    ))
                )
                c = QColor("#FFFFFF")
                c.setAlpha(int(180 * twinkle))
                painter.setBrush(QBrush(c))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(
                    QPointF(x, y), star["size"], star["size"]
                )

        elif key == "control_room":
            # مانیتورهای دور، کوچک، کمرنگ
            for m in self._back_data.get("distant_monitors", []):
                x = m["x"] * w
                y = m["y"] * h
                mw = m["w"] * w
                mh = m["h"] * h
                c = QColor(m["hue"])
                c.setAlpha(45)
                painter.setBrush(QBrush(c))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRect(QRectF(x, y, mw, mh))

        elif key == "corridor":
            # قوس‌های بسیار دور
            cx = w / 2
            cy = h * 0.45
            for arc in self._back_data.get("distant_arcs", []):
                t = arc["t"]
                arc_w = w * (0.15 + 1.2 * t)
                arc_h = h * (0.2 + 1.1 * t)
                c = QColor(accent)
                c.setAlpha(int(20 * (1 - t * 0.8)))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.setPen(QPen(c, 1))
                painter.drawEllipse(
                    QPointF(cx, cy), arc_w / 2, arc_h / 2
                )

        elif key == "data_lab":
            # نقاط داده‌ی دور، کمرنگ
            for node in self._back_data.get("grid_nodes", []):
                x = node["x"] * w
                y = node["y"] * h
                c = QColor(accent)
                c.setAlpha(35)
                painter.setBrush(QBrush(c))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(
                    QPointF(x, y), node["r"], node["r"]
                )

        elif key == "council_hall":
            # صندلی‌های دور
            for seat in self._back_data.get("distant_seats", []):
                x = seat["x"] * w
                y = seat["y"] * h
                c = QColor(accent)
                c.setAlpha(40)
                painter.setBrush(QBrush(c))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(QPointF(x, y), 4, 4)

    # ==========================================================
    # لایه‌ی میانی — چهار تم (منتقل‌شده از نسخه‌ی قبلی)
    # ==========================================================
    def _paint_control_room_mid(self, painter, w, h):
        accent = QColor(self._theme["accent"])

        # چراغ‌های سقف
        for light in self._mid_data.get("lights", []):
            x = light["x"] * w
            y = light["y"] * h
            glow = QRadialGradient(QPointF(x, y), 60)
            c1 = QColor(accent)
            c1.setAlpha(60)
            c2 = QColor(accent)
            c2.setAlpha(0)
            glow.setColorAt(0.0, c1)
            glow.setColorAt(1.0, c2)
            painter.setBrush(QBrush(glow))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPointF(x, y), 60, 60)

        # مانیتورهای اصلی
        for scr in self._mid_data.get("screens", []):
            x = scr["x"] * w
            y = scr["y"] * h
            sw = scr["w"] * w
            sh = scr["h"] * h

            body = QColor("#03060F")
            painter.setBrush(QBrush(body))
            painter.setPen(QPen(accent, 1))
            painter.drawRoundedRect(
                QRectF(x, y, sw, sh), 4, 4
            )

            line_color = QColor(scr["hue"])
            line_color.setAlpha(180)
            painter.setPen(QPen(line_color, 1))

            n_lines = 6
            inner_x = x + sw * 0.08
            inner_w = sw * 0.84
            for i in range(n_lines):
                ly = y + sh * (0.15 + (i + 1) * 0.13)
                wave = 0.5 + 0.5 * math.sin(
                    self._phase + scr["seed"] + i * 0.8
                )
                lw = inner_w * (0.3 + 0.6 * wave)
                painter.drawLine(
                    QPointF(inner_x, ly),
                    QPointF(inner_x + lw, ly),
                )

            blink = 0.5 + 0.5 * math.sin(self._phase * 3)
            dot_color = QColor(scr["hue"])
            dot_color.setAlpha(int(80 + 130 * blink))
            painter.setBrush(QBrush(dot_color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(
                QPointF(x + sw * 0.92, y + sh * 0.08), 2, 2
            )

        # خطوط افقی محیط
        frame_color = QColor(accent)
        frame_color.setAlpha(30)
        painter.setPen(QPen(frame_color, 1))
        for i in range(6):
            y = h * (0.75 + i * 0.03)
            painter.drawLine(
                QPointF(w * 0.05, y), QPointF(w * 0.95, y)
            )

    def _paint_corridor_mid(self, painter, w, h):
        accent = QColor(self._theme["accent"])
        vanishing_x = w * 0.5
        vanishing_y = h * 0.45

        n = 8
        for i in range(n):
            t = (i + 1) / n
            arc_w = w * (0.4 + 0.7 * t)
            arc_h = h * (0.5 + 0.7 * t)
            alpha = int(50 * (1.0 - t * 0.7))
            c = QColor(accent)
            c.setAlpha(alpha)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(c, 1))
            painter.drawEllipse(
                QPointF(vanishing_x, vanishing_y),
                arc_w / 2, arc_h / 2,
            )

        # غبار
        random.seed(42)
        for _ in range(30):
            x = random.random() * w
            y = random.random() * h
            size = random.uniform(0.6, 1.8)
            drift = math.sin(self._phase * 0.5 + x * 0.01) * 5
            c = QColor(accent)
            c.setAlpha(random.randint(30, 90))
            painter.setBrush(QBrush(c))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPointF(x + drift, y), size, size)
        random.seed()

    def _paint_data_lab_mid(self, painter, w, h):
        accent = QColor(self._theme["accent"])

        # شبکه
        grid_color = QColor(accent)
        grid_color.setAlpha(18)
        painter.setPen(QPen(grid_color, 1))
        step = 40
        for x in range(0, w, step):
            painter.drawLine(QPointF(x, 0), QPointF(x, h))
        for y in range(0, h, step):
            painter.drawLine(QPointF(0, y), QPointF(w, y))

        # نقاط داده
        for node in self._mid_data.get("nodes", []):
            x = node["x"] * w
            y = node["y"] * h
            pulse = 0.5 + 0.5 * math.sin(
                self._phase + node["phase"]
            )
            c = QColor(accent)
            c.setAlpha(int(40 + 120 * pulse))
            painter.setBrush(QBrush(c))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(
                QPointF(x, y), node["r"], node["r"]
            )

        # نمودارها
        for chart in self._mid_data.get("charts", []):
            x = chart["x"] * w
            y = chart["y"] * h
            cw = chart["w"] * w
            ch = chart["h"] * h

            box_color = QColor(chart["hue"])
            box_color.setAlpha(50)
            painter.setPen(QPen(box_color, 1))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(QRectF(x, y, cw, ch))

            line_color = QColor(chart["hue"])
            line_color.setAlpha(200)
            painter.setPen(QPen(line_color, 2))

            n_points = 30
            path_pts = []
            for i in range(n_points):
                px = x + (i / (n_points - 1)) * cw
                wave = (
                    0.5
                    + 0.3 * math.sin(
                        i * 0.4 + chart["seed"] + self._phase
                    )
                    + 0.15 * math.sin(
                        i * 0.9 + chart["seed"] * 2
                    )
                )
                py = y + ch * (1.0 - wave)
                path_pts.append(QPointF(px, py))

            for i in range(len(path_pts) - 1):
                painter.drawLine(path_pts[i], path_pts[i + 1])

            for i in range(0, n_points, 4):
                p = path_pts[i]
                painter.setBrush(QBrush(line_color))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(p, 2.5, 2.5)

    def _paint_council_hall_mid(self, painter, w, h):
        accent = QColor(self._theme["accent"])

        for ch in self._mid_data.get("chandeliers", []):
            x = ch["x"] * w
            y = ch["y"] * h

            wire_color = QColor(accent)
            wire_color.setAlpha(60)
            painter.setPen(QPen(wire_color, 1))
            painter.drawLine(QPointF(x, 0), QPointF(x, y))

            glow = QRadialGradient(QPointF(x, y), 80)
            c1 = QColor(accent)
            c1.setAlpha(70)
            c2 = QColor(accent)
            c2.setAlpha(0)
            glow.setColorAt(0.0, c1)
            glow.setColorAt(1.0, c2)
            painter.setBrush(QBrush(glow))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPointF(x, y), 80, 80)

            painter.setBrush(QBrush(accent))
            painter.drawEllipse(QPointF(x, y), 6, 6)

        # میز نیم‌دایره
        cx = w * 0.5
        cy = h * 0.7
        rx = w * 0.42
        ry = h * 0.18

        table_grad = QRadialGradient(
            QPointF(cx, cy), max(rx, ry)
        )
        c1 = QColor(self._theme["secondary"])
        c1.setAlpha(70)
        c2 = QColor(self._theme["secondary"])
        c2.setAlpha(20)
        table_grad.setColorAt(0.0, c1)
        table_grad.setColorAt(1.0, c2)

        painter.setBrush(QBrush(table_grad))
        painter.setPen(QPen(
            QColor(self._theme["secondary"]), 2
        ))
        painter.drawEllipse(QPointF(cx, cy), rx, ry)

        for seat in self._mid_data.get("seats", []):
            angle = seat["angle"]
            sx = cx + rx * math.cos(angle) * 0.85
            sy = cy - ry * math.sin(angle) * 0.85

            c = QColor(accent)
            c.setAlpha(180)
            painter.setBrush(QBrush(c))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPointF(sx, sy), 6, 6)

            c.setAlpha(60)
            painter.setBrush(QBrush(c))
            painter.drawEllipse(QPointF(sx, sy), 12, 12)

    def _paint_space_mid(self, painter, w, h, key):
        if key == "space":
            px = w * 0.82
            py = h * 0.28
            pr = min(w, h) * 0.09

            atmo = QRadialGradient(
                QPointF(px, py), pr * 1.6
            )
            c1 = QColor("#4FC3F7")
            c1.setAlpha(60)
            c2 = QColor("#4FC3F7")
            c2.setAlpha(0)
            atmo.setColorAt(0.0, c1)
            atmo.setColorAt(1.0, c2)
            painter.setBrush(QBrush(atmo))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(
                QPointF(px, py), pr * 1.6, pr * 1.6
            )

            planet = QRadialGradient(
                QPointF(px - pr * 0.3, py - pr * 0.3),
                pr * 1.4,
            )
            planet.setColorAt(0.0, QColor("#2B4A6F"))
            planet.setColorAt(0.7, QColor("#0F2035"))
            planet.setColorAt(1.0, QColor("#050A18"))
            painter.setBrush(QBrush(planet))
            painter.drawEllipse(QPointF(px, py), pr, pr)

        if key == "night":
            mx = w * 0.85
            my = h * 0.22
            mr = min(w, h) * 0.06

            glow = QRadialGradient(QPointF(mx, my), mr * 2.2)
            c1 = QColor("#B0BEC5")
            c1.setAlpha(70)
            c2 = QColor("#B0BEC5")
            c2.setAlpha(0)
            glow.setColorAt(0.0, c1)
            glow.setColorAt(1.0, c2)
            painter.setBrush(QBrush(glow))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(
                QPointF(mx, my), mr * 2.2, mr * 2.2
            )

            painter.setBrush(QBrush(QColor("#E0E0E0")))
            painter.drawEllipse(QPointF(mx, my), mr, mr)

    # ==========================================================
    # لایه‌ی نزدیک (Near) — عناصر تار در گوشه‌ها
    # ==========================================================
    def _paint_near_layer(self, painter, w, h):
        key = self._theme_key

        # در فضا/شب: یک vignette تاریک در گوشه‌ها
        if key in ("space", "night"):
            self._paint_vignette(painter, w, h)
            return

        # برای بقیه تم‌ها: عناصر تیره در لبه‌ها
        near_color = QColor("#000000")
        near_color.setAlpha(120)

        # کنسول پایین
        console = self._near_data.get("console")
        if console:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(near_color))
            painter.drawRect(QRectF(
                console["x"] * w,
                console["y"] * h,
                console["w"] * w,
                console["h"] * h,
            ))
            # خط لبه‌ی نورانی بالای کنسول
            edge_color = QColor(self._theme["accent"])
            edge_color.setAlpha(80)
            painter.setPen(QPen(edge_color, 2))
            painter.drawLine(
                QPointF(0, console["y"] * h),
                QPointF(w, console["y"] * h),
            )

        # پنل‌های کناری
        for panel in self._near_data.get("side_panels", []):
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(near_color))
            painter.drawRect(QRectF(
                panel["x"] * w,
                panel["y"] * h,
                panel["w"] * w,
                panel["h"] * h,
            ))

        # ستون‌های جلو
        for pillar in self._near_data.get("front_pillars", []):
            pc = QColor("#000000")
            pc.setAlpha(150)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(pc))
            painter.drawRect(QRectF(
                pillar["x"] * w,
                pillar["y"] * h,
                pillar["w"] * w,
                pillar["h"] * h,
            ))

        # قوس سقف
        arch = self._near_data.get("ceiling_arch")
        if arch:
            ac = QColor("#000000")
            ac.setAlpha(130)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(ac))
            painter.drawRect(QRectF(
                arch["x"] * w,
                arch["y"] * h,
                arch["w"] * w,
                arch["h"] * h,
            ))

        # ترمینال پایین
        term = self._near_data.get("terminal")
        if term:
            tc = QColor("#000000")
            tc.setAlpha(110)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(tc))
            painter.drawRect(QRectF(
                term["x"] * w,
                term["y"] * h,
                term["w"] * w,
                term["h"] * h,
            ))
            edge_color = QColor(self._theme["accent"])
            edge_color.setAlpha(70)
            painter.setPen(QPen(edge_color, 1))
            painter.drawLine(
                QPointF(0, term["y"] * h),
                QPointF(w, term["y"] * h),
            )

        # لبه‌ی میز
        table = self._near_data.get("table_edge")
        if table:
            tc = QColor("#000000")
            tc.setAlpha(140)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(tc))
            painter.drawRect(QRectF(
                table["x"] * w,
                table["y"] * h,
                table["w"] * w,
                table["h"] * h,
            ))

    # ----------------------------------------------------------
    def _paint_vignette(self, painter, w, h):
        """Vignette تیره در گوشه‌ها برای فضا"""
        grad = QRadialGradient(
            QPointF(w / 2, h / 2), max(w, h) * 0.7
        )
        grad.setColorAt(0.0, QColor(0, 0, 0, 0))
        grad.setColorAt(0.7, QColor(0, 0, 0, 40))
        grad.setColorAt(1.0, QColor(0, 0, 0, 150))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(grad))
        painter.drawRect(0, 0, w, h)