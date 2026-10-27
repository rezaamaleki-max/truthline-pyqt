"""
ویجت پازل ترکیب — CFI-01
نسخه 3.0 — با Drag & Drop به سینی ترکیب

تغییرات نسخه 3.0:
- کشیدن آیکون‌ها به سینی ترکیب وسط صفحه
- انیمیشن sparkle هنگام موفقیت
- افکت قرمز هنگام شکست
- حفظ سنجش قدیمی (attempted_combinations)

نسخه: 3.0.0
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QMessageBox, QGridLayout
)
from PyQt6.QtCore import (
    Qt, QTimer, pyqtSignal, QMimeData, QPoint, QRectF, QPointF
)
from PyQt6.QtGui import (
    QDrag, QFont, QPainter, QPixmap, QColor, QPen, QBrush
)
import time
import random
import math

FONT_FAMILY = "Vazirmatn"
MIME_TYPE = "application/x-truthline-puzzle-item-id"


# ====================================================================
# کارت آیتم قابل کشیدن
# ====================================================================
class _DraggableItem(QFrame):
    """آیتم قابل کشیدن به سینی"""

    def __init__(self, item: dict, parent=None):
        super().__init__(parent)
        self.item_id = item["id"]
        self._drag_start: QPoint | None = None
        self._used = False

        self.setObjectName("puzzleItem")
        self._apply_style()
        self.setMinimumHeight(80)
        self.setMaximumHeight(90)
        self.setCursor(Qt.CursorShape.OpenHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(3)

        # ردیف بالا: آیکون + نام
        top_row = QHBoxLayout()
        top_row.setSpacing(6)

        icon_lbl = QLabel(item.get("icon", "●"))
        icon_lbl.setFont(QFont("Arial", 18))
        icon_lbl.setStyleSheet("border: none;")
        icon_lbl.setFixedWidth(24)
        icon_lbl.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents, True
        )
        top_row.addWidget(icon_lbl)

        name_lbl = QLabel(item["name"])
        name_lbl.setFont(
            QFont(FONT_FAMILY, 11, QFont.Weight.Bold)
        )
        name_lbl.setStyleSheet(
            "color: #FFFFFF; border: none;"
        )
        name_lbl.setWordWrap(True)
        name_lbl.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents, True
        )
        top_row.addWidget(name_lbl, 1)

        layout.addLayout(top_row)

        brief_lbl = QLabel(item.get("brief", ""))
        brief_lbl.setFont(QFont(FONT_FAMILY, 9))
        brief_lbl.setStyleSheet(
            "color: #B0BEC5; border: none;"
        )
        brief_lbl.setWordWrap(True)
        brief_lbl.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents, True
        )
        layout.addWidget(brief_lbl)

        self.hint_lbl = QLabel("← بکشید به سینی")
        self.hint_lbl.setFont(QFont(FONT_FAMILY, 8))
        self.hint_lbl.setStyleSheet(
            "color: #90A4AE; border: none; "
            "font-style: italic;"
        )
        self.hint_lbl.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents, True
        )
        layout.addWidget(self.hint_lbl)

    def _apply_style(self):
        self.setStyleSheet("""
            QFrame#puzzleItem {
                background-color: rgba(26, 42, 74, 0.85);
                border: 2px solid #4FC3F7;
                border-radius: 8px;
            }
            QFrame#puzzleItem:hover {
                background-color: rgba(79, 195, 247, 0.15);
                border: 2px solid #FFFFFF;
            }
        """)

    def set_used(self, used: bool):
        self._used = used
        if used:
            self.setStyleSheet("""
                QFrame#puzzleItem {
                    background-color: rgba(26, 42, 74, 0.3);
                    border: 2px solid #444444;
                    border-radius: 8px;
                }
            """)
            self.hint_lbl.setText("در سینی")
            self.setCursor(Qt.CursorShape.ForbiddenCursor)
        else:
            self._apply_style()
            self.hint_lbl.setText("← بکشید به سینی")
            self.setCursor(Qt.CursorShape.OpenHandCursor)

    # ----------------------------------------------------------------
    def mousePressEvent(self, event):  # type: ignore
        if self._used:
            return
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):  # type: ignore
        if not self._used:
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        self._drag_start = None
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):  # type: ignore
        if self._used or self._drag_start is None:
            return
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        dist = (event.pos() - self._drag_start).manhattanLength()
        if dist < 8:
            return

        drag = QDrag(self)
        mime = QMimeData()
        mime.setData(MIME_TYPE, self.item_id.encode("utf-8"))
        drag.setMimeData(mime)

        pixmap = self.grab()
        faded = QPixmap(pixmap.size())
        faded.fill(Qt.GlobalColor.transparent)
        painter = QPainter(faded)
        painter.setOpacity(0.85)
        painter.drawPixmap(0, 0, pixmap)
        painter.end()
        drag.setPixmap(faded)
        drag.setHotSpot(event.pos())

        drag.exec(Qt.DropAction.MoveAction)
        if not self._used:
            self.setCursor(Qt.CursorShape.OpenHandCursor)


# ====================================================================
# سینی ترکیب
# ====================================================================
class _CombineTray(QFrame):
    """سینی ترکیب — Drop target برای دو آیتم"""

    item_dropped = pyqtSignal(str)
    item_removed = pyqtSignal(str)
    combine_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("combineTray")
        self.setAcceptDrops(True)
        self.setMinimumHeight(120)
        self.setMaximumHeight(140)
        self._items: list = []
        self._flash_color: QColor | None = None
        self._flash_alpha: float = 0.0

        # انیمیشن flash
        self._flash_timer = QTimer(self)
        self._flash_timer.timeout.connect(self._decay_flash)

        self._apply_style()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        self.left_slot = _TraySlot("جایگاه اول")
        self.left_slot.removed.connect(self._on_slot_removed)
        layout.addWidget(self.left_slot, 1)

        plus_lbl = QLabel("+")
        plus_lbl.setFont(QFont("Arial", 28, QFont.Weight.Bold))
        plus_lbl.setStyleSheet(
            "color: #4FC3F7; border: none;"
        )
        plus_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(plus_lbl)

        self.right_slot = _TraySlot("جایگاه دوم")
        self.right_slot.removed.connect(self._on_slot_removed)
        layout.addWidget(self.right_slot, 1)

        # دکمه‌ی ترکیب
        self.combine_btn = QPushButton("⚡ ترکیب")
        self.combine_btn.setFont(
            QFont(FONT_FAMILY, 13, QFont.Weight.Bold)
        )
        self.combine_btn.setMinimumHeight(70)
        self.combine_btn.setMinimumWidth(120)
        self.combine_btn.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.combine_btn.setFocusPolicy(
            Qt.FocusPolicy.NoFocus
        )
        self.combine_btn.setEnabled(False)
        self.combine_btn.setStyleSheet("""
            QPushButton {
                background-color: #2B4A6F;
                color: #FFFFFF;
                border: 2px solid #4FC3F7;
                border-radius: 10px;
                padding: 10px;
                font-weight: bold;
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
        self.combine_btn.clicked.connect(
            self.combine_requested.emit
        )
        layout.addWidget(self.combine_btn)

    def _apply_style(self):
        self.setStyleSheet("""
            QFrame#combineTray {
                background-color: rgba(79, 195, 247, 0.06);
                border: 2px dashed #4FC3F7;
                border-radius: 12px;
            }
        """)

    # ----------------------------------------------------------------
    def get_items(self) -> list:
        return [self.left_slot.item_id, self.right_slot.item_id]

    def add_item(self, item_id: str, name: str, icon: str):
        if self.left_slot.item_id is None:
            self.left_slot.set_item(item_id, name, icon)
        elif self.right_slot.item_id is None:
            self.right_slot.set_item(item_id, name, icon)
        else:
            # جایگزینی آیتم اول
            old = self.left_slot.item_id
            self.left_slot.set_item(item_id, name, icon)
            if old is not None:
                self.item_removed.emit(old)
        self._update_combine_state()

    def clear_items(self):
        old1 = self.left_slot.item_id
        old2 = self.right_slot.item_id
        self.left_slot.clear_item()
        self.right_slot.clear_item()
        if old1 is not None:
            self.item_removed.emit(old1)
        if old2 is not None:
            self.item_removed.emit(old2)
        self._update_combine_state()

    def _on_slot_removed(self, item_id: str):
        self.item_removed.emit(item_id)
        self._update_combine_state()

    def _update_combine_state(self):
        ready = (
            self.left_slot.item_id is not None
            and self.right_slot.item_id is not None
        )
        self.combine_btn.setEnabled(ready)

    # ----------------------------------------------------------------
    def flash(self, color: str, duration_ms: int = 800):
        """فلاش رنگی روی سینی"""
        self._flash_color = QColor(color)
        self._flash_alpha = 0.9
        self._flash_timer.start(30)
        QTimer.singleShot(duration_ms, self._flash_timer.stop)

    def _decay_flash(self):
        self._flash_alpha = max(0.0, self._flash_alpha - 0.05)
        self.update()
        if self._flash_alpha <= 0.01:
            self._flash_timer.stop()

    def paintEvent(self, event):  # type: ignore
        # اول paintEvent پیش‌فرض
        super().paintEvent(event)
        # سپس فلاش رنگی
        if self._flash_color is not None and self._flash_alpha > 0:
            painter = QPainter(self)
            painter.setRenderHint(
                QPainter.RenderHint.Antialiasing
            )
            c = QColor(self._flash_color)
            c.setAlpha(int(100 * self._flash_alpha))
            painter.setBrush(QBrush(c))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(
                QRectF(self.rect()), 12, 12
            )
            painter.end()

    # ----------------------------------------------------------------
    def dragEnterEvent(self, event):  # type: ignore
        if event.mimeData().hasFormat(MIME_TYPE):
            event.acceptProposedAction()

    def dropEvent(self, event):  # type: ignore
        if event.mimeData().hasFormat(MIME_TYPE):
            item_id = bytes(
                event.mimeData().data(MIME_TYPE)
            ).decode("utf-8")
            self.item_dropped.emit(item_id)
            event.acceptProposedAction()


# ====================================================================
# جایگاه داخل سینی
# ====================================================================
class _TraySlot(QFrame):
    removed = pyqtSignal(str)

    def __init__(self, placeholder: str, parent=None):
        super().__init__(parent)
        self.item_id: str | None = None
        self._placeholder = placeholder

        self.setObjectName("traySlot")
        self.setMinimumHeight(76)
        self.setStyleSheet("""
            QFrame#traySlot {
                background-color: rgba(26, 42, 74, 0.6);
                border: 1px dashed #4FC3F7;
                border-radius: 8px;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(8)

        self.icon_lbl = QLabel("—")
        self.icon_lbl.setFont(QFont("Arial", 22))
        self.icon_lbl.setStyleSheet("border: none;")
        self.icon_lbl.setFixedWidth(32)
        layout.addWidget(self.icon_lbl)

        self.name_lbl = QLabel(placeholder)
        self.name_lbl.setFont(QFont(FONT_FAMILY, 11))
        self.name_lbl.setStyleSheet(
            "color: #666666; border: none; "
            "font-style: italic;"
        )
        layout.addWidget(self.name_lbl, 1)

        self.clear_btn = QPushButton("✕")
        self.clear_btn.setFont(QFont(FONT_FAMILY, 12))
        self.clear_btn.setFixedSize(26, 26)
        self.clear_btn.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.clear_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
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
        self.clear_btn.clicked.connect(self._on_clear)
        layout.addWidget(self.clear_btn)

    def set_item(self, item_id: str, name: str, icon: str):
        self.item_id = item_id
        self.icon_lbl.setText(icon)
        self.name_lbl.setText(name)
        self.name_lbl.setStyleSheet(
            "color: #FFFFFF; border: none;"
        )
        self.clear_btn.setVisible(True)

    def clear_item(self):
        self.item_id = None
        self.icon_lbl.setText("—")
        self.name_lbl.setText(self._placeholder)
        self.name_lbl.setStyleSheet(
            "color: #666666; border: none; "
            "font-style: italic;"
        )
        self.clear_btn.setVisible(False)

    def _on_clear(self):
        if self.item_id is not None:
            old = self.item_id
            self.clear_item()
            self.removed.emit(old)


# ====================================================================
# ویجت اصلی پازل
# ====================================================================
class PuzzleWidget(QWidget):
    """پازل ترکیب — با Drag&Drop"""

    puzzle_done = pyqtSignal(dict)

    def __init__(self, items: list, valid_combinations: list,
                 solution_hint: str = "", parent=None):
        super().__init__(parent)
        self.items = items
        self.valid_combinations = [
            set(c) for c in valid_combinations
        ]
        self.solution_hint = solution_hint

        self.start_time = int(time.time() * 1000)
        self.attempted_combinations: list = []
        self.solved = False
        self.solution_time_ms = 0

        self.item_map = {i["id"]: i for i in items}
        self.item_cards: dict = {}
        self._sparkles: list = []

        # انیمیشن sparkle
        self._sparkle_timer = QTimer(self)
        self._sparkle_timer.timeout.connect(self._tick_sparkles)

        self._setup_ui()
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

    # ================================================================
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 12, 30, 12)
        main_layout.setSpacing(10)

        title = QLabel("در قفل‌شده")
        tf = QFont(FONT_FAMILY, 18)
        tf.setBold(True)
        title.setFont(tf)
        title.setStyleSheet("color: #4FC3F7;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        desc = QLabel(
            "دو آیتم را بکشید و در سینی ترکیب رها کنید. "
            "سپس دکمه‌ی «ترکیب» را بزنید."
        )
        desc.setFont(QFont(FONT_FAMILY, 11))
        desc.setStyleSheet("color: #CCCCCC;")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        main_layout.addWidget(desc)

        # سینی ترکیب
        self.tray = _CombineTray()
        self.tray.item_dropped.connect(self._on_item_dropped)
        self.tray.item_removed.connect(self._on_item_removed)
        self.tray.combine_requested.connect(self._on_combine)
        main_layout.addWidget(self.tray)

        # آیتم‌ها
        items_label = QLabel("آیتم‌های موجود:")
        items_label.setFont(
            QFont(FONT_FAMILY, 12, QFont.Weight.Bold)
        )
        items_label.setStyleSheet("color: #FFFFFF;")
        main_layout.addWidget(items_label)

        # ✅ چیدمان دوستونی
        items_grid = QGridLayout()
        items_grid.setHorizontalSpacing(8)
        items_grid.setVerticalSpacing(6)

        for i, item in enumerate(self.items):
            row = i // 2
            col = i % 2
            card = _DraggableItem(item)
            items_grid.addWidget(card, row, col)
            self.item_cards[item["id"]] = card

        main_layout.addLayout(items_grid)
        main_layout.addStretch()

    # ================================================================
    def _on_item_dropped(self, item_id: str):
        if self.solved:
            return
        item = self.item_map.get(item_id)
        if item is None:
            return

        # اگر قبلاً در سینی است، نادیده بگیر
        current = self.tray.get_items()
        if item_id in current:
            return

        self.tray.add_item(
            item_id, item["name"], item.get("icon", "●")
        )
        # به‌روزرسانی کارت
        card = self.item_cards.get(item_id)
        if card is not None:
            card.set_used(True)

        # صدای drop
        try:
            from core.audio_manager import get_audio_manager
            get_audio_manager().play_sfx("click")
        except Exception:
            pass

    def _on_item_removed(self, item_id: str):
        card = self.item_cards.get(item_id)
        if card is not None:
            card.set_used(False)

    # ================================================================
    def _on_combine(self):
        if self.solved:
            return

        items = self.tray.get_items()
        if None in items or len(items) != 2:
            return

        # ✅ پخش صدای دکمه‌ی ترکیب
        try:
            from core.audio_manager import get_audio_manager
            get_audio_manager().play_sfx("scan")
        except Exception:
            pass

        combo = set(items)
        self.attempted_combinations.append(
            tuple(sorted(items))
        )
        print(f"   [CFI-01] تلاش: {items}")

        if any(combo == vc for vc in self.valid_combinations):
            # موفق
            self.solved = True
            self.solution_time_ms = (
                int(time.time() * 1000) - self.start_time
            )
            print(
                f"   [CFI-01] حل شد در "
                f"{self.solution_time_ms}ms"
            )

            # افکت sparkle سبز
            self.tray.flash("#4CAF50", duration_ms=1200)
            self._spawn_sparkles(success=True)

            QTimer.singleShot(600, self._show_success_msg)
            return

        # ناموفق
        self.tray.flash("#D32F2F", duration_ms=800)
        print(f"   [CFI-01] ترکیب نامعتبر: {items}")

        # پیام کوتاه
        msg = QMessageBox(self)
        msg.setWindowTitle("نتیجه")
        msg.setText(
            "این ترکیب راه‌حل نداد. دوباره فکر کن؛ "
            "شاید ترکیب متفاوتی لازم باشه."
        )
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        msg.exec()

        # پاک کردن سینی
        self.tray.clear_items()

    def _show_success_msg(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("موفقیت")
        msg.setText(
            f"✓ ترکیب صحیح!\n\n{self.solution_hint}"
        )
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        msg.exec()
        QTimer.singleShot(200, self._finalize)

    # ================================================================
    def _spawn_sparkles(self, success: bool = True):
        """تولید sparkles"""
        color = "#4CAF50" if success else "#D32F2F"
        center = self.tray.rect().center()
        tray_pos = self.tray.pos()

        for _ in range(20):
            self._sparkles.append({
                "x": center.x() + random.uniform(-80, 80),
                "y": center.y() + random.uniform(-40, 40),
                "vx": random.uniform(-1.5, 1.5),
                "vy": random.uniform(-2.0, -0.5),
                "life": 1.0,
                "size": random.uniform(2, 5),
                "color": color,
                "offset_x": tray_pos.x(),
                "offset_y": tray_pos.y(),
            })
        self._sparkle_timer.start(30)
        self.update()

    def _tick_sparkles(self):
        alive = []
        for s in self._sparkles:
            s["life"] -= 0.04
            s["x"] += s["vx"]
            s["y"] += s["vy"]
            s["vy"] += 0.08  # گرانش
            if s["life"] > 0:
                alive.append(s)
        self._sparkles = alive
        self.update()
        if not self._sparkles:
            self._sparkle_timer.stop()

    def paintEvent(self, event):  # type: ignore
        super().paintEvent(event)
        if not self._sparkles:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)

        for s in self._sparkles:
            c = QColor(s["color"])
            c.setAlpha(int(255 * s["life"]))
            painter.setBrush(QBrush(c))
            painter.drawEllipse(
                QPointF(s["x"], s["y"]),
                s["size"] * s["life"],
                s["size"] * s["life"],
            )

        painter.end()

    # ================================================================
    def _finalize(self):
        unique = len(set(self.attempted_combinations))
        total_attempts = len(self.attempted_combinations)
        old_attempts = total_attempts - 1

        result = {
            "solved": self.solved,
            "solution_time_ms": self.solution_time_ms,
            "attempted_combinations": list(
                self.attempted_combinations
            ),
            "total_attempts": total_attempts,
            "unique_attempts": unique,
            "old_solution_attempts": max(0, old_attempts),
        }
        print(f"   [DEBUG] نتیجه CFI-01: {result}")
        self.puzzle_done.emit(result)