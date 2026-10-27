"""
ویجت کار تکراری — TC-01
بررسی ۲۰ لاگ سیستمی با سه وسوسه‌ی متوالی از شخصیت‌های مختلف

نسخه 2.0:
- اسپینر «در حال بررسی» هنگام کلیک
- هایلایت ردیف بعدی برای بررسی
- نوار پیشرفت ۲۰ سلولی بصری
- سه وسوسه با شخصیت‌های متفاوت
- صدای کلیک هنگام بررسی

نسخه: 2.0.0
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QRectF, QPointF
from PyQt6.QtGui import QFont, QPainter, QPen, QBrush, QColor
import time

FONT_FAMILY = "Vazirmatn"


# ================================================================
# سه وسوسه با شخصیت‌های متفاوت
# ================================================================
TEMPTATIONS = [
    {
        "trigger": 5,
        "npc_message": (
            "مهندس رحیمی: تکنسین، یه لحظه. لی رو دیدی؟ "
            "راستش، من نگرانشم. امروز صبح خیلی پریشون بود. "
            "اگه یه سر بهش بزنی، شاید بهتر بشه. "
            "این لاگ‌ها رو بعداً هم می‌تونی بررسی کنی."
        ),
        "mood": "concerned",
        "shortcut_label": "باشه، برم سراغش",
        "continue_label": "الان نمی‌تونم — اول کارم",
    },
    {
        "trigger": 10,
        "npc_message": (
            "دکتر آرتمیس: (از بی‌سیم) تکنسین، یه آنومالی جدید "
            "توی داده‌ها پیدا کردم. نیاز دارم همین الان بیای. "
            "لاگ‌ها رو بذار برای بعد. این فوری‌تره."
        ),
        "mood": "urgent",
        "shortcut_label": "باشه، میام",
        "continue_label": "لاگ‌هام رو تموم کنم، بعد میام",
    },
    {
        "trigger": 15,
        "npc_message": (
            "مهندس رحیمی: تکنسین، جلسه‌ی شورا فرداست. "
            "بذار این رو به یکی دیگه بسپاریم و بریم گزارش رو "
            "برای شورا آماده کنیم. تمرکزت روی اون مهم‌تره."
        ),
        "mood": "pragmatic",
        "shortcut_label": "باشه، بریم گزارش",
        "continue_label": "این هم بخشی از گزارشه",
    },
]


# ================================================================
# نوار پیشرفت ۲۰ سلولی
# ================================================================
class _LogProgressBar(QWidget):
    """نوار پیشرفت با ۲۰ سلول کوچک"""

    def __init__(self, total: int = 20, parent=None):
        super().__init__(parent)
        self.total = max(1, total)
        self._filled = 0
        self._auto = 0  # تعداد خودکار (کم‌رنگ)

        self.setMinimumHeight(20)
        self.setMaximumHeight(20)
        self.setStyleSheet("background: transparent;")

    def set_filled(self, count: int, auto: int = 0):
        self._filled = max(0, min(self.total, count))
        self._auto = max(0, min(self.total - self._filled, auto))
        self.update()

    def paintEvent(self, event):  # type: ignore
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        gap = 2
        cell_w = max(2.0, (w - gap * (self.total - 1)) / self.total)
        radius = 2.0

        for i in range(self.total):
            x = i * (cell_w + gap)
            rect = QRectF(x, 4, cell_w, h - 8)

            if i < self._filled:
                # بررسی‌شده‌ی واقعی
                color = QColor(76, 175, 80)
            elif i < self._filled + self._auto:
                # خودکار (نصفه)
                color = QColor(255, 143, 0, 180)
            else:
                # باقی‌مانده
                color = QColor(26, 42, 74)

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(color))
            painter.drawRoundedRect(rect, radius, radius)

        painter.end()


# ================================================================
# ویجت اصلی
# ================================================================
class RepetitiveTaskWidget(QWidget):
    """بررسی تعاملی لاگ‌های تکراری با سه وسوسه‌ی متوالی"""

    task_done = pyqtSignal(dict)

    TOTAL_ROWS = 20
    SPINNER_MS = 600  # مدت اسپینر برای هر بررسی

    def __init__(self, npc_name: str = "مهندس رحیمی",
                 npc_message: str = "", parent=None):
        super().__init__(parent)
        self.npc_name = npc_name
        self.legacy_npc_message = npc_message

        self.start_time = int(time.time() * 1000)
        self.checked_rows: set = set()
        self.row_status: dict = {}
        self.cheat_used = False
        self.cheat_trigger_row: int = -1

        self.temptations_shown: list = []
        self.temptations_rejected: int = 0
        self.temptations_accepted: int = 0

        self.is_done = False
        self._spinner_active: bool = False

        self.row_frames: dict = {}
        self.row_buttons: dict = {}
        self.row_status_labels: dict = {}

        # اسپینر
        self._spinner_chars = ["◐", "◓", "◑", "◒"]
        self._spinner_index = 0
        self._spinner_timer = QTimer(self)
        self._spinner_timer.timeout.connect(self._tick_spinner)

        self._setup_ui()
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

    # ================================================================
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 12, 30, 12)
        main_layout.setSpacing(8)

        # ---------- عنوان ----------
        title = QLabel("بررسی لاگ‌های سیستمی")
        tf = QFont(FONT_FAMILY, 18)
        tf.setBold(True)
        title.setFont(tf)
        title.setStyleSheet("color: #4FC3F7;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        # ---------- توضیح ----------
        desc = QLabel(
            f"برای یافتن الگوی ناهنجار، باید {self.TOTAL_ROWS} "
            "لاگ را یکی‌یکی بررسی کنید."
        )
        desc.setFont(QFont(FONT_FAMILY, 11))
        desc.setStyleSheet("color: #CCCCCC;")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        main_layout.addWidget(desc)

        # ---------- نوار پیشرفت ----------
        progress_frame = QFrame()
        progress_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(26, 42, 74, 0.85);
                border: 2px solid #FF8F00;
                border-radius: 8px;
            }
        """)
        pf_layout = QVBoxLayout(progress_frame)
        pf_layout.setContentsMargins(12, 8, 12, 8)
        pf_layout.setSpacing(4)

        pf_top = QHBoxLayout()
        pf_label = QLabel("پیشرفت:")
        pf_label.setFont(
            QFont(FONT_FAMILY, 12, QFont.Weight.Bold)
        )
        pf_label.setStyleSheet(
            "color: #FF8F00; border: none;"
        )
        pf_top.addWidget(pf_label)
        pf_top.addStretch()

        self.progress_label = QLabel(f"0 از {self.TOTAL_ROWS}")
        self.progress_label.setFont(
            QFont(FONT_FAMILY, 12, QFont.Weight.Bold)
        )
        self.progress_label.setStyleSheet(
            "color: #FFFFFF; border: none;"
        )
        self.progress_label.setLayoutDirection(
            Qt.LayoutDirection.LeftToRight
        )
        pf_top.addWidget(self.progress_label)

        pf_layout.addLayout(pf_top)

        self.progress_bar = _LogProgressBar(self.TOTAL_ROWS)
        pf_layout.addWidget(self.progress_bar)

        main_layout.addWidget(progress_frame)

        # ---------- ناحیه اسکرول با ۲۰ لاگ ----------
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setStyleSheet(
            "QScrollArea { background-color: #0B1D3A; border: none; }"
        )

        content = QWidget()
        content.setStyleSheet("background-color: #0B1D3A;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(4, 4, 4, 4)
        content_layout.setSpacing(4)

        for i in range(self.TOTAL_ROWS):
            row = self._create_log_row(i)
            content_layout.addWidget(row)

        content_layout.addStretch()
        scroll_area.setWidget(content)
        self._scroll_area = scroll_area
        main_layout.addWidget(scroll_area, stretch=1)

        # ---------- دکمه ثبت ----------
        self.submit_btn = QPushButton("پایان بررسی و ثبت گزارش")
        sbf = QFont(FONT_FAMILY, 14)
        sbf.setBold(True)
        self.submit_btn.setFont(sbf)
        self.submit_btn.setMinimumHeight(48)
        self.submit_btn.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.submit_btn.setFocusPolicy(
            Qt.FocusPolicy.NoFocus
        )
        self.submit_btn.setEnabled(False)
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
            }
            QPushButton:disabled {
                background-color: #1A2A4A;
                color: #666666;
                border: 2px solid #444444;
            }
        """)
        self.submit_btn.clicked.connect(self._on_submit)
        main_layout.addWidget(self.submit_btn)

        # هایلایت ردیف اول
        self._highlight_next_row()

    # ================================================================
    def _create_log_row(self, index):
        frame = QFrame()
        frame.setStyleSheet(self._row_style_pending())
        frame.setMinimumHeight(46)

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(10, 4, 10, 4)
        layout.setSpacing(10)

        num_lbl = QLabel(f"#{index + 1:02d}")
        num_lbl.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        num_lbl.setStyleSheet("color: #4FC3F7; border: none;")
        num_lbl.setFixedWidth(38)
        layout.addWidget(num_lbl)

        code_lbl = QLabel(self._make_log_text(index))
        code_lbl.setFont(QFont("Consolas", 9))
        code_lbl.setStyleSheet("color: #B0BEC5; border: none;")
        code_lbl.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        layout.addWidget(code_lbl, 1)

        status_lbl = QLabel("در انتظار")
        status_lbl.setFont(QFont(FONT_FAMILY, 10))
        status_lbl.setStyleSheet("color: #666666; border: none;")
        status_lbl.setFixedWidth(100)
        layout.addWidget(status_lbl)
        frame.setProperty("status_lbl", status_lbl)

        btn = QPushButton("بررسی")
        btn.setFont(QFont(FONT_FAMILY, 11, QFont.Weight.Bold))
        btn.setMinimumHeight(32)
        btn.setMinimumWidth(100)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn.setStyleSheet("""
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
        btn.clicked.connect(lambda _, i=index: self._on_check_row(i))
        layout.addWidget(btn)

        self.row_frames[index] = frame
        self.row_buttons[index] = btn
        self.row_status_labels[index] = status_lbl
        self.row_status[index] = "pending"

        return frame

    # ----------------------------------------------------------------
    def _row_style_pending(self) -> str:
        return """
            QFrame {
                background-color: rgba(26, 42, 74, 0.6);
                border: 1px solid #2B4A6F;
                border-radius: 6px;
            }
        """

    def _row_style_next(self) -> str:
        return """
            QFrame {
                background-color: rgba(79, 195, 247, 0.10);
                border: 2px solid #4FC3F7;
                border-radius: 6px;
            }
        """

    def _row_style_done_honest(self) -> str:
        return """
            QFrame {
                background-color: rgba(76, 175, 80, 0.10);
                border: 1px solid #4CAF50;
                border-radius: 6px;
            }
        """

    def _row_style_done_auto(self) -> str:
        return """
            QFrame {
                background-color: rgba(255, 143, 0, 0.10);
                border: 1px solid #FF8F00;
                border-radius: 6px;
            }
        """

    def _make_log_text(self, index):
        patterns = [
            "LOG.SYS bus_temp={}°C status=OK",
            "LOG.SYS gas_press={}kPa status=OK",
            "LOG.SYS rad_meter={}mSv status=OK",
            "LOG.SYS cpu_load={}% status=OK",
        ]
        p = patterns[index % len(patterns)]
        val = 20 + (index * 7) % 60
        return p.format(val)

    # ================================================================
    # هایلایت ردیف بعدی
    # ================================================================
    def _highlight_next_row(self):
        """ردیف بعدی که باید بررسی شود را هایلایت می‌کند"""
        next_idx = None
        for i in range(self.TOTAL_ROWS):
            if self.row_status.get(i) == "pending":
                next_idx = i
                break

        for i in range(self.TOTAL_ROWS):
            if self.row_status.get(i) != "pending":
                continue
            frame = self.row_frames.get(i)
            if frame is None:
                continue
            if i == next_idx:
                frame.setStyleSheet(self._row_style_next())
            else:
                frame.setStyleSheet(self._row_style_pending())

    # ================================================================
    # بررسی ردیف
    # ================================================================
    def _on_check_row(self, index):
        if self.cheat_used or self.is_done:
            return
        if self._spinner_active:
            return
        if self.row_status.get(index) != "pending":
            return

        # صدای کلیک
        try:
            from core.audio_manager import get_audio_manager
            get_audio_manager().play_sfx("click")
        except Exception:
            pass

        # شروع اسپینر
        self._start_spinner(index)

    def _start_spinner(self, index):
        """شروع انیمیشن اسپینر روی دکمه‌ی این ردیف"""
        self._spinner_active = True
        self._spinner_target = index
        self._spinner_index = 0

        btn = self.row_buttons.get(index)
        if btn is None:
            self._finish_check(index)
            return

        btn.setEnabled(False)
        btn.setText("◐ در حال بررسی")
        self._spinner_timer.start(120)

        # ✅ تایمر اتمام اسپینر — این خط قبلاً نبود و باعث
        #    فریز می‌شد: اسپینر تا ابد می‌چرخید و _finish_check
        #    هیچ‌وقت صدا زده نمی‌شد
        QTimer.singleShot(self.SPINNER_MS, self._finish_spinner)

    def _tick_spinner(self):
        self._spinner_index = (
            self._spinner_index + 1
        ) % len(self._spinner_chars)
        char = self._spinner_chars[self._spinner_index]
        btn = self.row_buttons.get(self._spinner_target)
        if btn is not None:
            btn.setText(f"{char} در حال بررسی")

    def _finish_spinner(self):
        """
        ✅ پایان اسپینر — از طریق QTimer.singleShot صدا زده
        می‌شود. اگر قبلاً تمام شده، نادیده می‌گیرد.
        """
        if not self._spinner_active:
            return
        index = self._spinner_target
        self._finish_check(index)

    def _finish_check(self, index):
        """اتمام اسپینر و علامت‌گذاری ردیف"""
        self._spinner_timer.stop()
        self._spinner_active = False

        self._mark_row(index, "honest")
        self.checked_rows.add(index)
        self._update_progress()
        self._highlight_next_row()

        # وسوسه‌ها
        count = len(self.checked_rows)
        for temp in TEMPTATIONS:
            if (
                temp["trigger"] == count
                and temp["trigger"] not in self.temptations_shown
            ):
                self.temptations_shown.append(temp["trigger"])
                QTimer.singleShot(
                    400,
                    lambda t=temp: self._show_temptation(t),
                )
                break

    def _mark_row(self, index, status):
        self.row_status[index] = status
        frame = self.row_frames[index]
        lbl = self.row_status_labels.get(index)
        btn = self.row_buttons[index]

        if status == "honest":
            if lbl is not None:
                lbl.setText("✓ بررسی شد")
                lbl.setStyleSheet(
                    "color: #4CAF50; border: none;"
                )
            frame.setStyleSheet(self._row_style_done_honest())
        elif status == "auto":
            if lbl is not None:
                lbl.setText("◐ خودکار")
                lbl.setStyleSheet(
                    "color: #FF8F00; border: none;"
                )
            frame.setStyleSheet(self._row_style_done_auto())

        btn.setEnabled(False)
        btn.setText("✓")

    # ================================================================
    def _update_progress(self):
        count = len(self.checked_rows)
        auto_count = sum(
            1 for s in self.row_status.values() if s == "auto"
        )
        self.progress_bar.set_filled(
            count - auto_count, auto_count
        )
        self.progress_label.setText(
            f"{count} از {self.TOTAL_ROWS}"
        )

        if count >= self.TOTAL_ROWS:
            self.submit_btn.setEnabled(True)
            self.submit_btn.setText("✓ پایان و ثبت گزارش")

    # ================================================================
    # وسوسه
    # ================================================================
    def _show_temptation(self, temp: dict):
        if self.is_done or self.cheat_used:
            return

        msg = QMessageBox(self)
        msg.setWindowTitle("پیام فوری")
        msg.setText(temp["npc_message"])
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        btn_continue = msg.addButton(
            temp["continue_label"],
            QMessageBox.ButtonRole.AcceptRole,
        )
        btn_shortcut = msg.addButton(
            temp["shortcut_label"],
            QMessageBox.ButtonRole.RejectRole,
        )
        msg.setDefaultButton(btn_continue)
        msg.exec()

        if msg.clickedButton() == btn_shortcut:
            self._use_shortcut(
                trigger_row=temp["trigger"],
                mood=temp["mood"],
            )
        else:
            self.temptations_rejected += 1
            print(
                f"   [TC-01] وسوسه‌ی مرحله {temp['trigger']} "
                f"رد شد (تعداد رد: {self.temptations_rejected})"
            )

    def _use_shortcut(self, trigger_row: int, mood: str):
        """بازیکن تسلیم وسوسه شد — خودکار جلو می‌رود"""
        self.cheat_used = True
        self.cheat_trigger_row = trigger_row
        self.temptations_accepted += 1

        remaining = [
            i for i in range(self.TOTAL_ROWS)
            if self.row_status[i] == "pending"
        ]
        for i in remaining:
            self._mark_row(i, "auto")
            self.checked_rows.add(i)

        self._update_progress()
        self._highlight_next_row()
        print(
            f"   [TC-01] بازیکن در مرحله {trigger_row} تسلیم شد "
            f"(mood={mood})"
        )

        # ✅ خودکار ثبت گزارش بعد از ۱.۲ ثانیه
        #    (به بازیکن فرصت دیدن وضعیت را می‌دهد)
        self.submit_btn.setEnabled(True)
        self.submit_btn.setText("✓ در حال ثبت گزارش...")
        QTimer.singleShot(1200, self._auto_submit)

    def _auto_submit(self):
        """ثبت خودکار بعد از تسلیم شدن به وسوسه"""
        if self.is_done:
            return
        print("   [TC-01] ثبت خودکار گزارش پس از تسلیم")
        self._on_submit()

    # ================================================================
    def _on_submit(self):
        if self.is_done:
            return
        self.is_done = True

        total_time = int(time.time() * 1000) - self.start_time
        honest = sum(
            1 for s in self.row_status.values() if s == "honest"
        )
        auto = sum(
            1 for s in self.row_status.values() if s == "auto"
        )

        result = {
            "total_rows": self.TOTAL_ROWS,
            "honest_checked": honest,
            "auto_checked": auto,
            "completion_rate": round(
                honest / self.TOTAL_ROWS, 3
            ),
            "cheat_used": self.cheat_used,
            "cheat_trigger_row": self.cheat_trigger_row,
            "temptations_shown": len(self.temptations_shown),
            "temptations_rejected": self.temptations_rejected,
            "temptations_accepted": self.temptations_accepted,
            "rejected_temptation": (
                self.temptations_rejected > 0
                and self.temptations_accepted == 0
            ),
            "total_time_ms": total_time,
        }
        print(f"   [DEBUG] نتیجه TC-01: {result}")
        self.task_done.emit(result)