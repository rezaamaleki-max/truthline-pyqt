"""
ویجت نمودار راداری برای نمایش پروفایل شایستگی
=====================================
ویژگی‌ها:
- رسم با QPainter (سریع و حرفه‌ای)
- پشتیبانی از ۴ شایستگی
- نمایش نمرات و برچسب‌ها با فونت Vazirmatn
- طراحی متعادل با شبکه‌بندی واضح

نسخه: 2.1.0
"""
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont, QPolygonF
)
import math


class RadarChart(QWidget):
    """ویجت نمودار راداری برای نمایش پروفایل شایستگی"""

    def __init__(self, parent=None):
        super().__init__(parent)

        # تنظیمات
        self.setMinimumSize(400, 400)

        # داده‌ها
        self.competencies: list[str] = [
            "صداقت و یکپارچگی",
            "قابلیت اعتماد",
            "حل مسئله",
            "مسئولیت‌پذیری",
        ]
        self.scores: list[float] = [0.0, 0.0, 0.0, 0.0]  # بین ۰ تا ۱۰۰

        # رنگ‌ها
        self.bg_color = QColor("#0B1D3A")
        self.grid_color = QColor("#2B4A6F")
        self.axis_color = QColor("#3A5A7F")
        self.data_color = QColor("#4FC3F7")
        self.data_fill_color = QColor(79, 195, 247, 70)
        self.point_color = QColor("#FFFFFF")
        self.text_color = QColor("#FFFFFF")
        self.score_color = QColor("#FF8F00")

        print("✓ RadarChart راه‌اندازی شد")

    def set_scores(self, scores: list[float]):
        """
        تنظیم نمرات شایستگی‌ها

        Args:
            scores: لیست ۴ نمره بین ۰ تا ۱۰۰
        """
        if len(scores) != 4:
            print(f"⚠️ هشدار: انتظار ۴ نمره داشتیم، اما {len(scores)} دریافت شد")
            return

        # محدود کردن نمرات به بازه ۰ تا ۱۰۰
        self.scores = [max(0.0, min(100.0, float(s))) for s in scores]
        self.update()

    def paintEvent(self, event):  # type: ignore[reportIncompatibleMethodOverride]
        """رویداد رسم ویجت"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # محاسبه مرکز و شعاع
        center_x: float = self.width() / 2
        center_y: float = self.height() / 2
        radius: float = min(self.width(), self.height()) / 2 - 70

        # اگر فضا خیلی کم است، رسم نکن
        if radius < 50:
            return

        # ========================================
        # رسم پس‌زمینه
        # ========================================
        painter.fillRect(self.rect(), self.bg_color)

        # ========================================
        # رسم شبکه (Grid) — پنج حلقه هم‌مرکز
        # ========================================
        grid_pen = QPen(self.grid_color, 1, Qt.PenStyle.DashLine)
        painter.setPen(grid_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        for level in range(1, 6):
            r = radius * level / 5
            painter.drawEllipse(QPointF(center_x, center_y), r, r)

        # ========================================
        # رسم خطوط شعاعی (چهار محور)
        # ========================================
        num_axes = len(self.competencies)
        angle_step = 2 * math.pi / num_axes

        axis_pen = QPen(self.axis_color, 1, Qt.PenStyle.SolidLine)
        painter.setPen(axis_pen)

        for i in range(num_axes):
            angle = i * angle_step - math.pi / 2  # شروع از بالا
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            painter.drawLine(
                QPointF(center_x, center_y),
                QPointF(x, y)
            )

        # ========================================
        # ساخت نقاط داده
        # ========================================
        points: list[QPointF] = []
        for i, score in enumerate(self.scores):
            angle = i * angle_step - math.pi / 2
            r = radius * score / 100
            x = center_x + r * math.cos(angle)
            y = center_y + r * math.sin(angle)
            points.append(QPointF(x, y))

        # ========================================
        # رسم ناحیه پر شده
        # ========================================
        polygon = QPolygonF(points)
        painter.setBrush(QBrush(self.data_fill_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPolygon(polygon)

        # ========================================
        # رسم خطوط دور ناحیه
        # ========================================
        outline_pen = QPen(self.data_color, 3)
        painter.setPen(outline_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPolygon(polygon)

        # ========================================
        # رسم نقاط (vertices)
        # ========================================
        painter.setBrush(QBrush(self.point_color))
        painter.setPen(QPen(self.data_color, 2))
        for point in points:
            painter.drawEllipse(point, 6, 6)

        # ========================================
        # رسم برچسب‌ها و نمرات
        # ========================================
        label_font = QFont("Vazirmatn", 12, QFont.Weight.Bold)
        score_font = QFont("Vazirmatn", 13, QFont.Weight.Bold)

        for i, (comp, score) in enumerate(zip(self.competencies, self.scores)):
            angle = i * angle_step - math.pi / 2
            label_r = radius + 45
            x = center_x + label_r * math.cos(angle)
            y = center_y + label_r * math.sin(angle)

            # برچسب شایستگی
            painter.setPen(self.text_color)
            painter.setFont(label_font)
            painter.drawText(
                QRectF(x - 80, y - 22, 160, 22),
                Qt.AlignmentFlag.AlignCenter,
                comp,
            )

            # نمره
            painter.setPen(self.score_color)
            painter.setFont(score_font)
            painter.drawText(
                QRectF(x - 50, y, 100, 22),
                Qt.AlignmentFlag.AlignCenter,
                f"{int(score)}",
            )

        painter.end()