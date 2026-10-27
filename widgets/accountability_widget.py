"""
ویجت بازخواست شورا — نسخه 5.0
=====================================
تغییرات نسخه 5.0:
- انیمیشن ورود اعضا (Fade + Slide از راست)
- نوار پیشرفت جلسه (بالای صفحه)
- کارت عضو با هاله‌ی فشار
- انیمیشن pulse روی فشار زیاد
- حذف دکمه‌ی «ادامه» — کلیک روی هرجای صفحه

نسخه: 5.0.0
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QStackedWidget, QSizePolicy, QProgressBar,
    QGraphicsOpacityEffect
)
from PyQt6.QtCore import (
    Qt, QTimer, pyqtSignal, QPropertyAnimation,
    QEasingCurve, QPoint
)
from PyQt6.QtGui import (
    QFont, QPainter, QPen, QColor, QBrush, QRadialGradient
)
from PyQt6.QtCore import QPointF
import random
import time
import math

FONT_FAMILY = "Vazirmatn"
RLM = "\u200F"


PRESSURE_META = {
    1: {
        "label": "کم",
        "color": "#4FC3F7",
        "bg": "rgba(79, 195, 247, 0.10)",
        "desc": "شورا عمدتاً توضیح می‌خواهد",
        "icon": "🌤",
    },
    2: {
        "label": "متوسط",
        "color": "#FF8F00",
        "bg": "rgba(255, 143, 0, 0.12)",
        "desc": "شورا شروع به انتقاد می‌کند",
        "icon": "⛅",
    },
    3: {
        "label": "زیاد",
        "color": "#D32F2F",
        "bg": "rgba(211, 47, 47, 0.15)",
        "desc": "شورا خشمگین است و بازخواست شدید می‌کند",
        "icon": "⛈",
    },
}


# ====================================================================
# نشانگر بصری یک دور
# ====================================================================
class _RoundIndicator(QFrame):
    """یک دایره در نوار نشانگر دورها"""

    def __init__(self, index: int, member_name: str, parent=None):
        super().__init__(parent)
        self.index = index
        self.setFixedSize(120, 56)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.dot_label = QLabel("○")
        self.dot_label.setFont(
            QFont("Arial", 20, QFont.Weight.Bold)
        )
        self.dot_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.dot_label)

        self.name_label = QLabel(member_name)
        self.name_label.setFont(
            QFont(FONT_FAMILY, 9, QFont.Weight.Bold)
        )
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.name_label)

        self.set_state("pending")

    def set_state(self, state: str):
        if state == "pending":
            dot, color, bg, border = (
                "○", "#666666",
                "rgba(26, 42, 74, 0.4)", "#444444",
            )
        elif state == "active":
            dot, color, bg, border = (
                "●", "#FF8F00",
                "rgba(255, 143, 0, 0.15)", "#FF8F00",
            )
        else:
            dot, color, bg, border = (
                "✓", "#4CAF50",
                "rgba(76, 175, 80, 0.15)", "#4CAF50",
            )

        self.dot_label.setText(dot)
        self.dot_label.setStyleSheet(
            f"color: {color}; background: transparent; "
            "border: none;"
        )
        self.name_label.setStyleSheet(
            f"color: {color}; background: transparent; "
            "border: none;"
        )
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg};
                border: 2px solid {border};
                border-radius: 10px;
            }}
        """)


# ====================================================================
# دکمه گزینه شورا
# ====================================================================
class _CouncilChoiceButton(QFrame):
    """دکمه گزینه با شماره و پشتیبانی از فارسی راست‌چین"""

    clicked = pyqtSignal(dict)

    def __init__(self, choice_data: dict, display_number: int,
                 parent=None):
        super().__init__(parent)
        self.choice_data = choice_data
        self.setObjectName("councilChoice")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setMinimumHeight(70)

        self._apply_normal_style()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        # ✅ در RTL، AlignLeft یعنی راست فیزیکی
        _R = (
            Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignVCenter
        )

        # ─── شماره‌ی گزینه ───
        self.number_label = QLabel(f"{display_number}")
        self.number_label.setFont(
            QFont(FONT_FAMILY, 16, QFont.Weight.Bold)
        )
        self.number_label.setStyleSheet(
            "color: #4FC3F7; background: transparent; border: none;"
        )
        self.number_label.setFixedWidth(28)
        self.number_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.number_label.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents, True
        )
        layout.addWidget(self.number_label)

        # ─── ستون متن: thought + متن اصلی ───
        text_col = QVBoxLayout()
        text_col.setSpacing(6)

        # ✅ نمایش توجیه درونی با 💭
        thought = choice_data.get("thought", "").strip()
        if thought:
            thought_lbl = QLabel(f"💭  {RLM}{thought}")
            thought_lbl.setWordWrap(True)
            thought_lbl.setFont(QFont(FONT_FAMILY, 11))
            thought_lbl.setStyleSheet(
                "color: #90A4AE; background: transparent; "
                "border: none; font-style: italic; padding: 2px 4px;"
            )
            thought_lbl.setLayoutDirection(
                Qt.LayoutDirection.RightToLeft
            )
            thought_lbl.setAlignment(_R)
            thought_lbl.setAttribute(
                Qt.WidgetAttribute.WA_TransparentForMouseEvents, True
            )
            text_col.addWidget(thought_lbl)

            # خط جداکننده
            sep = QFrame()
            sep.setFrameShape(QFrame.Shape.HLine)
            sep.setStyleSheet(
                "background-color: #2B4A6F; "
                "max-height: 1px; border: none;"
            )
            sep.setAttribute(
                Qt.WidgetAttribute.WA_TransparentForMouseEvents, True
            )
            text_col.addWidget(sep)

        # ─── متن اصلی گزینه ───
        text = choice_data.get(
            "text_fa", choice_data.get("text", "")
        )
        self.label = QLabel(f"{RLM}{text}")
        self.label.setWordWrap(True)
        self.label.setFont(QFont(FONT_FAMILY, 12))
        self.label.setStyleSheet(
            "color: #FFFFFF; background: transparent; border: none;"
        )
        self.label.setLayoutDirection(
            Qt.LayoutDirection.RightToLeft
        )
        self.label.setAlignment(_R)
        self.label.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents, True
        )
        text_col.addWidget(self.label)

        layout.addLayout(text_col, 1)

    def _apply_normal_style(self):
        self.setStyleSheet("""
            QFrame#councilChoice {
                background-color: #1A2A4A;
                border: 2px solid #4FC3F7;
                border-radius: 10px;
            }
        """)

    def _apply_hover_style(self):
        self.setStyleSheet("""
            QFrame#councilChoice {
                background-color: #2B4A6F;
                border: 2px solid #FFFFFF;
                border-radius: 10px;
            }
        """)

    def enterEvent(self, event):  # type: ignore
        self._apply_hover_style()
        super().enterEvent(event)

    def leaveEvent(self, event):  # type: ignore
        self._apply_normal_style()
        super().leaveEvent(event)

    def mousePressEvent(self, event):  # type: ignore
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.choice_data)
        super().mousePressEvent(event)


# ====================================================================
# کارت عضو شورا با هاله‌ی پویا
# ====================================================================
class _MemberCard(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("memberCard")
        self.setStyleSheet("""
            QFrame#memberCard {
                background-color: rgba(26, 42, 74, 0.85);
                border: 2px solid #4FC3F7;
                border-radius: 12px;
            }
        """)
        self.setMinimumHeight(120)   # ✅ افزایش ارتفاع برای پرتره
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(14)

        # ✅ استفاده از PortraitWidget به‌جای ایموجی
        from widgets.portrait_widget import PortraitWidget

        self.portrait_widget = PortraitWidget(width=80, height=110)
        layout.addWidget(
            self.portrait_widget,
            alignment=Qt.AlignmentFlag.AlignVCenter,
        )

        # نگه‌داشتن icon_label برای سازگاری
        self.icon_label = QLabel("")
        self.icon_label.setVisible(False)

        info = QVBoxLayout()
        info.setSpacing(4)

        self.name_label = QLabel("—")
        nf = QFont(FONT_FAMILY, 16, QFont.Weight.Bold)
        self.name_label.setFont(nf)
        self.name_label.setStyleSheet(
            "color: #FFFFFF; border: none; "
            "background: transparent;"
        )
        info.addWidget(self.name_label)

        self.role_label = QLabel("—")
        self.role_label.setFont(QFont(FONT_FAMILY, 11))
        self.role_label.setStyleSheet(
            "color: #B0BEC5; border: none; "
            "background: transparent;"
        )
        info.addWidget(self.role_label)

        layout.addLayout(info, 1)

        self.round_label = QLabel("دور ۱ از ۳")
        rlf = QFont(FONT_FAMILY, 13, QFont.Weight.Bold)
        self.round_label.setFont(rlf)
        self.round_label.setStyleSheet(
            "color: #FF8F00; border: none; "
            "background: transparent; padding: 6px 12px;"
        )
        self.round_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        layout.addWidget(self.round_label)

    def set_member(self, name: str, role: str, icon: str,
                   member_key: str = ""):
        self.name_label.setText(name)
        self.role_label.setText(role)
        self.icon_label.setText(icon if icon else "👤")

        # ✅ بارگذاری پرتره بر اساس member_key
        from core.character_registry import (
            get_character,
            get_character_by_key,        # ✅ اضافه شد
            resolve_portrait_path,
        )
        if member_key:
            char = get_character_by_key(member_key)
            if char:
                portrait_path = resolve_portrait_path(
                    char, "neutral"
                )
                self.portrait_widget.set_character(
                    char, "neutral", portrait_path
                )

    def set_round(self, current: int, total: int):
        self.round_label.setText(f"دور {current} از {total}")

    def set_pressure_color(self, color: str):
        self.setStyleSheet(f"""
            QFrame#memberCard {{
                background-color: rgba(26, 42, 74, 0.85);
                border: 3px solid {color};
                border-radius: 12px;
            }}
        """)


# ====================================================================
# نوار فشار سه‌بخشی
# ====================================================================
class _PressureSegments(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(28)
        self.setLayoutDirection(Qt.LayoutDirection.LeftToRight)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.segments = []
        for _ in range(3):
            seg = QFrame()
            seg.setFixedHeight(18)
            seg.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Fixed,
            )
            self.segments.append(seg)
            layout.addWidget(seg)

        self.set_level(0)

    def set_level(self, level: int):
        colors = {1: "#4FC3F7", 2: "#FF8F00", 3: "#D32F2F"}
        for i, seg in enumerate(self.segments):
            if i < level:
                c = colors[level]
                seg.setStyleSheet(f"""
                    QFrame {{
                        background-color: {c};
                        border: 1px solid {c};
                        border-radius: 4px;
                    }}
                """)
            else:
                seg.setStyleSheet("""
                    QFrame {
                        background-color: #1A2A4A;
                        border: 1px solid #444444;
                        border-radius: 4px;
                    }
                """)

    def set_rolling(self):
        for seg in self.segments:
            seg.setStyleSheet("""
                QFrame {
                    background-color: #2B4A6F;
                    border: 1px solid #4FC3F7;
                    border-radius: 4px;
                }
            """)


# ====================================================================
# ویجت اصلی
# ====================================================================
class AccountabilityDialogWidget(QWidget):
    """مکالمه سه‌مرحله‌ای با شورای عالی — نسخه 5.0"""

    round_completed = pyqtSignal(dict)
    finished = pyqtSignal(dict)

    def __init__(self, rounds_data, analyzer_config, parent=None):
        super().__init__(parent)
        self.rounds_data = rounds_data
        self.analyzer_config = analyzer_config

        # جایگشت فشار
        self.pressure_plan = random.sample([1, 2, 3], 3)
        print(
            f"   [COUNCIL] جایگشت فشار انتخاب شد: "
            f"{self.pressure_plan}"
        )

        self.current_round_index = -1
        self.current_round: dict | None = None
        self.round_results: list = []
        self.total_start_time = int(time.time() * 1000)

        self.current_pressure = 0
        self.question_start_time = 0
        self.roll_start_time = 0
        self.roll_duration_ms = analyzer_config.get(
            "activation_delay_ms", 1500
        )
        self.roll_target = 0
        self.is_rolling = False

        self.roll_timer = QTimer(self)
        self.roll_timer.timeout.connect(self._on_roll_tick)
        self.reveal_timer = QTimer(self)
        self.reveal_timer.setSingleShot(True)
        self.reveal_timer.timeout.connect(self._on_pressure_revealed)

        self._setup_ui()
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self._start_round(0)

    # ================================================================
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 12, 30, 12)
        main_layout.setSpacing(10)

        # سرصفحه
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        self.header_icon = QLabel("🏛")
        self.header_icon.setFont(QFont("Arial", 26))
        self.header_icon.setStyleSheet("border: none;")
        header_layout.addWidget(self.header_icon)

        self.header_label = QLabel("شورای عالی ایستگاه")
        hf = QFont(FONT_FAMILY, 19, QFont.Weight.Bold)
        self.header_label.setFont(hf)
        self.header_label.setStyleSheet("color: #4FC3F7;")
        header_layout.addWidget(self.header_label)
        header_layout.addStretch()

        self.round_counter = QLabel("آماده شروع")
        self.round_counter.setFont(
            QFont(FONT_FAMILY, 12, QFont.Weight.Bold)
        )
        self.round_counter.setStyleSheet(
            "color: #FF8F00; padding: 4px 10px; "
            "border: 1px solid #FF8F00; border-radius: 6px;"
        )
        header_layout.addWidget(self.round_counter)

        main_layout.addLayout(header_layout)

        # نوار نشانگر دورها
        self.indicators_row = QHBoxLayout()
        self.indicators_row.setSpacing(10)
        self.indicators_row.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.round_indicators: list[_RoundIndicator] = []
        for i, rnd in enumerate(self.rounds_data):
            name = rnd.get("member_name", f"عضو {i+1}")
            short_name = name.split()[0] if name else f"عضو {i+1}"
            ind = _RoundIndicator(i, short_name)
            self.indicators_row.addWidget(ind)
            self.round_indicators.append(ind)

        main_layout.addLayout(self.indicators_row)

        # کارت عضو
        self.member_card = _MemberCard()
        main_layout.addWidget(self.member_card)

        # کادر فشار
        self.pressure_frame = QFrame()
        self._apply_pressure_theme(0)
        pf_layout = QVBoxLayout(self.pressure_frame)
        pf_layout.setContentsMargins(15, 10, 15, 10)
        pf_layout.setSpacing(6)

        pressure_header = QHBoxLayout()
        pressure_header.setSpacing(8)

        self.pressure_icon = QLabel("🎯")
        self.pressure_icon.setFont(QFont("Arial", 14))
        self.pressure_icon.setStyleSheet("border: none;")
        pressure_header.addWidget(self.pressure_icon)

        self.pressure_label = QLabel("وضعیت تحلیل‌گر: آماده")
        self.pressure_label.setFont(
            QFont(FONT_FAMILY, 12, QFont.Weight.Bold)
        )
        self.pressure_label.setStyleSheet(
            "color: #4FC3F7; border: none;"
        )
        pressure_header.addWidget(self.pressure_label, 1)

        self.pressure_value_label = QLabel("—")
        self.pressure_value_label.setFont(
            QFont(FONT_FAMILY, 13, QFont.Weight.Bold)
        )
        self.pressure_value_label.setStyleSheet(
            "color: #4FC3F7; border: none;"
        )
        pressure_header.addWidget(self.pressure_value_label)

        pf_layout.addLayout(pressure_header)

        self.pressure_segments = _PressureSegments()
        pf_layout.addWidget(self.pressure_segments)

        main_layout.addWidget(self.pressure_frame)

        # پشته محتوا
        self.content_stack = QStackedWidget()

        # صفحه‌ی ۰: فعال‌سازی
        self.analyzer_page = QWidget()
        ap = QVBoxLayout(self.analyzer_page)
        ap.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ap.setSpacing(14)

        self.analyzer_hint = QLabel(
            "برای شروع، تحلیل‌گر را فعال کنید تا سطح فشار "
            "شورا مشخص شود."
        )
        self.analyzer_hint.setFont(QFont(FONT_FAMILY, 12))
        self.analyzer_hint.setStyleSheet("color: #B0BEC5;")
        self.analyzer_hint.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.analyzer_hint.setWordWrap(True)
        ap.addWidget(self.analyzer_hint)

        self.analyzer_btn = QPushButton(
            self.analyzer_config.get(
                "button_label", "شروع بازخواست"
            )
        )
        abf = QFont(FONT_FAMILY, 14, QFont.Weight.Bold)
        self.analyzer_btn.setFont(abf)
        self.analyzer_btn.setMinimumHeight(60)
        self.analyzer_btn.setMinimumWidth(420)
        self.analyzer_btn.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.analyzer_btn.setFocusPolicy(
            Qt.FocusPolicy.NoFocus
        )
        self.analyzer_btn.setStyleSheet("""
            QPushButton {
                background-color: #2B4A6F;
                color: #FFFFFF;
                border: 2px solid #4FC3F7;
                border-radius: 10px;
                padding: 12px;
                font-weight: bold;
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
        self.analyzer_btn.clicked.connect(self._on_activate_analyzer)
        ap.addWidget(
            self.analyzer_btn,
            alignment=Qt.AlignmentFlag.AlignCenter,
        )

        self.content_stack.addWidget(self.analyzer_page)

        # صفحه‌ی ۱: در حال سنجش
        self.rolling_page = QWidget()
        rp = QVBoxLayout(self.rolling_page)
        rp.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.rolling_label = QLabel(
            "⏳ در حال پردازش گفتار..."
        )
        self.rolling_label.setFont(
            QFont(FONT_FAMILY, 15, QFont.Weight.Bold)
        )
        self.rolling_label.setStyleSheet("color: #FF8F00;")
        self.rolling_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        rp.addWidget(self.rolling_label)

        self.content_stack.addWidget(self.rolling_page)

        # صفحه‌ی ۲: سؤال
        self.question_page = QWidget()
        qp = QVBoxLayout(self.question_page)
        qp.setSpacing(10)

        self.question_frame = QFrame()
        self.question_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 143, 0, 0.12);
                border: 2px solid #FF8F00;
                border-radius: 10px;
            }
        """)
        qf = QVBoxLayout(self.question_frame)
        qf.setContentsMargins(18, 14, 18, 14)
        qf.setSpacing(6)

        self.question_speaker = QLabel("—")
        qsf = QFont(FONT_FAMILY, 12, QFont.Weight.Bold)
        self.question_speaker.setFont(qsf)
        self.question_speaker.setStyleSheet(
            "color: #FFB74D; border: none;"
        )
        qf.addWidget(self.question_speaker)

        self.question_text = QLabel("—")
        self.question_text.setFont(QFont(FONT_FAMILY, 13))
        self.question_text.setStyleSheet(
            "color: #FFFFFF; border: none;"
        )
        self.question_text.setWordWrap(True)
        self.question_text.setMinimumHeight(60)
        self.question_text.setLayoutDirection(
            Qt.LayoutDirection.RightToLeft
        )
        self.question_text.setAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignAbsolute
        )
        qf.addWidget(self.question_text)

        qp.addWidget(self.question_frame)

        self.choices_container = QVBoxLayout()
        self.choices_container.setSpacing(8)
        qp.addLayout(self.choices_container)

        self.content_stack.addWidget(self.question_page)

        # صفحه‌ی ۳: واکنش
        self.reaction_page = QWidget()
        rp2 = QVBoxLayout(self.reaction_page)
        rp2.setSpacing(10)

        self.reaction_frame = QFrame()
        self.reaction_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(26, 42, 74, 0.9);
                border: 2px solid #4FC3F7;
                border-radius: 10px;
            }
        """)
        rf = QVBoxLayout(self.reaction_frame)
        rf.setContentsMargins(18, 14, 18, 14)
        rf.setSpacing(6)

        self.reaction_icon = QLabel("💬")
        self.reaction_icon.setFont(QFont("Arial", 22))
        self.reaction_icon.setStyleSheet(
            "border: none; background: transparent;"
        )
        self.reaction_icon.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        rf.addWidget(self.reaction_icon)

        self.reaction_speaker = QLabel("—")
        rsf = QFont(FONT_FAMILY, 12, QFont.Weight.Bold)
        self.reaction_speaker.setFont(rsf)
        self.reaction_speaker.setStyleSheet(
            "color: #4FC3F7; border: none;"
        )
        self.reaction_speaker.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        rf.addWidget(self.reaction_speaker)

        self.reaction_text = QLabel("—")
        self.reaction_text.setFont(QFont(FONT_FAMILY, 13))
        self.reaction_text.setStyleSheet(
            "color: #FFFFFF; border: none;"
        )
        self.reaction_text.setWordWrap(True)
        self.reaction_text.setMinimumHeight(70)
        self.reaction_text.setLayoutDirection(
            Qt.LayoutDirection.RightToLeft
        )
        self.reaction_text.setAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignAbsolute
        )
        rf.addWidget(self.reaction_text)

        rp2.addWidget(self.reaction_frame)
        rp2.addStretch()
        self.content_stack.addWidget(self.reaction_page)

        main_layout.addWidget(self.content_stack, stretch=1)

        # نشانگر کلیک (به جای دکمه‌ی ادامه)
        self.continue_btn = QLabel(
            "▼  برای ادامه کلیک کنید  ▼"
        )
        self.continue_btn.setFont(
            QFont(FONT_FAMILY, 12, QFont.Weight.Bold)
        )
        self.continue_btn.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.continue_btn.setStyleSheet("""
            QLabel {
                color: #4FC3F7;
                background-color: rgba(79, 195, 247, 0.10);
                border: 1px dashed #4FC3F7;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        self.continue_btn.setVisible(False)
        main_layout.addWidget(self.continue_btn)

        # نوار پیشرفت
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, len(self.rounds_data))
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setLayoutDirection(
            Qt.LayoutDirection.LeftToRight
        )
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #1A2A4A;
                border: 1px solid #2B4A6F;
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background-color: #4FC3F7;
                border-radius: 2px;
            }
        """)
        main_layout.addWidget(self.progress_bar)

    # ================================================================
    def _apply_pressure_theme(self, level: int):
        if level == 0:
            self.pressure_frame.setStyleSheet("""
                QFrame {
                    background-color: rgba(79, 195, 247, 0.06);
                    border: 2px dashed #4FC3F7;
                    border-radius: 10px;
                }
            """)
            return
        meta = PRESSURE_META[level]
        self.pressure_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {meta['bg']};
                border: 2px solid {meta['color']};
                border-radius: 10px;
            }}
        """)

    # ================================================================
    def _start_round(self, index):
        if index >= len(self.rounds_data):
            self._finish_all()
            return

        self.current_round_index = index
        self.current_round = self.rounds_data[index]
        cr = self.current_round
        if cr is None:
            return

        # انیمیشن ورود کارت عضو
        self._animate_member_card_in()

        # نگاشت member_id JSON به کلید character_registry
        member_key_map = {
            "member_1": "council_science",   # دکتر مهرانی
            "member_2": "council_ethics",    # خانم آذری
            "member_3": "council_chair",     # آقای کیانی
        }
        member_key = member_key_map.get(
            cr.get("member_id", ""), ""
        )

        self.member_card.set_member(
            cr.get("member_name", ""),
            cr.get("member_role", ""),
            cr.get("member_icon", "👤"),
            member_key=member_key,
        )
        self.member_card.set_round(index + 1, len(self.rounds_data))
        self.member_card.set_pressure_color("#4FC3F7")

        for i, ind in enumerate(self.round_indicators):
            if i < index:
                ind.set_state("done")
            elif i == index:
                ind.set_state("active")
            else:
                ind.set_state("pending")

        self.round_counter.setText(
            f"دور {index + 1} از {len(self.rounds_data)}"
        )
        self.progress_bar.setValue(index)

        self.current_pressure = 0
        self.pressure_icon.setText("🎯")
        self.pressure_label.setText("وضعیت تحلیل‌گر: آماده")
        self.pressure_label.setStyleSheet(
            "color: #4FC3F7; border: none; font-weight: bold;"
        )
        self.pressure_value_label.setText("—")
        self.pressure_value_label.setStyleSheet(
            "color: #4FC3F7; border: none;"
        )
        self.pressure_segments.set_level(0)
        self._apply_pressure_theme(0)

        self._clear_choices()
        self.content_stack.setCurrentWidget(self.analyzer_page)
        self.analyzer_btn.setEnabled(True)
        self.continue_btn.setVisible(False)
        self.setFocus()

    def _animate_member_card_in(self):
        """انیمیشن Fade + Slide برای کارت عضو"""
        try:
            effect = QGraphicsOpacityEffect(self.member_card)
            effect.setOpacity(0.0)
            self.member_card.setGraphicsEffect(effect)

            final_pos = self.member_card.pos()
            start_pos = QPoint(final_pos.x() + 40, final_pos.y())
            self.member_card.move(start_pos)

            fade = QPropertyAnimation(
                effect, b"opacity", self.member_card
            )
            fade.setDuration(320)
            fade.setStartValue(0.0)
            fade.setEndValue(1.0)
            fade.setEasingCurve(QEasingCurve.Type.OutCubic)

            pos = QPropertyAnimation(
                self.member_card, b"pos", self.member_card
            )
            pos.setDuration(320)
            pos.setStartValue(start_pos)
            pos.setEndValue(final_pos)
            pos.setEasingCurve(QEasingCurve.Type.OutCubic)

            def _cleanup():
                try:
                    self.member_card.setGraphicsEffect(None)
                except Exception:
                    pass

            fade.finished.connect(_cleanup)
            self._member_anim_fade = fade
            self._member_anim_pos = pos
            fade.start()
            pos.start()
        except Exception as e:
            print(f"⚠️ خطا در انیمیشن کارت عضو: {e}")

    def _clear_choices(self):
        while self.choices_container.count():
            item = self.choices_container.takeAt(0)
            if item is None:
                continue
            w = item.widget()
            if w is not None:
                w.deleteLater()

    # ================================================================
    def _on_activate_analyzer(self):
        self.analyzer_btn.setEnabled(False)
        self.roll_target = self.pressure_plan[
            self.current_round_index
        ]
        print(
            f"   [COUNCIL] فشار دور {self.current_round_index + 1} "
            f"= {self.roll_target} "
            f"(از جایگشت {self.pressure_plan})"
        )
        self.is_rolling = True
        self.roll_start_time = int(time.time() * 1000)

        self.pressure_icon.setText("⏳")
        self.pressure_label.setText("در حال سنجش شاخص‌ها...")
        self.pressure_label.setStyleSheet(
            "color: #FF8F00; border: none; font-weight: bold;"
        )
        self.pressure_value_label.setText("...")
        self.pressure_value_label.setStyleSheet(
            "color: #FF8F00; border: none;"
        )
        self.pressure_segments.set_rolling()

        self.content_stack.setCurrentWidget(self.rolling_page)
        self.roll_timer.start(80)
        self.reveal_timer.start(self.roll_duration_ms)

    def _on_roll_tick(self):
        self.pressure_segments.set_rolling()

    def _on_pressure_revealed(self):
        self.roll_timer.stop()
        self.is_rolling = False
        self.current_pressure = self.roll_target

        # صدای اعلام فشار
        try:
            from core.audio_manager import get_audio_manager
            get_audio_manager().play_sfx("scan")
        except Exception:
            pass

        meta = PRESSURE_META[self.current_pressure]
        self.pressure_segments.set_level(self.current_pressure)
        self.pressure_value_label.setText(
            f"{self.current_pressure} از ۳"
        )
        self.pressure_value_label.setStyleSheet(
            f"color: {meta['color']}; border: none; "
            "font-weight: bold;"
        )
        self.pressure_icon.setText(meta["icon"])
        self.pressure_label.setText(
            f"سطح فشار: {meta['label']} — {meta['desc']}"
        )
        self.pressure_label.setStyleSheet(
            f"color: {meta['color']}; border: none; "
            "font-weight: bold;"
        )
        self._apply_pressure_theme(self.current_pressure)
        self.member_card.set_pressure_color(meta["color"])

        cr = self.current_round
        if cr is None:
            return

        question_text = cr.get(
            "question_by_pressure", {}
        ).get(str(self.current_pressure), "—")
        self.question_speaker.setText(
            f"{cr.get('member_name', '')} — "
            f"{cr.get('member_role', '')}"
        )
        self.question_text.setText(question_text)
        self._build_choices()
        self.content_stack.setCurrentWidget(self.question_page)
        self.question_start_time = int(time.time() * 1000)
        self.setFocus()

    def _build_choices(self):
        self._clear_choices()
        cr = self.current_round
        if cr is None:
            return

        import re
        _PATTERN = re.compile(
            r"\n\n\(توجیه منطقی:\s*(.+?)\)\s*$",
            re.DOTALL,
        )

        choices = cr.get("choices", [])
        for i, choice in enumerate(choices):
            clean_choice = dict(choice)
            raw_text = clean_choice.get("text_fa", "")
            m = _PATTERN.search(raw_text)
            if m:
                # ✅ استخراج توجیه به فیلد جدا
                clean_choice["thought"] = m.group(1).strip()
                clean_choice["text_fa"] = _PATTERN.sub(
                    "", raw_text
                ).strip()

            btn = _CouncilChoiceButton(clean_choice, i + 1)
            btn.clicked.connect(self._on_choice_made)
            self.choices_container.addWidget(btn)

    # ================================================================
    def _on_choice_made(self, choice):
        cr = self.current_round
        if cr is None:
            return

        choice_id = choice.get("id", 0)
        decision_time = (
            int(time.time() * 1000) - self.question_start_time
        )

        round_result = {
            "round_index": self.current_round_index,
            "member_id": cr.get("member_id", ""),
            "pressure": self.current_pressure,
            "choice_id": choice_id,
            "decision_time_ms": decision_time,
        }
        self.round_results.append(round_result)
        self.round_completed.emit(round_result)

        # ✅ استخراج واکنش با محافظت
        reactions_map = cr.get("reactions_by_choice", {}) or {}
        reactions = reactions_map.get(str(choice_id), [])
        print(
            f"   [COUNCIL] واکنش برای دور "
            f"{self.current_round_index + 1}, "
            f"انتخاب {choice_id}: "
            f"{len(reactions)} مورد"
        )

        if reactions:
            # ✅ ادغام همه‌ی واکنش‌ها در یک متن
            all_speakers = []
            all_texts = []
            for r in reactions:
                sp = r.get("speaker", "")
                if sp and sp not in all_speakers:
                    all_speakers.append(sp)
                all_texts.append(r.get("text_fa", ""))

            self.reaction_speaker.setText(
                " / ".join(all_speakers)
            )
            # ✅ جدا کردن جملات با <br><br>
            self.reaction_text.setText(
                "<br><br>".join(all_texts)
            )

            if self.current_pressure == 3:
                self.reaction_icon.setText("😠")
            elif self.current_pressure == 2:
                self.reaction_icon.setText("🤔")
            else:
                self.reaction_icon.setText("💬")
        else:
            # ✅ fallback اگر واکنش ثبت نشده بود
            print(
                f"   [COUNCIL] ⚠️ واکنش برای این دور ثبت نشده "
                f"— نمایش پیام پیش‌فرض"
            )
            self.reaction_speaker.setText(
                cr.get("member_name", "شورا")
            )
            self.reaction_text.setText(
                "(شورا بدون واکنش ثبت‌شده، به عضو بعدی "
                "می‌رود.)"
            )
            self.reaction_icon.setText("💬")

        self.content_stack.setCurrentWidget(self.reaction_page)

        if self.current_round_index < len(self.rounds_data) - 1:
            next_name = self.rounds_data[
                self.current_round_index + 1
            ].get("member_name", "عضو بعدی")
            self.continue_btn.setText(
                f"▼  برای ادامه به {next_name} کلیک کنید  ▼"
            )
        else:
            self.continue_btn.setText(
                "▼  برای پایان جلسه‌ی شورا کلیک کنید  ▼"
            )
        self.continue_btn.setVisible(True)

        # ✅ محافظت از پرش ناخواسته:
        #    به مدت 600ms، ادامه غیرفعال است تا بازیکن واکنش را ببیند
        self.continue_btn.setEnabled(False)
        self._continue_enabled = False

        def _enable_continue():
            try:
                self._continue_enabled = True
                self.continue_btn.setEnabled(True)
            except RuntimeError:
                pass

        QTimer.singleShot(600, _enable_continue)

        self.setFocus()

    def _on_continue(self):
        self.continue_btn.setVisible(False)
        self._start_round(self.current_round_index + 1)

    # ================================================================
    def mousePressEvent(self, event):  # type: ignore
        if event.button() != Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)
            return

        current = self.content_stack.currentWidget()

        if current is self.analyzer_page:
            if self.analyzer_btn.isEnabled():
                self._on_activate_analyzer()
            return

        if current is self.reaction_page:
            if self.continue_btn.isVisible():
                self._on_continue()
            return

        super().mousePressEvent(event)

    # ================================================================
    def handle_space(self) -> bool:
        current = self.content_stack.currentWidget()
        if current is self.reaction_page:
            # ✅ فقط اگر continue فعال شده باشد (بعد از ۶۰۰ms)
            if (self.continue_btn.isVisible()
                    and self.continue_btn.isEnabled()):
                self._on_continue()
                return True
        if current is self.analyzer_page:
            if self.analyzer_btn.isEnabled():
                self._on_activate_analyzer()
                return True
        return False

    def _finish_all(self):
        self.progress_bar.setValue(len(self.rounds_data))
        total_time = int(time.time() * 1000) - self.total_start_time
        result = {
            "rounds": self.round_results,
            "total_time_ms": total_time,
        }
        self.finished.emit(result)