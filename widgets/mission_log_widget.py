"""
پنجره‌ی دفترچه‌ی مأموریت
- یک QDialog شفاف با اسکرول
- ورودی‌ها بر اساس روز گروه‌بندی می‌شوند
- بدون هیچ نمره‌ای
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QScrollArea, QFrame,
    QPushButton, QHBoxLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

FONT_FAMILY = "Vazirmatn"


class MissionLogDialog(QDialog):
    """پنجره‌ی دفترچه‌ی مأموریت"""

    def __init__(self, entries: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("دفترچه‌ی مأموریت")
        self.setMinimumSize(720, 620)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setStyleSheet("QDialog { background-color: #0B1D3A; }")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        # ---------------- سرصفحه ----------------
        header_row = QHBoxLayout()

        icon_lbl = QLabel("📔")
        icon_lbl.setFont(QFont("Arial", 26))
        icon_lbl.setStyleSheet("border: none;")
        header_row.addWidget(icon_lbl)

        title = QLabel("دفترچه‌ی مأموریت")
        tf = QFont(FONT_FAMILY, 22)
        tf.setBold(True)
        title.setFont(tf)
        title.setStyleSheet("color: #FF8F00; border: none;")
        header_row.addWidget(title)
        header_row.addStretch()
        layout.addLayout(header_row)

        # زیرعنوان
        subtitle = QLabel(
            "تصمیم‌هایی که در طول مأموریت گرفته‌اید. "
            "این دفترچه صرفاً برای مرور شخصی شماست."
        )
        subtitle.setFont(QFont(FONT_FAMILY, 11))
        subtitle.setStyleSheet(
            "color: #B0BEC5; border: none; padding: 4px;"
        )
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        # خط جداکننده
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(
            "background-color: #2B4A6F; max-height: 1px; border: none;"
        )
        layout.addWidget(sep)

        # ---------------- Scroll Area ----------------
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(
            "QScrollArea { background-color: transparent; border: none; }"
        )

        content = QFrame()
        content.setStyleSheet("""
            QFrame {
                background-color: rgba(26, 42, 74, 0.4);
                border: 1px solid #2B4A6F;
                border-radius: 10px;
            }
        """)
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(18, 18, 18, 18)
        content_layout.setSpacing(14)

        # اگر خالی است
        if not entries:
            empty_lbl = QLabel(
                "هنوز تصمیمی در این مأموریت ثبت نشده است.\n\n"
                "با پیشرفت در بازی، تصمیم‌های شما یکی‌یکی در این "
                "دفترچه ثبت خواهند شد."
            )
            empty_lbl.setFont(QFont(FONT_FAMILY, 13))
            empty_lbl.setStyleSheet(
                "color: #888888; border: none; padding: 40px;"
            )
            empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_lbl.setWordWrap(True)
            content_layout.addWidget(empty_lbl)
        else:
            current_phase = None
            counter = 0
            for entry in entries:
                # ✅ جداکننده‌ی روز
                if entry["phase"] != current_phase:
                    current_phase = entry["phase"]
                    sep_lbl = QLabel(f"─── {current_phase} ───")
                    sep_lbl.setFont(
                        QFont(FONT_FAMILY, 13, QFont.Weight.Bold)
                    )
                    sep_lbl.setStyleSheet(
                        "color: #FF8F00; border: none; padding: 10px;"
                    )
                    sep_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    content_layout.addWidget(sep_lbl)

                counter += 1
                content_layout.addWidget(
                    self._build_entry_frame(counter, entry)
                )

        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll, stretch=1)

        # ---------------- دکمه‌ی بستن ----------------
        close_btn = QPushButton("بستن  (کلید Esc)")
        close_btn.setFont(
            QFont(FONT_FAMILY, 13, QFont.Weight.Bold)
        )
        close_btn.setMinimumHeight(46)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #2B4A6F;
                color: #FFFFFF;
                border: 2px solid #4FC3F7;
                border-radius: 10px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #4FC3F7;
                color: #0B1D3A;
            }
        """)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    # ------------------------------------------------------------------
    def _build_entry_frame(self, number: int, entry: dict) -> QFrame:
        """یک قاب برای یک تصمیم — شامل بازتاب بی‌طرف"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: rgba(11, 29, 58, 0.7);
                border: 1px solid #4FC3F7;
                border-radius: 8px;
            }
        """)
        vbox = QVBoxLayout(frame)
        vbox.setContentsMargins(14, 10, 14, 10)
        vbox.setSpacing(6)

        # عنوان سناریو
        title_lbl = QLabel(f"{number}. {entry['title']}")
        title_lbl.setFont(
            QFont(FONT_FAMILY, 13, QFont.Weight.Bold)
        )
        title_lbl.setStyleSheet(
            "color: #4FC3F7; border: none; background: transparent;"
        )
        title_lbl.setWordWrap(True)
        vbox.addWidget(title_lbl)

        # متن انتخاب
        choice_lbl = QLabel(f"▸ {entry['choice_text']}")
        choice_lbl.setFont(QFont(FONT_FAMILY, 11))
        choice_lbl.setStyleSheet(
            "color: #FFFFFF; border: none; "
            "background: transparent; padding-right: 6px;"
        )
        choice_lbl.setWordWrap(True)
        choice_lbl.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        choice_lbl.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignAbsolute
        )
        vbox.addWidget(choice_lbl)

        # ✅ بازتاب بی‌طرف — اگر موجود باشد
        reflection = entry.get("reflection", "")
        if reflection:
            refl_lbl = QLabel(f"💭 {reflection}")
            refl_lbl.setFont(QFont(FONT_FAMILY, 10))
            refl_lbl.setStyleSheet(
                "color: #90A4AE; border: none; "
                "background: transparent; padding-right: 6px; "
                "font-style: italic;"
            )
            refl_lbl.setWordWrap(True)
            refl_lbl.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            refl_lbl.setAlignment(
                Qt.AlignmentFlag.AlignRight
                | Qt.AlignmentFlag.AlignAbsolute
            )
            vbox.addWidget(refl_lbl)

        return frame

    # ------------------------------------------------------------------
    def keyPressEvent(self, event):  # type: ignore
        if event.key() == Qt.Key.Key_Escape:
            self.accept()
        else:
            super().keyPressEvent(event)