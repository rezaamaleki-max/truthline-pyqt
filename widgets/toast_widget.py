"""
سیستم اعلان کوچک (Toast) برای بازخورد فوری
- در گوشه بالا-راست ظاهر می‌شود
- بعد از ۲ ثانیه شروع به محو شدن می‌کند
- در ۴۰۰ میلی‌ثانیه به‌طور کامل ناپدید می‌شود

نسخه: 1.2.0
  - رفع باگ: تابع محو شدن که هرگز صدا زده نمی‌شد
  - مدت نمایش پیش‌فرض از ۲.۵ به ۲ ثانیه کاهش یافت
"""
from PyQt6.QtWidgets import (
    QLabel, QWidget, QGraphicsOpacityEffect
)
from PyQt6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QPoint, QEasingCurve
)
from PyQt6.QtGui import QFont

FONT_FAMILY = "Vazirmatn"

TOAST_STYLES = {
    "info":    ("#4FC3F7", "ℹ"),
    "success": ("#4CAF50", "✓"),
    "warning": ("#FF8F00", "⚠"),
    "error":   ("#D32F2F", "✗"),
}


class _ToastLabel(QLabel):
    """
    زیرکلاس QLabel برای نگه‌داشتن مرجع انیمیشن‌ها
    (رفع خطای Pylance reportAttributeAccessIssue)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # ✅ تعریف صریح با type hint تا Pylance راضی شود
        self._anim_in: QPropertyAnimation | None = None
        self._fade: QPropertyAnimation | None = None
        self._effect: QGraphicsOpacityEffect | None = None


def show_toast(parent_widget: QWidget, message: str,
               kind: str = "info", duration_ms: int = 2000):
    """
    نمایش Toast در گوشه بالا-راست parent_widget
    ...
    """
    # ✅ احترام به فلگ پژوهش — در مطالعه‌ی نهایی نباید بازخورد فوری داد
    try:
        from config import SHOW_TOASTS
        if not SHOW_TOASTS:
            return
    except Exception:
        pass

    if parent_widget is None:
        return

    color, icon = TOAST_STYLES.get(kind, TOAST_STYLES["info"])

    toast = _ToastLabel(f"  {icon}  {message}  ", parent_widget)
    toast.setFont(QFont(FONT_FAMILY, 12, QFont.Weight.Bold))
    toast.setStyleSheet(f"""
        QLabel {{
            background-color: rgba(26, 42, 74, 0.95);
            color: {color};
            border: 2px solid {color};
            border-radius: 10px;
            padding: 10px 18px;
        }}
    """)
    toast.setAlignment(Qt.AlignmentFlag.AlignCenter)
    toast.adjustSize()
    toast.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

    # موقعیت: گوشه بالا-راست با حاشیه 20px
    pw = parent_widget.width()
    x = pw - toast.width() - 20
    y = 20
    toast.move(x, -toast.height())  # شروع از بالا خارج
    toast.show()
    toast.raise_()

    # ✅ صدای Toast
    try:
        from core.audio_manager import get_audio_manager
        get_audio_manager().play_sfx("toast")
    except Exception:
        pass

    # ✅ اثر شفافیت — برای محو شدن نرم
    effect = QGraphicsOpacityEffect(toast)
    effect.setOpacity(1.0)
    toast.setGraphicsEffect(effect)
    toast._effect = effect

    # ✅ انیمیشن ورود از بالا
    anim_in = QPropertyAnimation(toast, b"pos", toast)
    anim_in.setDuration(280)
    anim_in.setStartValue(QPoint(x, -toast.height()))
    anim_in.setEndValue(QPoint(x, y))
    anim_in.setEasingCurve(QEasingCurve.Type.OutBack)
    anim_in.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
    toast._anim_in = anim_in

    # ✅ محو تدریجی و حذف — این‌بار واقعاً فراخوانی می‌شود
    def _start_fade():
        try:
            fade = QPropertyAnimation(effect, b"opacity", toast)
            fade.setDuration(400)
            fade.setStartValue(1.0)
            fade.setEndValue(0.0)
            fade.setEasingCurve(QEasingCurve.Type.InOutQuad)
            fade.finished.connect(toast.deleteLater)
            fade.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
            toast._fade = fade
        except RuntimeError:
            # اگر toast در این فاصله (مثلاً با بستن پنجره) حذف شده باشد
            pass

    QTimer.singleShot(duration_ms, _start_fade)