"""
پکیج صحنه‌های بازی (نسخه نهایی)
"""
from scenes.base_scene import BaseScene
from scenes.menu_scene import MenuScene
from scenes.intro_scene import IntroScene
from scenes.phase1_scene import Phase1Scene
from scenes.phase2_scene import Phase2Scene
from scenes.phase3_scene import Phase3Scene
from scenes.phase4_scene import Phase4Scene
from scenes.results_scene import ResultsScene

__all__ = [
    "BaseScene",
    "MenuScene",
    "IntroScene",
    "Phase1Scene",
    "Phase2Scene",
    "Phase3Scene",
    "Phase4Scene",
    "ResultsScene",
]

__version__ = "2.0.0"
__author__ = "Reza Maleki"