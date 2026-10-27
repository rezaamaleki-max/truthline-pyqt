"""
ویجت جعبه دیالوگ - نسخه اصلاح‌شده
رفع باگ: text_label به layout اضافه شده بود ولی نه واقعاً!
تغییر: نشانگر ادامه به یک فلش کوچک و کمرنگ تبدیل شد.
"""
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame,
    QBoxLayout, QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPixmap, QFont
import os
from typing import Optional

from data.glossary import GLOSSARY
from widgets.portrait_widget import PortraitWidget
from core.character_registry import resolve_portrait_auto

FONT_FAMILY = "Vazirmatn"


class DialogueWidget(QWidget):
    dialogue_finished = pyqtSignal()
    choice_requested = pyqtSignal(list)
    advanced = pyqtSignal()  # ✅ سیگنال جدید: هنگام کلیک کاربر

    def __init__(self, parent=None, data_logger=None):
        super().__init__(parent)

        self.data_logger = data_logger

        self.current_text = ""
        self.full_text = ""
        self.speaker_name = ""
        self.portrait_path = None
        self.char_index = 0
        self.typing_speed = 15
        self._glossary_terms_in_text: list = []

        self.typing_timer = QTimer()
        self.typing_timer.timeout.connect(self._type_next_char)

        # ✅ اطمینان از دریافت کلید Space روی این ویجت
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self._setup_ui()
        print("✓ DialogueWidget راه‌اندازی شد (نسخه اصلاح‌شده)")

    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(15, 10, 15, 10)
        main_layout.setSpacing(15)
        main_layout.setDirection(QBoxLayout.Direction.LeftToRight)

        # ---------- پرتره (مربعی) ----------
        self.portrait_label = PortraitWidget(width=180, height=180)
        # ✅ سایه‌ی QGraphicsDropShadowEffect حذف شد —
        #    دلیل کرش‌های QPainter re-entrancy بود
        main_layout.addWidget(
            self.portrait_label,
            alignment=Qt.AlignmentFlag.AlignTop,
        )

        # ---------- کادر دیالوگ ----------
        dialogue_frame = QFrame()
        dialogue_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(26, 42, 74, 0.95);
                border: 2px solid #4FC3F7;
                border-radius: 12px;
            }
        """)
        # ✅ سایه حذف شد
        dialogue_frame.setMaximumHeight(360)

        dialogue_layout = QVBoxLayout(dialogue_frame)
        dialogue_layout.setContentsMargins(15, 12, 15, 12)
        dialogue_layout.setSpacing(8)
        dialogue_layout.setDirection(QBoxLayout.Direction.TopToBottom)

        # ---------- نام گوینده ----------
        self.speaker_label = QLabel()
        self.speaker_label.setTextFormat(Qt.TextFormat.PlainText)
        # نام گوینده PlainText می‌ماند — بدون تگ
        self.speaker_label.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.speaker_label.setAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignAbsolute
            | Qt.AlignmentFlag.AlignVCenter
        )
        # ✅ Typography نام گوینده
        from widgets.typography import make_speaker_name
        self.speaker_label.setFont(make_speaker_name(16))
        self.speaker_label.setStyleSheet("""
            QLabel {
                color: #4FC3F7;
                padding-right: 5px;
                background: transparent;
            }
        """)
        self.speaker_label.setMinimumHeight(28)
        dialogue_layout.addWidget(self.speaker_label, 0)

        # ---------- متن دیالوگ ✅ این‌بار به layout اضافه می‌شود ----------
        self.text_label = QLabel()
        self.text_label.setTextFormat(Qt.TextFormat.RichText)
        self.text_label.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.text_label.setAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignAbsolute
            | Qt.AlignmentFlag.AlignTop
        )
        # ✅ Typography روایی
        from widgets.typography import make_narrative
        self.text_label.setFont(make_narrative(16))
        self.text_label.setWordWrap(True)
        self.text_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                padding-right: 5px;
                background: transparent;
            }
        """)
        self.text_label.setMinimumHeight(90)
        self.text_label.setMaximumHeight(220)
        # ✅✅✅ این خط کلیدی است که قبلاً فراموش شده بود ✅✅✅
        dialogue_layout.addWidget(self.text_label, 1)

        # ---------- نشانگر ادامه (فلش کوچک و کمرنگ) ----------
        self.continue_label = QLabel()
        self.continue_label.setTextFormat(Qt.TextFormat.PlainText)
        self.continue_label.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.continue_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignAbsolute
        )
        self.continue_label.setFont(QFont(FONT_FAMILY, 12))
        self.continue_label.setStyleSheet("""
            QLabel {
                color: #4FC3F7;
                background: transparent;
                padding-left: 4px;
            }
        """)
        self.continue_label.setMinimumHeight(18)
        self.continue_label.setVisible(False)
        # ✅ فقط یک فلش ساده، بدون متن «کلیک یا Space»
        self.continue_label.setText("▼")
        dialogue_layout.addWidget(self.continue_label, 0)

        # ---------- ردیف پایین: واژه‌نامه + Skip ----------
        bottom_row = QHBoxLayout()
        bottom_row.setContentsMargins(0, 0, 0, 0)
        bottom_row.setSpacing(8)
        bottom_row.setDirection(QBoxLayout.Direction.RightToLeft)

        # دکمه واژه‌نامه
        self.glossary_btn = QPushButton("ⓘ  واژه‌های تخصصی")
        self.glossary_btn.setFont(QFont(FONT_FAMILY, 11))
        self.glossary_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.glossary_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.glossary_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #FFB74D;
                border: 1px dashed #FF8F00;
                border-radius: 6px;
                padding: 4px 10px;
            }
            QPushButton:hover {
                background-color: rgba(255, 143, 0, 0.15);
                color: #FFFFFF;
            }
        """)
        self.glossary_btn.setVisible(False)
        self.glossary_btn.clicked.connect(self._show_glossary)
        bottom_row.addWidget(self.glossary_btn)

        bottom_row.addStretch(1)

        # دکمه Skip
        self.skip_btn = QPushButton("⏭")
        self.skip_btn.setFont(QFont(FONT_FAMILY, 12))
        self.skip_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.skip_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.skip_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #90A4AE;
                border: 1px solid #546E7A;
                border-radius: 6px;
                padding: 3px 10px;
            }
            QPushButton:hover {
                background-color: rgba(144, 164, 174, 0.15);
                color: #FFFFFF;
                border: 1px solid #B0BEC5;
            }
        """)
        self.skip_btn.setToolTip("پرش به پایان این دیالوگ (کلید S)")
        self.skip_btn.clicked.connect(self._on_skip_clicked)
        bottom_row.addWidget(self.skip_btn)

        dialogue_layout.addLayout(bottom_row)

        main_layout.addWidget(dialogue_frame, stretch=1)

    # ------------------------------------------------------------------
    def _on_skip_clicked(self):
        """پرش فوری به پایان دیالوگ جاری"""
        self.typing_timer.stop()
        self.char_index = len(self.full_text)
        self.current_text = self.full_text
        self.text_label.setText(self.current_text)
        self.continue_label.setVisible(True)
        self.skip_btn.setVisible(False)

        if self.data_logger is not None:
            try:
                self.data_logger.log_event(
                    scene_id="dialogue",
                    scenario_id="dialogue_skip",
                    event_type="skip_used",
                    metadata={
                        "speaker": self.speaker_name,
                        "text_length": len(self.full_text),
                    }
                )
            except Exception as e:
                print(f"⚠️ خطا در log_event برای skip: {e}")

    def show_dialogue(self, speaker_name: str, text: str,
                      portrait_path: Optional[str] = None,
                      emotion: Optional[str] = None):
        self.speaker_name = speaker_name
        self.full_text = text
        self.portrait_path = portrait_path
        self.char_index = 0
        self.current_text = ""

        self.speaker_label.setText(speaker_name)
        self.text_label.setText("")
        self.continue_label.setVisible(False)

        from core.character_registry import get_character
        char = get_character(speaker_name)
        char_color = char.get("color", "#4FC3F7")

        # ✅ تشخیص راوی
        is_narrator = (
            char.get("key") == "narrator"
            or speaker_name in ("راوی", "narrator")
        )

        self.speaker_label.setStyleSheet(f"""
            QLabel {{
                color: {char_color};
                padding-right: 5px;
                background: transparent;
            }}
        """)

        self._update_glossary(text)

        # ✅ اگر راوی است، از تنظیم پرتره صرف‌نظر کن
        if is_narrator:
            self.portrait_label.setVisible(False)
            # ✅ متن روایت کمی متفاوت از دیالوگ شخصیت‌ها
            self.text_label.setStyleSheet("""
                QLabel {
                    color: #E8E8E8;
                    padding-right: 5px;
                    background: transparent;
                }
            """)
            self.skip_btn.setVisible(True)
            
            # ✅ بررسی حالت سریع برای راوی
            from core.app_config import get_fast_mode
            if get_fast_mode():
                self.char_index = len(text)
                self.current_text = text
                self.text_label.setText(self._format_html(text))
                self.continue_label.setVisible(True)
                self.skip_btn.setVisible(False)
            else:
                self.typing_timer.start(self.typing_speed)
            return

        # برای شخصیت‌ها، استایل پیش‌فرض برمی‌گردد
        self.text_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                padding-right: 5px;
                background: transparent;
            }
        """)

        # از این نقطه به بعد، گوینده شخصیت است
        self.portrait_label.setVisible(True)

        # ✅ تعیین emotion: اول override، بعد تشخیص از متن
        from core.character_registry import (
            get_character,
            detect_emotion,
            resolve_portrait_path,
        )
        char = get_character(speaker_name)

        if emotion:
            # ✅ اگر صریح داده شده، از آن استفاده کن
            final_emotion = emotion
        else:
            # ✅ در غیر این صورت، از متن تشخیص بده
            final_emotion = detect_emotion(text)

        # ✅ تعیین مسیر پرتره
        if portrait_path:
            auto_path = portrait_path
        else:
            auto_path = resolve_portrait_path(char, final_emotion)

        self.portrait_label.setFixedSize(180, 180)
        self.portrait_label.set_character(
            char, final_emotion, auto_path
        )

        self.skip_btn.setVisible(True)

        # ✅ حالت سریع: نمایش فوری متن بدون تایپ
        from core.app_config import get_fast_mode
        if get_fast_mode():
            self.char_index = len(text)
            self.current_text = text
            self.text_label.setText(self._format_html(text))
            self.continue_label.setVisible(True)
            self.skip_btn.setVisible(False)
        else:
            self.typing_timer.start(self.typing_speed)

    def _update_glossary(self, text: str):
        self._glossary_terms_in_text = []
        for term, definition in GLOSSARY.items():
            if term in text:
                self._glossary_terms_in_text.append((term, definition))

        self.glossary_btn.setVisible(bool(self._glossary_terms_in_text))

    def _show_glossary(self):
        if not self._glossary_terms_in_text:
            return
        lines = []
        for term, definition in self._glossary_terms_in_text:
            lines.append(f"◆ {term}\n   {definition}")
        msg = QMessageBox(self)
        msg.setWindowTitle("واژه‌های تخصصی")
        msg.setText("\n\n".join(lines))
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        msg.exec()

    def _type_next_char(self):
        if self.char_index < len(self.full_text):
            self.char_index += 1
            self.current_text = self.full_text[:self.char_index]
            # ✅ استفاده از HTML برای line-height بهتر
            self.text_label.setText(
                self._format_html(self.current_text)
            )
        else:
            self.typing_timer.stop()
            # ✅ اتمام تایپ — قالب نهایی با line-height کامل
            self.text_label.setText(
                self._format_html(self.full_text)
            )
            self.continue_label.setVisible(True)

    def _format_html(self, text: str) -> str:
        """
        قالب‌بندی HTML برای متن دیالوگ با line-height بهتر.
        کاراکترهای خاص را escape می‌کند.
        """
        # escape کاراکترهای HTML
        safe = (
            text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
        )
        # تبدیل \n به <br>
        safe = safe.replace("\n", "<br>")
        return (
            f'<div style="line-height: 170%; '
            f'color: #FFFFFF;">{safe}</div>'
        )

    def advance(self) -> bool:
        """اگر در حال تایپ بود، متن را کامل می‌کند و False برمی‌گرداند.
        اگر تایپ تمام شده بود، True برمی‌گرداند (یعنی caller پیشروی کند)."""
        if self.typing_timer.isActive():
            self.typing_timer.stop()
            self.char_index = len(self.full_text)
            self.current_text = self.full_text
            self.text_label.setText(
                self._format_html(self.full_text)
            )
            self.continue_label.setVisible(True)
            self.skip_btn.setVisible(False)
            return False
        return True

    def is_typing(self) -> bool:
        return self.typing_timer.isActive()

    def is_complete(self) -> bool:
        return (self.char_index >= len(self.full_text)
                and not self.typing_timer.isActive())

    def clear(self):
        self.typing_timer.stop()
        self.speaker_label.setText("")
        self.text_label.setText("")
        self.portrait_label.set_character({}, "neutral", None)
        self.continue_label.setVisible(False)
        self.glossary_btn.setVisible(False)
        self._glossary_terms_in_text = []
        self.char_index = 0
        self.current_text = ""
        self.full_text = ""

    def mousePressEvent(self, event):  # type: ignore
        """کلیک روی هرجای کادر دیالوگ = پیشروی"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.advanced.emit()
        super().mousePressEvent(event)

