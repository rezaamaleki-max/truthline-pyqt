"""
پنجره‌ی پرونده‌ی شخصیت‌ها — نسخه ۲.۰
=====================================
تغییرات:
- انیمیشن ورود کارت‌ها (Fade-in + Slide)
- Hover effect روی کارت‌ها
- انیمیشن تعداد یادداشت‌های باز‌شده
- طراحی سینمایی‌تر

نسخه: 2.0.0
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFrame, QPushButton, QGraphicsOpacityEffect
)
from PyQt6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint
)
from PyQt6.QtGui import QFont

FONT_FAMILY = "Vazirmatn"


class _AnimatedCard(QFrame):
    """کارت شخصیت با انیمیشن ورود و Hover"""

    def __init__(self, dossier: dict, parent=None):
        super().__init__(parent)
        self._dossier = dossier
        self._accent = dossier["color"]
        self._hover_active = False

        self.setObjectName("dossierCard")
        self._apply_normal_style()
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        self._build_content()

    # ------------------------------------------------------------------
    def _apply_normal_style(self):
        self.setStyleSheet(f"""
            QFrame#dossierCard {{
                background-color: rgba(11, 29, 58, 0.7);
                border: 2px solid {self._accent};
                border-radius: 10px;
            }}
        """)

    def _apply_hover_style(self):
        self.setStyleSheet(f"""
            QFrame#dossierCard {{
                background-color: rgba(26, 42, 74, 0.85);
                border: 3px solid {self._accent};
                border-radius: 10px;
            }}
        """)

    def enterEvent(self, event):  # type: ignore
        self._hover_active = True
        self._apply_hover_style()
        super().enterEvent(event)

    def leaveEvent(self, event):  # type: ignore
        self._hover_active = False
        self._apply_normal_style()
        super().leaveEvent(event)

    # ------------------------------------------------------------------
    def _build_content(self):
        d = self._dossier
        accent = d["color"]

        vbox = QVBoxLayout(self)
        vbox.setContentsMargins(16, 14, 16, 14)
        vbox.setSpacing(10)

        # ---------------- سرصفحه ----------------
        head_row = QHBoxLayout()
        head_row.setSpacing(12)

        icon_lbl = QLabel(d["icon"])
        icon_lbl.setFont(QFont("Arial", 28))
        icon_lbl.setStyleSheet(
            "border: none; background: transparent;"
        )
        head_row.addWidget(icon_lbl)

        name_col = QVBoxLayout()
        name_col.setSpacing(2)

        name_lbl = QLabel(d["name"])
        nf = QFont(FONT_FAMILY, 17, QFont.Weight.Bold)
        name_lbl.setFont(nf)
        name_lbl.setStyleSheet(
            f"color: {accent}; border: none; background: transparent;"
        )
        name_col.addWidget(name_lbl)

        role_lbl = QLabel(d["role"])
        role_lbl.setFont(QFont(FONT_FAMILY, 11))
        role_lbl.setStyleSheet(
            "color: #B0BEC5; border: none; background: transparent;"
        )
        name_col.addWidget(role_lbl)

        head_row.addLayout(name_col, 1)

        # شمارنده
        counter_lbl = QLabel(
            f"{d['unlocked_count']} / {d['total_count']}"
        )
        counter_lbl.setFont(
            QFont(FONT_FAMILY, 11, QFont.Weight.Bold)
        )
        counter_lbl.setStyleSheet(f"""
            color: {accent};
            border: 1px solid {accent};
            border-radius: 8px;
            padding: 4px 10px;
            background: transparent;
        """)
        head_row.addWidget(counter_lbl)

        vbox.addLayout(head_row)

        # خط جداکننده
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(
            f"background-color: {accent}; max-height: 1px; "
            "border: none;"
        )
        sep.setGraphicsEffect(self._make_opacity_effect(0.4))
        vbox.addWidget(sep)

        # ---------------- یادداشت‌ها ----------------
        if not d["notes"]:
            empty = QLabel("هنوز اطلاعاتی ثبت نشده.")
            empty.setFont(QFont(FONT_FAMILY, 11))
            empty.setStyleSheet(
                "color: #666666; border: none; "
                "background: transparent; padding: 8px;"
            )
            empty.setWordWrap(True)
            vbox.addWidget(empty)

        for note in d["notes"]:
            vbox.addWidget(self._build_note_row(note, accent))

        # ---------------- قفل‌شده‌ها ----------------
        if d["locked_count"] > 0:
            locked_lbl = QLabel(
                f"🔒  {d['locked_count']} یادداشت دیگر "
                "با پیشرفت مأموریت باز می‌شود."
            )
            locked_lbl.setFont(QFont(FONT_FAMILY, 10))
            locked_lbl.setStyleSheet(
                "color: #666666; border: none; "
                "background: transparent; padding: 4px; "
                "font-style: italic;"
            )
            locked_lbl.setWordWrap(True)
            vbox.addWidget(locked_lbl)

    # ------------------------------------------------------------------
    def _build_note_row(self, note: dict, accent: str) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: rgba(26, 42, 74, 0.5);
                border: none;
                border-radius: 6px;
            }
        """)
        nl = QHBoxLayout(frame)
        nl.setContentsMargins(12, 8, 12, 8)
        nl.setSpacing(8)

        bullet = QLabel("◆")
        bullet.setFont(QFont("Arial", 11))
        bullet.setStyleSheet(
            f"color: {accent}; border: none; "
            "background: transparent;"
        )
        bullet.setFixedWidth(18)
        nl.addWidget(bullet)

        txt = QLabel(note["text"])
        txt.setFont(QFont(FONT_FAMILY, 11))
        txt.setStyleSheet(
            "color: #E0E0E0; border: none; "
            "background: transparent;"
        )
        txt.setWordWrap(True)
        txt.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        txt.setAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignAbsolute
        )
        nl.addWidget(txt, 1)

        return frame

    # ------------------------------------------------------------------
    @staticmethod
    def _make_opacity_effect(value: float) -> QGraphicsOpacityEffect:
        eff = QGraphicsOpacityEffect()
        eff.setOpacity(value)
        return eff

    # ------------------------------------------------------------------
    def animate_in(self, delay_ms: int = 0):
        """انیمیشن ورود: Fade-in + Slide از پایین"""
        # ابتدا شفافیت ۰
        opacity = QGraphicsOpacityEffect(self)
        opacity.setOpacity(0.0)
        self.setGraphicsEffect(opacity)

        # موقعیت اولیه (کمی پایین‌تر)
        final_pos = self.pos()
        start_pos = QPoint(final_pos.x(), final_pos.y() + 30)
        self.move(start_pos)

        # انیمیشن شفافیت
        fade_anim = QPropertyAnimation(opacity, b"opacity", self)
        fade_anim.setDuration(500)
        fade_anim.setStartValue(0.0)
        fade_anim.setEndValue(1.0)
        fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        # انیمیشن موقعیت
        pos_anim = QPropertyAnimation(self, b"pos", self)
        pos_anim.setDuration(500)
        pos_anim.setStartValue(start_pos)
        pos_anim.setEndValue(final_pos)
        pos_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        # نگه‌داشتن مرجع برای جلوگیری از GC
        self._fade_anim = fade_anim
        self._pos_anim = pos_anim

        def _start():
            fade_anim.start()
            pos_anim.start()
            # پاک کردن effect بعد از پایان
            fade_anim.finished.connect(
                lambda: self.setGraphicsEffect(None)
            )

        QTimer.singleShot(delay_ms, _start)


# ====================================================================
# پنجره‌ی اصلی
# ====================================================================
class CharacterDossierDialog(QDialog):
    """پنجره‌ی نمایش پرونده‌ی شخصیت‌ها — نسخه انیمیشنی"""

    def __init__(self, dossiers: list, parent=None):
        super().__init__(parent)
        self.dossiers = dossiers
        self._cards: list = []

        self.setWindowTitle("پرونده‌ی شخصیت‌ها")
        self.setMinimumSize(780, 680)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setStyleSheet("QDialog { background-color: #0B1D3A; }")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        # ---------------- سرصفحه ----------------
        header_row = QHBoxLayout()

        icon_lbl = QLabel("👥")
        icon_lbl.setFont(QFont("Arial", 26))
        icon_lbl.setStyleSheet("border: none;")
        header_row.addWidget(icon_lbl)

        title = QLabel("پرونده‌ی شخصیت‌ها")
        tf = QFont(FONT_FAMILY, 22)
        tf.setBold(True)
        title.setFont(tf)
        title.setStyleSheet("color: #4FC3F7; border: none;")
        header_row.addWidget(title)
        header_row.addStretch()
        layout.addLayout(header_row)

        subtitle = QLabel(
            "اطلاعاتی که در طول مأموریت درباره‌ی همکاران خود "
            "جمع کرده‌اید. با پیشرفت بازی، اطلاعات بیشتری باز "
            "می‌شود."
        )
        subtitle.setFont(QFont(FONT_FAMILY, 11))
        subtitle.setStyleSheet(
            "color: #B0BEC5; border: none; padding: 4px;"
        )
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(
            "background-color: #2B4A6F; max-height: 1px; border: none;"
        )
        layout.addWidget(sep)

        # ---------------- Scroll ----------------
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
        content_layout.setContentsMargins(16, 16, 16, 16)
        content_layout.setSpacing(16)

        for d in dossiers:
            card = _AnimatedCard(d)
            content_layout.addWidget(card)
            self._cards.append(card)

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

        # شروع انیمیشن ورود کارت‌ها با تأخیر پله‌ای
        QTimer.singleShot(50, self._start_intro_animations)

    # ------------------------------------------------------------------
    def _start_intro_animations(self):
        for i, card in enumerate(self._cards):
            card.animate_in(delay_ms=i * 120)

    # ------------------------------------------------------------------
    def keyPressEvent(self, event):  # type: ignore
        if event.key() == Qt.Key.Key_Escape:
            self.accept()
        else:
            super().keyPressEvent(event)