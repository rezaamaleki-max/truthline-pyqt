"""
کلاس پایه برای تمام صحنه‌های بازی
تمام صحنه‌ها (منو، مقدمه، فازها، نتایج) از این کلاس ارث می‌برند.

نسخه: 2.0.0
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import Qt


class BaseScene(QWidget):
    """کلاس پایه انتزاعی برای تمام صحنه‌های بازی"""
    
    def __init__(self, game_manager):
        """
        مقداردهی اولیه صحنه
        
        Args:
            game_manager: نمونه GameManager برای دسترسی به DataLogger و تغییر صحنه
        """
        super().__init__()
        self.game_manager = game_manager
        self.data_logger = game_manager.data_logger
        
        # چیدمان اصلی صحنه
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # استایل پایه (پس‌زمینه تیره)
        self.setStyleSheet("""
            BaseScene {
                background-color: #0B1D3A;
            }
        """)
        
        # جهت راست‌چین برای تمام صحنه‌ها
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    
    def on_enter(self, **kwargs):
        """
        متدی که هنگام ورود به صحنه فراخوانی می‌شود
        صحنه‌های فرزند می‌توانند این متد را بازنویسی کنند
        """
        pass
    
    def on_exit(self):
        """
        متدی که هنگام خروج از صحنه فراخوانی می‌شود
        صحنه‌های فرزند می‌توانند این متد را بازنویسی کنند
        """
        pass
    
    def change_scene(self, scene_name: str, **kwargs):
        """
        تغییر به صحنه دیگر (متد کمکی)
        
        Args:
            scene_name: نام صحنه مقصد
            **kwargs: آرگومان‌های اضافی برای صحنه مقصد
        """
        self.game_manager.change_scene(scene_name, **kwargs)