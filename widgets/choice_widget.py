"""
ویجت پنل انتخاب گزینه‌ها — نسخه 2.2
====================================
- حذف QGraphicsOpacityEffect (تعارض QPainter)
- انیمیشن ورود با تغییر تدریجی رنگ پس‌زمینه
- شماره‌ی هر گزینه به‌صورت بج دایره‌ای
- اسکرول برای گزینه‌های بلند

نسخه: 2.2.0
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont
import random
import time

RLM = "\u200F"
FONT_FAMILY = "Vazirmatn"

# ✅ تبدیل ارقام انگلیسی به فارسی
_PERSIAN_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def to_persian_digits(text) -> str:
    """تبدیل ارقام انگلیسی به ارقام فارسی"""
    return str(text).translate(_PERSIAN_DIGITS)

# مدت انیمیشن ورود هر دکمه (ms)
FADE_IN_MS = 320
# تأخیر پله‌ای بین دکمه‌ها (ms)
STAGGER_DELAY_MS = 70
# تعداد گام‌های انیمیشن
ANIM_STEPS = 12


# ====================================================================
# بج دایره‌ای شماره
# ====================================================================
class _NumberBadge(QLabel):
    """دایره‌ی کوچک با شماره‌ی گزینه — با ارقام فارسی"""

    def __init__(self, number: int, parent=None):
        # ✅ ارقام فارسی به‌جای انگلیسی
        super().__init__(to_persian_digits(number), parent)
        self.setFixedSize(32, 32)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFont(
            QFont(FONT_FAMILY, 13, QFont.Weight.Bold)
        )
        self.setStyleSheet("""
            QLabel {
                color: #4FC3F7;
                background-color: rgba(79, 195, 247, 0.15);
                border: 2px solid #4FC3F7;
                border-radius: 16px;
            }
        """)
        self.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents, True
        )


# ====================================================================
# دکمه گزینه
# ====================================================================
class ChoiceButton(QFrame):
    """دکمه‌ی گزینه با بج شماره و متن"""

    clicked = pyqtSignal(dict)

    def __init__(self, choice: dict, display_number: int,
                 parent=None):
        super().__init__(parent)
        self.choice_data = choice
        self.setObjectName("choiceButton")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setMinimumHeight(76)

        # ✅ شدت پس‌زمینه (0.0 تا 1.0) — به‌جای opacity effect
        self._bg_intensity = 0.0

        self._apply_style()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(14)

        badge = _NumberBadge(display_number)
        layout.addWidget(
            badge,
            alignment=Qt.AlignmentFlag.AlignTop
            | Qt.AlignmentFlag.AlignRight,
        )

        text_col = QVBoxLayout()
        text_col.setSpacing(6)

        thought = choice.get("thought", "").strip()
        if thought:
            thought_lbl = QLabel(f"💭  {RLM}{thought}")
            thought_lbl.setWordWrap(True)
            thought_lbl.setFont(QFont(FONT_FAMILY, 11))
            thought_lbl.setStyleSheet(
                "color: #90A4AE; background: transparent; "
                "border: none; font-style: italic; "
                "padding: 2px 4px;"
            )
            thought_lbl.setLayoutDirection(
                Qt.LayoutDirection.RightToLeft
            )
            thought_lbl.setAlignment(
                Qt.AlignmentFlag.AlignRight
                | Qt.AlignmentFlag.AlignAbsolute
            )
            thought_lbl.setAttribute(
                Qt.WidgetAttribute.WA_TransparentForMouseEvents,
                True,
            )
            text_col.addWidget(thought_lbl)

            sep = QFrame()
            sep.setFrameShape(QFrame.Shape.HLine)
            sep.setStyleSheet(
                "background-color: #2B4A6F; "
                "max-height: 1px; border: none;"
            )
            sep.setAttribute(
                Qt.WidgetAttribute.WA_TransparentForMouseEvents,
                True,
            )
            text_col.addWidget(sep)

        text = choice.get("text_fa", choice.get("text", ""))
        self.label = QLabel(f"{RLM}{text}")
        self.label.setWordWrap(True)
        self.label.setFont(QFont(FONT_FAMILY, 13))
        self.label.setStyleSheet(
            "color: #FFFFFF; background: transparent; "
            "border: none;"
        )
        self.label.setLayoutDirection(
            Qt.LayoutDirection.RightToLeft
        )
        self.label.setAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignAbsolute
            | Qt.AlignmentFlag.AlignVCenter
        )
        self.label.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents, True
        )
        text_col.addWidget(self.label)

        layout.addLayout(text_col, 1)

    # ------------------------------------------------------------------
    def set_bg_intensity(self, value: float):
        """تنظیم شدت پس‌زمینه (برای انیمیشن ورود)"""
        self._bg_intensity = max(0.0, min(1.0, value))
        self._apply_style()

    def _apply_style(self):
        """اعمال استایل با شدت فعلی"""
        # رنگ پس‌زمینه بین #0B1D3A و #1A2A4A نوسان می‌کند
        intensity = self._bg_intensity
        # از شفافیت استفاده می‌کنیم (rgba)
        alpha = int(40 + 120 * intensity)  # 40 تا 160
        self.setStyleSheet(f"""
            QFrame#choiceButton {{
                background-color: rgba(26, 42, 74, {alpha / 255:.3f});
                border: 2px solid #4FC3F7;
                border-radius: 12px;
            }}
        """)

    def _apply_hover_style(self):
        self.setStyleSheet("""
            QFrame#choiceButton {
                background-color: #2B4A6F;
                border: 2px solid #FFFFFF;
                border-radius: 12px;
            }
        """)

    def enterEvent(self, event):  # type: ignore
        self._apply_hover_style()
        super().enterEvent(event)

    def leaveEvent(self, event):  # type: ignore
        self._apply_style()  # بازگشت به حالت عادی (با intensity فعلی)
        super().leaveEvent(event)

    def mousePressEvent(self, event):  # type: ignore
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.choice_data)
        super().mousePressEvent(event)


# ====================================================================
# ویجت اصلی
# ====================================================================
class ChoiceWidget(QWidget):
    choice_made = pyqtSignal(dict, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.choices = []
        self.buttons = []
        self.decision_start_time = 0
        self.is_visible = False
        self._already_emitted = False
        self._scenario_id: str = ""
        # ✅ نگه‌داری تایمرهای انیمیشن
        self._anim_timers: list = []

        self._setup_ui()
        print("✓ ChoiceWidget راه‌اندازی شد (نسخه 2.2)")

    # ------------------------------------------------------------------
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 20, 30, 20)
        main_layout.setSpacing(12)

        title_label = QLabel("انتخاب کنید:")
        title_font = QFont(FONT_FAMILY, 22)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("QLabel { color: #4FC3F7; }")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(
            "QScrollArea { background-color: transparent; "
            "border: none; }"
        )
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        scroll_content = QWidget()
        scroll_content.setStyleSheet(
            "background-color: transparent;"
        )
        self.buttons_container = QVBoxLayout(scroll_content)
        self.buttons_container.setSpacing(14)
        self.buttons_container.setContentsMargins(6, 6, 6, 6)
        self.buttons_container.addStretch()

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll, stretch=1)

        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

    # ------------------------------------------------------------------
    def show_choices(self, choices: list, scenario_id: str = ""):
        self._stop_all_anims()
        self._clear_buttons()
        self._already_emitted = False
        self._scenario_id = scenario_id

        shuffled = list(choices)
        random.shuffle(shuffled)

        self.choices = shuffled
        self.is_visible = True
        self.decision_start_time = time.time()

        for i, choice in enumerate(shuffled):
            display_number = i + 1
            btn = ChoiceButton(choice, display_number)
            btn.clicked.connect(self._on_choice_clicked)
            self.buttons_container.insertWidget(
                self.buttons_container.count() - 1, btn
            )
            self.buttons.append(btn)

            # ✅ شروع از شدت 0
            btn.set_bg_intensity(0.0)

            delay = i * STAGGER_DELAY_MS
            QTimer.singleShot(
                delay,
                lambda b=btn: self._animate_button_in(b),
            )

    # ------------------------------------------------------------------
    def _animate_button_in(self, btn: ChoiceButton):
        """انیمیشن ورود با تغییر تدریجی رنگ پس‌زمینه"""
        try:
            _ = btn.width()
        except RuntimeError:
            return

        step = {"i": 0}

        timer = QTimer(self)

        def _tick():
            step["i"] += 1
            progress = min(1.0, step["i"] / ANIM_STEPS)
            try:
                btn.set_bg_intensity(progress)
            except RuntimeError:
                timer.stop()
                return
            if progress >= 1.0:
                timer.stop()

        timer.timeout.connect(_tick)
        interval = max(20, FADE_IN_MS // ANIM_STEPS)
        timer.start(interval)
        self._anim_timers.append(timer)

    # ------------------------------------------------------------------
    def _on_choice_clicked(self, choice: dict):
        if self._already_emitted:
            print("⚠️ تلاش برای emit دوباره نادیده گرفته شد")
            return
        self._already_emitted = True

        decision_time = int(
            (time.time() - self.decision_start_time) * 1000
        )

        self.choice_made.emit(choice, decision_time)

    # ------------------------------------------------------------------
    def _stop_all_anims(self):
        for timer in self._anim_timers:
            try:
                timer.stop()
            except RuntimeError:
                pass
        self._anim_timers.clear()

    def _clear_buttons(self):
        for button in self.buttons:
            try:
                self.buttons_container.removeWidget(button)
                button.deleteLater()
            except RuntimeError:
                pass
        self.buttons.clear()

    # ------------------------------------------------------------------
    def hide_choices(self):
        self._stop_all_anims()
        self._clear_buttons()
        self.is_visible = False
        self.hide()

    def is_showing(self) -> bool:
        return self.is_visible