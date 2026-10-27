"""
پکیج ویجت‌های UI پروژه Truthline (PyQt6 Version)
این پکیج شامل تمام کامپوننت‌های رابط کاربری بازی است.

ویژگی‌های کلیدی:
- پشتیبانی بومی از فارسی و RTL
- چیدمان خودکار (Auto-Layout)
- طراحی Data-Driven (بارگذاری از JSON)
- استایل‌دهی با CSS-like syntax

نسخه: 2.0.0 (PyQt6 Migration)
"""

from widgets.dialogue_widget import DialogueWidget
from widgets.choice_widget import ChoiceWidget
from widgets.hud_widget import HUDWidget
from widgets.radar_chart import RadarChart

__all__ = [
    "DialogueWidget",
    "ChoiceWidget",
    "HUDWidget",
    "RadarChart",
]

__version__ = "2.0.0"
__author__ = "Reza Maleki"