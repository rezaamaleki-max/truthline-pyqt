"""
پنل کلیدهای میانبر — نمایش با کلید ?
======================================
- QDialog شفاف با لیست کلیدها
- بسته می‌شود با Esc یا کلیک

نسخه: 1.0.0
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

FONT_FAMILY = "Vazirmatn"


SHORTCUTS = [
    ("Space", "پیشروی دیالوگ / تأیید"),
    ("Enter", "تأیید در فرم‌ها"),
    ("L", "دفترچه‌ی مأموریت"),
    ("C", "پرونده‌ی شخصیت‌ها"),
    ("F11", "تمام‌صفحه"),
    ("Esc", "خروج / بستن"),
    ("F1  /  ?", "این راهنما"),
    ("Ctrl+Enter", "ثبت سریع (در نامه به خود)"),
]


class ShortcutsDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("کلیدهای میانبر")
        self.setMinimumSize(520, 480)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setStyleSheet("""
            QDialog {
                background-color: #0B1D3A;
                border: 2px solid #4FC3F7;
                border-radius: 12px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        # سرصفحه
        head = QHBoxLayout()
        icon = QLabel("⌨️")
        icon.setFont(QFont("Arial", 26))
        icon.setStyleSheet("border: none;")
        head.addWidget(icon)

        title = QLabel("کلیدهای میانبر")
        tf = QFont(FONT_FAMILY, 18, QFont.Weight.Bold)
        title.setFont(tf)
        title.setStyleSheet("color: #4FC3F7; border: none;")
        head.addWidget(title)
        head.addStretch()
        layout.addLayout(head)

        # خط جداکننده
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(
            "background-color: #2B4A6F; max-height: 1px; "
            "border: none;"
        )
        layout.addWidget(sep)

        # لیست کلیدها
        for key, desc in SHORTCUTS:
            row = QFrame()
            row.setStyleSheet("""
                QFrame {
                    background-color: rgba(26, 42, 74, 0.5);
                    border: none;
                    border-radius: 6px;
                }
            """)
            rl = QHBoxLayout(row)
            rl.setContentsMargins(14, 8, 14, 8)

            key_lbl = QLabel(key)
            key_lbl.setFont(
                QFont("Consolas", 12, QFont.Weight.Bold)
            )
            key_lbl.setStyleSheet("""
                QLabel {
                    color: #FF8F00;
                    background-color: rgba(255, 143, 0, 0.12);
                    border: 1px solid #FF8F00;
                    border-radius: 4px;
                    padding: 4px 12px;
                }
            """)
            key_lbl.setMinimumWidth(120)
            key_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            rl.addWidget(key_lbl)

            rl.addSpacing(16)

            desc_lbl = QLabel(desc)
            desc_lbl.setFont(QFont(FONT_FAMILY, 12))
            desc_lbl.setStyleSheet(
                "color: #FFFFFF; border: none;"
            )
            desc_lbl.setLayoutDirection(
                Qt.LayoutDirection.RightToLeft
            )
            rl.addWidget(desc_lbl, 1)

            layout.addWidget(row)

        layout.addStretch()

        # دکمه بستن
        close_btn = QPushButton("بستن")
        close_btn.setFont(
            QFont(FONT_FAMILY, 13, QFont.Weight.Bold)
        )
        close_btn.setMinimumHeight(44)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #2B4A6F;
                color: #FFFFFF;
                border: 2px solid #4FC3F7;
                border-radius: 8px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #4FC3F7;
                color: #0B1D3A;
            }
        """)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def keyPressEvent(self, event):  # type: ignore
        if event.key() == Qt.Key.Key_Escape:
            self.accept()
        else:
            super().keyPressEvent(event)