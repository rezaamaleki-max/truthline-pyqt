"""
صحنه‌ی پایانی حالت نمایش
- یک صفحه‌ی تشکر ساده
- بدون نمودار، بدون نمره
- دعوت به ادامه‌ی گفتگو در مصاحبه

نسخه: 1.0.0
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from scenes.base_scene import BaseScene

FONT_FAMILY = "Vazirmatn"


class TheaterEndScene(BaseScene):
    """پایان حالت نمایش"""

    def __init__(self, game_manager):
        super().__init__(game_manager)
        self._setup_ui()
        print("✓ TheaterEndScene راه‌اندازی شد")

    def _setup_ui(self):
        main_layout = self.main_layout
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        center = QWidget()
        center.setStyleSheet(
            "background: qlineargradient("
            "x1:0, y1:0, x2:0.3, y2:1, "
            "stop:0 #050A18, stop:1 #0B1D3A);"
        )
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(120, 60, 120, 60)
        center_layout.setSpacing(20)
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # آیکون
        icon_lbl = QLabel("✦")
        icon_lbl.setFont(QFont("Arial", 48))
        icon_lbl.setStyleSheet("color: #4FC3F7;")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(icon_lbl)

        # عنوان
        title = QLabel("پایان مأموریت")
        tf = QFont(FONT_FAMILY, 32)
        tf.setBold(True)
        title.setFont(tf)
        title.setStyleSheet("color: #4FC3F7;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(title)

        center_layout.addSpacing(20)

        # متن تشکر
        thanks = QLabel(
            "از وقتی که گذاشتید سپاسگزاریم.\n\n"
            "چهار روز در ایستگاه کاسپین — با همه‌ی تصمیم‌ها، "
            "همه‌ی لحظه‌های تأمل، و همه‌ی چالش‌هایی که پشت سر "
            "گذاشتید.\n\n"
            "در گفتگوی مصاحبه، بیشتر درباره‌ی انتخاب‌های شما "
            "صحبت خواهیم کرد."
        )
        thanks.setFont(QFont(FONT_FAMILY, 14))
        thanks.setStyleSheet("color: #CCCCCC;")
        thanks.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thanks.setWordWrap(True)
        center_layout.addWidget(thanks)

        center_layout.addSpacing(30)

        # خط جداکننده
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFixedWidth(400)
        sep.setStyleSheet(
            "background-color: #4FC3F7; max-height: 1px; "
            "border: none;"
        )
        center_layout.addWidget(
            sep, alignment=Qt.AlignmentFlag.AlignCenter
        )

        center_layout.addSpacing(20)

        # شماره‌ی شرکت‌کننده (برای هماهنگی در مصاحبه)
        participant_id = getattr(
            self.game_manager.data_logger, "participant_id", "—"
        )
        id_lbl = QLabel(f"شماره‌ی شما: {participant_id}")
        id_lbl.setFont(QFont(FONT_FAMILY, 12))
        id_lbl.setStyleSheet(
            "color: #FF8F00; "
            "background-color: rgba(255, 143, 0, 0.10); "
            "border: 1px dashed #FF8F00; "
            "border-radius: 6px; padding: 8px 16px;"
        )
        id_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(
            id_lbl, alignment=Qt.AlignmentFlag.AlignCenter
        )

        center_layout.addSpacing(20)

        # دکمه‌ی خروج
        exit_btn = QPushButton("خروج از برنامه")
        exit_btn.setFont(
            QFont(FONT_FAMILY, 14, QFont.Weight.Bold)
        )
        exit_btn.setMinimumHeight(54)
        exit_btn.setMinimumWidth(280)
        exit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        exit_btn.setStyleSheet("""
            QPushButton {
                background-color: #2B4A6F;
                color: #FFFFFF;
                border: 2px solid #4FC3F7;
                border-radius: 10px;
                padding: 12px;
            }
            QPushButton:hover {
                background-color: #4FC3F7;
                color: #0B1D3A;
            }
        """)
        exit_btn.clicked.connect(self._on_exit)
        center_layout.addWidget(
            exit_btn, alignment=Qt.AlignmentFlag.AlignCenter
        )

        main_layout.addWidget(center, stretch=1)

    def on_enter(self, **kwargs):
        print("✓ ورود به پایان نمایش")
        self.data_logger.log_event(
            scene_id="theater_end",
            scenario_id="theater_end",
            event_type="scene_enter",
            metadata={}
        )

    def _on_exit(self):
        print("✓ خروج از حالت نمایش")
        main_window = self.window()
        if main_window is not None:
            close_method = getattr(main_window, "close", None)
            if callable(close_method):
                close_method()

    def keyPressEvent(self, event):  # type: ignore
        if event.key() == Qt.Key.Key_Escape:
            self._on_exit()
        else:
            super().keyPressEvent(event)