"""
صحنه‌ی نامه به خود
- یک متن آزاد پیش از پایان بازی
- ذخیره در دیتابیس برای پژوهشگر
- در حالت Short و Theater غیرفعال است

نسخه: 1.0.0
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from scenes.base_scene import BaseScene
from widgets.hud_widget import HUDWidget

FONT_FAMILY = "Vazirmatn"


class LetterToSelfScene(BaseScene):
    """صحنه‌ی نوشتن نامه به خود"""

    def __init__(self, game_manager):
        super().__init__(game_manager)

        self.next_scene: str = "results"
        self._submitted: bool = False

        self.hud = HUDWidget()
        self._setup_ui()

        from core.rtl_helper import apply_rtl_fixes
        apply_rtl_fixes(self)

        print("✓ LetterToSelfScene راه‌اندازی شد")

    def _setup_ui(self):
        main_layout = self.main_layout
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.hud.set_mission("ایستگاه کاسپین")
        self.hud.set_phase("لحظه‌ی تأمل")
        self.hud.set_phase_color("#4CAF50")
        self.hud.set_objective("نوشتن نامه به خود")
        main_layout.addWidget(self.hud)

        # ناحیه‌ی مرکزی
        center = QWidget()
        center.setStyleSheet(
            "background: qlineargradient("
            "x1:0, y1:0, x2:0.3, y2:1, "
            "stop:0 #050A18, stop:1 #0B1D3A);"
        )
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(100, 30, 100, 30)
        center_layout.setSpacing(16)

        # عنوان
        title = QLabel("نامه به خود")
        tf = QFont(FONT_FAMILY, 32)
        tf.setBold(True)
        title.setFont(tf)
        title.setStyleSheet("color: #4CAF50;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(title)

        # زیرعنوان
        subtitle = QLabel("لحظه‌ای برای خلوت کردن با خود")
        subtitle.setFont(QFont(FONT_FAMILY, 16))
        subtitle.setStyleSheet("color: #FF8F00;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(subtitle)

        # فضاسازی
        intro = QLabel(
            "پیش از دیدن نتایج نهایی، این لحظه فقط مال خودت است. "
            "هیچ‌کس این متن را نمی‌بیند — مگر خودت که روزی "
            "بازخواهی خواند.\n\n"
            "اگر بخواهی به خودت، به آن کسی که در این چهار روز "
            "تصمیم گرفت، یک جمله بگویی، آن جمله چیست؟"
        )
        intro.setFont(QFont(FONT_FAMILY, 13))
        intro.setStyleSheet(
            "color: #CCCCCC; padding: 14px; "
            "background-color: rgba(26, 42, 74, 0.4); "
            "border: 1px solid #2B4A6F; border-radius: 8px;"
        )
        intro.setWordWrap(True)
        intro.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        intro.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignAbsolute
        )
        intro.setMinimumHeight(100)
        center_layout.addWidget(intro)

        # QTextEdit برای نوشتن
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText(
            "اینجا بنویس... (اگر نمی‌خواهی، می‌توانی این بخش را "
            "خالی بگذاری)"
        )
        self.text_edit.setFont(QFont(FONT_FAMILY, 13))
        self.text_edit.setLayoutDirection(
            Qt.LayoutDirection.RightToLeft
        )
        self.text_edit.setMinimumHeight(180)
        self.text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #1A2A4A;
                color: #FFFFFF;
                border: 2px solid #4FC3F7;
                border-radius: 10px;
                padding: 12px;
            }
            QTextEdit:focus {
                border: 2px solid #4CAF50;
            }
        """)
        center_layout.addWidget(self.text_edit)

        # شمارنده‌ی کلمات
        self.counter_label = QLabel("۰ کلمه")
        self.counter_label.setFont(QFont(FONT_FAMILY, 11))
        self.counter_label.setStyleSheet("color: #B0BEC5;")
        self.counter_label.setAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignVCenter
        )
        center_layout.addWidget(self.counter_label)

        self.text_edit.textChanged.connect(self._on_text_changed)

        # دکمه‌ها
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(12)

        skip_btn = QPushButton("رد کردن")
        skip_btn.setFont(QFont(FONT_FAMILY, 13))
        skip_btn.setMinimumHeight(52)
        skip_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        skip_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #B0BEC5;
                border: 2px solid #546E7A;
                border-radius: 10px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: rgba(176, 190, 197, 0.15);
                color: #FFFFFF;
            }
        """)
        skip_btn.clicked.connect(self._on_skip)
        buttons_layout.addWidget(skip_btn, 2)

        submit_btn = QPushButton("ذخیره و ادامه")
        submit_btn.setFont(
            QFont(FONT_FAMILY, 14, QFont.Weight.Bold)
        )
        submit_btn.setMinimumHeight(52)
        submit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        submit_btn.setStyleSheet("""
            QPushButton {
                background-color: #2B4A6F;
                color: #FFFFFF;
                border: 2px solid #4CAF50;
                border-radius: 10px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #4CAF50;
                color: #0B1D3A;
            }
        """)
        submit_btn.clicked.connect(self._on_submit)
        buttons_layout.addWidget(submit_btn, 1)

        center_layout.addLayout(buttons_layout)
        center_layout.addStretch()

        main_layout.addWidget(center, stretch=1)

    # ================================================================
    def on_enter(self, **kwargs):
        self.next_scene = str(kwargs.get("next_scene", "results"))
        self._submitted = False

        # ریست کردن متن
        self.text_edit.clear()

        self.data_logger.log_event(
            scene_id="letter_to_self",
            scenario_id="letter_start",
            event_type="scene_enter",
            metadata={"next_scene": self.next_scene}
        )

        self.text_edit.setFocus()
        print(f"✓ ورود به نامه به خود — next={self.next_scene}")

    # ================================================================
    def _on_text_changed(self):
        text = self.text_edit.toPlainText()
        words = len(text.split()) if text.strip() else 0
        self.counter_label.setText(f"{words} کلمه")

    # ================================================================
    def _on_submit(self):
        if self._submitted:
            return
        self._submitted = True

        text = self.text_edit.toPlainText().strip()

        try:
            self.data_logger.save_self_letter(text)
        except Exception as e:
            print(f"⚠️ خطا در ذخیره‌ی نامه: {e}")

        self.data_logger.log_event(
            scene_id="letter_to_self",
            scenario_id="letter_complete",
            event_type="letter_submitted",
            metadata={
                "word_count": len(text.split()) if text else 0,
                "char_count": len(text),
            }
        )

        print(f"✓ نامه ذخیره شد — {len(text)} کاراکتر")
        self._go_to_next()

    def _on_skip(self):
        if self._submitted:
            return
        self._submitted = True

        try:
            self.data_logger.save_self_letter("")
        except Exception as e:
            print(f"⚠️ خطا در ذخیره‌ی نامه: {e}")

        self.data_logger.log_event(
            scene_id="letter_to_self",
            scenario_id="letter_complete",
            event_type="letter_skipped",
            metadata={}
        )

        print("✓ نامه رد شد")
        self._go_to_next()

    def _go_to_next(self):
        # ✅ اگر مرحله‌ی بعد HEXACO است، با یک میان‌پرده‌ی
        #    روایی، سبک را عوض می‌کنیم
        if self.next_scene == "hexaco":
            self.change_scene(
                "interlude",
                next_scene="hexaco",
                title="گزارش شخصیتی",
                subtitle="چند دقیقه با خودت",
                body_text=(
                    "چند ساعت بعد. پرونده‌ی شورا بسته شده، و "
                    "کارهای اداری مأموریت به پایان رسیده. "
                    "قبل از اینکه همه چیز به مرکز فرستاده شود، "
                    "مرکز فرماندهی یک پرسشنامه‌ی استاندارد "
                    "شخصیتی هم درخواست کرده — بخشی از "
                    "پروتکل ارزیابی تکنسین‌های ارشد."
                ),
                dialogues=[
                    {
                        "speaker": "راوی",
                        "text": (
                            "به اتاق کوچکی می‌روی که فقط یک "
                            "میز و یک نمایشگر دارد. صفحه، "
                            "انتظار شروع را نشان می‌دهد."
                        )
                    },
                ],
                video_path="interlude_hexaco.png",
            )
        else:
            self.change_scene(self.next_scene)

    # ================================================================
    def keyPressEvent(self, event):  # type: ignore
        # Ctrl+Enter برای ثبت سریع
        if (
            event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter)
            and event.modifiers() & Qt.KeyboardModifier.ControlModifier
        ):
            self._on_submit()
        else:
            super().keyPressEvent(event)