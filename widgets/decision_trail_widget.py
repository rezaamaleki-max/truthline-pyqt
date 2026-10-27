"""
نقشه‌ی تصمیم — خط افقی با نقاط توپر/خالی
============================================
طراحی بی‌طرف: هیچ رنگ یا کیفیتی نشان نمی‌دهد.
- نقطه‌ی توپر: تصمیم گرفته‌شده
- نقطه‌ی خالی: در انتظار

نسخه: 1.0.0
"""
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor


class DecisionTrailWidget(QWidget):
    """نقشه‌ی تصمیم — خط افقی با نقاط"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._total: int = 0
        self._filled: int = 0
        self.setMinimumHeight(26)
        self.setMinimumWidth(180)
        self.setStyleSheet("background: transparent;")

    def set_total(self, total: int):
        self._total = max(0, int(total))
        self._filled = 0
        self.update()

    def mark_next(self):
        if self._filled < self._total:
            self._filled += 1
            self.update()

    def reset(self):
        self._filled = 0
        self.update()

    def paintEvent(self, event):  # type: ignore
        if self._total <= 0:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        cy = h / 2

        # نقطه‌های شروع و پایان
        margin = 12
        start_x = margin
        end_x = w - margin

        if self._total == 1:
            positions = [(start_x + end_x) / 2]
        else:
            step = (end_x - start_x) / (self._total - 1)
            positions = [start_x + i * step
                         for i in range(self._total)]

        # خط افقی
        line_color = QColor(79, 195, 247, 80)
        painter.setPen(QPen(line_color, 2))
        painter.drawLine(
            int(start_x), int(cy), int(end_x), int(cy)
        )

        # نقاط
        for i, x in enumerate(positions):
            if i < self._filled:
                # توپر
                painter.setPen(QPen(QColor("#4FC3F7"), 2))
                painter.setBrush(QBrush(QColor("#4FC3F7")))
                painter.drawEllipse(QPointF(x, cy), 6, 6)
            else:
                # خالی
                painter.setPen(QPen(QColor(79, 195, 247, 130), 2))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawEllipse(QPointF(x, cy), 6, 6)

        painter.end()