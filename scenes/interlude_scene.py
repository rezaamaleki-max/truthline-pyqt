"""
صحنه میان‌پرده — انتقال بین فازها
- پشتیبانی از چند دیالوگ پیوسته (dialogue_sequence)
- سازگار با API قدیمی (dialogue_speaker + dialogue_text)
- دنباله‌ی خودکار با Space یا کلیک
- لحظه‌ی سکوت بین دیالوگ‌ها

نسخه: 2.0.0
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPixmap, QShortcut, QKeySequence
import os

from scenes.base_scene import BaseScene
from widgets.hud_widget import HUDWidget
from widgets.procedural_background import ProceduralBackground
from config import ASSETS_DIR

FONT_FAMILY = "Vazirmatn"


class InterludeScene(BaseScene):
    """میان‌پرده روایی بین فازها — با پشتیبانی از چند دیالوگ"""

    def __init__(self, game_manager):
        super().__init__(game_manager)
        self.next_scene: str = "menu"
        self.video_path: str | None = None

        self.current_title: str = ""
        self.current_subtitle: str = ""
        self.current_body: str = ""

        # ✅ دنباله‌ی دیالوگ‌ها
        self._dialogues: list = []
        self._dialogue_index: int = 0

        # ✅ kwargs برای صحنه‌ی بعدی (پاس‌دهی)
        self._next_scene_kwargs: dict = {}

        self._setup_ui()

        self._space_shortcut = QShortcut(
            QKeySequence(Qt.Key.Key_Space), self
        )
        self._space_shortcut.setContext(
            Qt.ShortcutContext.WindowShortcut
        )
        self._space_shortcut.activated.connect(self._on_continue)

        print("✓ InterludeScene راه‌اندازی شد (نسخه چند‌دیالوگی)")

    def _setup_ui(self):
        main_layout = self.main_layout
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # HUD
        self.hud = HUDWidget()
        self.hud.set_mission("ایستگاه کاسپین")
        main_layout.addWidget(self.hud)

        # QScrollArea برای محتوای بلند
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(
            "QScrollArea { background-color: #0B1D3A; border: none; }"
        )

        # ✅ پس‌زمینه‌ی رویه‌ای — فضا
        center = ProceduralBackground("space")
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(60, 20, 60, 20)
        center_layout.setSpacing(14)

        # فضای ویدیو
        self.video_frame = QFrame()
        self.video_frame.setMinimumHeight(180)
        self.video_frame.setMaximumHeight(220)
        self.video_frame.setStyleSheet("""
            QFrame {
                background-color: #050A18;
                border: 2px solid #2B4A6F;
                border-radius: 10px;
            }
        """)
        video_layout = QVBoxLayout(self.video_frame)
        video_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.video_placeholder = QLabel("▶  [صحنه سینمایی]")
        self.video_placeholder.setStyleSheet(
            "color: #4FC3F7; font-size: 18px; "
            "background: transparent; border: none;"
        )
        self.video_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        video_layout.addWidget(self.video_placeholder)

        self.video_image = QLabel()
        self.video_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_image.setStyleSheet(
            "background: transparent; border: none;"
        )
        self.video_image.setVisible(False)
        video_layout.addWidget(self.video_image)

        center_layout.addWidget(self.video_frame)

        # عنوان روز
        self.title_label = QLabel()
        tf = QFont(FONT_FAMILY, 32)
        tf.setBold(True)
        self.title_label.setFont(tf)
        self.title_label.setStyleSheet("color: #4FC3F7;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(self.title_label)

        # زیرعنوان
        self.subtitle_label = QLabel()
        sf = QFont(FONT_FAMILY, 18)
        self.subtitle_label.setFont(sf)
        self.subtitle_label.setStyleSheet("color: #FF8F00;")
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(self.subtitle_label)

        # متن روایی (atmospheric body)
        self.body_label = QLabel()
        from widgets.typography import make_narrative
        self.body_label.setFont(make_narrative(14))
        self.body_label.setStyleSheet("color: #CCCCCC;")
        # ✅ RTL برای متن فارسی
        self.body_label.setLayoutDirection(
            Qt.LayoutDirection.RightToLeft
        )
        self.body_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignAbsolute
        )
        self.body_label.setWordWrap(True)
        self.body_label.setMinimumHeight(50)
        center_layout.addWidget(self.body_label)

        # کادر دیالوگ
        self.dialogue_frame = QFrame()
        self.dialogue_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(26, 42, 74, 0.85);
                border: 2px solid #4FC3F7;
                border-radius: 10px;
            }
        """)
        dialogue_layout = QVBoxLayout(self.dialogue_frame)
        dialogue_layout.setContentsMargins(18, 12, 18, 12)
        dialogue_layout.setSpacing(6)

        self.speaker_label = QLabel()
        spf = QFont(FONT_FAMILY, 13)
        spf.setBold(True)
        self.speaker_label.setFont(spf)
        self.speaker_label.setStyleSheet(
            "color: #4FC3F7; border: none; background: transparent;"
        )
        self.speaker_label.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.speaker_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignAbsolute
        )
        dialogue_layout.addWidget(self.speaker_label)

        self.dialogue_label = QLabel()
        from widgets.typography import make_narrative
        self.dialogue_label.setFont(make_narrative(15))
        self.dialogue_label.setStyleSheet(
            "color: #FFFFFF; border: none; background: transparent;"
        )
        # ✅ RTL برای متن فارسی
        self.dialogue_label.setLayoutDirection(
            Qt.LayoutDirection.RightToLeft
        )
        self.dialogue_label.setWordWrap(True)
        self.dialogue_label.setMinimumHeight(60)
        self.dialogue_label.setAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignAbsolute
            | Qt.AlignmentFlag.AlignTop
        )
        dialogue_layout.addWidget(self.dialogue_label)

        center_layout.addWidget(self.dialogue_frame)

        # نشانگر ادامه — فلش کوچک
        self.hint_label = QLabel("▼  برای ادامه، Space بزنید یا کلیک کنید")
        hf = QFont(FONT_FAMILY, 11)
        self.hint_label.setFont(hf)
        self.hint_label.setStyleSheet(
            "color: #4FC3F7; background: transparent; "
            "border: none; padding: 6px;"
        )
        self.hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(self.hint_label)

        center_layout.addStretch()

        scroll.setWidget(center)
        main_layout.addWidget(scroll, stretch=1)

    # ------------------------------------------------------------------
    def _type_text_in(self, label: QLabel, full_text: str,
                       duration_ms: int = 1500):
        if not full_text:
            label.setText("")
            return

        # ✅ حالت سریع: نمایش فوری متن
        from core.app_config import get_fast_mode
        if get_fast_mode():
            label.setText(full_text)
            return

        # اگر حالت کاهش انیمیشن فعال است، بدون تایپ
        try:
            from core.app_config import get_accessibility_settings
            acc = get_accessibility_settings()
            if acc["reduce_motion"]:
                label.setText(full_text)
                return
        except Exception:
            pass

        # ✅ تقسیم به کلمات
        words = full_text.split(" ")
        n = len(words)
        if n == 0:
            label.setText("")
            return

        # فاصله بین هر کلمه
        interval = max(60, duration_ms // n)

        label.setText("")
        counter = {"i": 0}
        timer = QTimer(self)

        def _tick():
            i = counter["i"]
            if i >= n:
                timer.stop()
                label.setText(full_text)
                return
            counter["i"] += 1
            partial = " ".join(words[:counter["i"]])
            label.setText(partial)

        timer.timeout.connect(_tick)
        timer.start(interval)

        if not hasattr(self, "_type_timers"):
            self._type_timers = []
        self._type_timers.append(timer)

    def _stop_type_timers(self):
        """متوقف کردن همه‌ی تایمرهای تایپ"""
        if not hasattr(self, "_type_timers"):
            return
        for t in self._type_timers:
            try:
                t.stop()
            except Exception:
                pass
        self._type_timers = []

    # ------------------------------------------------------------------
    def on_enter(self, **kwargs):
        next_scene_val = kwargs.get("next_scene", "menu")
        self.next_scene = (
            str(next_scene_val) if next_scene_val else "menu"
        )

        # ✅ ذخیره‌ی kwargs برای صحنه‌ی بعدی
        self._next_scene_kwargs = (
            kwargs.get("next_scene_kwargs", {}) or {}
        )

        self.current_title = str(kwargs.get("title", ""))
        self.current_subtitle = str(kwargs.get("subtitle", ""))
        self.current_body = str(kwargs.get("body_text", ""))

        video_path_val = kwargs.get("video_path", None)
        self.video_path = (
            str(video_path_val) if video_path_val else None
        )

        # ✅ دیباگ موقت — برای تشخیص مسیر تصویر
        print(
            f"   [VIDEO-DEBUG] video_path دریافت‌شده: "
            f"{video_path_val!r}"
        )
        print(
            f"   [VIDEO-DEBUG] self.video_path نهایی: "
            f"{self.video_path!r}"
        )

        # ✅ ساخت دنباله‌ی دیالوگ‌ها
        # حالت ۱: caller یک لیست از dialogues داده
        dialogues_raw = kwargs.get("dialogues", None)
        if isinstance(dialogues_raw, list) and dialogues_raw:
            self._dialogues = list(dialogues_raw)
        else:
            # حالت ۲: API قدیمی — یک دیالوگ
            speaker = str(kwargs.get("dialogue_speaker", ""))
            text = str(kwargs.get("dialogue_text", ""))
            if speaker or text:
                self._dialogues = [
                    {"speaker": speaker, "text": text}
                ]
            else:
                self._dialogues = []

        self._dialogue_index = 0

        # HUD
        self.hud.set_phase(self.current_title)
        self.hud.set_objective(self.current_subtitle)
        self.hud.hide_scenario_progress()

        # ✅ بازیابی پیشرفت مأموریت از scene قبلی
        try:
            gm = self.game_manager
            last_pct = getattr(gm, "_last_progress_pct", None)
            if last_pct is None:
                # fallback: محاسبه از فازهای تکمیل‌شده
                completed = len(gm._flags.get("phases_completed", []))
                last_pct = int((completed / 4.0) * 100)
            self.hud.set_progress(max(0, min(100, last_pct)))
        except Exception as e:
            print(f"⚠️ خطا در بازیابی پیشرفت: {e}")

        # ✅ متوقف کردن تایمرهای تایپ قبلی
        self._stop_type_timers()

        # محتوا — عنوان‌ها فوری
        self.title_label.setText(self.current_title)
        self.subtitle_label.setText(self.current_subtitle)

        # ✅ متن روایی با انیمیشن تایپ
        self._type_text_in(
            self.body_label, self.current_body,
            duration_ms=1800,
        )

        # نمایش اولین دیالوگ
        self._show_current_dialogue()

        self._try_load_video()

        self.data_logger.log_event(
            scene_id="interlude",
            scenario_id=f"interlude_{self.current_title}",
            event_type="scene_enter",
            metadata={
                "next_scene": self.next_scene,
                "dialogue_count": len(self._dialogues),
            }
        )

        # اسکرول به بالا
        for scroll in self.findChildren(QScrollArea):
            vbar = scroll.verticalScrollBar()
            if vbar is not None:
                vbar.setValue(0)

        self.setFocus()

    # ------------------------------------------------------------------
    def _show_current_dialogue(self):
        """نمایش دیالوگ فعلی از دنباله"""
        if not self._dialogues:
            self.dialogue_frame.setVisible(False)
            return

        if self._dialogue_index >= len(self._dialogues):
            self.dialogue_frame.setVisible(False)
            return

        dlg = self._dialogues[self._dialogue_index]
        speaker = str(dlg.get("speaker", ""))
        text = str(dlg.get("text", dlg.get("text_fa", "")))

        self.dialogue_frame.setVisible(True)
        self.speaker_label.setText(speaker)

        # ✅ دیالوگ با انیمیشن تایپ
        self._type_text_in(
            self.dialogue_label, text,
            duration_ms=2200,
        )

        # رنگ گوینده بر اساس character_registry
        try:
            from core.character_registry import get_character
            char_color = get_character(speaker).get("color", "#4FC3F7")
        except Exception:
            char_color = "#4FC3F7"

        self.speaker_label.setStyleSheet(f"""
            QLabel {{
                color: {char_color};
                border: none;
                background: transparent;
            }}
        """)

        # به‌روزرسانی متن راهنما بر اساس جایگاه
        if self._dialogue_index < len(self._dialogues) - 1:
            self.hint_label.setText(
                "▼  برای ادامه، Space بزنید یا کلیک کنید"
            )
        else:
            self.hint_label.setText(
                "▼  برای ادامه به صحنه‌ی بعد، Space بزنید"
            )

    def _try_load_video(self):
        # ✅ دیباگ موقت — برای عیب‌یابی مسیر تصویر
        print(f"   [VIDEO] video_path = {self.video_path}")

        if not self.video_path:
            print("   [VIDEO] video_path خالی است — placeholder")
            self.video_placeholder.setVisible(True)
            self.video_image.setVisible(False)
            return

        full_path = os.path.join(
            ASSETS_DIR, "videos", self.video_path
        )
        print(f"   [VIDEO] جستجو در: {full_path}")
        print(f"   [VIDEO] وجود فایل: {os.path.exists(full_path)}")

        if os.path.exists(full_path) and full_path.lower().endswith(
            (".png", ".jpg", ".jpeg")
        ):
            pixmap = QPixmap(full_path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(
                    900, 200,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.video_image.setPixmap(scaled)
                self.video_image.setVisible(True)
                self.video_placeholder.setVisible(False)
                return

        self.video_placeholder.setVisible(True)
        self.video_image.setVisible(False)

    # ------------------------------------------------------------------
    def _on_continue(self):
        """پیشروی در دنباله‌ی دیالوگ‌ها یا انتقال به صحنه‌ی بعد"""
        if self._dialogue_index < len(self._dialogues) - 1:
            # دیالوگ بعدی
            self._dialogue_index += 1
            self._show_current_dialogue()
            self.data_logger.log_event(
                scene_id="interlude",
                scenario_id=f"interlude_{self.current_title}_next",
                event_type="dialogue_advanced",
                metadata={"index": self._dialogue_index}
            )
            return

        # پایان دنباله — انتقال به صحنه‌ی بعد
        self.data_logger.log_event(
            scene_id="interlude",
            scenario_id=f"interlude_{self.current_title}_continue",
            event_type="button_click",
            metadata={"next_scene": self.next_scene}
        )
        self.change_scene(
            self.next_scene, **self._next_scene_kwargs
        )

    def mousePressEvent(self, event):  # type: ignore[reportIncompatibleMethodOverride]
        self._on_continue()
        super().mousePressEvent(event)

    def keyPressEvent(self, event):  # type: ignore[reportIncompatibleMethodOverride]
        if event.key() in (
            Qt.Key.Key_Space,
            Qt.Key.Key_Return,
            Qt.Key.Key_Enter,
        ):
            self._on_continue()
        elif event.key() == Qt.Key.Key_Escape:
            self.change_scene("menu")
        else:
            super().keyPressEvent(event)