"""
صحنه‌ی ویدیوی معرفی — پیش از منو
- پخش ویدیوی کوتاه opening.mp4 (H.264/AAC)
- با کلید Space یا Esc قابل پرش
- اگر فایل نبود یا پخش نشد، مستقیم به منو می‌رود

نسخه: 1.2.0 — تغییر از WebM/VP9 به MP4/H.264 برای پایداری
"""
import os

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton
)
from PyQt6.QtCore import Qt, QUrl, QTimer
from PyQt6.QtGui import QFont, QShortcut, QKeySequence
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget

from scenes.base_scene import BaseScene
from config import ASSETS_DIR

FONT_FAMILY = "Vazirmatn"
# ✅ MP4 با کدک H.264/AAC — پایداری کامل با QtMultimedia
#    (WebM/VP9 با نسخه‌های قدیمی QtMultimedia خطا می‌دهد)
VIDEO_FILE = "opening.webm"

# تایمر ایمنی — اگر ویدیو گیر کرد، بعد از این مدت پرش کن
SAFETY_TIMEOUT_MS = 10000

# صدای ویدیو (0.0 تا 1.0)
VIDEO_VOLUME = 0.5


class VideoIntroScene(BaseScene):
    """پخش ویدیوی معرفی پیش از منو"""

    def __init__(self, game_manager):
        super().__init__(game_manager)

        self._player: QMediaPlayer | None = None
        self._audio_output: QAudioOutput | None = None
        self._video_widget: QVideoWidget | None = None
        self._finished: bool = False
        self._safety_timer: QTimer | None = None

        # ✅ از main_layout موجود BaseScene استفاده کن
        self._setup_ui()

        # ✅ کلیدهای پرش
        self._shortcut_space = QShortcut(
            QKeySequence(Qt.Key.Key_Space), self
        )
        self._shortcut_space.activated.connect(self._skip)

        self._shortcut_esc = QShortcut(
            QKeySequence(Qt.Key.Key_Escape), self
        )
        self._shortcut_esc.activated.connect(self._skip)

        print("✓ VideoIntroScene راه‌اندازی شد")

    # ================================================================
    def _setup_ui(self):
        # ✅ از main_layout استفاده کن — نه QVBoxLayout(self)
        layout = self.main_layout
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        container = QWidget()
        container.setStyleSheet("background-color: #000000;")
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # ✅ QVideoWidget
        try:
            self._video_widget = QVideoWidget()
            self._video_widget.setStyleSheet(
                "background-color: #000000; border: none;"
            )
            container_layout.addWidget(self._video_widget, stretch=1)
        except Exception as e:
            print(f"⚠️ QVideoWidget راه‌اندازی نشد: {e}")
            self._video_widget = None

        # ✅ متن fallback
        self.fallback_label = QLabel("در حال شروع مأموریت...")
        self.fallback_label.setFont(QFont(FONT_FAMILY, 20))
        self.fallback_label.setStyleSheet(
            "color: #4FC3F7; background-color: #050A18;"
        )
        self.fallback_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.fallback_label.setVisible(False)
        container_layout.addWidget(self.fallback_label, stretch=1)

        layout.addWidget(container, stretch=1)

        # ✅ دکمه‌ی پرش — بدون QWidget اضافی، مستقیم در layout اصلی
        self.skip_btn = QPushButton(
            "پرش به منو  (Space یا Esc)"
        )
        self.skip_btn.setFont(QFont(FONT_FAMILY, 11))
        self.skip_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.skip_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.skip_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(26, 42, 74, 0.85);
                color: #B0BEC5;
                border: 1px solid #4FC3F7;
                border-radius: 8px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #4FC3F7;
                color: #0B1D3A;
            }
        """)
        self.skip_btn.clicked.connect(self._skip)
        layout.addWidget(
            self.skip_btn,
            alignment=Qt.AlignmentFlag.AlignRight,
        )

    # ================================================================
    def on_enter(self, **kwargs):
        self._finished = False

        video_path = os.path.join(
            ASSETS_DIR, "videos", VIDEO_FILE
        )

        # اگر فایل نیست، به fallback برو
        if not os.path.exists(video_path):
            print(f"⚠️ ویدیو یافت نشد: {video_path}")
            print("   → پرش مستقیم به منو")
            self._show_fallback()
            QTimer.singleShot(500, self._go_to_menu)
            return

        # تلاش برای راه‌اندازی QMediaPlayer
        if not self._init_player():
            print("   → پخش ویدیو ممکن نیست، پرش به منو")
            QTimer.singleShot(300, self._go_to_menu)
            return

        # ✅ گرفتن متغیر محلی — Pylance می‌داند این None نیست
        player = self._player
        if player is None:
            print("   → player None است، پرش به منو")
            QTimer.singleShot(300, self._go_to_menu)
            return

        # پخش ویدیو
        try:
            player.setSource(QUrl.fromLocalFile(video_path))
            player.mediaStatusChanged.connect(
                self._on_media_status
            )
            player.errorOccurred.connect(self._on_error)
            player.play()
            print(f"🎬 در حال پخش ویدیو: {VIDEO_FILE}")

            # ✅ تایمر ایمنی — به‌عنوان QTimer جدا (نه singleShot)
            #    تا اگر لازم شد بتوانیم لغو کنیم
            self._safety_timer = QTimer(self)
            self._safety_timer.setSingleShot(True)
            self._safety_timer.timeout.connect(self._safety_check)
            self._safety_timer.start(SAFETY_TIMEOUT_MS)
        except Exception as e:
            print(f"⚠️ خطا در پخش ویدیو: {e}")
            QTimer.singleShot(300, self._go_to_menu)

    def _init_player(self) -> bool:
        """راه‌اندازی QMediaPlayer برای ویدیو"""
        try:
            if self._video_widget is None:
                return False

            self._player = QMediaPlayer()

            self._audio_output = QAudioOutput()
            self._audio_output.setVolume(VIDEO_VOLUME)
            self._player.setAudioOutput(self._audio_output)

            self._player.setVideoOutput(self._video_widget)
            return True
        except Exception as e:
            print(f"⚠️ خطا در راه‌اندازی player: {e}")
            return False

    def _show_fallback(self):
        """نمایش متن fallback"""
        if self._video_widget is not None:
            self._video_widget.setVisible(False)
        if self.fallback_label is not None:
            self.fallback_label.setVisible(True)

    # ================================================================
    def _on_media_status(self, status):
        """
        شناسایی پایان ویدیو.
        ✅ نکته‌ی کلیدی: این callback داخل event loop خود
        QMediaPlayer اجرا می‌شود. نباید مستقیماً change_scene
        را صدا بزنیم، وگرنه deadlock می‌شود. بنابراین از
        QTimer.singleShot(0, ...) برای تعویق به tick بعدی استفاده می‌کنیم.
        """
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            print("✓ ویدیو تمام شد")
            # ✅ تعویق به tick بعدی event loop
            QTimer.singleShot(0, self._go_to_menu)

    def _on_error(self, error, error_string):
        print(f"⚠️ خطای ویدیو: {error} — {error_string}")
        QTimer.singleShot(0, self._go_to_menu)

    def _safety_check(self):
        """اگر بعد از ۱۰ ثانیه هنوز تمام نشده، پرش کن"""
        if not self._finished:
            print("⚠️ زمان ویدیو طول کشید — پرش ایمنی")
            self._go_to_menu()

    def _skip(self):
        """پرش توسط کاربر"""
        if self._finished:
            return
        print("⏭ کاربر ویدیو را رد کرد")
        QTimer.singleShot(0, self._go_to_menu)

    def _go_to_menu(self):
        """رفتن به منو"""
        if self._finished:
            return
        self._finished = True

        # لغو تایمر ایمنی
        if self._safety_timer is not None:
            try:
                self._safety_timer.stop()
            except Exception:
                pass

        # ✅ توقف player — بدون setSource(QUrl())
        #    setSource جدید در callback فعلی باعث deadlock می‌شود
        player = self._player
        if player is not None:
            try:
                player.stop()
            except Exception:
                pass
            # ✅ قطع سیگنال‌ها — تا callback دوباره اجرا نشود
            try:
                player.mediaStatusChanged.disconnect()
            except Exception:
                pass
            try:
                player.errorOccurred.disconnect()
            except Exception:
                pass

        self.change_scene("menu")

    def on_exit(self):
        """پاک‌سازی هنگام خروج"""
        if self._safety_timer is not None:
            try:
                self._safety_timer.stop()
            except Exception:
                pass

        player = self._player
        if player is not None:
            try:
                player.stop()
            except Exception:
                pass