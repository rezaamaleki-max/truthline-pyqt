"""
پکیج هسته پروژه Truthline (PyQt6 Version)
این پکیج شامل اجزای اصلی مدیریت بازی و ثبت داده‌ها است.

نسخه: 2.0.0 (PyQt6 Migration)
"""

from core.data_logger import DataLogger
from core.game_manager import GameManager
from core.evidence_engine import EvidenceEngine

__all__ = [
    "DataLogger",
    "GameManager",
    "EvidenceEngine",
]

__version__ = "2.0.0"
__author__ = "Reza Maleki"