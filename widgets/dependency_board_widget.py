"""
ویجت تخته وابستگی — SPA-01
چیدمان دو ستونی با Drag & Drop واقعی

نسخه 3.0:
- کشیدن کارت‌ها از ستون راست به جایگاه‌های ستون چپ
- Drop روی هر جایگاه خالی
- جایگزینی کارت در جایگاه پر (با بازگشت کارت قبلی)
- بدون چک بصری ترتیب
- Undo برای حذف آخرین
- حفظ منطق distractor

نسخه: 3.0.0
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea
)
from PyQt6.QtCore import (
    Qt, QTimer, pyqtSignal, QMimeData, QPoint
)
from PyQt6.QtGui import (
    QDrag, QFont, QPainter, QColor, QPen, QBrush, QPixmap
)
import time

FONT_FAMILY = "Vazirmatn"
MIME_TYPE = "application/x-truthline-action-id"


# ====================================================================
# کارت قابل کشیدن
# ====================================================================
class _DraggableCard(QFrame):
    """کارت اقدام که می‌توان آن را کشید"""

    def __init__(self, action: dict, parent=None):
        super().__init__(parent)
        self.action_id = action["id"]
        self._drag_start: QPoint | None = None
        self._is_disabled = False

        self.setObjectName("actionCard")
        self.setStyleSheet("""
            QFrame#actionCard {
                background-color: rgba(26, 42, 74, 0.85);
                border: 2px solid #4FC3F7;
                border-radius: 8px;
            }
            QFrame#actionCard:hover {
                background-color: rgba(79, 195, 247, 0.20);
                border: 2px solid #FFFFFF;
            }
        """)
        self.setMinimumHeight(64)
        self.setCursor(Qt.CursorShape.OpenHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(8)

        icon_lbl = QLabel(action.get("icon", "●"))
        icon_lbl.setFont(QFont("Arial", 18))
        icon_lbl.setStyleSheet("border: none;")
        icon_lbl.setFixedWidth(28)
        icon_lbl.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents, True
        )
        layout.addWidget(icon_lbl)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)

        name = QLabel(action["name"])
        name.setFont(
            QFont(FONT_FAMILY, 11, QFont.Weight.Bold)
        )
        name.setStyleSheet(
            "color: #FFFFFF; border: none;"
        )
        name.setWordWrap(True)
        name.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents, True
        )
        text_col.addWidget(name)

        brief = QLabel(action.get("brief", ""))
        brief.setFont(QFont(FONT_FAMILY, 9))
        brief.setStyleSheet(
            "color: #B0BEC5; border: none;"
        )
        brief.setWordWrap(True)
        brief.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents, True
        )
        text_col.addWidget(brief)

        layout.addLayout(text_col, 1)

    # ----------------------------------------------------------------
    def mousePressEvent(self, event):  # type: ignore
        if self._is_disabled:
            return
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):  # type: ignore
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self._drag_start = None
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):  # type: ignore
        if self._is_disabled or self._drag_start is None:
            return
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        dist = (event.pos() - self._drag_start).manhattanLength()
        if dist < 8:
            return

        drag = QDrag(self)
        mime = QMimeData()
        mime.setData(MIME_TYPE, self.action_id.encode("utf-8"))
        mime.setText(self.action_id)
        drag.setMimeData(mime)

        # نمای درگ
        pixmap = self.grab()
        # شفافیت ۸۰٪
        faded = QPixmap(pixmap.size())
        faded.fill(Qt.GlobalColor.transparent)
        painter = QPainter(faded)
        painter.setOpacity(0.8)
        painter.drawPixmap(0, 0, pixmap)
        painter.end()
        drag.setPixmap(faded)
        drag.setHotSpot(event.pos())

        drag.exec(Qt.DropAction.MoveAction)
        self.setCursor(Qt.CursorShape.OpenHandCursor)


# ====================================================================
# جایگاه Drop
# ====================================================================
class _DropSlot(QFrame):
    """جایگاه که می‌تواند یک کارت را در خود جا دهد"""

    dropped = pyqtSignal(int, str)  # slot_index, action_id
    cleared = pyqtSignal(int)

    def __init__(self, index: int, parent=None):
        super().__init__(parent)
        self.slot_index = index
        self._filled_action_id: str | None = None
        self._is_highlighted = False

        self.setAcceptDrops(True)
        self.setMinimumHeight(52)
        self.setMaximumHeight(64)
        self._apply_style()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 4, 10, 4)
        layout.setSpacing(8)

        self.num_lbl = QLabel(f"{index + 1}.")
        self.num_lbl.setFont(
            QFont(FONT_FAMILY, 12, QFont.Weight.Bold)
        )
        self.num_lbl.setStyleSheet(
            "color: #FF8F00; border: none;"
        )
        self.num_lbl.setFixedWidth(28)
        layout.addWidget(self.num_lbl)

        self.icon_lbl = QLabel("—")
        self.icon_lbl.setFont(QFont("Arial", 16))
        self.icon_lbl.setStyleSheet("border: none;")
        self.icon_lbl.setFixedWidth(28)
        layout.addWidget(self.icon_lbl)

        self.name_lbl = QLabel("خالی")
        self.name_lbl.setFont(QFont(FONT_FAMILY, 11))
        self.name_lbl.setStyleSheet(
            "color: #666666; border: none;"
        )
        self.name_lbl.setLayoutDirection(
            Qt.LayoutDirection.RightToLeft
        )
        self.name_lbl.setAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignAbsolute
        )
        layout.addWidget(self.name_lbl, 1)

        # دکمه‌ی حذف کارت
        self.clear_btn = QPushButton("✕")
        self.clear_btn.setFont(QFont(FONT_FAMILY, 12))
        self.clear_btn.setFixedSize(26, 26)
        self.clear_btn.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.clear_btn.setFocusPolicy(
            Qt.FocusPolicy.NoFocus
        )
        self.clear_btn.setVisible(False)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #D32F2F;
                border: 1px solid #D32F2F;
                border-radius: 13px;
                padding: 0;
            }
            QPushButton:hover {
                background-color: #D32F2F;
                color: #FFFFFF;
            }
        """)
        self.clear_btn.clicked.connect(self._on_clear_clicked)
        layout.addWidget(self.clear_btn)

    # ----------------------------------------------------------------
    def _apply_style(self):
        if self._is_highlighted:
            self.setStyleSheet("""
                QFrame {
                    background-color: rgba(79, 195, 247, 0.20);
                    border: 2px solid #FFFFFF;
                    border-radius: 6px;
                }
            """)
        elif self._filled_action_id is not None:
            self.setStyleSheet("""
                QFrame {
                    background-color: rgba(76, 175, 80, 0.10);
                    border: 2px solid #4CAF50;
                    border-radius: 6px;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: rgba(26, 42, 74, 0.5);
                    border: 2px dashed #4FC3F7;
                    border-radius: 6px;
                }
            """)

    # ----------------------------------------------------------------
    def get_action_id(self) -> str | None:
        return self._filled_action_id

    def set_action(self, action_id: str, name: str, icon: str):
        self._filled_action_id = action_id
        self.icon_lbl.setText(icon)
        self.name_lbl.setText(name)
        self.name_lbl.setStyleSheet(
            "color: #FFFFFF; border: none;"
        )
        self.clear_btn.setVisible(True)
        self._apply_style()

    def clear_action(self):
        self._filled_action_id = None
        self.icon_lbl.setText("—")
        self.name_lbl.setText("خالی")
        self.name_lbl.setStyleSheet(
            "color: #666666; border: none;"
        )
        self.clear_btn.setVisible(False)
        self._apply_style()

    # ----------------------------------------------------------------
    def dragEnterEvent(self, event):  # type: ignore
        if event.mimeData().hasFormat(MIME_TYPE):
            self._is_highlighted = True
            self._apply_style()
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):  # type: ignore
        self._is_highlighted = False
        self._apply_style()

    def dropEvent(self, event):  # type: ignore
        self._is_highlighted = False
        self._apply_style()
        if event.mimeData().hasFormat(MIME_TYPE):
            action_id = bytes(
                event.mimeData().data(MIME_TYPE)
            ).decode("utf-8")
            self.dropped.emit(self.slot_index, action_id)
            event.acceptProposedAction()
        else:
            event.ignore()

    def _on_clear_clicked(self):
        if self._filled_action_id is not None:
            self.cleared.emit(self.slot_index)


# ====================================================================
# ویجت اصلی
# ====================================================================
class DependencyBoardWidget(QWidget):
    """تخته چیدمان اقدامات — با Drag&Drop"""

    board_done = pyqtSignal(dict)

    def __init__(self, actions: list, correct_order: list,
                 parent=None):
        super().__init__(parent)
        self.action_list = actions
        self.correct_order = correct_order

        self.start_time = int(time.time() * 1000)
        self.first_action_time = 0
        self.sequence: list = []
        self.is_done = False

        self.action_map = {a["id"]: a for a in actions}
        self.action_cards: dict = {}
        self.slots: list = []

        self._setup_ui()
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

    # ================================================================
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 10, 25, 10)
        main_layout.setSpacing(8)

        # عنوان
        title = QLabel("زنجیره نجات ایستگاه")
        tf = QFont(FONT_FAMILY, 17)
        tf.setBold(True)
        title.setFont(tf)
        title.setStyleSheet("color: #4FC3F7;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        # توضیح
        desc = QLabel(
            "کارت‌های ستون راست را با موس بکشید و در جایگاه‌های "
            "ستون چپ رها کنید. هر اقدام، پیش‌نیاز دیگری دارد."
        )
        desc.setFont(QFont(FONT_FAMILY, 10))
        desc.setStyleSheet("color: #CCCCCC;")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        main_layout.addWidget(desc)

        # دو ستون
        columns = QHBoxLayout()
        columns.setSpacing(15)

        available_col = self._build_available_column()
        columns.addWidget(available_col, 1)

        slots_col = self._build_slots_column()
        columns.addWidget(slots_col, 1)

        main_layout.addLayout(columns, stretch=1)

        # دکمه‌ی ثبت
        self.submit_btn = QPushButton("ثبت ترتیب و اجرا")
        self.submit_btn.setFont(
            QFont(FONT_FAMILY, 13, QFont.Weight.Bold)
        )
        self.submit_btn.setMinimumHeight(44)
        self.submit_btn.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.submit_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.submit_btn.setEnabled(False)
        self.submit_btn.setStyleSheet("""
            QPushButton {
                background-color: #2B4A6F;
                color: #FFFFFF;
                border: 2px solid #4FC3F7;
                border-radius: 8px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #4FC3F7;
                color: #0B1D3A;
            }
            QPushButton:disabled {
                background-color: #1A2A4A;
                color: #666666;
                border: 2px solid #444444;
            }
        """)
        self.submit_btn.clicked.connect(self._on_submit)
        main_layout.addWidget(self.submit_btn)

    # ----------------------------------------------------------------
    def _build_available_column(self):
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: rgba(26, 42, 74, 0.3);
                border: 1px solid #2B4A6F;
                border-radius: 8px;
            }
        """)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        header = QLabel("اقدامات در دسترس")
        header.setFont(
            QFont(FONT_FAMILY, 12, QFont.Weight.Bold)
        )
        header.setStyleSheet("color: #4FC3F7; border: none;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(
            "QScrollArea { background-color: transparent; "
            "border: none; }"
        )

        content = QWidget()
        content.setStyleSheet("background-color: transparent;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(2, 2, 2, 2)
        content_layout.setSpacing(6)

        # shuffle
        import random
        shuffled = list(self.action_list)
        random.shuffle(shuffled)
        print(
            f"   [SPA-01] ترتیب shuffle شده: "
            f"{[a['id'] for a in shuffled]}"
        )

        for action in shuffled:
            card = _DraggableCard(action)
            content_layout.addWidget(card)
            self.action_cards[action["id"]] = card

        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)

        return container

    # ----------------------------------------------------------------
    def _build_slots_column(self):
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 143, 0, 0.05);
                border: 2px dashed #FF8F00;
                border-radius: 8px;
            }
        """)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        header = QLabel("ترتیب اقدامات")
        header.setFont(
            QFont(FONT_FAMILY, 12, QFont.Weight.Bold)
        )
        header.setStyleSheet(
            "color: #FF8F00; border: none;"
        )
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        for i in range(len(self.correct_order)):
            slot = _DropSlot(i)
            slot.dropped.connect(self._on_slot_dropped)
            slot.cleared.connect(self._on_slot_cleared)
            layout.addWidget(slot)
            self.slots.append(slot)

        layout.addStretch()
        return container

    # ================================================================
    def _on_slot_dropped(self, slot_index: int, action_id: str):
        if self.is_done:
            return
        if action_id in self.sequence:
            # کارت قبلاً استفاده شده
            return

        if self.first_action_time == 0:
            self.first_action_time = (
                int(time.time() * 1000) - self.start_time
            )

        # اگر جایگاه قبلاً پر است، کارت قبلی را آزاد کن
        existing = self.slots[slot_index].get_action_id()
        if existing is not None:
            if existing in self.sequence:
                self.sequence.remove(existing)
            # برگرداندن کارت به حالت فعال
            self._set_card_active(existing, True)

        # پر کردن جایگاه
        action = self.action_map.get(action_id, {})
        self.slots[slot_index].set_action(
            action_id,
            action.get("name", "?"),
            action.get("icon", "●"),
        )
        self._set_card_active(action_id, False)

        # به‌روزرسانی sequence
        self.sequence = []
        for slot in self.slots:
            sid = slot.get_action_id()
            if sid is not None:
                self.sequence.append(sid)

        self._update_buttons()

    def _on_slot_cleared(self, slot_index: int):
        if self.is_done:
            return
        action_id = self.slots[slot_index].get_action_id()
        if action_id is None:
            return

        self.slots[slot_index].clear_action()
        if action_id in self.sequence:
            self.sequence.remove(action_id)
        self._set_card_active(action_id, True)

        # به‌روزرسانی sequence
        self.sequence = []
        for slot in self.slots:
            sid = slot.get_action_id()
            if sid is not None:
                self.sequence.append(sid)

        self._update_buttons()

    # ----------------------------------------------------------------
    def _set_card_active(self, action_id: str, active: bool):
        card = self.action_cards.get(action_id)
        if card is None:
            return
        card._is_disabled = not active
        if active:
            card.setVisible(True)
            card.setStyleSheet("""
                QFrame#actionCard {
                    background-color: rgba(26, 42, 74, 0.85);
                    border: 2px solid #4FC3F7;
                    border-radius: 8px;
                }
                QFrame#actionCard:hover {
                    background-color: rgba(79, 195, 247, 0.20);
                    border: 2px solid #FFFFFF;
                }
            """)
        else:
            card.setStyleSheet("""
                QFrame#actionCard {
                    background-color: rgba(26, 42, 74, 0.3);
                    border: 2px solid #444444;
                    border-radius: 8px;
                }
            """)

    def _update_buttons(self):
        self.submit_btn.setEnabled(
            len(self.sequence) == len(self.correct_order)
        )

    # ================================================================
    def _on_submit(self):
        if self.is_done:
            return
        if len(self.sequence) != len(self.correct_order):
            return
        self.is_done = True

        total_time = int(time.time() * 1000) - self.start_time

        distractor_ids = [
            a["id"] for a in self.action_list
            if a.get("is_distractor", False)
        ]

        score = self._sequence_score(
            self.sequence, self.correct_order, distractor_ids
        )

        distractor_used = [
            item for item in self.sequence
            if item in distractor_ids
        ]

        result = {
            "sequence": list(self.sequence),
            "correct_order": list(self.correct_order),
            "sequence_score": score,
            "planning_time_ms": self.first_action_time,
            "total_time_ms": total_time,
            "distractor_ids": distractor_ids,
            "distractor_used": distractor_used,
            "distractor_count": len(distractor_used),
        }
        print(f"   [DEBUG] نتیجه SPA-01: {result}")
        self.board_done.emit(result)

    def _sequence_score(self, seq: list, correct: list,
                         distractor_ids: list | None = None) -> float:
        if distractor_ids is None:
            distractor_ids = []

        m, n = len(seq), len(correct)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if seq[i - 1] == correct[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1] + 1
                else:
                    dp[i][j] = max(
                        dp[i - 1][j], dp[i][j - 1]
                    )

        base_score = dp[m][n] / max(1, n)
        distractor_count = sum(
            1 for item in seq if item in distractor_ids
        )
        penalty = distractor_count * 0.15

        final = max(0.0, base_score - penalty)
        return round(final, 3)