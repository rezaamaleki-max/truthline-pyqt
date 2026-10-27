"""
ویجت کالیبراسیون طاقت‌فرسا — نسخه ۳.۰
==========================================
۶ حسگر با ۳ نوع مختلف + بازخورد بصری زنده

تغییرات نسخه ۳.۰:
- نوار هدف گرافیکی برای هر حسگر (محدوده‌ی سبز)
- بازخورد رنگی عدد (سبز = در محدوده)
- رنگ حاشیه‌ی کارت بر اساس وضعیت
- نوار پیشرفت ۶ نقطه‌ای
- حفظ API قبلی (submit_btn، shortcut_btn، signal)

نسخه: 3.0.0
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider,
    QPushButton, QFrame, QMessageBox, QDial, QGridLayout,
    QSizePolicy
)
from PyQt6.QtCore import (
    Qt, pyqtSignal, QPointF, QRectF
)
from PyQt6.QtGui import (
    QFont, QPainter, QPen, QBrush, QColor
)
import time

FONT_FAMILY = "Vazirmatn"


# ====================================================================
# نوار هدف گرافیکی
# ====================================================================
class _TargetZoneBar(QWidget):
    """نوار افقی که محدوده‌ی هدف را با رنگ سبز نشان می‌دهد"""

    def __init__(
        self,
        target: float,
        tolerance: float,
        val_min: float = 0.0,
        val_max: float = 100.0,
        parent=None,
    ):
        super().__init__(parent)
        self.target = target
        self.tolerance = tolerance
        self.val_min = val_min
        self.val_max = val_max
        self._current = (val_min + val_max) / 2.0

        self.setMinimumHeight(8)
        self.setMaximumHeight(14)
        self.setStyleSheet("background: transparent;")

    def set_value(self, value: float):
        self._current = float(value)
        self.update()

    def paintEvent(self, event):  # type: ignore
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        margin = 4.0

        # پس‌زمینه
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(26, 42, 74)))
        painter.drawRoundedRect(
            QRectF(margin, 2, w - margin * 2, h - 4),
            3, 3,
        )

        # محدوده‌ی هدف (سبز)
        v_range = self.val_max - self.val_min
        if v_range > 0:
            low = self.target - self.tolerance
            high = self.target + self.tolerance
            x_low = (
                margin
                + (low - self.val_min) / v_range
                * (w - margin * 2)
            )
            x_high = (
                margin
                + (high - self.val_min) / v_range
                * (w - margin * 2)
            )
            x_low = max(margin, min(w - margin, x_low))
            x_high = max(margin, min(w - margin, x_high))

            painter.setBrush(QBrush(QColor(76, 175, 80, 140)))
            painter.drawRect(
                QRectF(x_low, 2, x_high - x_low, h - 4)
            )

        # نشانگر موقعیت فعلی
        if v_range > 0:
            norm = (self._current - self.val_min) / v_range
        else:
            norm = 0.5
        norm = max(0.0, min(1.0, norm))
        x_pos = margin + norm * (w - margin * 2)

        painter.setPen(QPen(QColor(79, 195, 247), 1))
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.drawEllipse(QPointF(x_pos, h / 2.0), 4, 4)

        painter.end()


# ====================================================================
# نوار پیشرفت نقطه‌ای
# ====================================================================
class _ProgressDots(QWidget):
    """ردیفی از نقاط که با رسیدن هر حسگر به هدف، سبز می‌شوند"""

    def __init__(self, count: int = 6, parent=None):
        super().__init__(parent)
        self.count = max(1, count)
        self._states: list = [False] * self.count

        self.setMinimumHeight(18)
        self.setMaximumHeight(18)
        self.setMinimumWidth(self.count * 22)
        self.setStyleSheet("background: transparent;")

    def set_state(self, index: int, in_zone: bool):
        if 0 <= index < self.count:
            self._states[index] = bool(in_zone)
            self.update()

    def reset(self):
        self._states = [False] * self.count
        self.update()

    def paintEvent(self, event):  # type: ignore
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        step = w / self.count
        radius = min(7.0, step * 0.3)

        for i in range(self.count):
            cx = step * (i + 0.5)
            cy = h / 2.0

            if self._states[i]:
                # در محدوده
                painter.setBrush(QBrush(QColor(76, 175, 80)))
                painter.setPen(QPen(QColor(255, 255, 255), 2))
            else:
                # هنوز نه
                painter.setBrush(QBrush(QColor(60, 80, 110)))
                painter.setPen(QPen(QColor(79, 195, 247, 180), 2))

            painter.drawEllipse(QPointF(cx, cy), radius, radius)

        painter.end()


# ====================================================================
# ویجت اصلی
# ====================================================================
class CalibrationWidget(QWidget):
    """ویجت کالیبراسیون حسگرها — نسخه ۳.۰"""

    calibration_done = pyqtSignal(dict)

    def __init__(self, sensors: list, parent=None):
        super().__init__(parent)
        self.sensors = sensors
        self.controls: list = []
        self.value_labels: list = []
        self.zone_bars: list = []
        self.sensor_frames: list = []

        self.start_time = 0
        self.is_done = False
        self.cheat_used = False

        self._setup_ui()
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

    # ================================================================
    # ساخت UI
    # ================================================================
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 12, 30, 12)
        main_layout.setSpacing(8)

        # ---------- عنوان ----------
        title = QLabel("کالیبراسیون دستی حسگرها")
        tf = QFont(FONT_FAMILY, 20)
        tf.setBold(True)
        title.setFont(tf)
        title.setStyleSheet("color: #4FC3F7;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        # ---------- توضیح ----------
        desc = QLabel(
            f"{len(self.sensors)} حسگر باید کالیبره شوند. "
            "هر کنترل را طوری تنظیم کنید که نشانگر سفید داخل "
            "محدوده‌ی سبز قرار بگیرد."
        )
        desc.setFont(QFont(FONT_FAMILY, 11))
        desc.setStyleSheet("color: #CCCCCC;")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        main_layout.addWidget(desc)

        # ---------- نوار پیشرفت نقطه‌ای ----------
        progress_frame = QFrame()
        progress_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(26, 42, 74, 0.9);
                border: 2px solid #FF8F00;
                border-radius: 8px;
            }
        """)
        pf_layout = QHBoxLayout(progress_frame)
        pf_layout.setContentsMargins(15, 6, 15, 6)
        pf_layout.setSpacing(12)

        pf_label = QLabel("پیشرفت:")
        pf_label.setFont(QFont(FONT_FAMILY, 12, QFont.Weight.Bold))
        pf_label.setStyleSheet("color: #FF8F00; border: none;")
        pf_layout.addWidget(pf_label)

        self.progress_dots = _ProgressDots(len(self.sensors))
        pf_layout.addWidget(self.progress_dots, 1)

        self.progress_count_label = QLabel(
            f"0 / {len(self.sensors)}"
        )
        cpf = QFont(FONT_FAMILY, 14, QFont.Weight.Bold)
        self.progress_count_label.setFont(cpf)
        self.progress_count_label.setStyleSheet(
            "color: #FFFFFF; border: none;"
        )
        self.progress_count_label.setLayoutDirection(
            Qt.LayoutDirection.LeftToRight
        )
        pf_layout.addWidget(self.progress_count_label)

        main_layout.addWidget(progress_frame)

        # ---------- گرید ۳ ستون ----------
        grid = QGridLayout()
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(6)

        for i, sensor in enumerate(self.sensors):
            row = i // 3
            col = i % 3
            widget = self._create_sensor_widget(sensor, i)
            grid.addWidget(widget, row, col)
            grid.setColumnStretch(col, 1)
            grid.setRowStretch(row, 1)

        main_layout.addLayout(grid, stretch=1)

        # ---------- دکمه‌ها ----------
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)

        self.shortcut_btn = QPushButton("استفاده از میان‌بر")
        sf = QFont(FONT_FAMILY, 13)
        self.shortcut_btn.setFont(sf)
        self.shortcut_btn.setMinimumHeight(44)
        self.shortcut_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.shortcut_btn.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.shortcut_btn.setStyleSheet("""
            QPushButton {
                background-color: #4A3A2B;
                color: #FFB74D;
                border: 2px dashed #FF8F00;
                border-radius: 8px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #FF8F00;
                color: #0B1D3A;
                border: 2px solid #FFFFFF;
            }
            QPushButton:disabled {
                background-color: #1A1A1A;
                color: #666666;
                border: 2px solid #444444;
            }
        """)
        self.shortcut_btn.setToolTip(
            "میان‌بر مخفی: سیستم فکر می‌کند همه حسگرها "
            "کالیبره شده‌اند."
        )
        self.shortcut_btn.clicked.connect(self._on_shortcut)
        buttons_layout.addWidget(self.shortcut_btn, 1)

        self.submit_btn = QPushButton("ثبت کالیبراسیون دقیق")
        bf = QFont(FONT_FAMILY, 15)
        bf.setBold(True)
        self.submit_btn.setFont(bf)
        self.submit_btn.setMinimumHeight(44)
        self.submit_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.submit_btn.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.submit_btn.setStyleSheet("""
            QPushButton {
                background-color: #2B4A6F;
                color: #FFFFFF;
                border: 2px solid #4FC3F7;
                border-radius: 8px;
                padding: 10px;
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
        self.submit_btn.clicked.connect(self._on_submit_normal)
        buttons_layout.addWidget(self.submit_btn, 2)

        main_layout.addLayout(buttons_layout)
        self.start_time = int(time.time() * 1000)

    # ================================================================
    # حسگرها
    # ================================================================
    def _create_sensor_widget(self, sensor, index):
        stype = sensor.get("type", "horizontal")
        if stype == "dial":
            return self._create_dial_sensor(sensor, index)
        if stype == "vertical":
            return self._create_vertical_sensor(sensor, index)
        return self._create_horizontal_sensor(sensor, index)

    # ----------------------------------------------------------------
    def _create_horizontal_sensor(self, sensor, index):
        frame = self._make_sensor_frame()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        layout.addLayout(self._make_sensor_header(sensor))

        zone_bar = _TargetZoneBar(
            target=sensor["target"],
            tolerance=sensor["tolerance"],
            val_min=0.0, val_max=100.0,
        )
        layout.addWidget(zone_bar)
        self.zone_bars.append(zone_bar)

        import random
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(0, 1000)
        # ✅ مقدار اولیه با فاصله‌ی تصادفی از هدف — تا مسئله
        #    "خود به خود درست است" رخ ندهد
        target_slider = int(sensor["target"] * 10)
        offset = random.choice([-180, -120, 120, 180])
        initial = max(0, min(1000, target_slider + offset))
        slider.setValue(initial)
        slider.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        slider.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._apply_slider_style(slider, vertical=False)
        layout.addWidget(slider)

        value_lbl = self._make_value_label()
        layout.addWidget(
            value_lbl,
            alignment=Qt.AlignmentFlag.AlignCenter,
        )

        slider.valueChanged.connect(
            lambda v, lbl=value_lbl, idx=index, zb=zone_bar:
                self._on_control_changed(idx, v, lbl, zb)
        )

        self.controls.append(slider)
        self.value_labels.append(value_lbl)
        self.sensor_frames.append(frame)
        return frame

    # ----------------------------------------------------------------
    def _create_dial_sensor(self, sensor, index):
        frame = self._make_sensor_frame()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        layout.addLayout(self._make_sensor_header(sensor))

        zone_bar = _TargetZoneBar(
            target=sensor["target"],
            tolerance=sensor["tolerance"],
            val_min=0.0, val_max=100.0,
        )
        layout.addWidget(zone_bar)
        self.zone_bars.append(zone_bar)

        import random
        dial = QDial()
        dial.setRange(0, 1000)
        # ✅ مقدار اولیه با فاصله‌ی تصادفی از هدف
        target_dial = int(sensor["target"] * 10)
        offset = random.choice([-180, -120, 120, 180])
        initial = max(0, min(1000, target_dial + offset))
        dial.setValue(initial)
        # ✅ حداقل اندازه به‌جای اندازه‌ی ثابت — اجازه‌ی
        #    کوچک‌شدن هنگام resize
        dial.setMinimumSize(44, 44)
        dial.setMaximumSize(80, 80)
        dial.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Preferred,
        )
        dial.setNotchesVisible(True)
        dial.setWrapping(False)
        dial.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        dial.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        # ⚠️ حذف border-radius ثابت — با تغییر اندازه
        #    مربع دیده می‌شود. از استایل پیش‌فرض استفاده می‌کنیم.
        dial.setStyleSheet("""
            QDial {
                background-color: #1A2A4A;
                border: 2px solid #4FC3F7;
            }
        """)
        layout.addWidget(
            dial, alignment=Qt.AlignmentFlag.AlignCenter
        )

        value_lbl = self._make_value_label()
        layout.addWidget(
            value_lbl,
            alignment=Qt.AlignmentFlag.AlignCenter,
        )

        dial.valueChanged.connect(
            lambda v, lbl=value_lbl, idx=index, zb=zone_bar:
                self._on_control_changed(idx, v, lbl, zb)
        )

        self.controls.append(dial)
        self.value_labels.append(value_lbl)
        self.sensor_frames.append(frame)
        return frame

    # ----------------------------------------------------------------
    def _create_vertical_sensor(self, sensor, index):
        frame = self._make_sensor_frame()
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        layout.addLayout(self._make_sensor_header(sensor))

        zone_bar = _TargetZoneBar(
            target=sensor["target"],
            tolerance=sensor["tolerance"],
            val_min=0.0, val_max=100.0,
        )
        layout.addWidget(zone_bar)
        self.zone_bars.append(zone_bar)

        row = QHBoxLayout()
        row.setSpacing(4)

        import random
        slider = QSlider(Qt.Orientation.Vertical)
        slider.setRange(0, 1000)
        target_slider = int(sensor["target"] * 10)
        offset = random.choice([-180, -120, 120, 180])
        initial = max(0, min(1000, target_slider + offset))
        slider.setValue(initial)
        # ✅ حداقل ارتفاع به‌جای ارتفاع ثابت
        slider.setMinimumHeight(44)
        slider.setMaximumHeight(80)
        slider.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Preferred,
        )
        slider.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        slider.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._apply_slider_style(slider, vertical=True)
        row.addWidget(
            slider,
            alignment=Qt.AlignmentFlag.AlignCenter,
        )

        value_lbl = self._make_value_label()
        row.addWidget(
            value_lbl,
            alignment=Qt.AlignmentFlag.AlignCenter,
        )
        row.addStretch()

        layout.addLayout(row)

        slider.valueChanged.connect(
            lambda v, lbl=value_lbl, idx=index, zb=zone_bar:
                self._on_control_changed(idx, v, lbl, zb)
        )

        self.controls.append(slider)
        self.value_labels.append(value_lbl)
        self.sensor_frames.append(frame)
        return frame

    # ================================================================
    # عناصر کمکی
    # ================================================================
    def _make_sensor_frame(self):
        f = QFrame()
        f.setStyleSheet(self._frame_normal_style())
        f.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        return f

    def _frame_normal_style(self) -> str:
        return """
            QFrame {
                background-color: rgba(26, 42, 74, 0.7);
                border: 1px solid #4FC3F7;
                border-radius: 8px;
            }
        """

    def _frame_inzone_style(self) -> str:
        return """
            QFrame {
                background-color: rgba(26, 42, 74, 0.7);
                border: 2px solid #4CAF50;
                border-radius: 8px;
            }
        """

    def _make_sensor_header(self, sensor):
        h = QHBoxLayout()
        name_lbl = QLabel(sensor["name"])
        name_lbl.setFont(
            QFont(FONT_FAMILY, 10, QFont.Weight.Bold)
        )
        name_lbl.setStyleSheet(
            "color: #FFFFFF; border: none;"
        )
        h.addWidget(name_lbl)
        h.addStretch()

        lo = sensor["target"] - sensor["tolerance"]
        hi = sensor["target"] + sensor["tolerance"]
        # ✅ LTR برای بازه‌ی عددی — تا در RTL جابجا نشود
        target_lbl = QLabel(f"هدف: {lo:.0f}–{hi:.0f}")
        target_lbl.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        target_lbl.setAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignVCenter
        )
        target_lbl.setFont(QFont(FONT_FAMILY, 9))
        target_lbl.setStyleSheet(
            "color: #4CAF50; border: none;"
        )
        target_lbl.setLayoutDirection(
            Qt.LayoutDirection.LeftToRight
        )
        h.addWidget(target_lbl)
        return h

    def _make_value_label(self):
        lbl = QLabel("50.0")
        lbl.setFont(
            QFont(FONT_FAMILY, 12, QFont.Weight.Bold)
        )
        lbl.setStyleSheet("color: #FF8F00; border: none;")
        lbl.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        # ✅ عرض کوچک‌تر تا در پنجره‌ی کوچک فشرده نشود
        lbl.setMinimumWidth(40)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return lbl

    def _apply_slider_style(self, slider, vertical=False):
        if vertical:
            slider.setStyleSheet("""
                QSlider::groove:vertical {
                    width: 8px;
                    background: #1A2A4A;
                    border-radius: 4px;
                    border: 1px solid #4FC3F7;
                }
                QSlider::handle:vertical {
                    background: #4FC3F7;
                    border: 2px solid #FFFFFF;
                    width: 14px;
                    height: 14px;
                    margin: 0 -4px;
                    border-radius: 7px;
                }
            """)
        else:
            slider.setStyleSheet("""
                QSlider::groove:horizontal {
                    height: 8px;
                    background: #1A2A4A;
                    border-radius: 4px;
                    border: 1px solid #4FC3F7;
                }
                QSlider::handle:horizontal {
                    background: #4FC3F7;
                    border: 2px solid #FFFFFF;
                    width: 14px;
                    height: 14px;
                    margin: -4px 0;
                    border-radius: 7px;
                }
            """)

    # ================================================================
    # رویداد تغییر کنترل
    # ================================================================
    def _on_control_changed(self, index, raw_value, label, zone_bar):
        value = raw_value / 10.0
        label.setText(f"{value:.1f}")

        zone_bar.set_value(value)

        sensor = self.sensors[index]
        in_zone = (
            abs(value - sensor["target"]) <= sensor["tolerance"]
        )

        if in_zone:
            label.setStyleSheet(
                "color: #4CAF50; border: none;"
            )
            if index < len(self.sensor_frames):
                self.sensor_frames[index].setStyleSheet(
                    self._frame_inzone_style()
                )
        else:
            label.setStyleSheet(
                "color: #FF8F00; border: none;"
            )
            if index < len(self.sensor_frames):
                self.sensor_frames[index].setStyleSheet(
                    self._frame_normal_style()
                )

        self.progress_dots.set_state(index, in_zone)
        self._update_progress()

    # ================================================================
    def _update_progress(self):
        in_zone = 0
        for i, sensor in enumerate(self.sensors):
            if i >= len(self.controls):
                continue
            value = self.controls[i].value() / 10.0
            if abs(value - sensor["target"]) <= sensor["tolerance"]:
                in_zone += 1

        total = len(self.sensors)
        self.progress_count_label.setText(f"{in_zone} / {total}")

        if in_zone == total:
            self.progress_count_label.setStyleSheet(
                "color: #4CAF50; border: none;"
            )
        elif in_zone >= total // 2:
            self.progress_count_label.setStyleSheet(
                "color: #FF8F00; border: none;"
            )
        else:
            self.progress_count_label.setStyleSheet(
                "color: #FFFFFF; border: none;"
            )

    # ================================================================
    # میان‌بر (cheat)
    # ================================================================
    def _on_shortcut(self):
        if self.is_done:
            return

        # ✅ پیام کاملاً ضمنی — پیشنهاد کمک از رحیمی
        #    هیچ اشاره‌ی صریحی به اخلاقیات یا عواقب نیست
        msg = QMessageBox(self)
        msg.setWindowTitle("پیام مهندس رحیمی")
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setText(
            "مهندس رحیمی: «تکنسین، راستش این چند روز "
            "همه‌مون تحت فشاریم. این حسگرها معمولاً نویز "
            "کمی دارن و تنظیمات کارخانه‌ای‌شون تقریباً "
            "کافیه. اگه بخوای، من الان از راه دور همه‌شون "
            "رو تأیید می‌کنم. تو وقتت رو بذار روی "
            "کار راکتور که فوری‌تره.»"
        )
        msg.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        btn_accept = msg.addButton(
            "باشه، ممنون",
            QMessageBox.ButtonRole.AcceptRole,
        )
        btn_refuse = msg.addButton(
            "نه، خودم انجام می‌دم",
            QMessageBox.ButtonRole.RejectRole,
        )
        msg.setDefaultButton(btn_refuse)
        msg.exec()

        if msg.clickedButton() != btn_accept:
            return

        self.cheat_used = True
        self.is_done = True
        total_time = int(time.time() * 1000) - self.start_time

        results = []
        for sensor in self.sensors:
            results.append({
                "name": sensor["name"],
                "value": sensor["target"],
                "target": sensor["target"],
                "error": 0.0,
                "in_zone": True,
            })

        self._disable_all()
        self.submit_btn.setText("✓ ثبت شد")
        self.shortcut_btn.setText("✓ تأیید شد")

        # به‌روزرسانی بصری
        for i in range(len(self.sensors)):
            self.progress_dots.set_state(i, True)
            if i < len(self.value_labels):
                self.value_labels[i].setText(
                    f"{self.sensors[i]['target']:.1f}"
                )
                self.value_labels[i].setStyleSheet(
                    "color: #4CAF50; border: none;"
                )
            if i < len(self.sensor_frames):
                self.sensor_frames[i].setStyleSheet(
                    self._frame_inzone_style()
                )
        self._update_progress()

        self.calibration_done.emit({
            "results": results,
            "in_zone_count": len(self.sensors),
            "total_count": len(self.sensors),
            "out_zone_count": 0,
            "total_time_ms": total_time,
            "cheat_used": True,
        })

    # ================================================================
    # ثبت دقیق
    # ================================================================
    def _on_submit_normal(self):
        if self.is_done:
            return
        self.is_done = True
        total_time = int(time.time() * 1000) - self.start_time

        results = []
        in_zone_count = 0
        for i, sensor in enumerate(self.sensors):
            value = self.controls[i].value() / 10.0
            error = abs(value - sensor["target"])
            in_zone = error <= sensor["tolerance"]
            if in_zone:
                in_zone_count += 1
            results.append({
                "name": sensor["name"],
                "value": round(value, 1),
                "target": sensor["target"],
                "error": round(error, 2),
                "in_zone": in_zone,
            })

        self._disable_all()
        self.submit_btn.setText("✓ کالیبراسیون ثبت شد")

        self.calibration_done.emit({
            "results": results,
            "in_zone_count": in_zone_count,
            "total_count": len(self.sensors),
            "out_zone_count": len(self.sensors) - in_zone_count,
            "total_time_ms": total_time,
            "cheat_used": False,
        })

    # ================================================================
    def _disable_all(self):
        for c in self.controls:
            c.setEnabled(False)
        self.submit_btn.setEnabled(False)
        self.shortcut_btn.setEnabled(False)