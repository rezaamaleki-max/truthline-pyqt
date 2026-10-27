"""
Splash Screen — صفحه‌ی شروع هنگام راه‌اندازی بازی
====================================================
- یک صفحه‌ی کوچک با لوگو و نام بازی
- نمایش ~۱.۸ ثانیه
- سپس به منو منتقل می‌شود
- انیمیشن Fade-in / Fade-out

نسخه: 1.0.0
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame,
    QGraphicsOpacityEffect
)
from PyQt6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve
)
from PyQt6.QtGui import QFont

from scenes.base_scene import BaseScene

FONT_FAMILY = "Vazirmatn"
HOLD_MS = 1800  # مدت نمایش splash
FADE_IN_MS = 500
FADE_OUT_MS = 400


class SplashScene(BaseScene):
    """صحنه‌ی شروع"""

    def __init__(self, game_manager):
        super().__init__(game_manager)
        self._setup_ui()
        print("✓ SplashScene راه‌اندازی شد")

    # ================================================================
    def _setup_ui(self):
        main_layout = self.main_layout
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # پس‌زمینه
        center = QWidget()
        center.setStyleSheet("""
            background: qlineargradient(
                x1:0, y1:0, x2:0.3, y2:1,
                stop:0 #010308, stop:0.5 #050E1F,
                stop:1 #0A1830
            );
        """)
        center_layout = QVBoxLayout(center)
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.setSpacing(16)
        center_layout.setContentsMargins(60, 60, 60, 60)

        # آیکون/لوگو
        self.logo_label = QLabel("◈")
        lf = QFont("Arial", 72)
        lf.setBold(True)
        self.logo_label.setFont(lf)
        self.logo_label.setStyleSheet(
            "color: #4FC3F7; background: transparent;"
        )
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(self.logo_label)

        # عنوان اصلی
        self.title_label = QLabel("TRUTHLINE")
        tf = QFont(FONT_FAMILY, 48)
        tf.setBold(True)
        self.title_label.setFont(tf)
        self.title_label.setStyleSheet(
            "color: #FFFFFF; background: transparent; "
            "letter-spacing: 12px;"
        )
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(self.title_label)

        # زیرعنوان
        self.subtitle_label = QLabel("بحران ایستگاه کاسپین")
        sf = QFont(FONT_FAMILY, 18)
        self.subtitle_label.setFont(sf)
        self.subtitle_label.setStyleSheet(
            "color: #FF8F00; background: transparent;"
        )
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(self.subtitle_label)

        # فضای بیشتر
        center_layout.addSpacing(30)

        # متن بارگذاری
        self.loading_label = QLabel("در حال آماده‌سازی مأموریت...")
        ldf = QFont(FONT_FAMILY, 12)
        self.loading_label.setFont(ldf)
        self.loading_label.setStyleSheet(
            "color: #B0BEC5; background: transparent; "
            "font-style: italic;"
        )
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(self.loading_label)

        main_layout.addWidget(center, stretch=1)

    # ================================================================
    def on_enter(self, **kwargs):
        print("✓ ورود به Splash Screen")

        # Fade-in
        self._fade_in()
        # پس از نمایش، به منو برو
        QTimer.singleShot(HOLD_MS, self._go_to_menu)

    def _fade_in(self):
        """نمایش بدون افکت شفافیت.

        دلیل: QGraphicsOpacityEffect روی صحنه‌ای که
        ProceduralBackground یا هر ویجت custom-painted
        دارد، خطای QPainter می‌دهد.
        """
        try:
            self.setGraphicsEffect(None)
        except Exception:
            pass

    def _go_to_menu(self):
        """انتقال به ویدیوی معرفی (سپس منو)"""
        print(
            "✓ Splash خاتمه یافت — انتقال به ویدیوی معرفی"
        )
        self.change_scene("video_intro")