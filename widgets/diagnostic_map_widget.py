"""
ویجت نقشه تشخیصی — PID-01
نسخه 4.0 — بازنویسی کامل برای رفع کرش:

تغییرات کلیدی نسبت به نسخه 3:
- حذف کامل _DependencyOverlay (منبع اصلی کرش: mapTo روی خواهر + TranslucentBackground)
- رسم خطوط وابستگی مستقیماً در paintEvent خودِ DiagnosticMapWidget
- حذف QWidget جداگانه با پس‌زمینه نیمه‌شفاف
- تایمر pulse با تاخیر ۵۰۰ms شروع می‌شود (بعد از پایدار شدن layout)

نسخه: 4.0.0
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGridLayout, QMessageBox
)
from PyQt6.QtCore import (
    Qt, QTimer, pyqtSignal, QPoint, QPointF
)
from PyQt6.QtGui import (
    QFont, QPainter, QPen, QColor, QBrush
)
import math
import time

FONT_FAMILY = "Vazirmatn"


# ====================================================================
# نگاشت وابستگی‌ها
# ====================================================================
SYSTEM_DEPENDENCIES = {
    "power_grid": [],
    "cooling": ["power_grid"],
    "communications": ["power_grid"],
    "life_support": ["power_grid"],
    "navigation": [],
    "structure": [],
}

RELATED_GROUPS = {
    "power_grid": "#4FC3F7",
    "cooling": "#4FC3F7",
    "communications": "#4FC3F7",
    "life_support": "#4FC3F7",
    "navigation": "#4CAF50",
    "structure": "#4CAF50",
}


class DiagnosticMapWidget(QWidget):
    """نقشه تشخیصی با بررسی تعاملی — نسخه 4.0"""

    diagnosis_done = pyqtSignal(dict)

    def __init__(self, systems: list, npc_hint: str = "",
                 investigation_time_ms: int = 1500, parent=None):
        super().__init__(parent)
        self.systems = systems
        self.npc_hint = npc_hint
        self.investigation_time_ms = investigation_time_ms

        self.start_time = int(time.time() * 1000)
        self.investigated: list = []
        self.investigation_times: dict = {}
        self.investigating: str | None = None
        self._investigation_start = 0
        self.time_to_first_action = 0
        self.chosen_root: str | None = None
        self.is_done = False
        self.perseveration_count = 0

        # انیمیشن pulse
        self._pulse_phase = 0.0
        self._pulse_timer = QTimer(self)
        self._pulse_timer.timeout.connect(self._tick_pulse)

        # ویجت‌ها
        self.cards: dict = {}
        self.inspect_buttons: dict = {}
        self.mark_buttons: dict = {}
        self.status_labels: dict = {}
        self.progress_bars: dict = {}

        self._setup_ui()
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        # ✅ تایمر بعد از پایدار شدن layout شروع می‌شود
        QTimer.singleShot(500, self._start_pulse)

    # ================================================================
    def _start_pulse(self):
        """شروع تایمر pulse — بعد از آماده شدن ویجت"""
        if not self._pulse_timer.isActive():
            self._pulse_timer.start(80)

    def _tick_pulse(self):
        """تیک انیمیشن pulse"""
        self._pulse_phase += 0.1
        if self._pulse_phase > 2 * math.pi:
            self._pulse_phase -= 2 * math.pi
        # ✅ فقط اگر visible و اندازه معقول دارد، update کن
        if not self.isVisible():
            return
        if self.width() < 10 or self.height() < 10:
            return
        self.update()

    def showEvent(self, event):  # type: ignore
        super().showEvent(event)
        if not self._pulse_timer.isActive():
            self._pulse_timer.start(80)

    def hideEvent(self, event):  # type: ignore
        super().hideEvent(event)
        if self._pulse_timer.isActive():
            self._pulse_timer.stop()

    def closeEvent(self, event):  # type: ignore
        try:
            self._pulse_timer.stop()
        except Exception:
            pass
        super().closeEvent(event)

    # ================================================================
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 12, 30, 12)
        main_layout.setSpacing(8)

        title = QLabel("نقشه تشخیصی سیستم‌ها")
        tf = QFont(FONT_FAMILY, 20)
        tf.setBold(True)
        title.setFont(tf)
        title.setStyleSheet("color: #4FC3F7;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        desc = QLabel(
            "چندین هشدار همزمان فعال شده است. روی هر کارت کلیک "
            "کنید تا اطلاعات سیستم را ببینید. سپس علت ریشه‌ای "
            "را علامت‌گذاری کنید."
        )
        desc.setFont(QFont(FONT_FAMILY, 11))
        desc.setStyleSheet("color: #CCCCCC;")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        main_layout.addWidget(desc)

        if self.npc_hint:
            hint_frame = QFrame()
            hint_frame.setStyleSheet("""
                QFrame {
                    background-color: rgba(255, 143, 0, 0.12);
                    border: 2px solid #FF8F00;
                    border-radius: 8px;
                }
            """)
            hl = QHBoxLayout(hint_frame)
            hl.setContentsMargins(15, 8, 15, 8)
            hint_lbl = QLabel(f"⚠  {self.npc_hint}")
            hint_lbl.setFont(QFont(FONT_FAMILY, 11))
            hint_lbl.setStyleSheet("color: #FFB74D; border: none;")
            hint_lbl.setWordWrap(True)
            hl.addWidget(hint_lbl)
            main_layout.addWidget(hint_frame)

        self.status_label = QLabel("هنوز هیچ سیستمی بررسی نشده است.")
        self.status_label.setFont(QFont(FONT_FAMILY, 11))
        self.status_label.setStyleSheet(
            "color: #FF8F00; padding: 4px;"
        )
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.status_label)

        # پنل جزئیات
        self.detail_frame = QFrame()
        self.detail_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(79, 195, 247, 0.10);
                border: 2px solid #4FC3F7;
                border-radius: 8px;
            }
        """)
        df_layout = QVBoxLayout(self.detail_frame)
        df_layout.setContentsMargins(15, 10, 15, 10)
        df_layout.setSpacing(4)

        self.detail_title = QLabel("جزئیات سیستم انتخاب‌شده:")
        self.detail_title.setFont(
            QFont(FONT_FAMILY, 11, QFont.Weight.Bold)
        )
        self.detail_title.setStyleSheet(
            "color: #4FC3F7; border: none;"
        )
        df_layout.addWidget(self.detail_title)

        self.detail_text = QLabel(
            "برای مشاهده جزئیات، روی «بررسی» هر کارت کلیک کنید."
        )
        self.detail_text.setFont(QFont(FONT_FAMILY, 11))
        self.detail_text.setStyleSheet(
            "color: #FFFFFF; border: none;"
        )
        self.detail_text.setWordWrap(True)
        self.detail_text.setMinimumHeight(60)
        self.detail_text.setLayoutDirection(
            Qt.LayoutDirection.RightToLeft
        )
        self.detail_text.setAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignAbsolute
        )
        df_layout.addWidget(self.detail_text)

        main_layout.addWidget(self.detail_frame)

        # گرید کارت‌ها
        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(10)

        for i, system in enumerate(self.systems):
            row = i // 3
            col = i % 3
            card = self._create_system_card(system)
            grid.addWidget(card, row, col)
            self.cards[system["id"]] = card
            grid.setColumnStretch(col, 1)
            grid.setRowStretch(row, 1)

        main_layout.addLayout(grid, stretch=1)

    # ================================================================
    # ✅ paintEvent مستقیماً روی خود ویجت — بدون overlay
    # ================================================================
    def paintEvent(self, event):  # type: ignore
        # قبل از رسم، اجازه بده Qt بک‌گراند و فرزندان را رسم کند
        # (این متد ابتدا فراخوانی می‌شود و سپس فرزندان رسم می‌شوند)
        super().paintEvent(event)

        # ✅ حفاظت‌های ساده
        if self.width() < 10 or self.height() < 10:
            return
        if not self.cards:
            return

        painter = QPainter(self)
        if not painter.isActive():
            return

        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # ✅ snapshot برای جلوگیری از تغییر حین پیمایش
            for sid, card in list(self.cards.items()):
                deps = SYSTEM_DEPENDENCIES.get(sid, [])
                for dep_id in deps:
                    dep_card = self.cards.get(dep_id)
                    if dep_card is None:
                        continue

                    try:
                        if not card.isVisible():
                            continue
                        if not dep_card.isVisible():
                            continue
                    except RuntimeError:
                        continue

                    # ✅ مختصات: هر دو کارت فرزند مستقیم self هستند
                    #    پس card.pos() نسبت به self است
                    try:
                        p1 = card.pos() + card.rect().center()
                        p2 = dep_card.pos() + dep_card.rect().center()
                    except RuntimeError:
                        continue

                    color = QColor("#4FC3F7")
                    color.setAlpha(60)

                    if self.investigating in (sid, dep_id):
                        pulse = 0.5 + 0.5 * math.sin(
                            self._pulse_phase
                        )
                        color.setAlpha(int(80 + 100 * pulse))

                    painter.setPen(
                        QPen(color, 1.5, Qt.PenStyle.DashLine)
                    )
                    painter.setBrush(Qt.BrushStyle.NoBrush)
                    painter.drawLine(p1, p2)

                    self._draw_arrow(
                        painter,
                        QPointF(p1),
                        QPointF(p2),
                        color,
                    )
        finally:
            try:
                painter.end()
            except Exception:
                pass

    # ================================================================
    def _draw_arrow(self, painter, p1, p2, color):
        """رسم فلش کوچک نزدیک p2"""
        angle = math.atan2(p2.y() - p1.y(), p2.x() - p1.x())
        arrow_len = 10

        margin = 40
        dx = p2.x() - p1.x()
        dy = p2.y() - p1.y()
        dist = math.hypot(dx, dy)
        if dist < margin * 2:
            return

        tip_x = p2.x() - margin * dx / dist
        tip_y = p2.y() - margin * dy / dist

        left_angle = angle + math.pi * 0.8
        right_angle = angle - math.pi * 0.8

        painter.setPen(QPen(color, 1.5))
        painter.drawLine(
            QPointF(tip_x, tip_y),
            QPointF(
                tip_x + arrow_len * math.cos(left_angle),
                tip_y + arrow_len * math.sin(left_angle),
            ),
        )
        painter.drawLine(
            QPointF(tip_x, tip_y),
            QPointF(
                tip_x + arrow_len * math.cos(right_angle),
                tip_y + arrow_len * math.sin(right_angle),
            ),
        )

    # ================================================================
    def _create_system_card(self, system):
        card = QFrame()
        card.setObjectName(f"card_{system['id']}")
        card.setStyleSheet(self._card_style_neutral(system["id"]))
        card.setMinimumHeight(130)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        top = QHBoxLayout()
        top.setSpacing(6)

        icon_lbl = QLabel(system.get("icon", "●"))
        icon_lbl.setFont(QFont("Arial", 18))
        icon_lbl.setStyleSheet("border: none;")
        top.addWidget(icon_lbl)

        name_lbl = QLabel(system["name"])
        name_lbl.setFont(
            QFont(FONT_FAMILY, 11, QFont.Weight.Bold)
        )
        name_lbl.setStyleSheet("color: #FFFFFF; border: none;")
        name_lbl.setWordWrap(True)
        top.addWidget(name_lbl, 1)
        layout.addLayout(top)

        status_text = {
            "ok": "عملکرد عادی",
            "warning": "هشدار",
            "failure": "نقص گزارش‌شده",
        }.get(system["status"], "?")

        status_color = {
            "ok": "#4CAF50",
            "warning": "#FF8F00",
            "failure": "#D32F2F",
        }.get(system["status"], "#B0BEC5")

        status_lbl = QLabel(status_text)
        status_lbl.setFont(QFont(FONT_FAMILY, 10))
        status_lbl.setStyleSheet(
            f"color: {status_color}; border: none; font-weight: bold;"
        )
        status_lbl.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        layout.addWidget(status_lbl)

        brief_lbl = QLabel(system.get("brief", ""))
        brief_lbl.setFont(QFont(FONT_FAMILY, 9))
        brief_lbl.setStyleSheet("color: #CCCCCC; border: none;")
        brief_lbl.setWordWrap(True)
        layout.addWidget(brief_lbl)

        progress_bar = QFrame()
        progress_bar.setFixedHeight(3)
        progress_bar.setStyleSheet(
            "background-color: rgba(79, 195, 247, 0.15); "
            "border: none; border-radius: 2px;"
        )
        layout.addWidget(progress_bar)
        self.progress_bars[system["id"]] = progress_bar

        layout.addStretch()

        inspect_btn = QPushButton("بررسی")
        inspect_btn.setFont(
            QFont(FONT_FAMILY, 11, QFont.Weight.Bold)
        )
        inspect_btn.setMinimumHeight(30)
        inspect_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        inspect_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        inspect_btn.setStyleSheet("""
            QPushButton {
                background-color: #2B4A6F;
                color: #FFFFFF;
                border: 2px solid #4FC3F7;
                border-radius: 6px;
                padding: 4px;
            }
            QPushButton:hover {
                background-color: #4FC3F7;
                color: #0B1D3A;
            }
            QPushButton:disabled {
                background-color: #1A2A4A;
                color: #666666;
                border: 2px solid #444444;
            }
        """)
        inspect_btn.clicked.connect(
            lambda _, sid=system["id"]: self._on_inspect(sid)
        )
        layout.addWidget(inspect_btn)
        self.inspect_buttons[system["id"]] = inspect_btn

        mark_btn = QPushButton("علامت‌گذاری به عنوان علت")
        mark_btn.setFont(
            QFont(FONT_FAMILY, 10, QFont.Weight.Bold)
        )
        mark_btn.setMinimumHeight(30)
        mark_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        mark_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        mark_btn.setStyleSheet("""
            QPushButton {
                background-color: #D32F2F;
                color: #FFFFFF;
                border: 2px solid #FFFFFF;
                border-radius: 6px;
                padding: 4px;
            }
            QPushButton:hover {
                background-color: #B71C1C;
            }
        """)
        mark_btn.setVisible(False)
        mark_btn.clicked.connect(
            lambda _, sid=system["id"]: self._on_mark(sid)
        )
        layout.addWidget(mark_btn)
        self.mark_buttons[system["id"]] = mark_btn

        return card

    # ================================================================
    def _card_style_neutral(self, system_id: str) -> str:
        group_color = RELATED_GROUPS.get(system_id, "#4FC3F7")
        return f"""
            QFrame {{
                background-color: rgba(26, 42, 74, 0.85);
                border: 2px solid {group_color};
                border-radius: 8px;
            }}
        """

    def _card_style_investigating(self, system_id: str) -> str:
        return """
            QFrame {
                background-color: rgba(255, 143, 0, 0.15);
                border: 3px solid #FF8F00;
                border-radius: 8px;
            }
        """

    def _card_style_investigated(self, system_id: str) -> str:
        return """
            QFrame {
                background-color: rgba(79, 195, 247, 0.15);
                border: 2px solid #4FC3F7;
                border-radius: 8px;
            }
        """

    def _card_style_marked(self, system_id: str) -> str:
        return """
            QFrame {
                background-color: rgba(211, 47, 47, 0.30);
                border: 3px solid #D32F2F;
                border-radius: 8px;
            }
        """

    # ================================================================
    def _on_inspect(self, system_id):
        if self.is_done:
            return
        if self.investigating is not None:
            return

        if system_id in self.investigated:
            self.perseveration_count += 1
            self._show_detail(system_id)
            return

        if self.time_to_first_action == 0:
            self.time_to_first_action = (
                int(time.time() * 1000) - self.start_time
            )

        self.investigating = system_id
        self._investigation_start = int(time.time() * 1000)

        card = self.cards[system_id]
        inspect_btn = self.inspect_buttons[system_id]
        inspect_btn.setEnabled(False)
        inspect_btn.setText("⏳ در حال بررسی...")

        card.setStyleSheet(
            self._card_style_investigating(system_id)
        )

        self._start_progress_animation(system_id)

        QTimer.singleShot(
            self.investigation_time_ms, self._finish_inspect
        )

    def _start_progress_animation(self, system_id):
        bar = self.progress_bars.get(system_id)
        if bar is None:
            return

        self._progress_steps = getattr(
            self, "_progress_steps", {}
        )
        self._progress_steps[system_id] = 0

        def _step():
            step = self._progress_steps.get(system_id, 0)
            if step >= 100:
                return
            step = min(100, step + 10)
            self._progress_steps[system_id] = step
            bar.setStyleSheet(f"""
                background-color: rgba(79, 195, 247, 0.15);
                border: none;
                border-radius: 2px;
            """)
            bar.setMinimumWidth(int(bar.width() * step / 100) or 1)
            QTimer.singleShot(150, _step)

        _step()

    def _finish_inspect(self):
        system_id = self.investigating
        if not system_id:
            return

        elapsed = int(time.time() * 1000) - self._investigation_start
        self.investigation_times[system_id] = elapsed
        self.investigated.append(system_id)
        self.investigating = None

        print(f"   [DEBUG] بررسی سیستم: {system_id} ({elapsed}ms)")

        card = self.cards[system_id]
        card.setStyleSheet(
            self._card_style_investigated(system_id)
        )

        inspect_btn = self.inspect_buttons[system_id]
        inspect_btn.setText("↻ مشاهده دوباره")
        inspect_btn.setEnabled(True)

        bar = self.progress_bars.get(system_id)
        if bar is not None:
            bar.setStyleSheet(
                "background-color: rgba(76, 175, 80, 0.4); "
                "border: none; border-radius: 2px;"
            )
            bar.setMinimumWidth(0)

        mark_btn = self.mark_buttons[system_id]
        mark_btn.setVisible(True)

        self._show_detail(system_id)

        count = len(self.investigated)
        total = len(self.systems)
        if count >= total - 1:
            self.status_label.setText(
                f"✓ {count} از {total} سیستم بررسی شد — "
                "می‌توانی علت را علامت‌گذاری کنی."
            )
            self.status_label.setStyleSheet(
                "color: #4CAF50; padding: 4px; font-weight: bold;"
            )
        else:
            self.status_label.setText(
                f"بررسی‌شده: {count} از {total} — "
                "برای یافتن الگو، سیستم‌های بیشتری را بررسی کن."
            )

    def _show_detail(self, system_id):
        system = next(
            (s for s in self.systems if s["id"] == system_id),
            None,
        )
        if not system:
            return
        self.detail_title.setText(
            f"جزئیات: {system['icon']} {system['name']}"
        )
        self.detail_text.setText(system.get("detail", ""))

    # ================================================================
    def _on_mark(self, system_id):
        if self.is_done:
            return

        if len(self.investigated) < 2:
            reply = QMessageBox.question(
                self, "تأیید تصمیم",
                "شما فقط یک سیستم را بررسی کرده‌اید. "
                "آیا مطمئنید که علت ریشه‌ای را درست "
                "تشخیص داده‌اید؟",
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        self.chosen_root = system_id
        self.is_done = True

        total_time = int(time.time() * 1000) - self.start_time

        for sid, card in self.cards.items():
            inspect_btn = self.inspect_buttons[sid]
            mark_btn = self.mark_buttons[sid]
            inspect_btn.setEnabled(False)
            mark_btn.setEnabled(False)
            if sid == system_id:
                mark_btn.setText("✓ علت انتخاب‌شده")
                card.setStyleSheet(self._card_style_marked(sid))

        system = next(
            (s for s in self.systems if s["id"] == system_id),
            None,
        )
        if system is None:
            return

        self.status_label.setText(
            f"✓ علت ریشه‌ای انتخاب‌شده: {system['name']}"
        )
        self.status_label.setStyleSheet(
            "color: #4CAF50; padding: 4px; font-weight: bold;"
        )

        result = {
            "chosen_root_cause": system_id,
            "systems_investigated": list(self.investigated),
            "investigation_times_ms": dict(
                self.investigation_times
            ),
            "time_to_first_action_ms": self.time_to_first_action,
            "total_time_ms": total_time,
            "total_investigated": len(self.investigated),
            "total_systems": len(self.systems),
            "perseveration_count": self.perseveration_count,
        }

        print(f"   [DEBUG] تشخیص نهایی: {result}")
        self.diagnosis_done.emit(result)