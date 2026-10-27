"""
صحنه‌ی ارزیابی متخصصان (SME Review)
=====================================
- بازیکن (متخصص) اطلاعات خود را وارد می‌کند
- 28 سناریو با خلاصه و تعریف شایستگی نمایش داده می‌شود
- هر سناریو در 5 بُعد ارزیابی می‌شود
- نتایج در فایل JSON ذخیره می‌شود
"""
import os
import json
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QPushButton, QLineEdit, QRadioButton,
    QButtonGroup, QTextEdit, QMessageBox, QComboBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from scenes.base_scene import BaseScene
from widgets.hud_widget import HUDWidget
from data.scenario_metadata import (
    SCENARIOS_METADATA,
    COMPETENCY_DEFINITIONS,
    get_full_competency_label,
)
from config import DATA_DIR

FONT_FAMILY = "Vazirmatn"

# مسیر ذخیره‌ی نتایج
OUTPUT_DIR = os.path.join(
    os.path.dirname(DATA_DIR), "analysis_output"
)


class SMEReviewScene(BaseScene):
    """فرم ارزیابی متخصصان — SME Review"""

    def __init__(self, game_manager):
        super().__init__(game_manager)

        # ---- داده‌ها ----
        self.expert_info = {
            "name": "",
            "degree": "",
            "field": "",
            "experience_years": "",
        }
        # {scenario_id: {
        #    "clarity": 1-5,
        #    "realism": 1-5,
        #    "cultural_fit": 1-5,
        #    "competency_match": 1-5,
        #    "essentiality": True/False,
        #    "comment": ""
        # }}
        self.evaluations: dict = {}

        self.info_inputs: dict = {}

        self._setup_ui()

        from core.rtl_helper import apply_rtl_fixes
        apply_rtl_fixes(self)

        print("✓ SMEReviewScene راه‌اندازی شد")

    # ================================================================
    def _setup_ui(self):
        main_layout = self.main_layout
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.hud = HUDWidget()
        self.hud.set_mission("حالت ارزیابی متخصصان")
        self.hud.set_phase("بازبینی سناریوها")
        self.hud.set_objective("ارزیابی روایی محتوایی")
        main_layout.addWidget(self.hud)

        # اسکرول
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(
            "QScrollArea { background-color: #0B1D3A; "
            "border: none; }"
        )
        content = QWidget()
        content.setStyleSheet("background-color: #0B1D3A;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(40, 20, 40, 20)
        content_layout.setSpacing(14)

        # ---- عنوان ----
        title = QLabel("فرم ارزیابی متخصصان (SME Review)")
        tf = QFont(FONT_FAMILY, 22, QFont.Weight.Bold)
        title.setFont(tf)
        title.setStyleSheet("color: #4FC3F7;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(title)

        # ---- توضیح ----
        desc = QLabel(
            "این فرم برای ارزیابی روایی محتوایی ۲۸ سناریوی "
            "بازی Truthline طراحی شده است. لطفاً هر سناریو "
            "را با دقت بخوانید و بر اساس معیارهای زیر "
            "ارزیابی کنید. برآورد شما به بهبود ابزار کمک "
            "می‌کند."
        )
        desc.setFont(QFont(FONT_FAMILY, 11))
        desc.setStyleSheet("color: #CCCCCC;")
        desc.setWordWrap(True)
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(desc)

        content_layout.addSpacing(10)

        # ---- اطلاعات متخصص ----
        content_layout.addWidget(self._build_expert_info_frame())

        # ---- راهنمای نمره‌گذاری ----
        content_layout.addWidget(self._build_scale_guide())

        # ---- سناریوها ----
        scenarios_header = QLabel("ارزیابی سناریوها")
        sf = QFont(FONT_FAMILY, 16, QFont.Weight.Bold)
        scenarios_header.setFont(sf)
        scenarios_header.setStyleSheet(
            "color: #FF8F00; padding: 10px;"
        )
        scenarios_header.setAlignment(Qt.AlignmentFlag.AlignRight)
        content_layout.addWidget(scenarios_header)

        current_phase = None
        for scenario in SCENARIOS_METADATA:
            # هدر فاز
            if scenario["phase"] != current_phase:
                current_phase = scenario["phase"]
                phase_lbl = QLabel(
                    f"── فاز {scenario['phase']}: "
                    f"{scenario['phase_name']} ──"
                )
                phase_lbl.setFont(
                    QFont(FONT_FAMILY, 13, QFont.Weight.Bold)
                )
                phase_lbl.setStyleSheet(
                    "color: #4FC3F7; padding: 8px; "
                    "border: none;"
                )
                phase_lbl.setAlignment(
                    Qt.AlignmentFlag.AlignCenter
                )
                content_layout.addWidget(phase_lbl)

            content_layout.addWidget(
                self._build_scenario_form(scenario)
            )

        content_layout.addSpacing(20)

        # ---- دکمه‌ها ----
        buttons = QHBoxLayout()
        buttons.setSpacing(15)

        save_btn = QPushButton("ذخیره‌ی نتایج ارزیابی")
        save_btn.setFont(
            QFont(FONT_FAMILY, 13, QFont.Weight.Bold)
        )
        save_btn.setMinimumHeight(50)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setStyleSheet("""
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
        save_btn.clicked.connect(self._on_save)
        buttons.addWidget(save_btn, 2)

        back_btn = QPushButton("بازگشت به منو")
        back_btn.setFont(QFont(FONT_FAMILY, 13))
        back_btn.setMinimumHeight(50)
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #1A2A4A;
                color: #B0BEC5;
                border: 2px solid #546E7A;
                border-radius: 10px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #546E7A;
                color: #FFFFFF;
            }
        """)
        back_btn.clicked.connect(self._on_back)
        buttons.addWidget(back_btn, 1)

        content_layout.addLayout(buttons)
        content_layout.addStretch()

        scroll.setWidget(content)
        main_layout.addWidget(scroll, stretch=1)

    # ================================================================
    def _build_expert_info_frame(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: rgba(26, 42, 74, 0.7);
                border: 2px solid #4FC3F7;
                border-radius: 10px;
            }
        """)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)

        header = QLabel("اطلاعات متخصص")
        header.setFont(
            QFont(FONT_FAMILY, 14, QFont.Weight.Bold)
        )
        header.setStyleSheet("color: #4FC3F7; border: none;")
        layout.addWidget(header)

        def make_row(label_text: str, key: str, placeholder: str):
            row = QHBoxLayout()
            row.setSpacing(10)

            lbl = QLabel(label_text)
            lbl.setFont(QFont(FONT_FAMILY, 12))
            lbl.setStyleSheet("color: #FFFFFF; border: none;")
            lbl.setMinimumWidth(180)
            lbl.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            row.addWidget(lbl)

            line = QLineEdit()
            line.setFont(QFont(FONT_FAMILY, 12))
            line.setPlaceholderText(placeholder)
            line.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            # ✅ متن داخل خط‌ادیت راست‌چین شود
            line.setAlignment(
                Qt.AlignmentFlag.AlignRight
                | Qt.AlignmentFlag.AlignVCenter
            )
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
                lambda txt, k=key: self._on_info_change(k, txt)
            )
            self.info_inputs[key] = line
            row.addWidget(line, 1)
            return row

        layout.addLayout(
            make_row("نام (اختیاری):", "name",
                     "نام و نام خانوادگی")
        )
        layout.addLayout(
            make_row("مدرک تحصیلی:", "degree",
                     "کارشناسی / ارشد / دکتری / پسادکتری")
        )
        layout.addLayout(
            make_row("رشته‌ی تخصصی:", "field",
                     "روان‌شناسی صنعتی-سازمانی، روان‌سنجی، ...")
        )
        layout.addLayout(
            make_row("سابقه‌ی تدریس/پژوهش (سال):",
                     "experience_years", "مثال: 12")
        )

        return frame

    def _build_scale_guide(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 143, 0, 0.08);
                border: 1px dashed #FF8F00;
                border-radius: 8px;
            }
        """)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(6)

        header = QLabel("راهنمای ارزیابی")
        header.setFont(
            QFont(FONT_FAMILY, 12, QFont.Weight.Bold)
        )
        header.setStyleSheet(
            "color: #FF8F00; border: none;"
        )
        layout.addWidget(header)

        items = [
            "وضوح: آیا متن سناریو واضح و قابل فهم است؟",
            "واقع‌گرایی: آیا سناریو در محیط کار واقعی امکان‌پذیر است؟",
            "تناسب فرهنگی: آیا سناریو با بافت فرهنگی ایران سازگار است؟",
            "تطابق شایستگی: آیا سناریو واقعاً همان شایستگی را می‌سنجد؟",
            "ضرورت: آیا این سناریو برای سنجش شایستگی هدف ضروری است؟",
        ]
        for item in items:
            lbl = QLabel(f"• {item}")
            lbl.setFont(QFont(FONT_FAMILY, 10))
            lbl.setStyleSheet(
                "color: #CCCCCC; border: none; "
                "padding-right: 10px;"
            )
            lbl.setWordWrap(True)
            layout.addWidget(lbl)

        return frame

    def _build_scenario_form(self, scenario: dict) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: rgba(26, 42, 74, 0.4);
                border: 1px solid #2B4A6F;
                border-radius: 10px;
            }
        """)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        # عنوان
        title = QLabel(
            f"▸ {scenario['id']} — {scenario['title']}"
        )
        tf = QFont(FONT_FAMILY, 13, QFont.Weight.Bold)
        title.setFont(tf)
        title.setStyleSheet("color: #4FC3F7; border: none;")
        title.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        title.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(title)

        # خلاصه
        summary = QLabel(scenario["summary"])
        summary.setFont(QFont(FONT_FAMILY, 11))
        # ⚠️ تست موقت — پس‌زمینه‌ی زرد برای دیدن کادر واقعی
        summary.setStyleSheet(
            "color: #000000; background-color: yellow; border: 2px solid red;"
        )
        summary.setWordWrap(True)
        summary.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        summary.setAlignment(
            Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignVCenter
        )
        layout.addWidget(summary)

        # شایستگی + تعریف
        comp_label = get_full_competency_label(scenario)
        comp_key = scenario["competency"]
        comp_info = COMPETENCY_DEFINITIONS.get(comp_key, {})
        short_def = comp_info.get("short_def", "")

        comp_frame = QFrame()
        comp_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(79, 195, 247, 0.08);
                border-left: 3px solid #4FC3F7;
                border-radius: 4px;
            }
        """)
        comp_layout = QVBoxLayout(comp_frame)
        comp_layout.setContentsMargins(12, 8, 12, 8)
        comp_layout.setSpacing(4)

        comp_lbl = QLabel(f"🎯 شایستگی: {comp_label}")
        comp_lbl.setFont(
            QFont(FONT_FAMILY, 11, QFont.Weight.Bold)
        )
        comp_lbl.setStyleSheet("color: #4FC3F7; border: none;")
        comp_lbl.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        comp_lbl.setAlignment(
            Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignVCenter
        )
        comp_layout.addWidget(comp_lbl)

        def_lbl = QLabel(f"تعریف: {short_def}")
        def_lbl.setFont(QFont(FONT_FAMILY, 10))
        def_lbl.setStyleSheet("color: #B0BEC5; border: none;")
        def_lbl.setWordWrap(True)
        def_lbl.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        def_lbl.setAlignment(
            Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignVCenter
        )
        comp_layout.addWidget(def_lbl)

        layout.addWidget(comp_frame)

        # ردیف‌های ارزیابی
        layout.addLayout(
            self._make_rating_row(
                "وضوح:", scenario["id"], "clarity"
            )
        )
        layout.addLayout(
            self._make_rating_row(
                "واقع‌گرایی:", scenario["id"], "realism"
            )
        )
        layout.addLayout(
            self._make_rating_row(
                "تناسب فرهنگی:", scenario["id"], "cultural_fit"
            )
        )
        layout.addLayout(
            self._make_rating_row(
                "تطابق شایستگی:", scenario["id"],
                "competency_match"
            )
        )
        layout.addLayout(
            self._make_essentiality_row(scenario["id"])
        )

        # پیشنهاد
        comment_lbl = QLabel("پیشنهاد/اصلاح (اختیاری):")
        comment_lbl.setFont(QFont(FONT_FAMILY, 10))
        comment_lbl.setStyleSheet(
            "color: #B0BEC5; border: none;"
        )
        comment_lbl.setLayoutDirection(
            Qt.LayoutDirection.RightToLeft
        )
        layout.addWidget(comment_lbl)

        comment_edit = QTextEdit()
        comment_edit.setFont(QFont(FONT_FAMILY, 10))
        comment_edit.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        # ✅ راست‌چین کردن متن و پلیس‌هولدر
        comment_edit.setAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignTop
        )
        comment_edit.setMaximumHeight(60)
        comment_edit.setPlaceholderText("در صورت نیاز بنویسید...")
        comment_edit.setStyleSheet("""
            QTextEdit {
                background-color: #1A2A4A;
                color: #FFFFFF;
                border: 1px solid #4FC3F7;
                border-radius: 4px;
                padding: 4px;
            }
        """)
        comment_edit.textChanged.connect(
            lambda sid=scenario["id"], te=comment_edit:
                self._on_comment_change(sid, te)
        )
        layout.addWidget(comment_edit)

        return frame

    def _make_rating_row(self, label_text: str,
                          scenario_id: str, key: str) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(8)

        lbl = QLabel(label_text)
        lbl.setFont(QFont(FONT_FAMILY, 11))
        lbl.setStyleSheet("color: #FFFFFF; border: none;")
        lbl.setMinimumWidth(160)
        lbl.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        row.addWidget(lbl)

        # ✅ parent = self (نه parent=row که یک layout است)
        group = QButtonGroup(self)
        group.setExclusive(True)
        for value in [1, 2, 3, 4, 5]:
            rb = QRadioButton(str(value))
            rb.setFont(QFont(FONT_FAMILY, 11))
            rb.setStyleSheet("""
                QRadioButton {
                    color: #FFFFFF;
                    border: none;
                    padding: 3px 6px;
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
            group.addButton(rb, value)
            row.addWidget(rb)

        row.addStretch()

        # ذخیره در evaluations
        def _on_clicked(_btn, sid=scenario_id, k=key, g=group):
            checked = g.checkedId()
            if checked > 0:
                if sid not in self.evaluations:
                    self.evaluations[sid] = {}
                self.evaluations[sid][k] = checked

        group.buttonClicked.connect(_on_clicked)
        return row

    def _make_essentiality_row(self,
                                scenario_id: str) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(8)

        lbl = QLabel("ضرورت:")
        lbl.setFont(QFont(FONT_FAMILY, 11))
        lbl.setStyleSheet("color: #FFFFFF; border: none;")
        lbl.setMinimumWidth(160)
        lbl.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        row.addWidget(lbl)

        # ✅ parent = self
        group = QButtonGroup(self)
        group.setExclusive(True)
        for label, value in [("بله", True), ("خیر", False)]:
            rb = QRadioButton(label)
            rb.setFont(QFont(FONT_FAMILY, 11))
            rb.setStyleSheet("""
                QRadioButton {
                    color: #FFFFFF;
                    border: none;
                    padding: 3px 8px;
                }
                QRadioButton::indicator {
                    width: 14px; height: 14px;
                    border: 2px solid #4CAF50;
                    border-radius: 7px;
                    background-color: #1A2A4A;
                }
                QRadioButton::indicator:checked {
                    background-color: #4CAF50;
                }
            """)
            rb.setCursor(Qt.CursorShape.PointingHandCursor)
            group.addButton(rb)
            rb.setProperty("answer_val", value)
            row.addWidget(rb)

        row.addStretch()

        def _on_clicked(_btn, sid=scenario_id, g=group):
            btn = g.checkedButton()
            if btn is not None:
                val = btn.property("answer_val")
                if sid not in self.evaluations:
                    self.evaluations[sid] = {}
                self.evaluations[sid]["essentiality"] = bool(val)

        group.buttonClicked.connect(_on_clicked)
        return row

    # ================================================================
    def _on_info_change(self, key: str, text: str):
        self.expert_info[key] = text.strip()

    def _on_comment_change(self, scenario_id: str,
                            text_edit: QTextEdit):
        text = text_edit.toPlainText().strip()
        if scenario_id not in self.evaluations:
            self.evaluations[scenario_id] = {}
        self.evaluations[scenario_id]["comment"] = text

    # ================================================================
    def _on_save(self):
        # بررسی: همه‌ی سناریوها ارزیابی شده‌اند؟
        missing = []
        for scenario in SCENARIOS_METADATA:
            sid = scenario["id"]
            ev = self.evaluations.get(sid, {})
            required = [
                "clarity", "realism", "cultural_fit",
                "competency_match", "essentiality",
            ]
            for key in required:
                if key not in ev:
                    missing.append(f"{sid}.{key}")
                    break

        if missing:
            reply = QMessageBox.question(
                self,
                "ارزیابی ناقص",
                f"برخی سناریوها ارزیابی نشده‌اند "
                f"({len(missing)} مورد).\n\n"
                f"آیا می‌خواهید نتایج ناقص را ذخیره کنید؟",
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        # ذخیره
        try:
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            name_safe = "".join(
                c for c in self.expert_info.get("name", "")
                if c.isalnum() or c in "-_"
            ) or "anonymous"
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"sme_review_{name_safe}_{timestamp}.json"
            path = os.path.join(OUTPUT_DIR, filename)

            payload = {
                "expert_info": self.expert_info,
                "evaluations": self.evaluations,
                "saved_at": datetime.now().isoformat(),
                "total_scenarios": len(SCENARIOS_METADATA),
                "completed_scenarios": len(self.evaluations),
            }
            with open(path, "w", encoding="utf-8") as f:
                json.dump(payload, f,
                           ensure_ascii=False, indent=2)

            print(f"✓ SME review ذخیره شد: {path}")
            QMessageBox.information(
                self,
                "ذخیره‌ی موفق",
                f"نتایج شما در فایل زیر ذخیره شد:\n\n{path}",
            )
        except Exception as e:
            print(f"⚠️ خطا در ذخیره: {e}")
            QMessageBox.critical(
                self,
                "خطا",
                f"ذخیره‌سازی ناموفق بود:\n{e}",
            )

    def _on_back(self):
        self.change_scene("menu")

    # ================================================================
    def on_enter(self, **kwargs):
        print("✓ ورود به حالت ارزیابی متخصصان")
        self.data_logger.log_event(
            scene_id="sme_review",
            scenario_id="sme_review_start",
            event_type="scene_enter",
            metadata={},
        )