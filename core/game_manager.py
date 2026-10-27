"""
مدیریت صحنه‌های بازی با استفاده از QStackedWidget
این کلاس مسئول جابجایی بین صحنه‌های مختلف بازی است.

نسخه: 2.1.0 (PyQt6 - رفع باگ QGraphicsOpacityEffect)
"""
from PyQt6.QtWidgets import (
    QStackedWidget, QGraphicsOpacityEffect
)
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QTimer
from typing import Dict, Optional

from scenes.base_scene import BaseScene


class GameManager:
    """مدیریت‌کننده مرکزی صحنه‌های بازی"""

    def __init__(self, main_window, data_logger):
        self.main_window = main_window
        self.data_logger = data_logger

        # ویجت اصلی که تمام صحنه‌ها را در خود نگه می‌دارد
        self.stacked_widget = QStackedWidget()

        self.scenes: Dict[str, BaseScene] = {}
        self.current_scene_name: Optional[str] = None

        # ✅ نگه‌داری مرجع قوی به انیمیشن‌ها و effectها
        #    (جلوگیری از حذف خودکار توسط garbage collector)
        self._current_anim: QPropertyAnimation | None = None
        self._current_effect: QGraphicsOpacityEffect | None = None

        # ✅ فلگ برای جلوگیری از فراخوانی همزمان
        self._is_transitioning: bool = False

        # ✅ وضعیت ذخیره‌ی خودکار
        self._scenario_indices: dict = {
            "phase1": 0, "phase2": 0, "phase3": 0, "phase4": 0,
        }
        self._flags: dict = {
            "council_prep_shown": False,
            "letter_shown": False,
            "nights_completed": [],
            "phases_completed": [],
        }

        print("✓ GameManager راه‌اندازی شد")

    # ================================================================
    def add_scene(self, name: str, scene_widget: BaseScene):
        """افزودن یک صحنه جدید"""
        if name in self.scenes:
            print(f"⚠️ هشدار: صحنه '{name}' قبلاً ثبت شده")
        self.scenes[name] = scene_widget
        self.stacked_widget.addWidget(scene_widget)
        print(f"✓ صحنه '{name}' اضافه شد")

    def _trigger_glitch(self, scene_name: str):
        """اجرای افکت glitch قبل از تغییر فاز"""
        try:
            from core.app_config import get_fast_mode
            if get_fast_mode():
                return  # ✅ در حالت سریع، افکت اجرا نشود
            
            from widgets.glitch_overlay import GlitchOverlay
            overlay = GlitchOverlay(self.stacked_widget)
            overlay.setGeometry(self.stacked_widget.rect())

            color_map = {
                "phase1": "#4FC3F7",
                "phase2": "#FF8F00",
                "phase3": "#9C27B0",
                "phase4": "#D32F2F",
            }
            color = color_map.get(scene_name, "#4FC3F7")
            overlay.start(duration_ms=500, color=color)
        except Exception as e:
            print(f"⚠️ خطا در glitch: {e}")

    # ================================================================
    def change_scene(self, scene_name: str, **kwargs):
        """تغییر صحنه فعال — با Glitch بین فازها"""
        if scene_name not in self.scenes:
            print(f"❌ خطا: صحنه '{scene_name}' یافت نشد.")
            print(f"   صحنه‌های موجود: {list(self.scenes.keys())}")
            return

        # ✅ تشخیص انتقال بین فازها
        is_phase_transition = (
            scene_name.startswith("phase") and
            self.current_scene_name is not None and
            self.current_scene_name.startswith("phase") and
            scene_name != self.current_scene_name
        )

        # ✅ اجرای glitch در انتقال بین فازها
        if is_phase_transition:
            self._trigger_glitch(scene_name)

        # اگر همان صحنه فعلی است، دوباره تغییر نده
        if (self.current_scene_name == scene_name
                and self.stacked_widget.currentWidget()
                    is self.scenes[scene_name]):
            return

        # به‌روزرسانی صدا
        try:
            from core.audio_manager import get_audio_manager
            audio = get_audio_manager()
            audio.play_sfx("transition")
            audio.on_scene_changed(scene_name)
        except Exception as e:
            print(f"⚠️ خطا در صدا: {e}")

        # ثبت خروج
        prev = self.current_scene_name
        if prev:
            self.data_logger.log_event(
                scene_id=prev,
                scenario_id="scene_transition",
                event_type="scene_exit",
                metadata={"next_scene": scene_name}
            )

        # on_exit صحنه قبلی
        if prev and prev in self.scenes:
            try:
                current_scene = self.scenes[prev]
                if hasattr(current_scene, 'on_exit'):
                    current_scene.on_exit()
            except Exception as e:
                print(f"⚠️ خطا در on_exit: {e}")

        new_scene = self.scenes[scene_name]

        # ثبت ورود
        self.data_logger.log_event(
            scene_id=scene_name,
            scenario_id="scene_transition",
            event_type="scene_enter",
            metadata={"previous_scene": prev}
        )

        # سوییچ مستقیم — بدون انیمیشن
        try:
            self.stacked_widget.setCurrentWidget(new_scene)
        except Exception as e:
            print(f"⚠️ خطا در سوییچ: {e}")
            return

        # on_enter
        if hasattr(new_scene, 'on_enter'):
            try:
                new_scene.on_enter(**kwargs)
            except Exception as e:
                print(f"⚠️ خطا در on_enter '{scene_name}': {e}")
                import traceback
                traceback.print_exc()

        self.current_scene_name = scene_name
        print(f"✓ تغییر صحنه به: {scene_name}")
        self.save_session()

    # ================================================================
    def _start_fade_out(self, new_scene, scene_name, kwargs):
        """اجرای Fade-Out امن"""
        try:
            # پاک کردن effect قبلی (اگر وجود دارد)
            self._clear_effect()

            # ساخت effect جدید
            effect_out = QGraphicsOpacityEffect()
            effect_out.setOpacity(1.0)
            self.stacked_widget.setGraphicsEffect(effect_out)
            self._current_effect = effect_out

            # ساخت انیمیشن
            anim_out = QPropertyAnimation(
                effect_out, b"opacity", self.stacked_widget
            )
            from core.app_config import get_fast_mode
            anim_out.setDuration(0 if get_fast_mode() else 180)
            anim_out.setStartValue(1.0)
            anim_out.setEndValue(0.0)
            anim_out.setEasingCurve(QEasingCurve.Type.InOutQuad)

            # ✅ مهم: نگه‌داشتن مرجع قوی
            self._current_anim = anim_out

            # اتصال به callback
            anim_out.finished.connect(
                lambda: self._on_fade_out_done(
                    new_scene, scene_name, kwargs
                )
            )

            anim_out.start()
        except Exception as e:
            print(f"⚠️ خطا در Fade-Out: {e}")
            # در صورت خطا، مستقیم سوییچ کن
            self._is_transitioning = False
            self._do_switch(new_scene, scene_name, kwargs)

    def _on_fade_out_done(self, new_scene, scene_name, kwargs):
        """بعد از پایان Fade-Out — سوییچ صحنه و شروع Fade-In"""
        # پاک کردن effect قدیمی
        self._clear_effect()

        # سوییچ ویجت
        try:
            self.stacked_widget.setCurrentWidget(new_scene)
        except Exception as e:
            print(f"⚠️ خطا در سوییچ ویجت: {e}")
            self._is_transitioning = False
            return

        # اجرای on_enter
        self._call_on_enter(new_scene, scene_name, kwargs)

        # شروع Fade-In
        self._start_fade_in(scene_name)

    def _start_fade_in(self, scene_name):
        """اجرای Fade-In امن"""
        try:
            effect_in = QGraphicsOpacityEffect()
            effect_in.setOpacity(0.0)
            self.stacked_widget.setGraphicsEffect(effect_in)
            self._current_effect = effect_in

            anim_in = QPropertyAnimation(
                effect_in, b"opacity", self.stacked_widget
            )
            from core.app_config import get_fast_mode
            anim_in.setDuration(0 if get_fast_mode() else 220)
            anim_in.setStartValue(0.0)
            anim_in.setEndValue(1.0)
            anim_in.setEasingCurve(QEasingCurve.Type.InOutQuad)

            self._current_anim = anim_in

            anim_in.finished.connect(self._on_fade_in_done)
            anim_in.start()
        except Exception as e:
            print(f"⚠️ خطا در Fade-In: {e}")
            self._is_transitioning = False

    def _on_fade_in_done(self):
        """پایان انیمیشن ورود"""
        self._clear_effect()
        self._is_transitioning = False
        self.save_session()
        print(f"✓ انتقال کامل شد: {self.current_scene_name}")

    # ================================================================
    def _do_switch(self, new_scene, scene_name, kwargs):
        """سوییچ مستقیم بدون انیمیشن"""
        try:
            self.stacked_widget.setCurrentWidget(new_scene)
        except Exception as e:
            print(f"⚠️ خطا در سوییچ ویجت: {e}")
            return

        self._call_on_enter(new_scene, scene_name, kwargs)

    def _call_on_enter(self, new_scene, scene_name, kwargs):
        """اجرای on_enter با محافظت از خطا"""
        if hasattr(new_scene, 'on_enter'):
            try:
                new_scene.on_enter(**kwargs)
            except Exception as e:
                print(f"⚠️ خطا در on_enter صحنه '{scene_name}': {e}")
                import traceback
                traceback.print_exc()

    def _clear_effect(self):
        """پاک کردن effect فعلی با اطمینان"""
        try:
            if self.stacked_widget is not None:
                self.stacked_widget.setGraphicsEffect(None)
        except Exception:
            pass
        self._current_effect = None

    # ================================================================
    def get_current_scene(self) -> Optional[BaseScene]:
        if (self.current_scene_name
                and self.current_scene_name in self.scenes):
            return self.scenes[self.current_scene_name]
        return None

    def get_current_scene_name(self) -> Optional[str]:
        return self.current_scene_name

    def get_scene(self, name: str) -> Optional[BaseScene]:
        return self.scenes.get(name)

    def list_scenes(self) -> list:
        return list(self.scenes.keys())

    # ================================================================
    # ذخیره‌ی خودکار session
    # ================================================================
    def update_scenario_index(self, phase_key: str, index: int):
        if phase_key in self._scenario_indices:
            self._scenario_indices[phase_key] = int(index)

    def set_flag(self, flag_name: str, value):
        if flag_name in self._flags:
            self._flags[flag_name] = value

    def add_night_completed(self, night_number: int):
        nights = self._flags.setdefault("nights_completed", [])
        if night_number not in nights:
            nights.append(night_number)

    def add_phase_completed(self, phase_key: str):
        phases = self._flags.setdefault("phases_completed", [])
        if phase_key not in phases:
            phases.append(phase_key)

    def get_flag(self, flag_name: str, default=None):
        return self._flags.get(flag_name, default)

    def save_session(self):
        try:
            from core.app_config import is_auto_resume_enabled
            if not is_auto_resume_enabled():
                return

            from core.session_state import save_state

            save_state(
                participant_id=self.data_logger.participant_id,
                current_scene=self.current_scene_name or "",
                scenario_indices=self._scenario_indices,
                flags=self._flags,
                relationships=self.data_logger.relationships,
                choice_memory=self.data_logger.choice_memory,
                random_seed=self.data_logger.random_seed,  # ✅ جدید
            )
        except Exception as e:
            print(f"⚠️ خطا در ذخیره‌ی خودکار: {e}")