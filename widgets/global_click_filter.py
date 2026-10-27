"""
فیلتر سراسری صدای کلیک — روی همه‌ی QPushButton ها
====================================================
با نصب این فیلتر روی QApplication، هر کلیک روی هر دکمه‌ای
در هر صحنه، صدای کلیک را پخش می‌کند.

نسخه: 1.0.1 — نام پارامترها با کلاس پایه QObject سازگار شد
"""
from PyQt6.QtCore import QObject, QEvent
from PyQt6.QtWidgets import QPushButton


class GlobalClickSoundFilter(QObject):
    """فیلتر سراسری برای صدای کلیک"""

    # ✅ نام پارامترها دقیقاً مثل کلاس پایه QObject
    def eventFilter(self, a0, a1):  # type: ignore[override]
        # a0 = obj (ویجت هدف), a1 = event (رویداد)
        try:
            if a1 is not None and a1.type() == QEvent.Type.MouseButtonRelease:
                if isinstance(a0, QPushButton):
                    if a0.isEnabled():
                        from core.audio_manager import (
                            get_audio_manager
                        )
                        get_audio_manager().play_sfx("click")
        except Exception:
            pass

        return super().eventFilter(a0, a1)


def install_global_click_filter(app):
    """نصب فیلتر روی QApplication"""
    global _filter_instance
    try:
        _filter_instance = GlobalClickSoundFilter(app)
        app.installEventFilter(_filter_instance)
        print("✓ GlobalClickSoundFilter نصب شد")
    except Exception as e:
        print(f"⚠️ خطا در نصب فیلتر صدای کلیک: {e}")


# نگه‌داری مرجع قوی
_filter_instance = None