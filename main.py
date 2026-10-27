"""
نقطه ورود اصلی بازی Truthline
"""
import sys
import os
import uuid
import hashlib
import random
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFontDatabase, QFont

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.data_logger import DataLogger
from core.game_manager import GameManager
from core.session_logger import (
    start_session_log, stop_session_log
)
from scenes.splash_scene import SplashScene
from scenes.video_intro_scene import VideoIntroScene        # ✅ جدید
from scenes.menu_scene import MenuScene
from scenes.demographic_scene import DemographicScene
from scenes.intro_scene import IntroScene
from scenes.interlude_scene import InterludeScene
from scenes.phase1_scene import Phase1Scene
from scenes.phase2_scene import Phase2Scene
from scenes.phase3_scene import Phase3Scene
from scenes.phase4_scene import Phase4Scene
from scenes.hexaco_scene import HexacoScene
from scenes.results_scene import ResultsScene
from scenes.council_prep_scene import CouncilPrepScene
from scenes.sme_review_scene import SMEReviewScene   # ✅ جدید


from config import (
    WINDOW_WIDTH, WINDOW_HEIGHT,
    MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT,
    MAX_WINDOW_WIDTH, MAX_WINDOW_HEIGHT,
    TITLE, FONT_PATH
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(TITLE)
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setMinimumSize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        self.setMaximumSize(MAX_WINDOW_WIDTH, MAX_WINDOW_HEIGHT)
        
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        # ✅ شناسه‌ی شرکت‌کننده — با پیشوند برای تفکیک حالت نمایش
        self.participant_id = str(uuid.uuid4())[:8]
        try:
            from core.app_config import is_theater_mode
            if is_theater_mode():
                self.participant_id = "THEATER_" + self.participant_id
                print("✓ حالت نمایش فعال — رکوردها با پیشوند "
                      "THEATER_ ثبت می‌شوند")
        except Exception as e:
            print(f"⚠️ خطا در تشخیص حالت: {e}")

        # ✅ شروع لاگ‌گیری جلسه
        try:
            log_path = start_session_log(self.participant_id)
            if log_path:
                print(f"✓ لاگ جلسه: {log_path}")
        except Exception as e:
            print(f"⚠️ خطا در لاگ: {e}")

        print(f"✓ شناسه شرکت‌کننده: {self.participant_id}")
        
        # ✅ تثبیت بذر تصادفی per-participant برای بازتولیدپذیری روایی
        seed_str = self.participant_id + "truthline_v2"
        seed_int = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)
        random.seed(seed_int)
        self.random_seed = seed_int
        print(f"✓ بذر تصادفی تثبیت شد (برای بازتولیدپذیری): {seed_int}")
        
        self.data_logger = DataLogger(self.participant_id,
                                       random_seed=self.random_seed)
        self.game_manager = GameManager(self, self.data_logger)
        self.setCentralWidget(self.game_manager.stacked_widget)

        # ✅ لایه‌ی بارگذاری سراسری
        from widgets.loading_overlay import LoadingOverlay
        self.loading_overlay = LoadingOverlay(
            self.centralWidget()
        )

        # ✅ راه‌اندازی مدیر صدا با تنظیمات ذخیره‌شده
        try:
            from core.audio_manager import get_audio_manager
            from core.app_config import get_audio_settings
            audio_settings = get_audio_settings()
            audio = get_audio_manager()
            audio.set_enabled(audio_settings["enabled"])
            audio.set_volume(audio_settings["volume"])
        except Exception as e:
            print(f"⚠️ خطا در راه‌اندازی صدا: {e}")

        # ✅ نصب منوی راست‌کلیک
        try:
            from widgets.context_menu import (
                install_context_menu
            )
            install_context_menu(
                self.game_manager.stacked_widget, self
            )
            install_context_menu(self, self)
        except Exception as e:
            print(f"⚠️ خطا در نصب context menu: {e}")

        self._register_scenes()
        # ✅ شروع از splash → سپس منو
        self.game_manager.change_scene("splash")
    
    def _register_scenes(self):
        # ✅ Splash اول ثبت می‌شود
        self.game_manager.add_scene(
            "splash", SplashScene(self.game_manager)
        )
        # ✅ ویدیوی معرفی — بین splash و منو
        self.game_manager.add_scene(
            "video_intro", VideoIntroScene(self.game_manager)
        )
        self.game_manager.add_scene(
            "menu", MenuScene(self.game_manager)
        )
        # ✅ صحنه تنظیمات
        from scenes.settings_scene import SettingsScene
        self.game_manager.add_scene(
            "settings", SettingsScene(self.game_manager)
        )
        # ✅ صحنه جدید دموگرافیک
        self.game_manager.add_scene("demographic", DemographicScene(self.game_manager))
        self.game_manager.add_scene("intro", IntroScene(self.game_manager))
        self.game_manager.add_scene("interlude", InterludeScene(self.game_manager))

        # ✅ صحنه‌ی شب ایستگاه
        from scenes.night_scene import NightScene
        self.game_manager.add_scene(
            "night", NightScene(self.game_manager)
        )

        self.game_manager.add_scene("phase1", Phase1Scene(self.game_manager))
        self.game_manager.add_scene("phase2", Phase2Scene(self.game_manager))
        self.game_manager.add_scene("phase3", Phase3Scene(self.game_manager))
        self.game_manager.add_scene("phase4", Phase4Scene(self.game_manager))
        self.game_manager.add_scene("hexaco", HexacoScene(self.game_manager))
        self.game_manager.add_scene("results", ResultsScene(self.game_manager))
        self.game_manager.add_scene(
            "council_prep", CouncilPrepScene(self.game_manager)
        )

        # ✅ صحنه‌ی ارزیابی متخصصان
        self.game_manager.add_scene(
            "sme_review", SMEReviewScene(self.game_manager)
        )

        # ✅ صحنه‌ی نامه به خود
        from scenes.letter_to_self_scene import LetterToSelfScene
        self.game_manager.add_scene(
            "letter_to_self", LetterToSelfScene(self.game_manager)
        )

        # ✅ صحنه‌ی پایان حالت نمایش
        from scenes.theater_end_scene import TheaterEndScene
        self.game_manager.add_scene(
            "theater_end", TheaterEndScene(self.game_manager)
        )

        
        print("✓ تمام صحنه‌ها با موفقیت ثبت شدند:")
        for scene_name in self.game_manager.list_scenes():
            print(f"  - {scene_name}")
    
    def closeEvent(self, event):          # type: ignore[reportIncompatibleMethodOverride]
        print("✓ بستن بازی و ذخیره نهایی داده‌ها...")

        # ✅ توقف صدا
        try:
            from core.audio_manager import get_audio_manager
            get_audio_manager().stop_all()
        except Exception:
            pass

        # ✅ پایان جلسه
        try:
            self.data_logger.end_session()
        except Exception as e:
            print(f"⚠️ خطا در پایان جلسه: {e}")

        # ✅ پشتیبان‌گیری خودکار پس از پایان
        try:
            from core.backup_manager import create_backup
            create_backup(reason="session_end")
        except Exception as e:
            print(f"⚠️ خطا در پشتیبان‌گیری: {e}")

        # ✅ بستن لاگ
        try:
            stop_session_log()
        except Exception:
            pass

        event.accept()
    
    def keyPressEvent(self, event):           # type: ignore[reportIncompatibleMethodOverride]
        if event.key() == Qt.Key.Key_F11:
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()
        elif event.key() == Qt.Key.Key_L:
            # ✅ باز کردن دفترچه‌ی مأموریت (در هر جای بازی)
            self._open_mission_log()
        elif event.key() == Qt.Key.Key_C:
            # ✅ باز کردن پرونده‌ی شخصیت‌ها
            self._open_character_dossier()
        elif event.key() in (
            Qt.Key.Key_Question, Qt.Key.Key_F1
        ):
            # ✅ پنل کلیدهای میانبر
            self._open_shortcuts()
        elif event.key() == Qt.Key.Key_Escape:
            if self.isFullScreen():
                self.showNormal()
            else:
                self.close()
        else:
            super().keyPressEvent(event)

    def _open_mission_log(self):
        """باز کردن پنجره‌ی دفترچه‌ی مأموریت"""
        try:
            from core.mission_log import get_mission_log_entries
            from widgets.mission_log_widget import MissionLogDialog

            entries = get_mission_log_entries(self.data_logger)
            print(f"✓ دفترچه باز شد — {len(entries)} ورودی")

            dlg = MissionLogDialog(entries, self)
            dlg.exec()
        except Exception as e:
            print(f"⚠️ خطا در باز کردن دفترچه: {e}")

    def _open_character_dossier(self):
        """باز کردن پنجره‌ی پرونده‌ی شخصیت‌ها"""
        try:
            from core.character_dossiers import get_all_dossiers
            from widgets.character_dossier_widget import (
                CharacterDossierDialog
            )

            dossiers = get_all_dossiers(self.data_logger)
            print(
                f"✓ پرونده‌ی شخصیت‌ها باز شد — "
                f"{len(dossiers)} شخصیت"
            )

            dlg = CharacterDossierDialog(dossiers, self)
            dlg.exec()
        except Exception as e:
            print(f"⚠️ خطا در باز کردن پرونده‌ی شخصیت‌ها: {e}")

    def _open_shortcuts(self):
        """باز کردن پنل کلیدهای میانبر"""
        try:
            from widgets.shortcuts_panel import ShortcutsDialog
            dlg = ShortcutsDialog(self)
            dlg.exec()
        except Exception as e:
            print(f"⚠️ خطا در پنل میانبرها: {e}")

def main():
    print("=" * 70)
    print("  Truthline: Crisis at Caspian Station")
    print("  بازی ارزیابی شایستگی مبتنی بر شواهد (ECD)")
    print("=" * 70)
    
    app = QApplication(sys.argv)

    # ✅ فعال‌سازی RTL سراسری — باید قبل از هر ویجتی باشه
    from core.rtl_helper import enable_rtl_app
    enable_rtl_app()

    # ✅ نصب فیلتر سراسری صدای کلیک
    try:
        from widgets.global_click_filter import (
            install_global_click_filter
        )
        install_global_click_filter(app)
    except Exception as e:
        print(f"⚠️ خطا در نصب فیلتر صدای کلیک: {e}")

    if os.path.exists(FONT_PATH):
        try:
            font_id = QFontDatabase.addApplicationFont(FONT_PATH)
            if font_id != -1:
                families = QFontDatabase.applicationFontFamilies(font_id)
                if families:
                    # ✅ اعمال اندازه بر اساس تنظیمات دسترس‌پذیری
                    try:
                        from core.app_config import (
                            get_accessibility_settings
                        )
                        acc = get_accessibility_settings()
                        base_size = 15 if acc["large_fonts"] else 12
                    except Exception:
                        base_size = 12

                    app_font = QFont(families[0])
                    app_font.setPointSize(base_size)
                    app.setFont(app_font)
                    print(
                        f"✓ فونت {families[0]} "
                        f"(اندازه {base_size}) اعمال شد"
                    )
        except Exception as e:
            print(f"⚠️ خطا در بارگذاری فونت: {e}")
    
    app.setStyleSheet("""
        QWidget {
            background-color: #0B1D3A;
            color: #FFFFFF;
        }
        QMainWindow {
            border: 2px solid #2B4A6F;
        }
        QPushButton {
            background-color: #2B4A6F;
            color: #FFFFFF;
            border: 2px solid #4FC3F7;
            border-radius: 8px;
            padding: 10px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #4FC3F7;
            color: #0B1D3A;
            border: 2px solid #FFFFFF;
        }
        QPushButton:pressed {
            background-color: #1A2A4A;
            color: #4FC3F7;
        }
    """)
    
    window = MainWindow()
    window.show()

    print("\n🎮 بازی در حال اجرا است...\n")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()