"""
ویجت تحلیلگر کوانتومی — اندازه‌گیر صداقت
بر اساس فیلم‌نامه: سه قرائت با اعداد از پیش تعیین‌شده
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QRectF, QPointF
from PyQt6.QtGui import (
    QFont, QPainter, QPen, QBrush, QColor,
    QRadialGradient, QLinearGradient, QPainterPath,
)
import math
import time

FONT_FAMILY = "Vazirmatn"


class QuantumAnalyzerWidget(QWidget):
    """
    ویجت تحلیلگر کوانتومی با سه قرائت از پیش تعیین‌شده
    """
    # سیگنال: (لیست قرائت‌ها، زمان کل به میلی‌ثانیه)
    sequence_completed = pyqtSignal(list, int)

    def __init__(self, readings: list, unit: str = "دامنه موج",
                 button_label: str = "فروپاشی تابع موج",
                 activation_delay_ms: int = 1400,
                 warning_text: str = "", parent=None):
        super().__init__(parent)
        self.readings = readings
        self.unit = unit
        self.button_label = button_label
        self.activation_delay_ms = activation_delay_ms
        self.warning_text = warning_text

        self.current_index = 0
        self.results = []
        self.is_animating = False
        self.sequence_start_time = 0
        self.sequence_started = False
        self.current_display_number = None

        # رنگ‌های هولوگرام
        self.holo_color = QColor("#4FC3F7")

        # انیمیشن چرخش ذرات — ✅ تایمر به عنوان فرزند ویجت
        self.rotation_angle = 0.0
        self.rotation_timer = QTimer(self)
        self.rotation_timer.timeout.connect(self._rotate_particles)

        # تایمر ظاهر شدن عدد — ✅ تایمر به عنوان فرزند ویجت
        self.reveal_timer = QTimer(self)
        self.reveal_timer.setSingleShot(True)
        self.reveal_timer.timeout.connect(self._on_reveal)

        self._setup_ui()
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

    # ----------------------------------------------------------------
    # ساخت UI
    # ----------------------------------------------------------------
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 15, 40, 15)
        main_layout.setSpacing(12)

        # عنوان
        title = QLabel("تحلیلگر کوانتومی")
        tf = QFont(FONT_FAMILY, 22); tf.setBold(True)
        title.setFont(tf)
        title.setStyleSheet("color: #4FC3F7;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        # توضیح
        desc = QLabel(
            f"برای اندازه‌گیری ناهنجاری سامانه خنک‌کننده، "
            f"سه بار تحلیلگر را فعال کنید."
        )
        desc.setFont(QFont(FONT_FAMILY, 12))
        desc.setStyleSheet("color: #CCCCCC;")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        main_layout.addWidget(desc)

        # ناحیه هولوگرام
        self.hologram_widget = _HologramCanvas(self)
        self.hologram_widget.setMinimumHeight(220)
        main_layout.addWidget(self.hologram_widget, stretch=1)

        # سابقه قرائت‌ها
        self.history_frame = QFrame()
        self.history_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(26, 42, 74, 0.7);
                border: 1px solid #4FC3F7;
                border-radius: 8px;
            }
        """)
        history_layout = QHBoxLayout(self.history_frame)
        history_layout.setContentsMargins(15, 8, 15, 8)
        history_layout.setSpacing(15)

        history_lbl = QLabel("سابقه قرائت‌ها:")
        history_lbl.setFont(QFont(FONT_FAMILY, 12))
        history_lbl.setStyleSheet("color: #FFFFFF; border: none;")
        history_layout.addWidget(history_lbl)

        self.history_values = QLabel("—")
        self.history_values.setFont(QFont(FONT_FAMILY, 14, QFont.Weight.Bold))
        self.history_values.setStyleSheet("color: #4FC3F7; border: none;")
        self.history_values.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        history_layout.addWidget(self.history_values)
        history_layout.addStretch()
        main_layout.addWidget(self.history_frame)

        # وضعیت
        self.status_label = QLabel("")
        self.status_label.setFont(QFont(FONT_FAMILY, 12))
        self.status_label.setStyleSheet("color: #4FC3F7;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.status_label)

        # هشدار
        self.warning_label = QLabel("")
        self.warning_label.setFont(QFont(FONT_FAMILY, 11))
        self.warning_label.setStyleSheet(
            "color: #FF8F00; padding: 8px; border: 1px dashed #FF8F00; "
            "border-radius: 6px; background-color: rgba(255, 143, 0, 0.08);"
        )
        self.warning_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.warning_label.setWordWrap(True)
        self.warning_label.setVisible(False)
        main_layout.addWidget(self.warning_label)

        # دکمه فعال‌سازی
        self.activate_button = QPushButton(self.button_label)
        btn_font = QFont(FONT_FAMILY, 16); btn_font.setBold(True)
        self.activate_button.setFont(btn_font)
        self.activate_button.setMinimumHeight(58)
        self.activate_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.activate_button.setStyleSheet("""
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
            QPushButton:pressed {
                background-color: #1A2A4A;
                color: #4FC3F7;
            }
            QPushButton:disabled {
                background-color: #1A2A4A;
                color: #888888;
                border: 2px solid #444444;
            }
        """)
        self.activate_button.clicked.connect(self._on_button_clicked)
        main_layout.addWidget(self.activate_button)

        # شروع چرخش ذرات
        self.rotation_timer.start(50)

    # ----------------------------------------------------------------
    # مدیریت کلیک دکمه
    # ----------------------------------------------------------------
    def _on_button_clicked(self):
        if self.current_index >= len(self.readings):
            self._on_finish()
        else:
            self._on_activate()

    def _on_activate(self):
        if self.is_animating:
            return
        if not self.sequence_started:
            self.sequence_start_time = int(time.time() * 1000)
            self.sequence_started = True

        # ✅ صدای پالس کوانتومی
        try:
            from core.audio_manager import get_audio_manager
            get_audio_manager().play_sfx("scan")
        except Exception:
            pass

        self.is_animating = True
        self.activate_button.setEnabled(False)
        self.status_label.setText(
            f"⏳ در حال فروپاشی تابع موج... "
            f"(قرائت {self.current_index + 1} از {len(self.readings)})"
        )
        self.warning_label.setVisible(False)
        self.current_display_number = None
        self.hologram_widget.update()
        self.reveal_timer.start(self.activation_delay_ms)

    def _on_reveal(self):
        if self.current_index >= len(self.readings):
            return

        value = self.readings[self.current_index]
        self.results.append(value)
        self.current_display_number = value

        # ✅ صدای پالس
        try:
            from core.audio_manager import get_audio_manager
            get_audio_manager().play_sfx("scan")
        except Exception:
            pass

        # به‌روزرسانی سابقه
        history_str = "  |  ".join([f"{v:.1f}" for v in self.results])
        self.history_values.setText(history_str)

        self.status_label.setText(
            f"✓ قرائت {self.current_index + 1}: {value:.1f} {self.unit}"
        )
        self.hologram_widget.update()
        self.current_index += 1
        self.is_animating = False

        if self.current_index >= len(self.readings):
            # تمام شد
            avg = sum(self.readings) / len(self.readings)
            self.status_label.setText(
                f"✓ هر سه قرائت انجام شد. میانگین: {avg:.2f} {self.unit}"
            )
            if self.warning_text:
                self.warning_label.setText(f"⚠  {self.warning_text}")
                self.warning_label.setVisible(True)
            self.activate_button.setText("ادامه به گزارش")
            self.activate_button.setEnabled(True)
        else:
            self.activate_button.setText(
                f"فعال‌سازی مجدد ({self.current_index + 1} از {len(self.readings)})"
            )
            self.activate_button.setEnabled(True)

    def _on_finish(self):
        total_time = int(time.time() * 1000) - self.sequence_start_time
        self.rotation_timer.stop()
        self.sequence_completed.emit(self.results.copy(), total_time)

    def _rotate_particles(self):
        self.rotation_angle = (self.rotation_angle + 3) % 360
        self.hologram_widget.update()


# ====================================================================
# صفحه رسم هولوگرام
# ====================================================================
class _HologramCanvas(QWidget):
    """صفحه رسم هولوگرام — نسخه 3.1 با ۱۴ لایه + افکت‌های پیشرفته"""

    def __init__(self, analyzer: "QuantumAnalyzerWidget"):
        super().__init__(analyzer)
        self.analyzer = analyzer
        self.setStyleSheet("background-color: transparent;")

    # --------------------------------------------------------------
    @staticmethod
    def _prand(seed: float, frame_seed: float) -> float:
        """pseudo-random [0,1)"""
        x = math.sin(seed * 12.9898 + frame_seed * 78.233) * 43758.5453
        return x - math.floor(x)

    # --------------------------------------------------------------
    def paintEvent(self, event):  # type: ignore[reportIncompatibleMethodOverride]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w_int = self.width()
        h_int = self.height()
        if w_int < 20 or h_int < 20:
            painter.end()
            return

        w = float(w_int)
        h = float(h_int)
        cx = w / 2.0
        cy = h / 2.0
        radius = min(w, h) / 2.0 - 30.0

        a = self.analyzer

        # ✅ استخراج امن
        ra_raw = getattr(a, "rotation_angle", 0.0)
        rotation_angle: float = (
            float(ra_raw) if ra_raw is not None else 0.0
        )
        is_animating: bool = bool(
            getattr(a, "is_animating", False)
        )
        current_number = getattr(a, "current_display_number", None)
        holo_color = getattr(a, "holo_color", QColor("#4FC3F7"))
        unit_text = str(getattr(a, "unit", ""))

        phase_rad = math.radians(rotation_angle)
        frame_seed = rotation_angle / 360.0

        # ============================================================
        # لایه ۱ — گرادیانت عمیق پس‌زمینه
        # ============================================================
        bg_grad = QRadialGradient(
            QPointF(cx, cy), max(w, h) * 0.75
        )
        bg_grad.setColorAt(0.0, QColor(15, 40, 80))
        bg_grad.setColorAt(0.5, QColor(8, 20, 45))
        bg_grad.setColorAt(1.0, QColor(2, 5, 15))
        painter.fillRect(self.rect(), QBrush(bg_grad))

        # ============================================================
        # لایه ۲ — گرید ریاضی
        # ============================================================
        grid_color = QColor(79, 195, 247, 28)
        painter.setPen(QPen(grid_color, 1))
        step = 36
        x = 0
        while x < w_int:
            painter.drawLine(x, 0, x, h_int)
            x += step
        y = 0
        while y < h_int:
            painter.drawLine(0, y, w_int, y)
            y += step

        main_grid = QColor(79, 195, 247, 60)
        painter.setPen(QPen(main_grid, 1))
        x = 0
        while x < w_int:
            painter.drawLine(x, 0, x, h_int)
            x += step * 4
        y = 0
        while y < h_int:
            painter.drawLine(0, y, w_int, y)
            y += step * 4

        # ============================================================
        # لایه ۳ — براکت‌های گوشه
        # ============================================================
        bracket_col = QColor(79, 195, 247, 200)
        painter.setPen(QPen(bracket_col, 2))
        blen = 28
        m = 12
        painter.drawLine(m, m, m + blen, m)
        painter.drawLine(m, m, m, m + blen)
        painter.drawLine(w_int - m - blen, m, w_int - m, m)
        painter.drawLine(w_int - m, m, w_int - m, m + blen)
        painter.drawLine(m, h_int - m, m + blen, h_int - m)
        painter.drawLine(m, h_int - m - blen, m, h_int - m)
        painter.drawLine(
            w_int - m - blen, h_int - m, w_int - m, h_int - m
        )
        painter.drawLine(
            w_int - m, h_int - m - blen, w_int - m, h_int - m
        )

        painter.setPen(QPen(QColor(79, 195, 247, 100), 1))
        mlen = 14
        mid_x = w_int // 2
        painter.drawLine(mid_x - mlen, m, mid_x + mlen, m)
        painter.drawLine(
            mid_x - mlen, h_int - m, mid_x + mlen, h_int - m
        )

        # ============================================================
        # لایه ۴ — ستون‌های داده
        # ============================================================
        painter.setPen(Qt.PenStyle.NoPen)
        n_cols = 5
        for i in range(n_cols):
            col_x = w * (0.1 + i * 0.2)
            col_offset = self._prand(i + 100, frame_seed) * h
            n_cells = 7
            for j in range(n_cells):
                cell_y = (col_offset + j * 18) % h
                cell_w = 10.0 + self._prand(
                    i * 10 + j + 200, frame_seed
                ) * 6
                cell_h = 3.0
                alpha = int(
                    50 + self._prand(
                        i * 10 + j + 300, frame_seed
                    ) * 130
                )
                if j == n_cells // 2:
                    alpha = min(220, alpha + 60)
                painter.setBrush(
                    QBrush(QColor(79, 195, 247, alpha))
                )
                painter.drawRect(
                    QRectF(col_x, cell_y, cell_w, cell_h)
                )

        # ============================================================
        # لایه ۵ — حلقه‌ها با Chromatic Aberration
        # ============================================================
        painter.setBrush(Qt.BrushStyle.NoBrush)

        painter.setPen(QPen(QColor(255, 60, 60, 70), 2))
        painter.drawEllipse(QPointF(cx - 1.5, cy), radius, radius)

        painter.setPen(QPen(QColor(60, 60, 255, 70), 2))
        painter.drawEllipse(QPointF(cx + 1.5, cy), radius, radius)

        painter.setPen(QPen(holo_color, 2))
        painter.drawEllipse(QPointF(cx, cy), radius, radius)

        pen_mid = QPen(QColor(79, 195, 247, 150), 1)
        pen_mid.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen_mid)
        painter.drawEllipse(
            QPointF(cx, cy), radius * 0.7, radius * 0.7
        )

        painter.setPen(QPen(QColor(79, 195, 247, 100), 1))
        painter.drawEllipse(
            QPointF(cx, cy), radius * 0.4, radius * 0.4
        )

        pulse = 0.5 + 0.5 * math.sin(phase_rad * 2)
        pulse_r = radius * (0.95 + 0.05 * pulse)
        pulse_alpha = int(70 + 70 * pulse)
        painter.setPen(
            QPen(QColor(79, 195, 247, pulse_alpha), 1)
        )
        painter.drawEllipse(QPointF(cx, cy), pulse_r, pulse_r)

        # ============================================================
        # لایه ۶ — قوس‌های انرژی
        # ============================================================
        n_arcs = 4
        for k in range(n_arcs):
            arc_start_deg = rotation_angle * (1 + k * 0.3) + k * 90
            arc_span_deg = 40 + 20 * math.sin(phase_rad + k)
            arc_r = radius * (0.55 + k * 0.12)

            n_samples = 12
            path = QPainterPath()
            first = True
            for s in range(n_samples):
                t = s / (n_samples - 1)
                ang_deg = arc_start_deg + arc_span_deg * t
                ang = math.radians(ang_deg)
                wobble = 4 * math.sin(t * math.pi * 4 + phase_rad * 3)
                px = cx + (arc_r + wobble) * math.cos(ang)
                py = cy + (arc_r + wobble) * math.sin(ang)
                if first:
                    path.moveTo(px, py)
                    first = False
                else:
                    path.lineTo(px, py)

            alpha = int(120 + 80 * math.sin(phase_rad * 2 + k))
            painter.setPen(
                QPen(QColor(79, 195, 247, alpha), 2)
            )
            painter.drawPath(path)

        # ============================================================
        # لایه ۷ — ذرات چرخان
        # ============================================================
        painter.setPen(Qt.PenStyle.NoPen)
        for i in range(12):
            ang = math.radians(rotation_angle + i * 30)
            r = radius * 0.86
            px = cx + r * math.cos(ang)
            py = cy + r * math.sin(ang)

            glow = QRadialGradient(QPointF(px, py), 14)
            glow.setColorAt(0.0, QColor(79, 195, 247, 240))
            glow.setColorAt(0.5, QColor(79, 195, 247, 120))
            glow.setColorAt(1.0, QColor(79, 195, 247, 0))
            painter.setBrush(QBrush(glow))
            painter.drawEllipse(QPointF(px, py), 14, 14)

            painter.setBrush(QBrush(QColor(200, 240, 255, 255)))
            painter.drawEllipse(QPointF(px, py), 2, 2)

        # ============================================================
        # لایه ۸ — موج‌های فروپاشی
        # ============================================================
        if is_animating:
            for k in range(4):
                wave_r = radius * (0.28 + k * 0.2)
                alpha = max(
                    0, 220 - int((rotation_angle % 120) * 1.8)
                )
                painter.setPen(
                    QPen(QColor(79, 195, 247, alpha), 2)
                )
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawEllipse(
                    QPointF(cx, cy), wave_r, wave_r
                )

        # ============================================================
        # لایه ۹ — هسته‌ی پالسی
        # ============================================================
        core_pulse = 0.7 + 0.3 * math.sin(phase_rad * 3)
        core_r = 30 * core_pulse

        core_grad = QRadialGradient(QPointF(cx, cy), 70)
        core_grad.setColorAt(0.0, QColor(79, 195, 247, 90))
        core_grad.setColorAt(0.4, QColor(79, 195, 247, 40))
        core_grad.setColorAt(1.0, QColor(79, 195, 247, 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(core_grad))
        painter.drawEllipse(QPointF(cx, cy), 70, 70)

        painter.setBrush(QBrush(QColor(220, 245, 255, 200)))
        painter.drawEllipse(
            QPointF(cx, cy), core_r * 0.15, core_r * 0.15
        )

        # ============================================================
        # لایه ۱۰ — Waveform پایین
        # ============================================================
        if h_int > 120:
            wave_y = h * 0.88
            wave_color = QColor(79, 195, 247, 140)
            painter.setPen(QPen(wave_color, 1))
            n_points = 60
            amp = 12.0 if is_animating else 5.0
            prev_x: float | None = None
            prev_y: float | None = None
            for i in range(n_points):
                t = i / (n_points - 1)
                px = 20 + t * (w - 40)
                noise_term = (
                    self._prand(i * 3, frame_seed) - 0.5
                ) * amp * 0.4
                py = wave_y + (
                    amp * math.sin(t * math.pi * 8 + phase_rad * 6)
                    + amp * 0.4 * math.sin(
                        t * math.pi * 20 + phase_rad * 10
                    )
                    + noise_term
                )
                if prev_x is not None and prev_y is not None:
                    painter.drawLine(
                        QPointF(prev_x, prev_y),
                        QPointF(px, py),
                    )
                prev_x = px
                prev_y = py

        # ============================================================
        # لایه ۱۱ — خط اسکن
        # ============================================================
        scan_y = (rotation_angle * 2) % (h + 60) - 30
        scan_grad = QLinearGradient(0, scan_y - 15, 0, scan_y + 15)
        scan_grad.setColorAt(0.0, QColor(79, 195, 247, 0))
        scan_grad.setColorAt(0.5, QColor(79, 195, 247, 100))
        scan_grad.setColorAt(1.0, QColor(79, 195, 247, 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(scan_grad))
        painter.drawRect(
            QRectF(0, scan_y - 15, w, 30)
        )

        # ============================================================
        # لایه ۱۲ — نویز نقطه‌ای
        # ============================================================
        for i in range(24):
            nx = self._prand(i * 17 + 1, frame_seed) * w
            ny = self._prand(i * 23 + 2, frame_seed) * h
            alpha = int(20 + self._prand(i + 500, frame_seed) * 100)
            painter.setBrush(QBrush(QColor(79, 195, 247, alpha)))
            painter.drawEllipse(QPointF(nx, ny), 1, 1)

        # ============================================================
        # لایه ۱۳ — نمایش عدد / متن انتظار
        # ============================================================
        if current_number is not None:
            halo = QRadialGradient(QPointF(cx, cy), 130)
            halo.setColorAt(0.0, QColor(79, 195, 247, 65))
            halo.setColorAt(1.0, QColor(79, 195, 247, 0))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(halo))
            painter.drawEllipse(QPointF(cx, cy), 130, 130)

            bg_rect = QRectF(cx - 85, cy - 38, 170, 76)
            painter.setBrush(QBrush(QColor(11, 29, 58, 230)))
            painter.drawRoundedRect(bg_rect, 12, 12)

            painter.setPen(QPen(holo_color, 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(bg_rect, 12, 12)

            painter.setPen(QColor("#FFFFFF"))
            painter.setFont(
                QFont("Vazirmatn", 30, QFont.Weight.Bold)
            )
            painter.drawText(
                bg_rect,
                int(Qt.AlignmentFlag.AlignCenter),
                f"{float(current_number):.1f}",
            )

            painter.setPen(QColor("#4FC3F7"))
            painter.setFont(QFont("Vazirmatn", 11))
            painter.drawText(
                QRectF(cx - 85, cy + 38, 170, 20),
                int(Qt.AlignmentFlag.AlignCenter),
                unit_text,
            )
        else:
            wait_pulse = 0.55 + 0.45 * math.sin(phase_rad * 3)
            wait_alpha = int(140 + 115 * wait_pulse)
            painter.setPen(QColor(79, 195, 247, wait_alpha))
            painter.setFont(QFont("Vazirmatn", 14))
            painter.drawText(
                QRectF(cx - 130, cy - 15, 260, 30),
                int(Qt.AlignmentFlag.AlignCenter),
                "●  آماده فروپاشی  ●",
            )

        # ============================================================
        # لایه ۱۴ — برچسب‌های HUD
        # ============================================================
        painter.setFont(
            QFont("Consolas", 8, QFont.Weight.Bold)
        )
        painter.setPen(QColor(79, 195, 247, 140))

        # ✅ استفاده از QRectF — نوع-safe
        painter.drawText(
            QRectF(20, 12, 130, 20),
            int(Qt.AlignmentFlag.AlignLeft
                | Qt.AlignmentFlag.AlignVCenter),
            "SCAN.ACTIVE",
        )
        painter.drawText(
            QRectF(w - 130, 12, 120, 20),
            int(Qt.AlignmentFlag.AlignRight
                | Qt.AlignmentFlag.AlignVCenter),
            "MODE.HOLO_01",
        )
        painter.drawText(
            QRectF(20, h - 30, 120, 20),
            int(Qt.AlignmentFlag.AlignLeft
                | Qt.AlignmentFlag.AlignVCenter),
            f"PHASE.{int(rotation_angle):03d}",
        )

        if is_animating:
            status = "SIGNAL.IN_PROGRESS"
        elif current_number is not None:
            status = "SIGNAL.LOCKED"
        else:
            status = "SIGNAL.IDLE"
        painter.drawText(
            QRectF(w - 170, h - 30, 160, 20),
            int(Qt.AlignmentFlag.AlignRight
                | Qt.AlignmentFlag.AlignVCenter),
            status,
        )

        # ============================================================
        # ✅ لایه‌های جدید — افکت‌های پیشرفته
        # ============================================================

        # لایه ۱۵ — Reticle (نشانگر مرکزی)
        reticle_alpha = int(120 + 60 * math.sin(phase_rad * 4))
        painter.setPen(QPen(QColor(79, 195, 247, reticle_alpha), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        reticle_len = 20
        reticle_gap = 55
        # چهار خط کوتاه اطراف مرکز
        painter.drawLine(
            QPointF(cx, cy - reticle_gap),
            QPointF(cx, cy - reticle_gap + reticle_len),
        )
        painter.drawLine(
            QPointF(cx, cy + reticle_gap),
            QPointF(cx, cy + reticle_gap - reticle_len),
        )
        painter.drawLine(
            QPointF(cx - reticle_gap, cy),
            QPointF(cx - reticle_gap + reticle_len, cy),
        )
        painter.drawLine(
            QPointF(cx + reticle_gap, cy),
            QPointF(cx + reticle_gap - reticle_len, cy),
        )

        # لایه ۱۶ — گوشه‌های براکت داخلی
        inner_col = QColor(79, 195, 247, 90)
        painter.setPen(QPen(inner_col, 1))
        inner_r = radius * 0.92
        # چهار قوس کوتاه در گوشه‌های دایره
        for k in range(4):
            ang_start = math.radians(k * 90 + 45)
            ang_end = math.radians(k * 90 + 45 + 15)
            path2 = QPainterPath()
            path2.moveTo(
                cx + inner_r * math.cos(ang_start),
                cy + inner_r * math.sin(ang_start),
            )
            n_sub = 6
            for s in range(1, n_sub + 1):
                t = s / n_sub
                ang = ang_start + (ang_end - ang_start) * t
                path2.lineTo(
                    cx + inner_r * math.cos(ang),
                    cy + inner_r * math.sin(ang),
                )
            painter.drawPath(path2)

        # لایه ۱۷ — Data particles (ذرات داده‌ی پراکنده)
        painter.setPen(Qt.PenStyle.NoPen)
        for i in range(8):
            seed_val = i * 37 + 900
            angle = self._prand(seed_val, frame_seed) * 2 * math.pi
            r_factor = 0.5 + 0.45 * self._prand(
                seed_val + 1, frame_seed
            )
            pr = radius * r_factor
            px = cx + pr * math.cos(angle + phase_rad)
            py = cy + pr * math.sin(angle + phase_rad)
            sz = 1.5 + self._prand(seed_val + 2, frame_seed) * 2
            alpha = int(60 + self._prand(seed_val + 3, frame_seed) * 120)
            painter.setBrush(QBrush(QColor(200, 240, 255, alpha)))
            painter.drawEllipse(QPointF(px, py), sz, sz)

        # ============================================================
        # ✅ لایه ۱۸ — Energy Trails (خطوط انرژی بین ذرات)
        # ============================================================
        # ذرات نزدیک به هم را با خطوط ظریف وصل می‌کنیم
        particles = []
        for i in range(12):
            ang = math.radians(rotation_angle + i * 30)
            r = radius * 0.86
            particles.append((
                cx + r * math.cos(ang),
                cy + r * math.sin(ang),
            ))

        painter.setPen(QPen(QColor(79, 195, 247, 35), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        for i in range(len(particles)):
            for j in range(i + 1, len(particles)):
                p1 = particles[i]
                p2 = particles[j]
                dist = math.hypot(p1[0] - p2[0], p1[1] - p2[1])
                if dist < radius * 0.7:
                    alpha_link = int(
                        80 * (1 - dist / (radius * 0.7))
                    )
                    painter.setPen(
                        QPen(QColor(79, 195, 247, alpha_link), 1)
                    )
                    painter.drawLine(
                        QPointF(p1[0], p1[1]),
                        QPointF(p2[0], p2[1]),
                    )

        # ============================================================
        # ✅ لایه ۱۹ — Central Ripple (موج مرکزی زنده)
        # ============================================================
        ripple_count = 3
        for k in range(ripple_count):
            phase_offset = k * 0.33
            ripple_progress = (
                (rotation_angle * 0.01 + phase_offset) % 1.0
            )
            ripple_r = ripple_progress * radius * 0.9
            ripple_alpha = int(90 * (1 - ripple_progress))
            painter.setPen(
                QPen(QColor(79, 195, 247, ripple_alpha), 1)
            )
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(
                QPointF(cx, cy), ripple_r, ripple_r
            )

        # ============================================================
        # ✅ لایه ۲۰ — Central HUD Meter (نوار افقی پایین)
        # ============================================================
        if h_int > 130:
            meter_y = h - 40
            meter_w = w * 0.5
            meter_x = (w - meter_w) / 2
            meter_h = 4

            # پس‌زمینه
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(
                QBrush(QColor(79, 195, 247, 40))
            )
            painter.drawRect(
                QRectF(meter_x, meter_y, meter_w, meter_h)
            )

            # مقدار متغیر
            fill = 0.5 + 0.5 * math.sin(phase_rad * 2)
            fill_w = meter_w * fill
            painter.setBrush(
                QBrush(QColor(79, 195, 247, 180))
            )
            painter.drawRect(
                QRectF(meter_x, meter_y, fill_w, meter_h)
            )

            # نشانگر
            marker_x = meter_x + fill_w
            painter.setBrush(
                QBrush(QColor(220, 245, 255, 240))
            )
            painter.drawEllipse(
                QPointF(marker_x, meter_y + meter_h / 2),
                3, 3
            )

        painter.end()