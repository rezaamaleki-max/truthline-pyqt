"""
صحنه جمع‌آوری اطلاعات دموگرافیک
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QComboBox, QSpinBox,
    QPushButton, QCheckBox, QFrame, QScrollArea, QMessageBox,
    QFormLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from scenes.base_scene import BaseScene
from widgets.hud_widget import HUDWidget

FONT_FAMILY = "Vazirmatn"


class DemographicScene(BaseScene):
    """صحنه فرم اطلاعات دموگرافیک"""
    
    def __init__(self, game_manager):
        super().__init__(game_manager)
        self.inputs = {}
        # ✅ تعریف صریح با type hint (رفع خطای Pylance)
        self.consent_checkbox: QCheckBox = QCheckBox()
        self._setup_ui()

        # ✅ رفع RTL ورودی‌ها و لیبل‌ها
        from core.rtl_helper import apply_rtl_fixes
        apply_rtl_fixes(self)

        print("✓ DemographicScene راه‌اندازی شد")
    
    def _create_combo(self, items: list) -> QComboBox:
        """ساخت ComboBox با استایل یکسان"""
        combo = QComboBox()
        combo.addItems(items)
        combo.setFont(QFont(FONT_FAMILY, 13))
        combo.setMinimumHeight(38)
        combo.setStyleSheet("""
            QComboBox {
                background-color: #1A2A4A;
                color: #FFFFFF;
                border: 2px solid #4FC3F7;
                border-radius: 6px;
                padding: 6px 12px;
            }
            QComboBox:hover {
                border: 2px solid #FFFFFF;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox QAbstractItemView {
                background-color: #1A2A4A;
                color: #FFFFFF;
                selection-background-color: #4FC3F7;
                selection-color: #0B1D3A;
                border: 2px solid #4FC3F7;
                padding: 4px;
            }
        """)
        combo.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        return combo
    
    def _setup_ui(self):
        main_layout = self.main_layout
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # HUD
        self.hud = HUDWidget()
        self.hud.set_mission("ایستگاه کاسپین")
        self.hud.set_phase("پیش از مأموریت")
        self.hud.set_objective("تکمیل اطلاعات اولیه")
        main_layout.addWidget(self.hud)
        
        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background-color: #0B1D3A; border: none; }")
        
        content = QWidget()
        content.setStyleSheet("background-color: #0B1D3A;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(100, 30, 100, 30)
        content_layout.setSpacing(20)
        
        # ========================================
        # عنوان
        # ========================================
        title = QLabel("اطلاعات دموگرافیک")
        title_font = QFont(FONT_FAMILY, 28)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setStyleSheet("color: #4FC3F7;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(title)
        
        desc = QLabel(
            "لطفاً اطلاعات زیر را با دقت تکمیل کنید. این اطلاعات محرمانه بوده "
            "و فقط برای تحلیل آماری پژوهش استفاده می‌شود."
        )
        desc.setFont(QFont(FONT_FAMILY, 12))
        desc.setStyleSheet("color: #CCCCCC;")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        content_layout.addWidget(desc)
        
        content_layout.addSpacing(20)
        
        # ========================================
        # فرم با QFormLayout
        # ========================================
        form_frame = QFrame()
        # ✅ اعمال RTL روی خود frame (نه روی QFormLayout)
        form_frame.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        form_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(26, 42, 74, 0.6);
                border: 1px solid #2B4A6F;
                border-radius: 10px;
            }
        """)
        
        form = QFormLayout(form_frame)
        form.setContentsMargins(30, 30, 30, 30)
        form.setSpacing(18)
        form.setLabelAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        form.setFormAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop
        )
        # ✅ راست‌چین کردن ستون فیلدها (به‌جای چپ‌چین پیش‌فرض)
        form.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow
        )
        # ✅ خط setLayoutDirection حذف شد (به frame منتقل شد)
        
        label_style = "color: #FFFFFF; padding-right: 10px;"
        
        def make_label(text):
            lbl = QLabel(text)
            lbl.setFont(QFont(FONT_FAMILY, 13))
            lbl.setStyleSheet(label_style)
            lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            return lbl
        
        # سن
        age_spin = QSpinBox()
        age_spin.setRange(15, 90)
        age_spin.setValue(25)
        age_spin.setFont(QFont(FONT_FAMILY, 13))
        age_spin.setMinimumHeight(38)
        age_spin.setStyleSheet("""
            QSpinBox {
                background-color: #1A2A4A;
                color: #FFFFFF;
                border: 2px solid #4FC3F7;
                border-radius: 6px;
                padding: 6px 12px;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                width: 20px;
            }
        """)
        age_spin.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        form.addRow(make_label("سن:"), age_spin)
        self.inputs["age"] = age_spin
        
        # جنسیت
        gender = self._create_combo(["زن", "مرد", "ترجیح می‌دهم نگویم"])
        form.addRow(make_label("جنسیت:"), gender)
        self.inputs["gender"] = gender
        
        # مقطع تحصیلی
        edu = self._create_combo([
            "دیپلم", "کاردانی", "کارشناسی", "کارشناسی ارشد", "دکتری", "پسادکتری"
        ])
        form.addRow(make_label("مقطع تحصیلی:"), edu)
        self.inputs["education"] = edu
        
        # رشته تحصیلی
        field = self._create_combo([
            "مهندسی",
            "علوم پایه (ریاضی/فیزیک/شیمی/زیست)",
            "علوم انسانی",
            "پزشکی و علوم وابسته",
            "هنر و معماری",
            "کشاورزی و منابع طبیعی",
            "سایر"
        ])
        form.addRow(make_label("رشته تحصیلی:"), field)
        self.inputs["field_of_study"] = field
        
        # سابقه کار
        work = self._create_combo([
            "بدون سابقه کار",
            "کمتر از ۱ سال",
            "۱ تا ۳ سال",
            "۳ تا ۵ سال",
            "۵ تا ۱۰ سال",
            "بیش از ۱۰ سال"
        ])
        form.addRow(make_label("سابقه کار:"), work)
        self.inputs["work_experience"] = work
        
        # سابقه بازی رایانه‌ای
        gaming = self._create_combo([
            "اصلاً بازی نمی‌کنم",
            "خیلی کم (چند بار در سال)",
            "کم (چند بار در ماه)",
            "متوسط (هفتگی)",
            "زیاد (روزانه کمتر از ۱ ساعت)",
            "خیلی زیاد (روزانه بیش از ۱ ساعت)"
        ])
        form.addRow(make_label("سابقه بازی‌های رایانه‌ای:"), gaming)
        self.inputs["gaming_experience"] = gaming
        
        # آشنایی با مفاهیم فضایی-مهندسی
        tech = self._create_combo([
            "اصلاً آشنایی ندارم",
            "خیلی کم",
            "کم",
            "متوسط",
            "زیاد",
            "خیلی زیاد"
        ])
        form.addRow(make_label("آشنایی با مفاهیم فضایی-مهندسی:"), tech)
        self.inputs["technical_familiarity"] = tech
        
        content_layout.addWidget(form_frame)
        
        # ========================================
        # رضایت‌نامه
        # ========================================
        # ✅ استفاده از همان ویجت تعریف‌شده در __init__ (نه ساخت مجدد)
        self.consent_checkbox.setText(
            "اینجانب با شرکت داوطلبانه در این پژوهش موافقم و می‌دانم که "
            "داده‌هایم به صورت محرمانه تحلیل خواهد شد."
        )
        self.consent_checkbox.setFont(QFont(FONT_FAMILY, 12))
        self.consent_checkbox.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.consent_checkbox.setStyleSheet("""
            QCheckBox {
                color: #FFFFFF;
                spacing: 10px;
                padding: 15px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #4FC3F7;
                border-radius: 4px;
                background-color: #1A2A4A;
            }
            QCheckBox::indicator:checked {
                background-color: #4FC3F7;
            }
        """)
        content_layout.addWidget(self.consent_checkbox)
        
        # ========================================
        # دکمه شروع
        # ========================================
        start_btn = QPushButton("شروع مأموریت")
        start_font = QFont(FONT_FAMILY, 18)
        start_font.setBold(True)
        start_btn.setFont(start_font)
        start_btn.setMinimumHeight(60)
        start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        start_btn.setStyleSheet("""
            QPushButton {
                background-color: #2B4A6F;
                color: #FFFFFF;
                border: 2px solid #4FC3F7;
                border-radius: 10px;
                padding: 15px;
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
        """)
        start_btn.clicked.connect(self._on_start_clicked)
        content_layout.addWidget(start_btn)
        
        content_layout.addStretch()
        
        scroll.setWidget(content)
        main_layout.addWidget(scroll, stretch=1)
    
    def on_enter(self, **kwargs):
        print("✓ ورود به صحنه دموگرافیک")
        self.data_logger.log_event(
            scene_id="demographic",
            scenario_id="demographic_start",
            event_type="scene_enter",
            metadata={}
        )
    
    def _on_start_clicked(self):
        # بررسی رضایت‌نامه
        if not self.consent_checkbox.isChecked():
            msg = QMessageBox()
            msg.setWindowTitle("توجه")
            msg.setText("برای ادامه، لطفاً تیک رضایت‌نامه را فعال کنید.")
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            msg.exec()
            return
        
        # جمع‌آوری داده‌ها
        data = {
            "age": self.inputs["age"].value(),
            "gender": self.inputs["gender"].currentText(),
            "education": self.inputs["education"].currentText(),
            "field_of_study": self.inputs["field_of_study"].currentText(),
            "work_experience": self.inputs["work_experience"].currentText(),
            "gaming_experience": self.inputs["gaming_experience"].currentText(),
            "technical_familiarity": self.inputs["technical_familiarity"].currentText(),
            "consent": True,
        }
        
        print(f"✓ داده‌های دموگرافیک ذخیره شد: {data}")
        
        # ذخیره در دیتابیس
        self.data_logger.save_demographic_data(data)
        
        # ثبت رویداد
        self.data_logger.log_event(
            scene_id="demographic",
            scenario_id="demographic_complete",
            event_type="form_submitted",
            metadata=data
        )
        
        # انتقال به مقدمه
        self.change_scene("intro")