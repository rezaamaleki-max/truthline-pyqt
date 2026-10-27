"""
ویجت پخش ویدیو کوتاه
- لوپ‌پذیر
- بدون صدا
- با fallback به تصویر ثابت
- فقط در صورت وجود فایل فعال می‌شود
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QUrl, QTimer
from PyQt6.QtGui import QPixmap
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
import os

from config import ASSETS_DIR


class VideoWidget(QWidget):
    """پخش ویدیوی کوتاه با fallback به تصویر"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._player: QMediaPlayer | None = None
        self._video_widget: QVideoWidget | None = None
        self._image_label: QLabel | None = None
        self._current_source: str = ""

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ✅ ویجت ویدیو
        try:
            self._video_widget = QVideoWidget()
            self._video_widget.setStyleSheet(
                "background-color: #050A18;"
            )
            layout.addWidget(self._video_widget)

            self._player = QMediaPlayer()
            audio_out = QAudioOutput()
            audio_out.setVolume(0.0)   # ✅ بی‌صدا
            self._player.setAudioOutput(audio_out)
            self._player.setVideoOutput(self._video_widget)
            self._player.setLoops(
                QMediaPlayer.Loops.Infinite
            )
        except Exception as e:
            print(f"⚠️ QMediaPlayer راه‌اندازی نشد: {e}")

        # ✅ لیبل تصویر (fallback)
        self._image_label = QLabel()
        self._image_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self._image_label.setStyleSheet(
            "background: transparent; border: none;"
        )
        self._image_label.setVisible(False)
        layout.addWidget(self._image_label)

    def play_video_or_image(
        self,
        video_name: str | None,
        image_name: str | None,
    ):
        """
        تلاش برای پخش ویدیو — اگر نبود، تصویر — اگر نبود، هیچ.
        """
        self.stop()

        # تلاش برای ویدیو
        if video_name:
            video_path = os.path.join(
                ASSETS_DIR, "videos", video_name
            )
            if (
                os.path.exists(video_path)
                and self._player is not None
                and self._video_widget is not None
            ):
                try:
                    self._player.setSource(
                        QUrl.fromLocalFile(video_path)
                    )
                    self._player.play()
                    self._video_widget.setVisible(True)
                    if self._image_label is not None:
                        self._image_label.setVisible(False)
                    self._current_source = f"video:{video_name}"
                    print(f"🎬 در حال پخش ویدیو: {video_name}")
                    return
                except Exception as e:
                    print(
                        f"⚠️ خطا در پخش ویدیو {video_name}: {e}"
                    )

        # fallback به تصویر
        if image_name:
            image_path = os.path.join(
                ASSETS_DIR, "videos", image_name
            )
            if os.path.exists(image_path):
                pixmap = QPixmap(image_path)
                if not pixmap.isNull():
                    # مقیاس‌دهی
                    scaled = pixmap.scaled(
                        900, 200,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                    if self._image_label is not None:
                        self._image_label.setPixmap(scaled)
                        self._image_label.setVisible(True)
                    if self._video_widget is not None:
                        self._video_widget.setVisible(False)
                    self._current_source = f"image:{image_name}"
                    print(f"🖼 در حال نمایش تصویر: {image_name}")
                    return

        # هیچ‌کدام نبود
        self._current_source = ""
        if self._image_label is not None:
            self._image_label.setVisible(False)
        if self._video_widget is not None:
            self._video_widget.setVisible(False)

    def stop(self):
        """توقف پخش"""
        if self._player is not None:
            try:
                self._player.stop()
                self._player.setSource(QUrl())
            except Exception:
                pass
        self._current_source = ""

    def on_enter(self):
        """هنگام ورود به صحنه"""
        if self._player is not None and self._current_source:
            try:
                self._player.play()
            except Exception:
                pass

    def on_exit(self):
        """هنگام خروج از صحنه"""
        if self._player is not None:
            try:
                self._player.pause()
            except Exception:
                pass