"""
منوی راست‌کلیک سراسری
========================
- روی هرجای بازی با راست‌کلیک ظاهر می‌شود
- شامل: ذخیره‌ی دستی، راهنمای کلیدها، بازگشت به منو، خروج
- در صحنه‌های فاز و منو کار می‌کند

نسخه: 1.0.0
"""
from PyQt6.QtWidgets import QMenu, QMessageBox, QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QFont

FONT_FAMILY = "Vazirmatn"


class GameContextMenu(QMenu):
    """منوی راست‌کلیک بازی"""

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window

        self.setFont(QFont(FONT_FAMILY, 11))
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setStyleSheet("""
            QMenu {
                background-color: #1A2A4A;
                color: #FFFFFF;
                border: 2px solid #4FC3F7;
                border-radius: 6px;
                padding: 6px;
                font-family: 'Vazirmatn';
                font-size: 11px;
            }
            QMenu::item {
                padding: 8px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #4FC3F7;
                color: #0B1D3A;
            }
            QMenu::separator {
                height: 1px;
                background-color: #2B4A6F;
                margin: 4px 8px;
            }
        """)

        self._build_menu()

    # ----------------------------------------------------------------
    def _build_menu(self):
        # ذخیره‌ی دستی
        save_action = QAction("💾  ذخیره‌ی دستی", self)
        save_action.triggered.connect(self._on_save)
        self.addAction(save_action)

        # بازگشت به منو
        menu_action = QAction("🏠  بازگشت به منو", self)
        menu_action.triggered.connect(self._on_back_to_menu)
        self.addAction(menu_action)

        self.addSeparator()

        # راهنمای کلیدها
        shortcuts_action = QAction("⌨️  راهنمای کلیدها", self)
        shortcuts_action.triggered.connect(
            self._on_show_shortcuts
        )
        self.addAction(shortcuts_action)

        # دفترچه
        log_action = QAction("📔  دفترچه‌ی مأموریت", self)
        log_action.triggered.connect(self._on_show_log)
        self.addAction(log_action)

        # پرونده
        dossier_action = QAction("👥  پرونده‌ی شخصیت‌ها", self)
        dossier_action.triggered.connect(self._on_show_dossier)
        self.addAction(dossier_action)

        self.addSeparator()

        # بستن منو
        close_action = QAction("✕  بستن منو", self)
        close_action.triggered.connect(self.close)
        self.addAction(close_action)

    # ================================================================
    def _on_save(self):
        try:
            from core.backup_manager import create_backup
            path = create_backup(reason="manual")
            if path:
                QMessageBox.information(
                    self.main_window,
                    "ذخیره شد",
                    f"✓ پشتیبان ساخته شد:\n{path}",
                )
            else:
                QMessageBox.warning(
                    self.main_window,
                    "خطا",
                    "ذخیره‌سازی ناموفق بود.",
                )
        except Exception as e:
            QMessageBox.warning(
                self.main_window,
                "خطا",
                f"ذخیره‌سازی ناموفق:\n{e}",
            )

    def _on_back_to_menu(self):
        reply = QMessageBox.question(
            self.main_window,
            "بازگشت به منو",
            "آیا می‌خواهید به منوی اصلی بازگردید؟\n"
            "پیشرفت جلسه ذخیره می‌شود.",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            gm = self.main_window.game_manager
            # ذخیره‌ی وضعیت
            try:
                gm.save_session()
            except Exception:
                pass
            gm.change_scene("menu")
        except Exception as e:
            print(f"⚠️ خطا در بازگشت به منو: {e}")

    def _on_show_shortcuts(self):
        try:
            from widgets.shortcuts_panel import ShortcutsDialog
            dlg = ShortcutsDialog(self.main_window)
            dlg.exec()
        except Exception as e:
            print(f"⚠️ خطا در نمایش میانبرها: {e}")

    def _on_show_log(self):
        try:
            if hasattr(self.main_window, "_open_mission_log"):
                self.main_window._open_mission_log()
        except Exception as e:
            print(f"⚠️ خطا در نمایش دفترچه: {e}")

    def _on_show_dossier(self):
        try:
            if hasattr(
                self.main_window, "_open_character_dossier"
            ):
                self.main_window._open_character_dossier()
        except Exception as e:
            print(f"⚠️ خطا در نمایش پرونده: {e}")


def install_context_menu(widget: QWidget, main_window):
    """نصب منوی راست‌کلیک روی یک widget"""
    widget.setContextMenuPolicy(
        Qt.ContextMenuPolicy.CustomContextMenu
    )

    def _show_menu(pos):
        menu = GameContextMenu(main_window, widget)
        menu.exec(widget.mapToGlobal(pos))

    widget.customContextMenuRequested.connect(_show_menu)