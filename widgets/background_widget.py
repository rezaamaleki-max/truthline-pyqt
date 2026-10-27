"""
ویجت پس‌زمینه هوشمند
- اگر تصویر در assets/backgrounds/{key}_v01.png باشد، استفاده می‌کند
- در غیر این صورت، گرادیانت با رنگ‌های theme رسم می‌کند

نسخه: 1.1.0 (رفع خطاهای Pylance)
"""
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import (
    QPainter, QLinearGradient, QColor, QPixmap, QPen
)
import os

from config import ASSETS_DIR


class BackgroundWidget(QWidget):
    """پس‌زمینه با پشتیبانی از تصویر + gradient fallback"""

    # ✅ پالت‌های رنگی برای هر موقعیت
    THEMES = {
        "menu":        ("#0B1D3A", "#2B4A6F"),
        "space":       ("#000510", "#0B1D3A"),
        "airlock":     ("#1A2A4A", "#4A3A2B"),
        "corridor":    ("#0F1E38", "#2B4A6F"),
        "control":     ("#0B1D3A", "#3A5A7F"),
        "reactor":     ("#3A1A0A", "#8B4513"),
        "coolant":     ("#1A0A0A", "#D32F2F"),
        "data_center": ("#050A18", "#2B4A6F"),
        "council":     ("#1A1A1A", "#B0BEC5"),
        "default":     ("#0B1D3A", "#2B4A6F"),
    }

    def __init__(self, theme_key: str = "default",
                 image_key: str | None = None, parent=None):
        super().__init__(parent)
        self.theme_key = theme_key
        self.image_key = image_key
        # ✅ تعریف صریح برای Pylance
        self._pixmap: QPixmap | None = None
        self._try_load_image()
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

    def _try_load_image(self):
        """تلاش برای بارگذاری تصویر از assets/backgrounds"""
        if self.image_key:
            path = os.path.join(
                ASSETS_DIR, "backgrounds", f"{self.image_key}_v01.png"
            )
            if os.path.exists(path):
                pm = QPixmap(path)
                if not pm.isNull():
                    self._pixmap = pm
                    return

    def paintEvent(self, event):  # type: ignore[reportIncompatibleMethodOverride]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        # ✅ اگر تصویر موجود است، با پوشش کامل رسم کن
        if self._pixmap is not None:
            scaled = self._pixmap.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
            # ✅ لایه تاریک برای خوانایی متن
            painter.fillRect(self.rect(), QColor(0, 0, 0, 80))
            return

        # ✅ گرادیانت fallback با جزئیات بیشتر برای عمق بصری
        top, bottom = self.THEMES.get(
            self.theme_key, self.THEMES["default"]
        )
        grad = QLinearGradient(0, 0, self.width(), self.height())
        grad.setColorAt(0.0, QColor(top))
        grad.setColorAt(0.5, QColor(bottom))
        grad.setColorAt(1.0, QColor(top))
        painter.fillRect(self.rect(), grad)

        # ✅ الگوی خطوط ظریف برای حس صنعتی
        pen = QPen(QColor(79, 195, 247, 15), 1)
        painter.setPen(pen)
        step = 40
        for x in range(0, self.width(), step):
            painter.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), step):
            painter.drawLine(0, y, self.width(), y)