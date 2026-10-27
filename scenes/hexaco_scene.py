"""
صحنه‌ی پرسشنامه‌های چندگانه
=============================
در چهار تب:
  1) HEXACO-24
  2) CRT7 — آزمون تأمل شناختی
  3) SD3 — مثلث تاریک
  4) SD — مطلوبیت اجتماعی

دکمه‌ی نهایی فقط وقتی فعال می‌شود که همه‌ی تب‌ها
تکمیل شده باشند.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QPushButton, QRadioButton, QButtonGroup,
    QMessageBox, QTabWidget, QLineEdit, QCheckBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from scenes.base_scene import BaseScene
from widgets.hud_widget import HUDWidget
from data.hexaco_items import (
    HEXACO_ITEMS, FACTORS, LIKERT_LABELS,
    compute_factor_scores
)
from data.crt_items import CRT_ITEMS, score_crt
from data.sd3_items import (
    SD3_ITEMS, SD3_FACTORS, SD3_LIKERT_LABELS,
    compute_sd3_scores
)
from data.social_desirability_items import (
    SD_ITEMS, compute_sd_score
)
from data.postgame_feedback_items import (
    FEEDBACK_ITEMS,
    FEEDBACK_SUBSCALES,
    FEEDBACK_LIKERT_LABELS,
    FEEDBACK_OPEN_QUESTIONS,
    FEEDBACK_DEMOGRAPHIC_ITEMS,
    compute_feedback_scores,
)

FONT_FAMILY = "Vazirmatn"


class HexacoScene(BaseScene):
    """صحنه‌ی چهار پرسشنامه با تب"""

    def __init__(self, game_manager):
        super().__init__(game_manager)

        # ---- داده‌ها ----
        self.hexaco_answers: dict = {}      # {item_id: 1..5}
        self.hexaco_groups: dict = {}
        self.hexaco_progress_label: QLabel | None = None

        self.crt_answers: dict = {}          # {item_id: val}
        self.crt_inputs: dict = {}           # {item_id: QLineEdit or QButtonGroup}
        self.crt_progress_label: QLabel | None = None

        self.sd3_answers: dict = {}
        self.sd3_groups: dict = {}
        self.sd3_progress_label: QLabel | None = None

        self.sd_answers: dict = {}           # {item_id: True/False}
        self.sd_groups: dict = {}
        self.sd_progress_label: QLabel | None = None

        # ✅ پس‌نگر
        self.feedback_answers: dict = {}       # {item_id: 1..5}
        self.feedback_groups: dict = {}
        self.feedback_progress_label: QLabel | None = None
        self.feedback_open_answers: dict = {}  # {open_id: text}
        self.feedback_open_inputs: dict = {}
        self.feedback_demo_answers: dict = {}  # {id: choice}
        self.feedback_demo_groups: dict = {}

        # پرچم‌های تکمیل هر بخش
        self._done_hexaco: bool = False
        self._done_crt: bool = False
        self._done_toh: bool = False       # ← جدید
        self._done_sd3: bool = False
        self._done_sd: bool = False
        self._done_feedback: bool = False

        self._setup_ui()

        # ✅ رفع RTL ورودی‌ها، لیبل‌ها، محتوای scroll
        from core.rtl_helper import apply_rtl_fixes
        apply_rtl_fixes(self)

        print("✓ HexacoScene (نسخه‌ی چند‌پرسشنامه) راه‌اندازی شد")

    # ================================================================
    def _setup_ui(self):
        main_layout = self.main_layout
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # HUD
        self.hud = HUDWidget()
        self.hud.set_mission("ایستگاه کاسپین")
        self.hud.set_phase("پرسشنامه‌های پایانی")
        self.hud.set_objective("HEXACO + CRT + SD3 + SD")
        main_layout.addWidget(self.hud)

        # تب‌ویجت
        self.tabs = QTabWidget()
        self.tabs.setFont(QFont(FONT_FAMILY, 12))
        self.tabs.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                background-color: #0B1D3A;
                border: 1px solid #2B4A6F;
            }
            QTabBar::tab {
                background-color: #1A2A4A;
                color: #B0BEC5;
                padding: 10px 20px;
                font-size: 13px;
                border: 1px solid #2B4A6F;
            }
            QTabBar::tab:selected {
                background-color: #2B4A6F;
                color: #4FC3F7;
                font-weight: bold;
            }
        """)
        main_layout.addWidget(self.tabs, stretch=1)

        # ✅ فقط تب‌های فعال را بساز
        from core.app_config import is_assessment_tool_enabled

        if is_assessment_tool_enabled("hexaco"):
            self._build_hexaco_tab()
        if is_assessment_tool_enabled("crt"):
            self._build_crt_tab()
        if is_assessment_tool_enabled("sd3"):
            self._build_sd3_tab()
        if is_assessment_tool_enabled("social_desirability"):
            self._build_sd_tab()
        if is_assessment_tool_enabled("postgame_feedback"):
            self._build_feedback_tab()

        # ---- دکمه‌ی نهایی ----
        submit_row = QWidget()
        submit_row.setStyleSheet("background-color: #0B1D3A;")
        submit_layout = QHBoxLayout(submit_row)
        submit_layout.setContentsMargins(40, 10, 40, 15)

        self.final_submit_btn = QPushButton(
            "ثبت همه‌ی پاسخ‌ها و پایان مأموریت"
        )
        self.final_submit_btn.setFont(
            QFont(FONT_FAMILY, 14, QFont.Weight.Bold)
        )
        self.final_submit_btn.setMinimumHeight(52)
        self.final_submit_btn.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.final_submit_btn.setEnabled(False)
        self.final_submit_btn.setStyleSheet("""
            QPushButton {
                background-color: #2B4A6F;
                color: #FFFFFF;
                border: 2px solid #4FC3F7;
                border-radius: 10px;
                padding: 12px;
            }
            QPushButton:hover:enabled {
                background-color: #4FC3F7;
                color: #0B1D3A;
            }
            QPushButton:disabled {
                background-color: #1A1A1A;
                color: #666666;
                border: 2px solid #444444;
            }
        """)
        self.final_submit_btn.clicked.connect(self._on_final_submit)
        submit_layout.addWidget(self.final_submit_btn)
        main_layout.addWidget(submit_row)

    # ================================================================
    # تب ۱: HEXACO
    # ================================================================
    def _build_hexaco_tab(self):
        tab = QWidget()
        tab.setStyleSheet("background-color: #0B1D3A;")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)

        desc = QLabel(
            "لطفاً هر گزاره را با دقت بخوانید و مشخص کنید که "
            "چقدر با آن موافقید. هیچ پاسخ درست یا غلطی وجود "
            "ندارد؛ تنها نظر صادقانه شما مهم است."
        )
        desc.setFont(QFont(FONT_FAMILY, 11))
        desc.setStyleSheet("color: #CCCCCC;")
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc)

        # نوار راهنمای مقیاس
        legend = QFrame()
        legend.setStyleSheet("""
            QFrame {
                background-color: rgba(26, 42, 74, 0.7);
                border: 1px solid #4FC3F7;
                border-radius: 8px;
            }
        """)
        legend_layout = QHBoxLayout(legend)
        legend_layout.setContentsMargins(15, 8, 15, 8)
        for value in [1, 2, 3, 4, 5]:
            lbl = QLabel(f"{value} = {LIKERT_LABELS[value]}")
            lbl.setFont(QFont(FONT_FAMILY, 10))
            lbl.setStyleSheet("color: #FFFFFF; border: none;")
            legend_layout.addWidget(lbl)
        legend_layout.addStretch()
        layout.addWidget(legend)

        # پیشرفت
        self.hexaco_progress_label = QLabel(
            "0 از 24 گویه پاسخ داده شده"
        )
        self.hexaco_progress_label.setFont(QFont(FONT_FAMILY, 11))
        self.hexaco_progress_label.setStyleSheet("color: #FF8F00;")
        self.hexaco_progress_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        layout.addWidget(self.hexaco_progress_label)

        # اسکرول
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(
            "QScrollArea { background-color: #0B1D3A; border: none; }"
        )
        content = QWidget()
        content.setStyleSheet("background-color: #0B1D3A;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(8, 8, 8, 8)
        content_layout.setSpacing(8)

        for item in HEXACO_ITEMS:
            content_layout.addWidget(self._build_hexaco_row(item))

        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll, stretch=1)

        # دکمه‌ی تایید HEXACO
        hexaco_done = QPushButton(
            "تکمیل HEXACO و رفتن به بخش بعدی"
        )
        hexaco_done.setFont(QFont(FONT_FAMILY, 12, QFont.Weight.Bold))
        hexaco_done.setMinimumHeight(44)
        hexaco_done.setCursor(Qt.CursorShape.PointingHandCursor)
        hexaco_done.setStyleSheet("""
            QPushButton {
                background-color: #2B4A6F;
                color: #FFFFFF;
                border: 2px solid #4CAF50;
                border-radius: 8px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #4CAF50;
                color: #0B1D3A;
            }
        """)
        hexaco_done.clicked.connect(self._on_hexaco_done)
        layout.addWidget(hexaco_done)

        self.tabs.addTab(tab, "۱. HEXACO-24")

    def _build_hexaco_row(self, item: dict) -> QFrame:
        row = QFrame()
        row.setStyleSheet("""
            QFrame {
                background-color: rgba(26, 42, 74, 0.4);
                border: 1px solid #2B4A6F;
                border-radius: 8px;
            }
        """)
        vbox = QVBoxLayout(row)
        vbox.setContentsMargins(12, 10, 12, 10)
        vbox.setSpacing(8)

        # ✅ RLM قبل از شماره — جلوگیری از چپ‌چین شدن bidi
        text_lbl = QLabel(f"\u200F{item['id']}. {item['text']}")
        text_lbl.setFont(QFont(FONT_FAMILY, 12))
        text_lbl.setStyleSheet("color: #FFFFFF; border: none;")
        text_lbl.setWordWrap(True)
        text_lbl.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        text_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        vbox.addWidget(text_lbl)

        radio_row = QHBoxLayout()
        radio_row.setSpacing(20)

        group = QButtonGroup(row)
        group.setExclusive(True)
        for value in [1, 2, 3, 4, 5]:
            rb = QRadioButton(str(value))
            rb.setFont(QFont(FONT_FAMILY, 13))
            rb.setStyleSheet("""
                QRadioButton {
                    color: #FFFFFF;
                    border: none;
                    padding: 4px 8px;
                }
                QRadioButton::indicator {
                    width: 16px; height: 16px;
                    border: 2px solid #4FC3F7;
                    border-radius: 8px;
                    background-color: #1A2A4A;
                }
                QRadioButton::indicator:checked {
                    background-color: #4FC3F7;
                }
            """)
            rb.setCursor(Qt.CursorShape.PointingHandCursor)
            rb.setToolTip(LIKERT_LABELS[value])
            group.addButton(rb, value)
            radio_row.addWidget(rb)

        radio_row.addStretch()

        group.buttonClicked.connect(
            lambda _b, iid=item["id"], g=group:
                self._on_hexaco_answer(iid, g)
        )
        self.hexaco_groups[item["id"]] = group
        vbox.addLayout(radio_row)
        return row

    def _on_hexaco_answer(self, item_id, group):
        checked = group.checkedId()
        if checked > 0:
            self.hexaco_answers[item_id] = checked
        self._update_hexaco_progress()

    def _update_hexaco_progress(self):
        if self.hexaco_progress_label is not None:
            n = len(self.hexaco_answers)
            self.hexaco_progress_label.setText(
                f"{n} از {len(HEXACO_ITEMS)} گویه پاسخ داده شده"
            )

    def _on_hexaco_done(self):
        if len(self.hexaco_answers) < len(HEXACO_ITEMS):
            QMessageBox.warning(
                self, "پاسخ‌های ناقص",
                f"شما به {len(self.hexaco_answers)} گویه از "
                f"{len(HEXACO_ITEMS)} پاسخ داده‌اید."
            )
            return
        # ✅ بررسی پاسخ‌های یکنواخت
        if len(set(self.hexaco_answers.values())) == 1:
            reply = QMessageBox.question(
                self, "تأیید پاسخ‌ها",
                "شما به همه‌ی گویه‌ها یک پاسخ داده‌اید. این "
                "می‌تواند اعتبار نتایج را کاهش دهد.\n\n"
                "مطمئن هستید؟",
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        self._done_hexaco = True
        print(
            f"✓ HEXACO تکمیل شد: "
            f"{len(self.hexaco_answers)} پاسخ"
        )
        self._update_final_button()
        # رفتن به تب بعدی
        self.tabs.setCurrentIndex(1)

    # ================================================================
    # تب ۲: CRT
    # ================================================================
    def _build_crt_tab(self):
        tab = QWidget()
        tab.setStyleSheet("background-color: #0B1D3A;")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)

        desc = QLabel(
            "این بخش شامل ۷ سؤال کوتاه است. لطفاً با دقت "
            "بخوانید و پاسخ خود را در کادر مقابل بنویسید. "
            "لازم نیست زیاد وقت بگذارید — اولین پاسخ درست "
            "به ذهنتان، معمولاً کافی است."
        )
        desc.setFont(QFont(FONT_FAMILY, 11))
        desc.setStyleSheet("color: #CCCCCC;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        self.crt_progress_label = QLabel(
            "0 از 7 سؤال پاسخ داده شده"
        )
        self.crt_progress_label.setFont(QFont(FONT_FAMILY, 11))
        self.crt_progress_label.setStyleSheet("color: #FF8F00;")
        self.crt_progress_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        layout.addWidget(self.crt_progress_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(
            "QScrollArea { background-color: #0B1D3A; border: none; }"
        )
        content = QWidget()
        content.setStyleSheet("background-color: #0B1D3A;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(8, 8, 8, 8)
        content_layout.setSpacing(10)

        for item in CRT_ITEMS:
            content_layout.addWidget(self._build_crt_row(item))

        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll, stretch=1)

        crt_done = QPushButton(
            "تکمیل CRT و رفتن به بخش بعدی"
        )
        crt_done.setFont(QFont(FONT_FAMILY, 12, QFont.Weight.Bold))
        crt_done.setMinimumHeight(44)
        crt_done.setCursor(Qt.CursorShape.PointingHandCursor)
        crt_done.setStyleSheet("""
            QPushButton {
                background-color: #2B4A6F;
                color: #FFFFFF;
                border: 2px solid #4CAF50;
                border-radius: 8px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #4CAF50;
                color: #0B1D3A;
            }
        """)
        crt_done.clicked.connect(self._on_crt_done)
        layout.addWidget(crt_done)

        self.tabs.addTab(tab, "۲. تأمل شناختی")

    def _build_crt_row(self, item: dict) -> QFrame:
        row = QFrame()
        row.setStyleSheet("""
            QFrame {
                background-color: rgba(26, 42, 74, 0.4);
                border: 1px solid #2B4A6F;
                border-radius: 8px;
            }
        """)
        vbox = QVBoxLayout(row)
        vbox.setContentsMargins(12, 10, 12, 10)
        vbox.setSpacing(8)

        # ✅ RLM قبل از شماره — جلوگیری از چپ‌چین شدن bidi
        text_lbl = QLabel(f"\u200F{item['id']}. {item['text']}")
        text_lbl.setFont(QFont(FONT_FAMILY, 12))
        text_lbl.setStyleSheet("color: #FFFFFF; border: none;")
        text_lbl.setWordWrap(True)
        text_lbl.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        text_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        vbox.addWidget(text_lbl)

        if item["type"] == "numeric":
            input_row = QHBoxLayout()
            line = QLineEdit()
            line.setFont(QFont(FONT_FAMILY, 13))
            line.setPlaceholderText(item.get("hint", "پاسخ..."))
            line.setFixedWidth(220)
            line.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            line.setStyleSheet("""
                QLineEdit {
                    background-color: #1A2A4A;
                    color: #FFFFFF;
                    border: 2px solid #4FC3F7;
                    border-radius: 6px;
                    padding: 6px 12px;
                }
            """)
            line.textChanged.connect(
                lambda txt, iid=item["id"]:
                    self._on_crt_numeric(iid, txt)
            )
            self.crt_inputs[item["id"]] = line
            input_row.addWidget(line)
            input_row.addStretch()
            vbox.addLayout(input_row)
        else:  # choice
            choice_row = QHBoxLayout()
            choice_row.setSpacing(20)
            group = QButtonGroup(row)
            group.setExclusive(True)
            for key, label in item["options"]:
                rb = QRadioButton(label)
                rb.setFont(QFont(FONT_FAMILY, 12))
                rb.setStyleSheet("""
                    QRadioButton {
                        color: #FFFFFF;
                        border: none;
                        padding: 4px 8px;
                    }
                    QRadioButton::indicator {
                        width: 16px; height: 16px;
                        border: 2px solid #4FC3F7;
                        border-radius: 8px;
                        background-color: #1A2A4A;
                    }
                    QRadioButton::indicator:checked {
                        background-color: #4FC3F7;
                    }
                """)
                rb.setCursor(Qt.CursorShape.PointingHandCursor)
                group.addButton(rb, hash(key) % 1000)
                rb.setProperty("answer_key", key)
                choice_row.addWidget(rb)

            choice_row.addStretch()

            group.buttonClicked.connect(
                lambda _b, iid=item["id"], g=group:
                    self._on_crt_choice(iid, g)
            )
            self.crt_inputs[item["id"]] = group
            vbox.addLayout(choice_row)

        return row

    def _on_crt_numeric(self, item_id, text):
        if text.strip():
            self.crt_answers[item_id] = text.strip()
        else:
            self.crt_answers.pop(item_id, None)
        self._update_crt_progress()

    def _on_crt_choice(self, item_id, group):
        btn = group.checkedButton()
        if btn is not None:
            key = btn.property("answer_key")
            self.crt_answers[item_id] = key
        self._update_crt_progress()

    def _update_crt_progress(self):
        if self.crt_progress_label is not None:
            n = len(self.crt_answers)
            self.crt_progress_label.setText(
                f"{n} از {len(CRT_ITEMS)} سؤال پاسخ داده شده"
            )

    def _on_crt_done(self):
        if len(self.crt_answers) < len(CRT_ITEMS):
            QMessageBox.warning(
                self, "پاسخ‌های ناقص",
                f"شما به {len(self.crt_answers)} سؤال از "
                f"{len(CRT_ITEMS)} پاسخ داده‌اید."
            )
            return
        self._done_crt = True
        print(f"✓ CRT تکمیل شد: {len(self.crt_answers)} پاسخ")
        self._update_final_button()

        # ✅ باز کردن دیالوگ ToH
        from core.app_config import is_assessment_tool_enabled
        if is_assessment_tool_enabled("tower_of_hanoi"):
            from widgets.tower_of_hanoi_widget import (
                TowerOfHanoiDialog,
            )
            dlg = TowerOfHanoiDialog(
                self.data_logger, parent=self
            )

            def _after_toh(metrics, moves):
                self._done_toh = True
                self._update_final_button()
                # بعد از بستن دیالوگ، به تب بعدی
                QTimer.singleShot(
                    100,
                    lambda: self.tabs.setCurrentIndex(
                        self._next_tab_after(1)  # بعد از CRT
                    )
                )

            dlg.finished_with_result.connect(_after_toh)
            dlg.exec()
            return

        # حالت بدون ToH
        self.tabs.setCurrentIndex(self._next_tab_after(1))

    # ================================================================
    # تب ۳: SD3
    # ================================================================
    def _build_sd3_tab(self):
        tab = QWidget()
        tab.setStyleSheet("background-color: #0B1D3A;")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)

        desc = QLabel(
            "لطفاً مشخص کنید چقدر با هر یک از جملات زیر موافقید. "
            "پاسخ صادقانه شما بسیار مهم است."
        )
        desc.setFont(QFont(FONT_FAMILY, 11))
        desc.setStyleSheet("color: #CCCCCC;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        self.sd3_progress_label = QLabel(
            "0 از 27 گویه پاسخ داده شده"
        )
        self.sd3_progress_label.setFont(QFont(FONT_FAMILY, 11))
        self.sd3_progress_label.setStyleSheet("color: #FF8F00;")
        self.sd3_progress_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        layout.addWidget(self.sd3_progress_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(
            "QScrollArea { background-color: #0B1D3A; border: none; }"
        )
        content = QWidget()
        content.setStyleSheet("background-color: #0B1D3A;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(8, 8, 8, 8)
        content_layout.setSpacing(8)

        for item in SD3_ITEMS:
            content_layout.addWidget(self._build_sd3_row(item))

        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll, stretch=1)

        sd3_done = QPushButton(
            "تکمیل SD3 و رفتن به بخش بعدی"
        )
        sd3_done.setFont(QFont(FONT_FAMILY, 12, QFont.Weight.Bold))
        sd3_done.setMinimumHeight(44)
        sd3_done.setCursor(Qt.CursorShape.PointingHandCursor)
        sd3_done.setStyleSheet("""
            QPushButton {
                background-color: #2B4A6F;
                color: #FFFFFF;
                border: 2px solid #4CAF50;
                border-radius: 8px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #4CAF50;
                color: #0B1D3A;
            }
        """)
        sd3_done.clicked.connect(self._on_sd3_done)
        layout.addWidget(sd3_done)

        self.tabs.addTab(tab, "۳. مثلث تاریک")

    def _build_sd3_row(self, item: dict) -> QFrame:
        row = QFrame()
        row.setStyleSheet("""
            QFrame {
                background-color: rgba(26, 42, 74, 0.4);
                border: 1px solid #2B4A6F;
                border-radius: 8px;
            }
        """)
        vbox = QVBoxLayout(row)
        vbox.setContentsMargins(12, 10, 12, 10)
        vbox.setSpacing(8)

        # ✅ RLM قبل از شماره — جلوگیری از چپ‌چین شدن bidi
        text_lbl = QLabel(f"\u200F{item['id']}. {item['text']}")
        text_lbl.setFont(QFont(FONT_FAMILY, 12))
        text_lbl.setStyleSheet("color: #FFFFFF; border: none;")
        text_lbl.setWordWrap(True)
        text_lbl.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        text_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        vbox.addWidget(text_lbl)

        radio_row = QHBoxLayout()
        radio_row.setSpacing(15)

        group = QButtonGroup(row)
        group.setExclusive(True)
        for value in [1, 2, 3, 4, 5]:
            rb = QRadioButton(str(value))
            rb.setFont(QFont(FONT_FAMILY, 13))
            rb.setStyleSheet("""
                QRadioButton {
                    color: #FFFFFF;
                    border: none;
                    padding: 4px 6px;
                }
                QRadioButton::indicator {
                    width: 16px; height: 16px;
                    border: 2px solid #4FC3F7;
                    border-radius: 8px;
                    background-color: #1A2A4A;
                }
                QRadioButton::indicator:checked {
                    background-color: #4FC3F7;
                }
            """)
            rb.setCursor(Qt.CursorShape.PointingHandCursor)
            rb.setToolTip(SD3_LIKERT_LABELS[value])
            group.addButton(rb, value)
            radio_row.addWidget(rb)

        radio_row.addStretch()

        group.buttonClicked.connect(
            lambda _b, iid=item["id"], g=group:
                self._on_sd3_answer(iid, g)
        )
        self.sd3_groups[item["id"]] = group
        vbox.addLayout(radio_row)
        return row

    def _on_sd3_answer(self, item_id, group):
        checked = group.checkedId()
        if checked > 0:
            self.sd3_answers[item_id] = checked
        self._update_sd3_progress()

    def _update_sd3_progress(self):
        if self.sd3_progress_label is not None:
            n = len(self.sd3_answers)
            self.sd3_progress_label.setText(
                f"{n} از {len(SD3_ITEMS)} گویه پاسخ داده شده"
            )

    def _on_sd3_done(self):
        if len(self.sd3_answers) < len(SD3_ITEMS):
            QMessageBox.warning(
                self, "پاسخ‌های ناقص",
                f"شما به {len(self.sd3_answers)} گویه از "
                f"{len(SD3_ITEMS)} پاسخ داده‌اید."
            )
            return
        self._done_sd3 = True
        print(f"✓ SD3 تکمیل شد: {len(self.sd3_answers)} پاسخ")
        self._update_final_button()
        self.tabs.setCurrentIndex(3)

    # ================================================================
    # تب ۴: مطلوبیت اجتماعی
    # ================================================================
    def _build_sd_tab(self):
        tab = QWidget()
        tab.setStyleSheet("background-color: #0B1D3A;")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)

        desc = QLabel(
            "با پاسخ گفتن به هر یک از ماده‌های زیر، درباره‌ی "
            "شخصیتتان پی ببرید. هر جمله را بخوانید و تعیین کنید "
            "که آیا در مورد شما درست است یا غلط."
        )
        desc.setFont(QFont(FONT_FAMILY, 11))
        desc.setStyleSheet("color: #CCCCCC;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        self.sd_progress_label = QLabel(
            "0 از 9 گویه پاسخ داده شده"
        )
        self.sd_progress_label.setFont(QFont(FONT_FAMILY, 11))
        self.sd_progress_label.setStyleSheet("color: #FF8F00;")
        self.sd_progress_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        layout.addWidget(self.sd_progress_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(
            "QScrollArea { background-color: #0B1D3A; border: none; }"
        )
        content = QWidget()
        content.setStyleSheet("background-color: #0B1D3A;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(8, 8, 8, 8)
        content_layout.setSpacing(8)

        for item in SD_ITEMS:
            content_layout.addWidget(self._build_sd_row(item))

        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll, stretch=1)

        # ✅ دکمه‌ی تکمیل SD (قبلاً نبود)
        sd_done = QPushButton(
            "تکمیل مطلوبیت اجتماعی و رفتن به بخش بعدی"
        )
        sd_done.setFont(QFont(FONT_FAMILY, 12, QFont.Weight.Bold))
        sd_done.setMinimumHeight(44)
        sd_done.setCursor(Qt.CursorShape.PointingHandCursor)
        sd_done.setStyleSheet("""
            QPushButton {
                background-color: #2B4A6F;
                color: #FFFFFF;
                border: 2px solid #4CAF50;
                border-radius: 8px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #4CAF50;
                color: #0B1D3A;
            }
        """)
        sd_done.clicked.connect(self._on_sd_done)
        layout.addWidget(sd_done)

        self.tabs.addTab(tab, "۴. مطلوبیت اجتماعی")

    def _build_sd_row(self, item: dict) -> QFrame:
        row = QFrame()
        row.setStyleSheet("""
            QFrame {
                background-color: rgba(26, 42, 74, 0.4);
                border: 1px solid #2B4A6F;
                border-radius: 8px;
            }
        """)
        vbox = QVBoxLayout(row)
        vbox.setContentsMargins(12, 10, 12, 10)
        vbox.setSpacing(8)

        # ✅ RLM قبل از شماره — جلوگیری از چپ‌چین شدن bidi
        text_lbl = QLabel(f"\u200F{item['id']}. {item['text']}")
        text_lbl.setFont(QFont(FONT_FAMILY, 12))
        text_lbl.setStyleSheet("color: #FFFFFF; border: none;")
        text_lbl.setWordWrap(True)
        text_lbl.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        text_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        vbox.addWidget(text_lbl)

        # دو رادیو باتن: درست / غلط
        radio_row = QHBoxLayout()
        radio_row.setSpacing(30)

        group = QButtonGroup(row)
        group.setExclusive(True)
        rb_true = QRadioButton("درست")
        rb_false = QRadioButton("غلط")
        for rb, val in [(rb_true, True), (rb_false, False)]:
            rb.setFont(QFont(FONT_FAMILY, 13))
            rb.setStyleSheet("""
                QRadioButton {
                    color: #FFFFFF;
                    border: none;
                    padding: 4px 12px;
                }
                QRadioButton::indicator {
                    width: 16px; height: 16px;
                    border: 2px solid #4FC3F7;
                    border-radius: 8px;
                    background-color: #1A2A4A;
                }
                QRadioButton::indicator:checked {
                    background-color: #4FC3F7;
                }
            """)
            rb.setCursor(Qt.CursorShape.PointingHandCursor)
            group.addButton(rb)
            rb.setProperty("answer_val", val)
            radio_row.addWidget(rb)

        radio_row.addStretch()

        group.buttonClicked.connect(
            lambda _b, iid=item["id"], g=group:
                self._on_sd_answer(iid, g)
        )
        self.sd_groups[item["id"]] = group
        vbox.addLayout(radio_row)
        return row

    def _on_sd_answer(self, item_id, group):
        btn = group.checkedButton()
        if btn is not None:
            val = btn.property("answer_val")
            self.sd_answers[item_id] = bool(val)
        self._update_sd_progress()

    def _on_sd_done(self):
        if len(self.sd_answers) < len(SD_ITEMS):
            from core.rtl_helper import rtl_message_box
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("پاسخ‌های ناقص")
            msg.setText(
                f"شما به {len(self.sd_answers)} گویه از "
                f"{len(SD_ITEMS)} پاسخ داده‌اید."
            )
            rtl_message_box(msg)
            msg.exec()
            return
        self._done_sd = True
        print(f"✓ SD تکمیل شد: {len(self.sd_answers)} پاسخ")
        self._update_final_button()
        # رفتن به تب بعدی (بازخورد)
        self.tabs.setCurrentIndex(4)

    # ================================================================
    # تب ۵: پرسشنامه‌ی پس‌نگر
    # ================================================================
    def _build_feedback_tab(self):
        tab = QWidget()
        tab.setStyleSheet("background-color: #0B1D3A;")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)

        desc = QLabel(
            "این بخش، بازخورد شما را درباره‌ی تجربه‌ی بازی "
            "جمع‌آوری می‌کند. پاسخ‌های شما به بهبود نسخه‌های "
            "بعدی کمک می‌کند. هیچ پاسخ درست یا غلطی وجود ندارد "
            "— لطفاً صادقانه پاسخ دهید."
        )
        desc.setFont(QFont(FONT_FAMILY, 11))
        desc.setStyleSheet("color: #CCCCCC;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # راهنمای مقیاس
        legend = QFrame()
        legend.setStyleSheet("""
            QFrame {
                background-color: rgba(26, 42, 74, 0.7);
                border: 1px solid #4FC3F7;
                border-radius: 8px;
            }
        """)
        legend_layout = QHBoxLayout(legend)
        legend_layout.setContentsMargins(15, 8, 15, 8)
        for value in [1, 2, 3, 4, 5]:
            lbl = QLabel(
                f"{value} = {FEEDBACK_LIKERT_LABELS[value]}"
            )
            lbl.setFont(QFont(FONT_FAMILY, 10))
            lbl.setStyleSheet("color: #FFFFFF; border: none;")
            legend_layout.addWidget(lbl)
        legend_layout.addStretch()
        layout.addWidget(legend)

        self.feedback_progress_label = QLabel(
            "0 از 25 گویه پاسخ داده شده"
        )
        self.feedback_progress_label.setFont(QFont(FONT_FAMILY, 11))
        self.feedback_progress_label.setStyleSheet("color: #FF8F00;")
        self.feedback_progress_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        layout.addWidget(self.feedback_progress_label)

        # اسکرول
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(
            "QScrollArea { background-color: #0B1D3A; border: none; }"
        )
        content = QWidget()
        content.setStyleSheet("background-color: #0B1D3A;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(8, 8, 8, 8)
        content_layout.setSpacing(10)

        # --- بخش ۱: 25 گویه‌ی بسته ---
        for item in FEEDBACK_ITEMS:
            content_layout.addWidget(self._build_feedback_row(item))

        # --- بخش ۲: سؤالات باز ---
        open_header = QLabel("سؤالات باز")
        open_header.setFont(
            QFont(FONT_FAMILY, 14, QFont.Weight.Bold)
        )
        open_header.setStyleSheet(
            "color: #4FC3F7; padding: 12px; border: none;"
        )
        open_header.setAlignment(Qt.AlignmentFlag.AlignRight)
        content_layout.addWidget(open_header)

        for q in FEEDBACK_OPEN_QUESTIONS:
            content_layout.addWidget(
                self._build_open_question(q)
            )

        # --- بخش ۳: دموگرافیک تکمیلی ---
        demo_header = QLabel("اطلاعات تکمیلی")
        demo_header.setFont(
            QFont(FONT_FAMILY, 14, QFont.Weight.Bold)
        )
        demo_header.setStyleSheet(
            "color: #4FC3F7; padding: 12px; border: none;"
        )
        demo_header.setAlignment(Qt.AlignmentFlag.AlignRight)
        content_layout.addWidget(demo_header)

        for item in FEEDBACK_DEMOGRAPHIC_ITEMS:
            content_layout.addWidget(
                self._build_demo_question(item)
            )

        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll, stretch=1)

        # دکمه‌ی تکمیل
        feedback_done = QPushButton(
            "تکمیل بازخورد و پایان مأموریت"
        )
        feedback_done.setFont(
            QFont(FONT_FAMILY, 13, QFont.Weight.Bold)
        )
        feedback_done.setMinimumHeight(48)
        feedback_done.setCursor(Qt.CursorShape.PointingHandCursor)
        feedback_done.setStyleSheet("""
            QPushButton {
                background-color: #2B4A6F;
                color: #FFFFFF;
                border: 2px solid #4CAF50;
                border-radius: 8px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #4CAF50;
                color: #0B1D3A;
            }
        """)
        feedback_done.clicked.connect(self._on_feedback_done)
        layout.addWidget(feedback_done)

        self.tabs.addTab(tab, "۵. بازخورد پس از بازی")

    def _build_feedback_row(self, item: dict) -> QFrame:
        row = QFrame()
        row.setStyleSheet("""
            QFrame {
                background-color: rgba(26, 42, 74, 0.4);
                border: 1px solid #2B4A6F;
                border-radius: 8px;
            }
        """)
        vbox = QVBoxLayout(row)
        vbox.setContentsMargins(12, 10, 12, 10)
        vbox.setSpacing(8)

        # ✅ RLM قبل از شماره — جلوگیری از چپ‌چین شدن bidi
        text_lbl = QLabel(f"\u200F{item['id']}. {item['text']}")
        text_lbl.setFont(QFont(FONT_FAMILY, 12))
        text_lbl.setStyleSheet("color: #FFFFFF; border: none;")
        text_lbl.setWordWrap(True)
        text_lbl.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        text_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        vbox.addWidget(text_lbl)

        radio_row = QHBoxLayout()
        radio_row.setSpacing(15)

        group = QButtonGroup(row)
        group.setExclusive(True)
        for value in [1, 2, 3, 4, 5]:
            rb = QRadioButton(str(value))
            rb.setFont(QFont(FONT_FAMILY, 13))
            rb.setStyleSheet("""
                QRadioButton {
                    color: #FFFFFF;
                    border: none;
                    padding: 4px 6px;
                }
                QRadioButton::indicator {
                    width: 16px; height: 16px;
                    border: 2px solid #4FC3F7;
                    border-radius: 8px;
                    background-color: #1A2A4A;
                }
                QRadioButton::indicator:checked {
                    background-color: #4FC3F7;
                }
            """)
            rb.setCursor(Qt.CursorShape.PointingHandCursor)
            rb.setToolTip(FEEDBACK_LIKERT_LABELS[value])
            group.addButton(rb, value)
            radio_row.addWidget(rb)

        radio_row.addStretch()

        group.buttonClicked.connect(
            lambda _b, iid=item["id"], g=group:
                self._on_feedback_answer(iid, g)
        )
        self.feedback_groups[item["id"]] = group
        vbox.addLayout(radio_row)
        return row

    def _build_open_question(self, q: dict) -> QFrame:
        from PyQt6.QtWidgets import QTextEdit
        row = QFrame()
        row.setStyleSheet("""
            QFrame {
                background-color: rgba(26, 42, 74, 0.4);
                border: 1px solid #2B4A6F;
                border-radius: 8px;
            }
        """)
        vbox = QVBoxLayout(row)
        vbox.setContentsMargins(12, 10, 12, 10)
        vbox.setSpacing(8)

        text_lbl = QLabel(q["text"])
        text_lbl.setFont(QFont(FONT_FAMILY, 12))
        text_lbl.setStyleSheet("color: #FFFFFF; border: none;")
        text_lbl.setWordWrap(True)
        text_lbl.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        text_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        vbox.addWidget(text_lbl)

        text_edit = QTextEdit()
        text_edit.setFont(QFont(FONT_FAMILY, 12))
        text_edit.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        text_edit.setMinimumHeight(80)
        text_edit.setMaximumHeight(120)
        text_edit.setPlaceholderText("پاسخ خود را این‌جا بنویسید...")
        text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #1A2A4A;
                color: #FFFFFF;
                border: 2px solid #4FC3F7;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        text_edit.textChanged.connect(
            lambda qid=q["id"], te=text_edit:
                self._on_feedback_open(qid, te)
        )
        self.feedback_open_inputs[q["id"]] = text_edit
        vbox.addWidget(text_edit)
        return row

    def _build_demo_question(self, item: dict) -> QFrame:
        row = QFrame()
        row.setStyleSheet("""
            QFrame {
                background-color: rgba(26, 42, 74, 0.4);
                border: 1px solid #2B4A6F;
                border-radius: 8px;
            }
        """)
        vbox = QVBoxLayout(row)
        vbox.setContentsMargins(12, 10, 12, 10)
        vbox.setSpacing(8)

        text_lbl = QLabel(item["text"])
        text_lbl.setFont(QFont(FONT_FAMILY, 12))
        text_lbl.setStyleSheet("color: #FFFFFF; border: none;")
        text_lbl.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        text_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        vbox.addWidget(text_lbl)

        radio_row = QHBoxLayout()
        radio_row.setSpacing(15)

        group = QButtonGroup(row)
        group.setExclusive(True)
        for idx, opt in enumerate(item["options"]):
            rb = QRadioButton(opt)
            rb.setFont(QFont(FONT_FAMILY, 11))
            rb.setStyleSheet("""
                QRadioButton {
                    color: #FFFFFF;
                    border: none;
                    padding: 4px 8px;
                }
                QRadioButton::indicator {
                    width: 14px; height: 14px;
                    border: 2px solid #4FC3F7;
                    border-radius: 7px;
                    background-color: #1A2A4A;
                }
                QRadioButton::indicator:checked {
                    background-color: #4FC3F7;
                }
            """)
            rb.setCursor(Qt.CursorShape.PointingHandCursor)
            group.addButton(rb, idx)
            rb.setProperty("option_text", opt)
            radio_row.addWidget(rb)

        radio_row.addStretch()

        group.buttonClicked.connect(
            lambda _b, iid=item["id"], g=group:
                self._on_feedback_demo(iid, g)
        )
        self.feedback_demo_groups[item["id"]] = group
        vbox.addLayout(radio_row)
        return row

    def _on_feedback_answer(self, item_id, group):
        checked = group.checkedId()
        if checked > 0:
            self.feedback_answers[item_id] = checked
        self._update_feedback_progress()

    def _update_feedback_progress(self):
        if self.feedback_progress_label is not None:
            n = len(self.feedback_answers)
            self.feedback_progress_label.setText(
                f"{n} از {len(FEEDBACK_ITEMS)} گویه پاسخ داده شده"
            )

    def _on_feedback_open(self, qid, text_edit):
        text = text_edit.toPlainText().strip()
        if text:
            self.feedback_open_answers[qid] = text
        else:
            self.feedback_open_answers.pop(qid, None)

    def _on_feedback_demo(self, item_id, group):
        btn = group.checkedButton()
        if btn is not None:
            opt_text = btn.property("option_text")
            self.feedback_demo_answers[item_id] = opt_text

    def _on_feedback_done(self):
        # بررسی: همه‌ی 25 گویه‌ی بسته پاسخ داده شده؟
        if len(self.feedback_answers) < len(FEEDBACK_ITEMS):
            QMessageBox.warning(
                self, "پاسخ‌های ناقص",
                f"شما به {len(self.feedback_answers)} گویه از "
                f"{len(FEEDBACK_ITEMS)} پاسخ داده‌اید."
            )
            return

        # سؤالات باز و دموگرافیک اختیاری هستند — اخطار نمی‌دهیم
        open_count = len(self.feedback_open_answers)
        demo_count = len(self.feedback_demo_answers)

        # اگر سؤال باز مهمی خالی است، یک تأیید
        if open_count < 3:
            reply = QMessageBox.question(
                self, "سؤالات باز",
                f"شما فقط به {open_count} سؤال از ۵ سؤال باز "
                f"پاسخ داده‌اید. این سؤالات برای بهبود بازی "
                f"ارزشمند هستند.\n\n"
                f"آیا مطمئن هستید که می‌خواهید ادامه دهید؟",
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        self._done_feedback = True
        print(
            f"✓ پرسشنامه‌ی پس‌نگر تکمیل شد: "
            f"{len(self.feedback_answers)} گویه بسته + "
            f"{open_count} سؤال باز + "
            f"{demo_count} دموگرافیک"
        )
        self._update_final_button()

        # اگر همه‌ی بخش‌ها تکمیل شد، به کاربر اطلاع بده
        if self.final_submit_btn.isEnabled():
            QMessageBox.information(
                self, "همه‌ی بخش‌ها تکمیل شد",
                "همه‌ی پرسشنامه‌ها با موفقیت تکمیل شدند. "
                "برای پایان مأموریت، روی دکمه‌ی پایین صفحه "
                "کلیک کنید."
            )

    def _update_sd_progress(self):
        if self.sd_progress_label is not None:
            n = len(self.sd_answers)
            self.sd_progress_label.setText(
                f"{n} از {len(SD_ITEMS)} گویه پاسخ داده شده"
            )

    # ================================================================
    # به‌روزرسانی دکمه‌ی نهایی
    # ================================================================
    def _update_final_button(self):
        from core.app_config import is_assessment_tool_enabled

        checks = []
        if is_assessment_tool_enabled("hexaco"):
            checks.append(self._done_hexaco)
        if is_assessment_tool_enabled("crt"):
            checks.append(self._done_crt)
        if is_assessment_tool_enabled("tower_of_hanoi"):
            checks.append(self._done_toh)  # ← جدید
        if is_assessment_tool_enabled("sd3"):
            checks.append(self._done_sd3)
        if is_assessment_tool_enabled("social_desirability"):
            checks.append(self._done_sd)
        if is_assessment_tool_enabled("postgame_feedback"):
            checks.append(self._done_feedback)

        total = len(checks)
        completed = sum(checks)
        all_done = (completed == total) if total > 0 else True

        self.final_submit_btn.setEnabled(all_done)
        if all_done:
            self.final_submit_btn.setText(
                "✓ همه‌ی بخش‌ها تکمیل شد — پایان مأموریت"
            )
        else:
            self.final_submit_btn.setText(
                f"برای پایان، همه‌ی بخش‌ها را تکمیل کنید "
                f"({completed} از {total})"
            )

    def _next_tab_after(self, current_tab_index: int) -> int:
        """
        پیدا کردن ایندکس تب بعدی که فعال است.
        تب‌ها: 0=HEXACO, 1=CRT, [2=ToH]، [3=SD3]، ...
        """
        from core.app_config import is_assessment_tool_enabled

        # ساخت لیست تب‌های فعال به ترتیب
        active_tabs = []
        if is_assessment_tool_enabled("hexaco"):
            active_tabs.append("hexaco")
        if is_assessment_tool_enabled("crt"):
            active_tabs.append("crt")
        if is_assessment_tool_enabled("tower_of_hanoi"):
            active_tabs.append("tower_of_hanoi")
        if is_assessment_tool_enabled("sd3"):
            active_tabs.append("sd3")
        if is_assessment_tool_enabled("social_desirability"):
            active_tabs.append("sd")
        if is_assessment_tool_enabled("postgame_feedback"):
            active_tabs.append("feedback")

        # پیدا کردن تب جاری و برگرداندن ایندکس بعدی
        # current_tab_index همان ایندکس تب فعلی است
        # اما ایندکس ممکن است با active_tabs هم‌ترتیب نباشد
        # (چون ToH ممکن است غیرفعال باشد)
        # پس از current_tab_index استفاده می‌کنیم
        for i, name in enumerate(active_tabs):
            if name == "crt" and current_tab_index == 1:
                if i + 1 < len(active_tabs):
                    # ایندکس واقعی: با احتساب غیرفعال‌ها
                    # همه تب‌ها به ترتیب اضافه شده‌اند
                    return 2  # بعد از CRT در TabWidget
        return 2  # fallback


    # ================================================================
    # ثبت نهایی
    # ================================================================
    def _on_final_submit(self):
        # محاسبه‌ی نمره‌ی هر بخش
        hexaco_scores = compute_factor_scores(self.hexaco_answers)
        crt_result = score_crt(self.crt_answers)
        sd3_scores = compute_sd3_scores(self.sd3_answers)
        sd_result = compute_sd_score(self.sd_answers)
        feedback_result = compute_feedback_scores(
            self.feedback_answers
        )

        print("=" * 60)
        print("✓ نتایج همه‌ی پرسشنامه‌ها:")
        print(f"  HEXACO: {hexaco_scores}")
        print(f"  CRT: {crt_result}")
        print(f"  SD3: {sd3_scores}")
        print(f"  Social Desirability: {sd_result}")
        print(f"  Feedback Subscales: "
              f"{feedback_result['subscale_scores']}")
        print(f"  Feedback Overall: "
              f"{feedback_result['overall_score']}")
        print("=" * 60)

        # ----------------------------------------------------------
        # ذخیره‌ی پرسشنامه‌های تکمیلی
        # نام کلیدها مطابق با امضای DataLogger.save_extended_questionnaires
        # ----------------------------------------------------------
        payload = {
            "hexaco_scores": {
                "scores": hexaco_scores,
                "raw_answers": self.hexaco_answers,
            },
            "crt_data": crt_result,
            "sd3_scores": {
                "scores": sd3_scores,
                "raw_answers": self.sd3_answers,
            },
            "social_desirability": {
                "score": sd_result["score"],
                "raw_answers": self.sd_answers,
            },
        }
        try:
            self.data_logger.save_extended_questionnaires(payload)
        except AttributeError:
            # Fallback: اگر متد جدید موجود نبود
            self.data_logger.save_hexaco_scores(payload["hexaco_scores"])
        except Exception as e:
            print(f"⚠️ خطا در ذخیره‌ی پرسشنامه‌های تکمیلی: {e}")

        # ----------------------------------------------------------
        # ذخیره‌ی بازخورد پس‌نگر
        # ----------------------------------------------------------
        feedback_payload = {
            "close_answers": self.feedback_answers,
            "open_answers": self.feedback_open_answers,
            "demographic_extra": self.feedback_demo_answers,
            "subscale_scores": feedback_result["subscale_scores"],
            "overall_score": feedback_result["overall_score"],
        }
        try:
            self.data_logger.save_postgame_feedback(feedback_payload)
        except AttributeError:
            print(
                "⚠️ متد save_postgame_feedback در DataLogger "
                "یافت نشد"
            )
        except Exception as e:
            print(f"⚠️ خطا در ذخیره‌ی پس‌نگر: {e}")

        # ----------------------------------------------------------
        # ثبت رویداد (فقط یک بار)
        # ----------------------------------------------------------
        self.data_logger.log_event(
            scene_id="hexaco",
            scenario_id="all_questionnaires_complete",
            event_type="form_submitted",
            metadata={
                "hexaco_count": len(self.hexaco_answers),
                "crt_score": crt_result["score"],
                "sd3_scores": sd3_scores,
                "sd_score": sd_result["score"],
                "feedback_overall":
                    feedback_result["overall_score"],
            },
        )

        # پایان روایی — فقط یک بار
        self._go_to_epilogue()

    def _go_to_epilogue(self):
        """پایان روایی — با استفاده از core.epilogue_helper"""
        from core.app_config import is_section_enabled

        if not is_section_enabled("epilogue"):
            self.change_scene("results")
            return

        from core.epilogue_helper import compute_epilogue

        epilogue = compute_epilogue(self.data_logger)

        print("=" * 60)
        print(f"✓ پایان روایی: {epilogue['code']} "
              f"({epilogue['subtitle']})")
        print(f"  روابط: {epilogue['relationships']} "
              f"(مجموع: {epilogue['total']})")
        print("=" * 60)

        self.change_scene(
            "interlude",
            next_scene="results",
            title="چهل و هشت ساعت بعد",
            subtitle=epilogue["subtitle"],
            body_text=(
                "چهل و هشت ساعت بعد. ایستگاه از دید "
                "ناپدید می‌شود."
            ),
            dialogues=epilogue["dialogues"],
            video_path=epilogue["video_path"],
        )

    # ================================================================
    def on_enter(self, **kwargs):
        print("✓ ورود به صحنه‌ی پرسشنامه‌های پایانی")
        self.data_logger.log_event(
            scene_id="hexaco",
            scenario_id="questionnaires_start",
            event_type="scene_enter",
            metadata={},
        )
        if hasattr(self, "hud") and self.hud is not None:
            self.hud.set_progress(100)