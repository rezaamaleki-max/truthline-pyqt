"""
کمکی برای اتصال صدای کلیک به دکمه‌های عمومی
"""
from PyQt6.QtWidgets import QPushButton


def attach_click_sound(button: QPushButton):
    """افزودن صدای کلیک به یک دکمه"""
    button.clicked.connect(_play_click)


def _play_click():
    try:
        from core.audio_manager import get_audio_manager
        get_audio_manager().play_sfx("click")
    except Exception:
        pass