"""
صحنه تنظیمات — کنترل فعال/غیرفعال بودن بخش‌های داستانی
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QFrame, QScrollArea, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from scenes.base_scene import BaseScene
from core.app_config import (
    load_config, save_config, apply_preset,
    PRESET_SHORT, PRESET_FULL, PRESET_THEATER,
    get_audio_settings, set_audio_settings,
    is_auto_resume_enabled, set_auto_resume,
    get_inner_dialogue_mode, set_inner_dialogue_mode,
    get_accessibility_settings, set_accessibility_settings,
    # ✅ جدید
    is_assessment_tool_enabled,
    set_assessment_tool_enabled,
    ASSESSMENT_TOOL_NAMES,
)

FONT_FAMILY = "Vazirmatn"


class SettingsScene(BaseScene):
    """صحنه تنظیمات — کنترل بخش‌های اختیاری و فازها"""

    def __init__(self, game_manager):
        super().__init__(game_manager)

        # ✅ نگه‌داری checkbox ها برای خواندن مقدار
        self.section_boxes: dict = {}
        self.phase_boxes: dict = {}
        self.tool_boxes: dict = {}      # ✅ جدید
        self._mode_label: QLabel = QLabel()

        self._setup_ui()
        self._load_from_config()
        print("✓ SettingsScene راه‌اندازی شد")

    # ================================================================
    def _setup_ui(self):
        main_layout = self.main_layout
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # عنوان
        title = QLabel("تنظیمات بازی")
        tf = QFont(FONT_FAMILY, 24)
        tf.setBold(True)
        title.setFont(tf)
        title.setStyleSheet("color: #4FC3F7; padding: 20px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        # حالت فعلی
        self._mode_label.setFont(QFont(FONT_FAMILY, 12))
        self._mode_label.setStyleSheet("color: #FF8F00; padding: 4px;")
        self._mode_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self._mode_label)

        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(
            "QScrollArea { background-color: transparent; border: none; }"
        )

        content = QWidget()
        content.setStyleSheet("background-color: #0B1D3A;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(80, 20, 80, 20)
        content_layout.setSpacing(14)

        # ============================================================
        # دکمه‌های پیش‌تنظیم
        # ============================================================
        preset_frame = QFrame()
        preset_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(26, 42, 74, 0.6);
                border: 2px solid #4FC3F7;
                border-radius: 10px;
            }
        """)
        preset_layout = QVBoxLayout(preset_frame)
        preset_layout.setContentsMargins(20, 14, 20, 14)
        preset_layout.setSpacing(8)

        preset_title = QLabel("حالت‌های آماده")
        pt_font = QFont(FONT_FAMILY, 14)
        pt_font.setBold(True)
        preset_title.setFont(pt_font)
        preset_title.setStyleSheet("color: #4FC3F7; border: none;")
        preset_layout.addWidget(preset_title)

        preset_desc = QLabel(
            "برای استفاده‌ی سریع، یکی از دو حالت زیر را انتخاب کنید. "
            "سپس می‌توانید تنظیمات را به‌صورت دلخواه تغییر دهید."
        )
        preset_desc.setFont(QFont(FONT_FAMILY, 11))
        preset_desc.setStyleSheet("color: #CCCCCC; border: none;")
        preset_desc.setWordWrap(True)
        preset_layout.addWidget(preset_desc)

        preset_buttons = QHBoxLayout()
        preset_buttons.setSpacing(10)

        full_btn = QPushButton("حالت پژوهش (کامل)")
        full_btn.setFont(QFont(FONT_FAMILY, 12, QFont.Weight.Bold))
        full_btn.setMinimumHeight(48)
        full_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        full_btn.setStyleSheet(self._preset_button_style("#4CAF50"))
        full_btn.clicked.connect(lambda: self._apply_preset("full"))
        preset_buttons.addWidget(full_btn)

        short_btn = QPushButton("حالت استخدام (سریع)")
        short_btn.setFont(QFont(FONT_FAMILY, 12, QFont.Weight.Bold))
        short_btn.setMinimumHeight(48)
        short_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        short_btn.setStyleSheet(self._preset_button_style("#FF8F00"))
        short_btn.clicked.connect(lambda: self._apply_preset("short"))
        preset_buttons.addWidget(short_btn)

        theater_btn = QPushButton("حالت نمایش")
        theater_btn.setFont(
            QFont(FONT_FAMILY, 12, QFont.Weight.Bold)
        )
        theater_btn.setMinimumHeight(48)
        theater_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        theater_btn.setStyleSheet(
            self._preset_button_style("#4FC3F7")
        )
        theater_btn.clicked.connect(
            lambda: self._apply_preset("theater")
        )
        preset_buttons.addWidget(theater_btn)

        preset_layout.addLayout(preset_buttons)
        content_layout.addWidget(preset_frame)

        # ============================================================
        # بخش‌های داستانی اختیاری
        # ============================================================
        sections_frame = QFrame()
        sections_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(26, 42, 74, 0.6);
                border: 2px solid #FF8F00;
                border-radius: 10px;
            }
        """)
        sections_layout = QVBoxLayout(sections_frame)
        sections_layout.setContentsMargins(20, 14, 20, 14)
        sections_layout.setSpacing(6)

        sections_title = QLabel("بخش‌های داستانی اختیاری")
        st_font = QFont(FONT_FAMILY, 14)
        st_font.setBold(True)
        sections_title.setFont(st_font)
        sections_title.setStyleSheet("color: #FF8F00; border: none;")
        sections_layout.addWidget(sections_title)

        sections_desc = QLabel(
            "این بخش‌ها بر نمرات نهایی اثر ندارند — فقط عمق روایی "
            "را بیشتر می‌کنند. خاموش کردنشان، زمان بازی را کوتاه‌تر "
            "می‌کند."
        )
        sections_desc.setFont(QFont(FONT_FAMILY, 10))
        sections_desc.setStyleSheet("color: #B0BEC5; border: none;")
        sections_desc.setWordWrap(True)
        sections_layout.addWidget(sections_desc)

        sections_layout.addSpacing(6)

        # چک‌باکس‌های بخش‌ها
        section_items = [
            ("prologue", "پرولوگ شخصی در مقدمه",
             "داستان داوطلبانه بودن مأموریت (~۱ دقیقه)"),
            ("interludes_extended", "میان‌پرده‌های چند‌دیالوگی",
             "میان‌پرده‌ها به‌جای یک دیالوگ، سه دیالوگ (~۳ دقیقه)"),
            ("nights", "شب‌های ایستگاه",
             "سه شب اختیاری بین فازها، با گفتگو و تأمل (~۴ دقیقه)"),
            ("flashbacks", "یادآوری تصمیم‌ها",
             "اشاره به تصمیم‌های قبلی هنگام تصمیم‌های کلیدی (~۲ دقیقه)"),
            ("multilayer_memory", "بازتاب الگوهای تصمیم",
             "نگاه به الگوی چند تصمیم در چهار سناریوی کلیدی (~۱ دقیقه)"),
            ("council_prep", "پیش از جلسه‌ی شورا",
             "آماده‌سازی در راهرو با سه انتخاب (~۱ دقیقه)"),
            ("council_outro", "پس از جلسه‌ی شورا",
             "قدم زدن در راهرو و بازتاب درونی (~۱ دقیقه)"),
            ("letter_to_self", "نامه به خود",
             "یک متن آزاد پیش از پایان — تأمل شخصی (~۱ دقیقه)"),
            ("epilogue", "پایان روایی متنوع",
             "داستان پایان بر اساس الگوی روابط (~۲ دقیقه)"),
        ]

        for key, label, hint in section_items:
            cb = self._make_checkbox(label, hint)
            self.section_boxes[key] = cb
            sections_layout.addWidget(cb)

        content_layout.addWidget(sections_frame)

        # ============================================================
        # فازهای اصلی (با هشدار)
        # ============================================================
        phases_frame = QFrame()
        phases_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(211, 47, 47, 0.10);
                border: 2px solid #D32F2F;
                border-radius: 10px;
            }
        """)
        phases_layout = QVBoxLayout(phases_frame)
        phases_layout.setContentsMargins(20, 14, 20, 14)
        phases_layout.setSpacing(6)

        phases_title = QLabel("⚠  فازهای اصلی (پیشرفته)")
        pt2_font = QFont(FONT_FAMILY, 14)
        pt2_font.setBold(True)
        phases_title.setFont(pt2_font)
        phases_title.setStyleSheet("color: #D32F2F; border: none;")
        phases_layout.addWidget(phases_title)

        phases_desc = QLabel(
            "هشدار: خاموش کردن هر فاز، نمره‌ی نهایی شایستگی‌های "
            "مرتبط را بی‌اعتبار می‌کند. این تنظیمات فقط برای "
            "پژوهشگر است."
        )
        phases_desc.setFont(QFont(FONT_FAMILY, 10))
        phases_desc.setStyleSheet("color: #FFB74D; border: none;")
        phases_desc.setWordWrap(True)
        phases_layout.addWidget(phases_desc)

        phases_layout.addSpacing(6)

        phase_items = [
            ("phase1", "روز اول — سکوت در ایستگاه"),
            ("phase2", "روز دوم — سایه‌های شک"),
            ("phase3", "روز سوم — معمای داده‌ها"),
            ("phase4", "روز چهارم — آستانه‌ی شورا"),
            ("hexaco", "پرسشنامه‌ی شخصیتی HEXACO-24"),
        ]

        for key, label in phase_items:
            cb = self._make_checkbox(label, "")
            self.phase_boxes[key] = cb
            phases_layout.addWidget(cb)

        content_layout.addWidget(phases_frame)

        # ============================================================
        # بخش صدا
        # ============================================================
        audio_frame = QFrame()
        audio_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(26, 42, 74, 0.6);
                border: 2px solid #4FC3F7;
                border-radius: 10px;
            }
        """)
        audio_layout = QVBoxLayout(audio_frame)
        audio_layout.setContentsMargins(20, 14, 20, 14)
        audio_layout.setSpacing(10)

        audio_title = QLabel("🔊  صدا و موسیقی")
        at_font = QFont(FONT_FAMILY, 14)
        at_font.setBold(True)
        audio_title.setFont(at_font)
        audio_title.setStyleSheet("color: #4FC3F7; border: none;")
        audio_layout.addWidget(audio_title)

        audio_desc = QLabel(
            "موسیقی ملایم پس‌زمینه برای هر صحنه. اگر فایل‌های "
            "صوتی در پوشه‌ی assets/audio موجود نباشند، برنامه "
            "با سکوت کار می‌کند."
        )
        audio_desc.setFont(QFont(FONT_FAMILY, 10))
        audio_desc.setStyleSheet("color: #B0BEC5; border: none;")
        audio_desc.setWordWrap(True)
        audio_layout.addWidget(audio_desc)

        audio_layout.addSpacing(6)

        # چک‌باکس روشن/خاموش
        self.audio_enabled_cb = QCheckBox("فعال بودن صدا")
        self.audio_enabled_cb.setFont(QFont(FONT_FAMILY, 12))
        self.audio_enabled_cb.setLayoutDirection(
            Qt.LayoutDirection.RightToLeft
        )
        self.audio_enabled_cb.setStyleSheet("""
            QCheckBox {
                color: #FFFFFF;
                spacing: 10px;
                padding: 6px;
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
        self.audio_enabled_cb.stateChanged.connect(
            self._on_audio_enabled_changed
        )
        audio_layout.addWidget(self.audio_enabled_cb)

        # اسلایدر صدا
        volume_row = QHBoxLayout()
        volume_row.setSpacing(10)

        vol_label = QLabel("بلندی صدا:")
        vol_label.setFont(QFont(FONT_FAMILY, 11))
        vol_label.setStyleSheet("color: #FFFFFF; border: none;")
        volume_row.addWidget(vol_label)

        from PyQt6.QtWidgets import QSlider
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(40)
        self.volume_slider.setLayoutDirection(
            Qt.LayoutDirection.LeftToRight
        )
        self.volume_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 8px;
                background: #1A2A4A;
                border-radius: 4px;
                border: 1px solid #4FC3F7;
            }
            QSlider::handle:horizontal {
                background: #4FC3F7;
                border: 2px solid #FFFFFF;
                width: 14px;
                height: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }
            QSlider::sub-page:horizontal {
                background: #4FC3F7;
                border-radius: 4px;
            }
        """)
        self.volume_slider.valueChanged.connect(
            self._on_volume_changed
        )
        volume_row.addWidget(self.volume_slider, 1)

        self.volume_value_label = QLabel("40%")
        self.volume_value_label.setFont(QFont(FONT_FAMILY, 11))
        self.volume_value_label.setStyleSheet(
            "color: #4FC3F7; border: none; min-width: 40px;"
        )
        self.volume_value_label.setLayoutDirection(
            Qt.LayoutDirection.LeftToRight
        )
        volume_row.addWidget(self.volume_value_label)

        audio_layout.addLayout(volume_row)

        content_layout.addWidget(audio_frame)

        # ============================================================
        # بخش ذخیره‌ی خودکار
        # ============================================================
        resume_frame = QFrame()
        resume_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(26, 42, 74, 0.6);
                border: 2px solid #4CAF50;
                border-radius: 10px;
            }
        """)
        resume_layout = QVBoxLayout(resume_frame)
        resume_layout.setContentsMargins(20, 14, 20, 14)
        resume_layout.setSpacing(8)

        resume_title = QLabel("💾  ذخیره‌ی خودکار")
        rt_font = QFont(FONT_FAMILY, 14)
        rt_font.setBold(True)
        resume_title.setFont(rt_font)
        resume_title.setStyleSheet("color: #4CAF50; border: none;")
        resume_layout.addWidget(resume_title)

        resume_desc = QLabel(
            "اگر بازی نیمه‌کاره بماند (بستن برنامه یا قطع "
            "برق)، در شروع بعدی می‌توانید از همان‌جا ادامه دهید."
        )
        resume_desc.setFont(QFont(FONT_FAMILY, 10))
        resume_desc.setStyleSheet(
            "color: #B0BEC5; border: none;"
        )
        resume_desc.setWordWrap(True)
        resume_layout.addWidget(resume_desc)

        resume_layout.addSpacing(6)

        self.auto_resume_cb = QCheckBox(
            "فعال بودن ذخیره‌ی خودکار"
        )
        self.auto_resume_cb.setFont(QFont(FONT_FAMILY, 12))
        self.auto_resume_cb.setLayoutDirection(
            Qt.LayoutDirection.RightToLeft
        )
        self.auto_resume_cb.setStyleSheet("""
            QCheckBox {
                color: #FFFFFF;
                spacing: 10px;
                padding: 6px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #4CAF50;
                border-radius: 4px;
                background-color: #1A2A4A;
            }
            QCheckBox::indicator:checked {
                background-color: #4CAF50;
            }
        """)
        resume_layout.addWidget(self.auto_resume_cb)

        content_layout.addWidget(resume_frame)

        # ============================================================
        # بخش دیالوگ درونی
        # ============================================================
        inner_frame = QFrame()
        inner_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(26, 42, 74, 0.6);
                border: 2px solid #FF8F00;
                border-radius: 10px;
            }
        """)
        inner_layout = QVBoxLayout(inner_frame)
        inner_layout.setContentsMargins(20, 14, 20, 14)
        inner_layout.setSpacing(8)

        inner_title = QLabel("💭  نسخه‌ی دیالوگ")
        it_font = QFont(FONT_FAMILY, 14)
        it_font.setBold(True)
        inner_title.setFont(it_font)
        inner_title.setStyleSheet(
            "color: #FF8F00; border: none;"
        )
        inner_layout.addWidget(inner_title)

        inner_desc = QLabel(
            "در نسخه‌ی «با توجیه»، هر گزینه شامل تحلیل هزینه-فایده "
            "است. این حالت فاصله‌ی تصمیم ضمنی و تأملی را می‌سنجد. "
            "حالت «تصادفی» برای پژوهش توصیه می‌شود."
        )
        inner_desc.setFont(QFont(FONT_FAMILY, 10))
        inner_desc.setStyleSheet(
            "color: #B0BEC5; border: none;"
        )
        inner_desc.setWordWrap(True)
        inner_layout.addWidget(inner_desc)

        inner_layout.addSpacing(6)

        # رادیو باتن‌ها
        from PyQt6.QtWidgets import QRadioButton, QButtonGroup

        self._inner_group = QButtonGroup(self)
        radio_off = QRadioButton("ساده (خاموش)")
        radio_on = QRadioButton("با توجیه (روشن)")
        radio_random = QRadioButton("تصادفی per-participant")

        for rb in [radio_off, radio_on, radio_random]:
            rb.setFont(QFont(FONT_FAMILY, 12))
            rb.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            rb.setStyleSheet("""
                QRadioButton {
                    color: #FFFFFF;
                    spacing: 10px;
                    padding: 4px;
                }
                QRadioButton::indicator {
                    width: 18px;
                    height: 18px;
                    border: 2px solid #FF8F00;
                    border-radius: 9px;
                    background-color: #1A2A4A;
                }
                QRadioButton::indicator:checked {
                    background-color: #FF8F00;
                }
            """)

        self._inner_group.addButton(radio_off, 0)
        self._inner_group.addButton(radio_on, 1)
        self._inner_group.addButton(radio_random, 2)

        self._radio_off = radio_off
        self._radio_on = radio_on
        self._radio_random = radio_random

        inner_layout.addWidget(radio_off)
        inner_layout.addWidget(radio_on)
        inner_layout.addWidget(radio_random)

        content_layout.addWidget(inner_frame)

        # ============================================================
        # بخش دسترس‌پذیری
        # ============================================================
        access_frame = QFrame()
        access_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(26, 42, 74, 0.6);
                border: 2px solid #9C27B0;
                border-radius: 10px;
            }
        """)
        access_layout = QVBoxLayout(access_frame)
        access_layout.setContentsMargins(20, 14, 20, 14)
        access_layout.setSpacing(8)

        access_title = QLabel("♿  دسترس‌پذیری")
        at_font = QFont(FONT_FAMILY, 14)
        at_font.setBold(True)
        access_title.setFont(at_font)
        access_title.setStyleSheet("color: #9C27B0; border: none;")
        access_layout.addWidget(access_title)

        access_desc = QLabel(
            "گزینه‌های زیر برای بهبود خوانایی و کاهش فشار "
            "بصری. توصیه می‌شود در صورت خستگی چشم یا "
            "استفاده بر روی نمایشگرهای کوچک فعال شوند."
        )
        access_desc.setFont(QFont(FONT_FAMILY, 10))
        access_desc.setStyleSheet(
            "color: #B0BEC5; border: none;"
        )
        access_desc.setWordWrap(True)
        access_layout.addWidget(access_desc)

        access_layout.addSpacing(6)

        # چک‌باکس‌ها
        self.acc_large_fonts = self._make_checkbox(
            "فونت‌های بزرگ‌تر (+۳۰٪)", ""
        )
        access_layout.addWidget(self.acc_large_fonts)

        self.acc_high_contrast = self._make_checkbox(
            "کنتراست بالا", ""
        )
        access_layout.addWidget(self.acc_high_contrast)

        self.acc_reduce_motion = self._make_checkbox(
            "کاهش انیمیشن‌ها و افکت‌ها", ""
        )
        access_layout.addWidget(self.acc_reduce_motion)

        content_layout.addWidget(access_frame)

        # ============================================================
        # ✅ بخش حالت سریع (Fast Mode)
        # ============================================================
        fast_frame = QFrame()
        fast_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 143, 0, 0.08);
                border: 2px solid #FF8F00;
                border-radius: 10px;
            }
        """)
        fast_layout = QVBoxLayout(fast_frame)
        fast_layout.setContentsMargins(20, 14, 20, 14)
        fast_layout.setSpacing(8)

        fast_title = QLabel("⚡  حالت سریع (تست و ارزیابی)")
        ft_font = QFont(FONT_FAMILY, 14)
        ft_font.setBold(True)
        fast_title.setFont(ft_font)
        fast_title.setStyleSheet("color: #FF8F00; border: none;")
        fast_layout.addWidget(fast_title)

        fast_desc = QLabel(
            "با فعال کردن این گزینه، انیمیشن‌های تایپ متن، "
            "افکت‌های محو شدن (Fade)، ذرات پس‌زمینه و لرزش‌های "
            "بصری حذف می‌شوند. این کار زمان هر جلسه را "
            "به‌طور چشمگیری کاهش می‌دهد."
        )
        fast_desc.setFont(QFont(FONT_FAMILY, 10))
        fast_desc.setStyleSheet("color: #B0BEC5; border: none;")
        fast_desc.setWordWrap(True)
        fast_layout.addWidget(fast_desc)

        fast_layout.addSpacing(6)

        # چک‌باکس حالت سریع
        self.fast_mode_cb = self._make_checkbox(
            "فعال بودن حالت سریع (حذف انیمیشن‌ها)", ""
        )
        fast_layout.addWidget(self.fast_mode_cb)

        content_layout.addWidget(fast_frame)

        # ============================================================
        # ✅ بخش ابزارهای ارزیابی (SME، CRT، SD3، ...)
        # ============================================================
        tools_frame = QFrame()
        tools_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(156, 39, 176, 0.08);
                border: 2px solid #9C27B0;
                border-radius: 10px;
            }
        """)
        tools_layout = QVBoxLayout(tools_frame)
        tools_layout.setContentsMargins(20, 14, 20, 14)
        tools_layout.setSpacing(6)

        tools_title = QLabel("🧪  ابزارهای ارزیابی")
        tt_font = QFont(FONT_FAMILY, 14)
        tt_font.setBold(True)
        tools_title.setFont(tt_font)
        tools_title.setStyleSheet(
            "color: #9C27B0; border: none;"
        )
        tools_layout.addWidget(tools_title)

        tools_desc = QLabel(
            "این ابزارها در صحنه‌ی پرسشنامه‌های پایانی به "
            "شرکت‌کننده نمایش داده می‌شوند. «ارزیابی "
            "متخصصان» برای پژوهشگران است و از منوی اصلی "
            "باز می‌شود."
        )
        tools_desc.setFont(QFont(FONT_FAMILY, 10))
        tools_desc.setStyleSheet(
            "color: #B0BEC5; border: none;"
        )
        tools_desc.setWordWrap(True)
        tools_layout.addWidget(tools_desc)

        tools_layout.addSpacing(6)

        for tool_key, tool_label in ASSESSMENT_TOOL_NAMES.items():
            cb = self._make_checkbox(
                tool_label,
                "فعال/غیرفعال کردن این ابزار"
            )
            cb.setStyleSheet("""
                QCheckBox {
                    color: #FFFFFF;
                    spacing: 10px;
                    padding: 6px;
                }
                QCheckBox::indicator {
                    width: 20px;
                    height: 20px;
                    border: 2px solid #9C27B0;
                    border-radius: 4px;
                    background-color: #1A2A4A;
                }
                QCheckBox::indicator:checked {
                    background-color: #9C27B0;
                }
            """)
            self.tool_boxes[tool_key] = cb
            tools_layout.addWidget(cb)

        content_layout.addWidget(tools_frame)

        content_layout.addStretch()
        scroll.setWidget(content)
        main_layout.addWidget(scroll, stretch=1)

        # ============================================================
        # دکمه‌های پایین
        # ============================================================
        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(40, 10, 40, 20)
        buttons_layout.setSpacing(12)

        cancel_btn = QPushButton("انصراف")
        cancel_btn.setFont(QFont(FONT_FAMILY, 14))
        cancel_btn.setMinimumHeight(52)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet(self._action_button_style("#666666"))
        cancel_btn.clicked.connect(self._on_cancel)
        buttons_layout.addWidget(cancel_btn, 1)

        save_btn = QPushButton("ذخیره و بازگشت")
        save_btn.setFont(QFont(FONT_FAMILY, 14, QFont.Weight.Bold))
        save_btn.setMinimumHeight(52)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setStyleSheet(self._action_button_style("#4CAF50"))
        save_btn.clicked.connect(self._on_save)
        buttons_layout.addWidget(save_btn, 2)

        main_layout.addLayout(buttons_layout)

    # ================================================================
    def _make_checkbox(self, label: str, hint: str) -> QCheckBox:
        cb = QCheckBox(label)
        cb.setFont(QFont(FONT_FAMILY, 12))
        cb.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        if hint:
            cb.setToolTip(hint)
        cb.setStyleSheet("""
            QCheckBox {
                color: #FFFFFF;
                spacing: 10px;
                padding: 6px;
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
        return cb

    def _preset_button_style(self, color: str) -> str:
        return f"""
            QPushButton {{
                background-color: #1A2A4A;
                color: {color};
                border: 2px solid {color};
                border-radius: 8px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: {color};
                color: #0B1D3A;
            }}
        """

    def _action_button_style(self, color: str) -> str:
        return f"""
            QPushButton {{
                background-color: #2B4A6F;
                color: #FFFFFF;
                border: 2px solid {color};
                border-radius: 10px;
                padding: 10px;
            }}
            QPushButton:hover {{
                background-color: {color};
                color: #FFFFFF;
            }}
        """

    # ================================================================
    def _load_from_config(self):
        """بارگذاری مقادیر از فایل تنظیمات"""
        cfg = load_config()
        sections = cfg.get("sections", {})
        phases = cfg.get("phases", {})

        for key, cb in self.section_boxes.items():
            cb.setChecked(bool(sections.get(key, True)))
        for key, cb in self.phase_boxes.items():
            cb.setChecked(bool(phases.get(key, True)))

        # ✅ بارگذاری تنظیمات صدا
        audio = get_audio_settings()
        # قطع سیگنال‌ها تا از حلقه جلوگیری شود
        self.audio_enabled_cb.blockSignals(True)
        self.volume_slider.blockSignals(True)

        self.audio_enabled_cb.setChecked(audio["enabled"])
        vol_pct = int(audio["volume"] * 100)
        self.volume_slider.setValue(vol_pct)
        self.volume_value_label.setText(f"{vol_pct}%")
        self.volume_slider.setEnabled(audio["enabled"])

        self.audio_enabled_cb.blockSignals(False)
        self.volume_slider.blockSignals(False)

        mode = cfg.get("mode", "custom")
        mode_fa = {
            "full": "حالت پژوهش (کامل)",
            "short": "حالت استخدام (سریع)",
            "theater": "حالت نمایش",
            "custom": "حالت سفارشی",
        }.get(mode, "حالت سفارشی")
        self._mode_label.setText(f"حالت فعلی: {mode_fa}")

        # ✅ بارگذاری تنظیمات ذخیره‌ی خودکار
        self.auto_resume_cb.blockSignals(True)
        self.auto_resume_cb.setChecked(is_auto_resume_enabled())
        self.auto_resume_cb.blockSignals(False)

        # ✅ بارگذاری حالت دیالوگ درونی
        mode = get_inner_dialogue_mode()
        if mode == "on":
            self._radio_on.setChecked(True)
        elif mode == "random":
            self._radio_random.setChecked(True)
        else:
            self._radio_off.setChecked(True)

        # ✅ بارگذاری تنظیمات دسترس‌پذیری
        acc = get_accessibility_settings()
        self.acc_large_fonts.blockSignals(True)
        self.acc_high_contrast.blockSignals(True)
        self.acc_reduce_motion.blockSignals(True)
        self.acc_large_fonts.setChecked(acc["large_fonts"])
        self.acc_high_contrast.setChecked(acc["high_contrast"])
        self.acc_reduce_motion.setChecked(acc["reduce_motion"])
        self.acc_large_fonts.blockSignals(False)
        self.acc_high_contrast.blockSignals(False)
        self.acc_reduce_motion.blockSignals(False)

        # ✅ بارگذاری ابزارهای ارزیابی
        for tool_key, cb in self.tool_boxes.items():
            cb.blockSignals(True)
            cb.setChecked(is_assessment_tool_enabled(tool_key))
            cb.blockSignals(False)

        # ✅ بارگذاری حالت سریع
        from core.app_config import get_fast_mode
        self.fast_mode_cb.blockSignals(True)
        self.fast_mode_cb.setChecked(get_fast_mode())
        self.fast_mode_cb.blockSignals(False)

    # ================================================================
    def _apply_preset(self, preset_name: str):
        """اعمال پیش‌تنظیم"""
        if preset_name == "full":
            cfg = dict(PRESET_FULL)
            label = "حالت پژوهش"
        elif preset_name == "short":
            cfg = dict(PRESET_SHORT)
            label = "حالت استخدام"
        elif preset_name == "theater":
            cfg = dict(PRESET_THEATER)
            label = "حالت نمایش"
        else:
            return

        save_config(cfg)
        self._load_from_config()

        msg = QMessageBox(self)
        msg.setWindowTitle("پیش‌تنظیم اعمال شد")
        msg.setText(f"✓ {label} با موفقیت اعمال شد.")
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        msg.exec()

    # ================================================================
    def _on_save(self):
        """ذخیره‌ی تنظیمات سفارشی"""
        # بررسی: حداقل یک فاز باید فعال باشد
        enabled_phases = [
            k for k, cb in self.phase_boxes.items() if cb.isChecked()
        ]
        if not enabled_phases:
            msg = QMessageBox(self)
            msg.setWindowTitle("تنظیمات نامعتبر")
            msg.setText(
                "حداقل یک فاز باید فعال باشد، وگرنه بازی قابل "
                "اجرا نیست."
            )
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            msg.exec()
            return

        # بررسی: فازها باید پیوسته باشند (phase1 اگر فعال نیست، phase3 هم نباید باشد)
        order = ["phase1", "phase2", "phase3", "phase4"]
        enabled_set = set(enabled_phases)
        first_disabled = None
        for p in order:
            if p not in enabled_set:
                first_disabled = p
                break

        if first_disabled:
            # آیا فاز بعدی فعال است؟
            idx = order.index(first_disabled)
            for later in order[idx + 1:]:
                if later in enabled_set:
                    msg = QMessageBox(self)
                    msg.setWindowTitle("تنظیمات نامعتبر")
                    msg.setText(
                        f"نمی‌توان «{first_disabled}» را خاموش "
                        f"کرد ولی «{later}» را روشن نگه داشت. "
                        "فازها باید پیوسته باشند."
                    )
                    msg.setIcon(QMessageBox.Icon.Warning)
                    msg.setLayoutDirection(
                        Qt.LayoutDirection.RightToLeft
                    )
                    msg.exec()
                    return

        # ذخیره
        cfg = load_config()
        cfg["mode"] = "custom"
        cfg["sections"] = {
            k: cb.isChecked() for k, cb in self.section_boxes.items()
        }
        cfg["phases"] = {
            k: cb.isChecked() for k, cb in self.phase_boxes.items()
        }
        save_config(cfg)

        # ✅ ذخیره‌ی تنظیمات صدا
        try:
            set_audio_settings(
                enabled=self.audio_enabled_cb.isChecked(),
                volume=self.volume_slider.value() / 100.0,
            )
        except Exception as e:
            print(f"⚠️ خطا در ذخیره‌ی تنظیمات صدا: {e}")

        # ✅ ذخیره‌ی تنظیمات auto_resume
        try:
            set_auto_resume(self.auto_resume_cb.isChecked())
        except Exception as e:
            print(f"⚠️ خطا در ذخیره‌ی auto_resume: {e}")

        # ✅ ذخیره‌ی حالت دیالوگ درونی
        try:
            checked_id = self._inner_group.checkedId()
            if checked_id == 1:
                set_inner_dialogue_mode("on")
            elif checked_id == 2:
                set_inner_dialogue_mode("random")
            else:
                set_inner_dialogue_mode("off")
        except Exception as e:
            print(f"⚠️ خطا در ذخیره‌ی inner_dialogue: {e}")

        # ✅ ذخیره‌ی دسترس‌پذیری
        try:
            set_accessibility_settings(
                large_fonts=self.acc_large_fonts.isChecked(),
                high_contrast=self.acc_high_contrast.isChecked(),
                reduce_motion=self.acc_reduce_motion.isChecked(),
            )
        except Exception as e:
            print(f"⚠️ خطا در ذخیره‌ی accessibility: {e}")

        # ✅ ذخیره‌ی ابزارهای ارزیابی
        try:
            for tool_key, cb in self.tool_boxes.items():
                set_assessment_tool_enabled(
                    tool_key, cb.isChecked()
                )
        except Exception as e:
            print(f"⚠️ خطا در ذخیره‌ی assessment_tools: {e}")

        # ✅ ذخیره‌ی حالت سریع
        try:
            from core.app_config import set_fast_mode
            set_fast_mode(self.fast_mode_cb.isChecked())
        except Exception as e:
            print(f"⚠️ خطا در ذخیره‌ی fast_mode: {e}")

        msg = QMessageBox(self)
        msg.setWindowTitle("ذخیره شد")
        msg.setText("✓ تنظیمات با موفقیت ذخیره شد.")
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        msg.exec()

        self.change_scene("menu")

    def _on_audio_enabled_changed(self, state: int):
        """تغییر فعال/غیرفعال بودن صدا"""
        enabled = bool(state)
        self.volume_slider.setEnabled(enabled)

        # ✅ اعمال فوری
        try:
            from core.audio_manager import get_audio_manager
            audio = get_audio_manager()
            audio.set_enabled(enabled)
        except Exception as e:
            print(f"⚠️ خطا در تغییر وضعیت صدا: {e}")

    def _on_volume_changed(self, value: int):
        """تغییر مقدار صدا"""
        self.volume_value_label.setText(f"{value}%")
        volume = value / 100.0

        try:
            from core.audio_manager import get_audio_manager
            get_audio_manager().set_volume(volume)
        except Exception as e:
            print(f"⚠️ خطا در تغییر صدا: {e}")

    def _on_cancel(self):
        self.change_scene("menu")

    def on_enter(self, **kwargs):
        self._load_from_config()
        print("✓ ورود به صحنه تنظیمات")