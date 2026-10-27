"""
صحنه‌ی شب‌های ایستگاه
- بین هر دو فاز، یک شب اختیاری
- بازیکن یکی از سه فعالیت را انتخاب می‌کند
- هر فعالیت، دیالوگ مخصوص به خود + اثر روابط دارد

نسخه: 1.0.0
"""
import os
import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from scenes.base_scene import BaseScene
from widgets.dialogue_widget import DialogueWidget
from widgets.hud_widget import HUDWidget
from widgets.procedural_background import ProceduralBackground
from config import DATA_DIR, PHASE_THEMES

FONT_FAMILY = "Vazirmatn"


class NightScene(BaseScene):
    """صحنه‌ی شب ایستگاه"""

    def __init__(self, game_manager):
        super().__init__(game_manager)

        self.night_number: int = 1
        self.next_scene: str = "menu"
        self.next_scene_kwargs: dict = {}

        self.data: dict = {}
        self.current_state: str = "choosing"
        self._current_dialogues: list = []
        self._current_dialogue_index: int = 0

        self.dialogue_widget = DialogueWidget(
            data_logger=self.data_logger
        )
        self.hud = HUDWidget()

        self._setup_ui()
        print("✓ NightScene راه‌اندازی شد")

    # ================================================================
    def _setup_ui(self):
        main_layout = self.main_layout
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.hud.set_mission("ایستگاه کاسپین")
        self.hud.set_phase("شب ایستگاه")
        self.hud.set_phase_color("#4FC3F7")
        self.hud.set_objective("لحظه‌ای برای خودت")
        main_layout.addWidget(self.hud)

        # QScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(
            "QScrollArea { background-color: transparent; "
            "border: none; }"
        )

        # ✅ پس‌زمینه‌ی رویه‌ای — شب
        self.scroll_content = ProceduralBackground("night")
        self.center_layout = QVBoxLayout(self.scroll_content)
        self.center_layout.setContentsMargins(80, 30, 80, 30)
        self.center_layout.setSpacing(16)

        # عنوان
        self.title_label = QLabel()
        tf = QFont(FONT_FAMILY, 30)
        tf.setBold(True)
        self.title_label.setFont(tf)
        self.title_label.setStyleSheet("color: #4FC3F7;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.center_layout.addWidget(self.title_label)

        # زیرعنوان
        self.subtitle_label = QLabel()
        sf = QFont(FONT_FAMILY, 16)
        self.subtitle_label.setFont(sf)
        self.subtitle_label.setStyleSheet("color: #FF8F00;")
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.center_layout.addWidget(self.subtitle_label)

        # متن مقدمه
        self.intro_label = QLabel()
        self.intro_label.setFont(QFont(FONT_FAMILY, 12))
        self.intro_label.setStyleSheet(
            "color: #CCCCCC; padding: 12px; "
            "background-color: rgba(26, 42, 74, 0.4); "
            "border: 1px solid #2B4A6F; border-radius: 8px;"
        )
        self.intro_label.setWordWrap(True)
        self.intro_label.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.intro_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignAbsolute
        )
        self.intro_label.setMinimumHeight(70)
        self.center_layout.addWidget(self.intro_label)

        # دکمه‌های فعالیت
        self.activities_layout = QVBoxLayout()
        self.activities_layout.setSpacing(10)
        self.center_layout.addLayout(self.activities_layout)

        # ویجت دیالوگ (برای فعالیت انتخابی)
        self.center_layout.addWidget(self.dialogue_widget)
        self.dialogue_widget.setVisible(False)

        # راهنما
        self.hint_label = QLabel(
            "▼  برای ادامه، Space بزنید یا کلیک کنید"
        )
        self.hint_label.setFont(QFont(FONT_FAMILY, 11))
        self.hint_label.setStyleSheet(
            "color: #4FC3F7; background: transparent; "
            "border: none; padding: 6px;"
        )
        self.hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hint_label.setVisible(False)
        self.center_layout.addWidget(self.hint_label)

        self.center_layout.addStretch()
        scroll.setWidget(self.scroll_content)
        main_layout.addWidget(scroll, stretch=1)

    # ================================================================
    def on_enter(self, **kwargs):
        self.night_number = int(kwargs.get("night_number", 1))
        self.next_scene = str(kwargs.get("next_scene", "menu"))
        self.next_scene_kwargs = (
            kwargs.get("next_scene_kwargs", {}) or {}
        )

        print(
            f"✓ ورود به شب {self.night_number} — "
            f"next={self.next_scene}"
        )

        self.data_logger.log_event(
            scene_id="night",
            scenario_id=f"night_{self.night_number}",
            event_type="scene_enter",
            metadata={"next_scene": self.next_scene}
        )

        # بارگذاری داده
        self.data = self._load_night_data(self.night_number)
        if not self.data:
            print(
                f"⚠️ داده‌ی شب {self.night_number} یافت نشد — "
                "پرش مستقیم"
            )
            self._go_to_next()
            return

        # تنظیم محتوا
        self.title_label.setText(self.data.get("title", ""))
        self.subtitle_label.setText(self.data.get("subtitle", ""))
        self.intro_label.setText(self.data.get("intro", ""))

        # ساخت دکمه‌های فعالیت
        self._build_activity_buttons()

        # نمایش حالت اولیه
        self.current_state = "choosing"
        self.dialogue_widget.setVisible(False)
        self.hint_label.setVisible(False)
        self.intro_label.setVisible(True)
        self.setFocus()

    # ================================================================
    def _load_night_data(self, night_number: int) -> dict:
        path = os.path.join(DATA_DIR, "night_dialogues.json")
        if not os.path.exists(path):
            print(f"⚠️ فایل شب‌ها یافت نشد: {path}")
            return {}

        try:
            with open(path, "r", encoding="utf-8") as f:
                all_nights = json.load(f)
        except Exception as e:
            print(f"⚠️ خطا در بارگذاری شب‌ها: {e}")
            return {}

        key = f"night_{night_number}"
        return all_nights.get(key, {})

    # ================================================================
    def _clear_activities_layout(self):
        while self.activities_layout.count():
            item = self.activities_layout.takeAt(0)
            if item is None:
                continue
            w = item.widget()
            if w is not None:
                w.deleteLater()

    def _build_activity_buttons(self):
        self._clear_activities_layout()

        activities = self.data.get("activities", {})
        # ترتیب: لی، آرتمیس، ستاره‌ها
        order = ["li", "artemis", "stars"]

        for key in order:
            activity = activities.get(key)
            if not activity:
                continue
            btn = self._make_activity_button(
                activity.get("label", key),
                activity.get("hint", ""),
                key,
            )
            self.activities_layout.addWidget(btn)

    def _make_activity_button(self, label: str, hint: str,
                               key: str) -> QPushButton:
        # ✅ RLM قبل از هر خط — متن چندخطی QPushButton
        #    را راست‌چین می‌کند
        RLM = "\u200F"
        if hint:
            text = f"{RLM}{label}\n{RLM}{hint}"
        else:
            text = f"{RLM}{label}"

        btn = QPushButton(text)
        btn.setFont(QFont(FONT_FAMILY, 13))
        btn.setMinimumHeight(70)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        # ⚠️ text-align از QSS حذف شد — با multiline کار نمی‌کند
        btn.setStyleSheet("""
            QPushButton {
                background-color: #1A2A4A;
                color: #FFFFFF;
                border: 2px solid #4FC3F7;
                border-radius: 10px;
                padding: 10px 16px;
            }
            QPushButton:hover {
                background-color: #2B4A6F;
                border: 2px solid #FFFFFF;
            }
        """)
        btn.clicked.connect(lambda _, k=key: self._on_activity_chosen(k))
        return btn

    # ================================================================
    def _on_activity_chosen(self, activity_key: str):
        if self.current_state != "choosing":
            return
        if not self.data:
            return

        activity = self.data.get("activities", {}).get(activity_key)
        if not activity:
            return

        # ثبت انتخاب
        self.data_logger.log_event(
            scene_id="night",
            scenario_id=f"night_{self.night_number}_activity",
            event_type="choice_made",
            metadata={"activity": activity_key}
        )

        # اعمال اثر بر روابط
        effect = activity.get("effect", {}) or {}
        for character, delta in effect.items():
            try:
                self.data_logger.adjust_relationship(
                    character, int(delta)
                )
            except Exception as e:
                print(f"⚠️ خطا در تنظیم رابطه: {e}")

        # پنهان کردن دکمه‌ها و مقدمه
        self._clear_activities_layout()
        self.intro_label.setVisible(False)

        # راه‌اندازی دیالوگ‌های فعالیت
        self._current_dialogues = activity.get("dialogues", []) or []
        self._current_dialogue_index = 0
        self.current_state = "dialogue"
        self.dialogue_widget.setVisible(True)
        self.hint_label.setVisible(True)
        self._show_current_dialogue()

    def _show_current_dialogue(self):
        if self._current_dialogue_index >= len(self._current_dialogues):
            # پایان فعالیت — به صحنه‌ی بعد
            self._go_to_next()
            return

        dlg = self._current_dialogues[self._current_dialogue_index]
        speaker = str(dlg.get("speaker", ""))
        text = str(dlg.get("text", dlg.get("text_fa", "")))

        self.dialogue_widget.show_dialogue(
            speaker_name=speaker, text=text
        )
        self.setFocus()

    # ================================================================
    def _advance_dialogue(self):
        """پیشروی در دنباله‌ی دیالوگ‌ها"""
        if self.dialogue_widget.is_typing():
            self.dialogue_widget.advance()
            return
        self._current_dialogue_index += 1
        self._show_current_dialogue()

    # ================================================================
    def _go_to_next(self):
        """رفتن به صحنه‌ی بعد"""
        # ✅ ثبت شب تکمیل‌شده
        if hasattr(self.game_manager, "add_night_completed"):
            self.game_manager.add_night_completed(self.night_number)

        try:
            self.change_scene(
                self.next_scene, **self.next_scene_kwargs
            )
        except Exception as e:
            print(f"⚠️ خطا در رفتن به {self.next_scene}: {e}")

    # ================================================================
    def mousePressEvent(self, event):  # type: ignore
        if self.current_state == "dialogue":
            self._advance_dialogue()
        super().mousePressEvent(event)

    def keyPressEvent(self, event):  # type: ignore
        if event.key() in (
            Qt.Key.Key_Space,
            Qt.Key.Key_Return,
            Qt.Key.Key_Enter,
        ):
            if self.current_state == "dialogue":
                self._advance_dialogue()
        else:
            super().keyPressEvent(event)