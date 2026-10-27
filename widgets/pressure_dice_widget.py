"""
ویجت تاس فشار شورا — تعیین شدت بازخواست
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QRectF, QPointF
from PyQt6.QtGui import QFont, QPainter, QPen, QBrush, QColor
import math
import time

FONT_FAMILY = "Vazirmatn"


class PressureDiceWidget(QWidget):
    """
    ویجت تاس فشار — یک بار کلیک → عدد ۱ تا ۶ → سطح فشار
    """
    # سیگنال: (عدد تاس، سطح فشار، زمان تصمیم)
    roll_completed = pyqtSignal(int, int, int)

    def __init__(self, roll_duration_ms: int = 1600,
                 button_label: str = "انداختن تاس",
                 intro_text: str = "بر اساس رویه‌ی استاندارد شورا، "
                                   "شدت بازخواست این جلسه تعیین می‌شود.",
                 parent=None):
        super().__init__(parent)
        self.roll_duration_ms = roll_duration_ms
        self.button_label = button_label
        self.intro_text = intro_text

        self.final_value = 0
        self.is_rolling = False
        self.roll_start_time = 0
        self.animation_progress = 0.0

        self.rotation_timer = QTimer(self)
        self.rotation_timer.timeout.connect(self._on_animation_tick)
        self.final_timer = QTimer(self)
        self.final_timer.setSingleShot(True)
        self.final_timer.timeout.connect(self._on_reveal_final)

        self._setup_ui()
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 15, 40, 15)
        main_layout.setSpacing(12)

        # عنوان
        title = QLabel("تعیین رویه‌ی جلسه")
        tf = QFont(FONT_FAMILY, 20)
        tf.setBold(True)
        title.setFont(tf)
        title.setStyleSheet("color: #4FC3F7;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        # توضیح
        desc = QLabel(self.intro_text)
        desc.setFont(QFont(FONT_FAMILY, 12))
        desc.setStyleSheet("color: #CCCCCC;")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        main_layout.addWidget(desc)

        # نمایش تاس
        self.dice_display = _DiceCanvas(self)
        self.dice_display.setMinimumHeight(180)
        main_layout.addWidget(self.dice_display, stretch=1)

        # نمایش عدد
        self.value_label = QLabel("—")
        vf = QFont(FONT_FAMILY, 42)
        vf.setBold(True)
        self.value_label.setFont(vf)
        self.value_label.setStyleSheet("color: #4FC3F7;")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.value_label)

        # نمایش سطح فشار
        self.level_label = QLabel("")
        self.level_label.setFont(QFont(FONT_FAMILY, 14))
        self.level_label.setStyleSheet("color: #FF8F00;")
        self.level_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.level_label.setVisible(False)
        main_layout.addWidget(self.level_label)

        # دکمه
        self.roll_button = QPushButton(self.button_label)
        bf = QFont(FONT_FAMILY, 16)
        bf.setBold(True)
        self.roll_button.setFont(bf)
        self.roll_button.setMinimumHeight(58)
        self.roll_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.roll_button.setStyleSheet("""
            QPushButton {
                background-color: #2B4A6F;
                color: #FFFFFF;
                border: 2px solid #4FC3F7;
                border-radius: 10px;
                padding: 12px;
            }
            QPushButton:hover {
                background-color: #4FC3F7;
                color: #0B1D3A;
                border: 2px solid #FFFFFF;
            }
            QPushButton:disabled {
                background-color: #1A2A4A;
                color: #888888;
                border: 2px solid #444444;
            }
        """)
        self.roll_button.clicked.connect(self._on_roll)
        main_layout.addWidget(self.roll_button)

    # ----------------------------------------------------------------
    def _on_roll(self):
        if self.is_rolling or self.final_value > 0:
            return
        import random
        self.is_rolling = True
        self.roll_start_time = int(time.time() * 1000)
        self.final_value = random.randint(1, 6)
        self.animation_progress = 0.0
        self.roll_button.setEnabled(False)
        self.roll_button.setText("تاس در حال چرخش...")
        self.rotation_timer.start(50)
        self.final_timer.start(self.roll_duration_ms)

    def _on_animation_tick(self):
        self.animation_progress += 50 / self.roll_duration_ms
        if self.animation_progress < 1.0:
            self.dice_display.update()

    def _on_reveal_final(self):
        self.rotation_timer.stop()
        self.is_rolling = False
        self.value_label.setText(str(self.final_value))

        # تعیین سطح فشار
        if self.final_value <= 2:
            level = 1
            level_text = "فشار کم — شورا عمدتاً توضیح می‌خواهد"
            color = "#4FC3F7"
        elif self.final_value <= 4:
            level = 2
            level_text = "فشار متوسط — شورا انتقاد می‌کند"
            color = "#FF8F00"
        else:
            level = 3
            level_text = "فشار زیاد — شورا خشمگین است"
            color = "#D32F2F"

        self.level_label.setText(level_text)
        self.level_label.setStyleSheet(f"color: {color}; font-weight: bold;")
        self.level_label.setVisible(True)
        self.dice_display.update()

        total_time = int(time.time() * 1000) - self.roll_start_time
        self.roll_button.setText("ادامه به بازخواست")
        self.roll_button.setEnabled(True)
        self.roll_button.clicked.disconnect()
        self.roll_button.clicked.connect(
            lambda: self.roll_completed.emit(
                self.final_value, level, total_time
            )
        )

    def get_pressure_level(self) -> int:
        if self.final_value <= 2:
            return 1
        elif self.final_value <= 4:
            return 2
        elif self.final_value > 0:
            return 3
        return 0


# ====================================================================
# صفحه رسم تاس
# ====================================================================
class _DiceCanvas(QWidget):
    def __init__(self, parent_widget):
        super().__init__(parent_widget)
        self.parent_widget = parent_widget
        self.setStyleSheet("background-color: transparent;")

    def paintEvent(self, event):  # type: ignore[reportIncompatibleMethodOverride]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        cx = w / 2
        cy = h / 2
        size = min(w, h) - 40

        a = self.parent_widget

        # محاسبه زاویه چرخش
        angle = 0
        if a.is_rolling:
            angle = int(a.animation_progress * 720) % 360
        elif a.final_value > 0:
            # قفل‌شده
            angle = 0

        painter.translate(cx, cy)
        painter.rotate(angle)
        painter.translate(-cx, -cy)

        # مربع تاس
        rect = QRectF(cx - size/2, cy - size/2, size, size)

        # سایه
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(0, 0, 0, 80)))
        painter.drawRoundedRect(
            QRectF(rect.x() + 5, rect.y() + 5, rect.width(), rect.height()),
            15, 15
        )

        # بدنه تاس
        painter.setBrush(QBrush(QColor(26, 42, 74)))
        pen = QPen(QColor("#4FC3F7"), 3)
        painter.setPen(pen)
        painter.drawRoundedRect(rect, 15, 15)

        # نقاط — بر اساس عدد فعلی (تصادفی در حال چرخش)
        display_value = a.final_value
        if a.is_rolling:
            # در حال چرخش: نمایش ۶ نقطه در حال تغییر
            import random
            display_value = random.randint(1, 6)

        if display_value > 0:
            self._draw_dots(painter, cx, cy, size, display_value)

    def _draw_dots(self, painter, cx, cy, size, value):
        """رسم نقطه‌های تاس بر اساس عدد"""
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#4FC3F7")))

        r = size * 0.06
        offset = size * 0.25

        # مختصات سه سطر و ستون
        positions = {
            (0, 0): (cx - offset, cy - offset),  # بالا-چپ
            (0, 2): (cx - offset, cy),           # وسط-چپ
            (0, 4): (cx - offset, cy + offset),  # پایین-چپ
            (1, 0): (cx, cy - offset),           # بالا-وسط
            (1, 2): (cx, cy),                    # مرکز
            (1, 4): (cx, cy + offset),           # پایین-وسط
            (2, 0): (cx + offset, cy - offset),  # بالا-راست
            (2, 2): (cx + offset, cy),           # وسط-راست
            (2, 4): (cx + offset, cy + offset),  # پایین-راست
        }

        # الگوی نقطه‌ها برای هر عدد
        patterns = {
            1: [(1, 2)],
            2: [(0, 0), (2, 4)],
            3: [(0, 0), (1, 2), (2, 4)],
            4: [(0, 0), (0, 4), (2, 0), (2, 4)],
            5: [(0, 0), (0, 4), (1, 2), (2, 0), (2, 4)],
            6: [(0, 0), (0, 2), (0, 4), (2, 0), (2, 2), (2, 4)],
        }

        for key in patterns.get(value, []):
            x, y = positions[key]
            painter.drawEllipse(QPointF(x, y), r, r)