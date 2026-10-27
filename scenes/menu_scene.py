"""
صحنه منوی اصلی بازی — نسخه ۳

رفع باگ‌ها:
- حذف QGraphicsOpacityEffect که باعث نامرئی شدن دکمه‌ها می‌شد
- حذف rgba از پس‌زمینه دکمه‌ها (برای سازگاری بهتر با QSS)
- حذف انیمیشن ورود (QPainter flood را تشدید می‌کرد)
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QFrame
)
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QFont

from widgets.procedural_icons import get_icon

from scenes.base_scene import BaseScene
from widgets.background_widget import BackgroundWidget
from core.session_state import has_saved_session, clear_state

FONT_FAMILY = "Vazirmatn"


class MenuScene(BaseScene):
    def __init__(self, game_manager):
        super().__init__(game_manager)
        self.setStyleSheet("MenuScene { background-color: #0B1D3A; }")
        self._setup_ui()
        print("✓ MenuScene راه‌اندازی شد (نسخه ۳)")

    def _setup_ui(self):
        # صدای کلیک به‌طور سراسری مدیریت می‌شود
        # (GlobalClickSoundFilter در main.py)

        # پس‌زمینه (بدون افکت شفافیت)
        self.bg = BackgroundWidget(
            theme_key="menu", image_key="menu_hero"
        )

        # ✅ لایه‌های پارالاکس
        from widgets.parallax_layer import ParallaxLayer
        self._parallax_far = ParallaxLayer(depth=3, parent=self.bg)
        self._parallax_mid = ParallaxLayer(depth=2, parent=self.bg)
        self._parallax_near = ParallaxLayer(depth=1, parent=self.bg)

        bg_layout = QVBoxLayout(self.bg)
        bg_layout.setContentsMargins(100, 60, 100, 60)
        bg_layout.setSpacing(24)
        bg_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # --- عنوان ---
        self.title_label = QLabel("TRUTHLINE")
        tf = QFont(FONT_FAMILY, 68)
        tf.setBold(True)
        self.title_label.setFont(tf)
        self.title_label.setStyleSheet(
            "color: #4FC3F7; letter-spacing: 10px; "
            "background: transparent;"
        )
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bg_layout.addWidget(self.title_label)

        # --- زیرعنوان ---
        subtitle = QLabel("بحران ایستگاه کاسپین")
        subtitle.setFont(QFont(FONT_FAMILY, 26))
        subtitle.setStyleSheet(
            "color: #FFFFFF; background: transparent;"
        )
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bg_layout.addWidget(subtitle)

        # --- جداکننده ---
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFixedWidth(400)
        sep.setStyleSheet(
            "QFrame { background-color: #4FC3F7; "
            "max-height: 1px; border: none; }"
        )
        bg_layout.addWidget(
            sep, alignment=Qt.AlignmentFlag.AlignCenter
        )
        bg_layout.addSpacing(30)

        # --- دکمه‌ی ادامه (فقط اگر session موجود باشد) ---
        self.resume_btn = self._make_button(
            "ادامه‌ی مأموریت قبلی", "#FF8F00"
        )
        self.resume_btn.setIcon(
            get_icon("play", size=32, color="#FF8F00")
        )
        self.resume_btn.setIconSize(QSize(26, 26))
        self.resume_btn.clicked.connect(self._on_resume_clicked)
        bg_layout.addWidget(
            self.resume_btn, alignment=Qt.AlignmentFlag.AlignCenter
        )
        self.resume_btn.setVisible(False)  # پیش‌فرض مخفی

        # --- دکمه‌های اصلی ---
        start_btn = self._make_button("شروع مأموریت جدید", "#4FC3F7")
        start_btn.setIcon(
            get_icon("play", size=32, color="#4FC3F7")
        )
        start_btn.setIconSize(QSize(26, 26))
        start_btn.clicked.connect(self._on_start_clicked)
        bg_layout.addWidget(
            start_btn, alignment=Qt.AlignmentFlag.AlignCenter
        )

        settings_btn = self._make_button("تنظیمات", "#4FC3F7")
        settings_btn.setIcon(
            get_icon("gear", size=32, color="#4FC3F7")
        )
        settings_btn.setIconSize(QSize(26, 26))
        settings_btn.clicked.connect(self._on_settings_clicked)
        bg_layout.addWidget(
            settings_btn, alignment=Qt.AlignmentFlag.AlignCenter
        )

        # ✅ دکمه‌ی ارزیابی متخصصان — فقط اگر فعال باشد
        try:
            from core.app_config import is_assessment_tool_enabled
            if is_assessment_tool_enabled("sme_review"):
                sme_btn = self._make_button(
                    "🧪  حالت ارزیابی متخصصان", "#9C27B0"
                )
                sme_btn.setIconSize(QSize(26, 26))
                sme_btn.clicked.connect(self._on_sme_clicked)
                bg_layout.addWidget(
                    sme_btn,
                    alignment=Qt.AlignmentFlag.AlignCenter,
                )
        except Exception as e:
            print(f"⚠️ خطا در افزودن دکمه‌ی SME: {e}")

        quit_btn = self._make_button("خروج", "#D32F2F")
        quit_btn.setIcon(
            get_icon("exit", size=32, color="#D32F2F")
        )
        quit_btn.setIconSize(QSize(26, 26))
        quit_btn.clicked.connect(self._on_quit_clicked)
        bg_layout.addWidget(
            quit_btn, alignment=Qt.AlignmentFlag.AlignCenter
        )

        bg_layout.addSpacing(20)

        version = QLabel("نسخه ۲.۰.۰ | پروژه پایان‌نامه دکتری")
        version.setFont(QFont(FONT_FAMILY, 11))
        version.setStyleSheet(
            "color: #888888; background: transparent;"
        )
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bg_layout.addWidget(version)

        # افزودن پس‌زمینه
        self.main_layout.addWidget(self.bg)

        # ✅ اندازه‌دهی اولیه پارالاکس
        QTimer.singleShot(
            50, self._resize_parallax
        )

    def _resize_parallax(self):
        """هم‌اندازه کردن لایه‌های پارالاکس با bg"""
        if not hasattr(self, "_parallax_far"):
            return
        rect = self.bg.rect()
        self._parallax_far.setGeometry(rect)
        self._parallax_mid.setGeometry(rect)
        self._parallax_near.setGeometry(rect)
        # ✅ نگه‌داشتن لایه‌ها روی پس‌زمینه ولی زیر محتوا
        self._parallax_far.lower()
        self._parallax_mid.lower()
        self._parallax_near.lower()

    def resizeEvent(self, event):  # type: ignore
        super().resizeEvent(event)
        self._resize_parallax()

    def _make_button(self, text: str, border_color: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setFont(QFont(FONT_FAMILY, 20))
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setMinimumSize(380, 64)
        # ✅ راست‌چین کردن متن دکمه
        btn.setLayoutDirection(
            Qt.LayoutDirection.RightToLeft
        )
        # رنگ‌های solid جای rgba (سازگارتر با QSS)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #2B4A6F;
                color: #FFFFFF;
                border: 2px solid {border_color};
                border-radius: 10px;
                padding: 10px 50px 10px 20px;
                text-align: right;
            }}
            QPushButton:hover {{
                background-color: {border_color};
                color: #0B1D3A;
                border: 2px solid #FFFFFF;
            }}
            QPushButton:pressed {{
                background-color: #1A2A4A;
                color: {border_color};
            }}
        """)
        return btn

    def _on_start_clicked(self):
        print("✓ دکمه شروع جدید کلیک شد")
        self.data_logger.log_event(
            scene_id="menu", scenario_id="menu_start",
            event_type="button_click", metadata={"button": "start_new"}
        )

        # ✅ پاک کردن session قبلی (اگر بود)
        clear_state()
        # ✅ بازنشانی پرچم‌های game_manager
        gm = self.game_manager
        if hasattr(gm, "_scenario_indices"):
            for key in gm._scenario_indices:
                gm._scenario_indices[key] = 0
        if hasattr(gm, "_flags"):
            gm._flags = {
                "council_prep_shown": False,
                "letter_shown": False,
                "nights_completed": [],
                "phases_completed": [],
            }

        self.change_scene("demographic")

    def _on_resume_clicked(self):
        """ادامه‌ی مأموریت قبلی"""
        print("✓ دکمه ادامه کلیک شد")
        self.data_logger.log_event(
            scene_id="menu", scenario_id="menu_resume",
            event_type="button_click",
            metadata={"button": "resume"}
        )

        try:
            from core.session_state import load_state
            state = load_state()
        except Exception as e:
            print(f"⚠️ خطا در بارگذاری session: {e}")
            return

        if not state:
            print("⚠️ session وجود ندارد")
            self.resume_btn.setVisible(False)
            return

        # ✅ بازیابی روابط و حافظه
        try:
            self.data_logger.restore_from_state(state)
        except Exception as e:
            print(f"⚠️ خطا در بازیابی state: {e}")

        # ✅ بازیابی ایندکس‌ها و پرچم‌ها
        gm = self.game_manager
        if hasattr(gm, "_scenario_indices"):
            for key, val in state.get(
                "current_scenario_indices", {}
            ).items():
                if key in gm._scenario_indices:
                    gm._scenario_indices[key] = int(val)
        if hasattr(gm, "_flags"):
            gm._flags = state.get("flags", gm._flags)

        # ✅ رفتن به صحنه‌ی قبلی
        target_scene = state.get("current_scene", "")
        if not target_scene or target_scene in ("menu", "settings"):
            # اگر در منو بود، از demographic شروع کن
            target_scene = "demographic"

        print(f"   [RESUME] رفتن به صحنه: {target_scene}")
        self.change_scene(target_scene)

    def _on_settings_clicked(self):
        print("⚙ ورود به تنظیمات")
        self.data_logger.log_event(
            scene_id="menu", scenario_id="menu_settings",
            event_type="button_click", metadata={"button": "settings"}
        )
        self.change_scene("settings")

    def _on_sme_clicked(self):
        print("🧪 ورود به حالت ارزیابی متخصصان")
        self.data_logger.log_event(
            scene_id="menu", scenario_id="menu_sme",
            event_type="button_click",
            metadata={"button": "sme_review"},
        )
        self.change_scene("sme_review")

    def _on_quit_clicked(self):
        print("✗ دکمه خروج")
        self.data_logger.log_event(
            scene_id="menu", scenario_id="menu_quit",
            event_type="button_click", metadata={"button": "quit"}
        )
        from PyQt6.QtWidgets import QApplication
        QApplication.quit()

    def on_enter(self, **kwargs):
        print("✓ ورود به منوی اصلی")
        # ✅ بررسی وجود session ذخیره‌شده
        if has_saved_session():
            self.resume_btn.setVisible(True)
            print("   ✓ session ذخیره‌شده یافت شد — دکمه‌ی "
                  "ادامه نمایش داده شد")
        else:
            self.resume_btn.setVisible(False)