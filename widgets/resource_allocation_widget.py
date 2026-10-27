"""
ویجت تخصیص منابع اضطراری — SPA-02
نسخه 4.0 — با Drag & Drop واقعی

تغییرات نسخه 4.0:
- منابع به‌صورت کارت‌های قابل کشیدن
- بخش‌ها به‌عنوان Drop target
- تایمر Sticky در بالا (همیشه در دید)
- بدون خطوط ارتباطی بین بخش‌ها

نسخه: 4.0.0
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QProgressBar, QMessageBox, QGridLayout, QScrollArea
)
from PyQt6.QtCore import (
    Qt, QTimer, pyqtSignal, QMimeData, QPoint
)
from PyQt6.QtGui import (
    QDrag, QFont, QPainter, QPixmap
)
import time

FONT_FAMILY = "Vazirmatn"
MIME_TYPE_RESOURCE = "application/x-truthline-resource-id"

RESOURCE_ICONS = {
    "battery": "🔋",
    "oxygen": "💊",
    "software": "💻",
}
RESOURCE_NAMES = {
    "battery": "باتری پر قدرت",
    "oxygen": "کپسول اکسیژن",
    "software": "کیت نرم‌افزاری",
}


# ====================================================================
# کارت منبع قابل کشیدن
# ====================================================================
class _DraggableResource(QFrame):
    """کارت منبع که می‌توان آن را کشید"""

    def __init__(self, resource: dict, parent=None):
        super().__init__(parent)
        self.resource_id = resource["id"]
        self._drag_start: QPoint | None = None

        self.setObjectName("resourceCard")
        self._apply_available_style()
        self.setMinimumHeight(64)
        self.setCursor(Qt.CursorShape.OpenHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)

        icon = RESOURCE_ICONS.get(self.resource_id, "●")
        name = RESOURCE_NAMES.get(
            self.resource_id, resource.get("name", "")
        )

        self.icon_lbl = QLabel(icon)
        self.icon_lbl.setFont(QFont("Arial", 22))
        self.icon_lbl.setStyleSheet("border: none;")
        self.icon_lbl.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents, True
        )
        layout.addWidget(self.icon_lbl)

        self.name_lbl = QLabel(name)
        self.name_lbl.setFont(
            QFont(FONT_FAMILY, 12, QFont.Weight.Bold)
        )
        self.name_lbl.setStyleSheet(
            "color: #FFFFFF; border: none;"
        )
        self.name_lbl.setLayoutDirection(
            Qt.LayoutDirection.RightToLeft
        )
        self.name_lbl.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents, True
        )
        layout.addWidget(self.name_lbl, 1)

        self.hint_lbl = QLabel("برای تخصیص بکشید")
        self.hint_lbl.setFont(QFont(FONT_FAMILY, 9))
        self.hint_lbl.setStyleSheet(
            "color: #90A4AE; border: none; "
            "font-style: italic;"
        )
        self.hint_lbl.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents, True
        )
        layout.addWidget(self.hint_lbl)

    def _apply_available_style(self):
        self.setStyleSheet("""
            QFrame#resourceCard {
                background-color: #1A2A4A;
                border: 2px solid #4FC3F7;
                border-radius: 10px;
            }
            QFrame#resourceCard:hover {
                background-color: #2B4A6F;
                border: 2px solid #FFFFFF;
            }
        """)

    def set_used(self, used: bool):
        """وقتی منبع تخصیص یافت"""
        if used:
            self.setStyleSheet("""
                QFrame#resourceCard {
                    background-color: rgba(11, 29, 58, 0.5);
                    border: 2px solid #444444;
                    border-radius: 10px;
                }
            """)
            self.name_lbl.setStyleSheet(
                "color: #666666; border: none; "
                "text-decoration: line-through;"
            )
            self.hint_lbl.setText("استفاده‌شده")
            self.hint_lbl.setStyleSheet(
                "color: #666666; border: none; "
                "font-style: italic;"
            )
            self.setCursor(Qt.CursorShape.ForbiddenCursor)
        else:
            self._apply_available_style()
            self.name_lbl.setStyleSheet(
                "color: #FFFFFF; border: none;"
            )
            self.hint_lbl.setText("برای تخصیص بکشید")
            self.hint_lbl.setStyleSheet(
                "color: #90A4AE; border: none; "
                "font-style: italic;"
            )
            self.setCursor(Qt.CursorShape.OpenHandCursor)

    # ----------------------------------------------------------------
    def mousePressEvent(self, event):  # type: ignore
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):  # type: ignore
        if self.cursor().shape() != Qt.CursorShape.ForbiddenCursor:
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        self._drag_start = None
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):  # type: ignore
        if self._drag_start is None:
            return
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        if self.cursor().shape() == Qt.CursorShape.ForbiddenCursor:
            return

        dist = (event.pos() - self._drag_start).manhattanLength()
        if dist < 8:
            return

        drag = QDrag(self)
        mime = QMimeData()
        mime.setData(
            MIME_TYPE_RESOURCE, self.resource_id.encode("utf-8")
        )
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
        if self.cursor().shape() != Qt.CursorShape.ForbiddenCursor:
            self.setCursor(Qt.CursorShape.OpenHandCursor)


# ====================================================================
# کارت بخش (Drop target)
# ====================================================================
class _SectionCard(QFrame):
    """بخش ایستگاه — Drop target برای منبع"""

    dropped = pyqtSignal(str, str)   # section_id, resource_id
    cleared = pyqtSignal(str)         # section_id
    info_clicked = pyqtSignal(str)    # section_id
    selected = pyqtSignal(str)        # section_id (کلیک روی بدنه)

    def __init__(self, section: dict, parent=None):
        super().__init__(parent)
        self.section_id = section["id"]
        self.section_name = section["name"]
        self._allocated_resource: str | None = None
        self._is_highlighted = False

        self.setObjectName("sectionCard")
        self.setAcceptDrops(True)
        self.setMinimumHeight(84)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._apply_style()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)

        # سرصفحه
        head = QHBoxLayout()
        head.setSpacing(6)

        name_lbl = QLabel(section["name"])
        name_lbl.setFont(
            QFont(FONT_FAMILY, 13, QFont.Weight.Bold)
        )
        name_lbl.setStyleSheet(
            "color: #FFFFFF; border: none;"
        )
        name_lbl.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents, True
        )
        head.addWidget(name_lbl, 1)

        self.info_btn = QPushButton("ℹ️")
        self.info_btn.setFont(
            QFont(FONT_FAMILY, 11, QFont.Weight.Bold)
        )
        self.info_btn.setFixedSize(32, 28)
        self.info_btn.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.info_btn.setFocusPolicy(
            Qt.FocusPolicy.NoFocus
        )
        self.info_btn.setToolTip(
            "مشاهده اطلاعات این بخش"
        )
        self.info_btn.setStyleSheet("""
            QPushButton {
                background-color: #2B4A6F;
                color: #FFB74D;
                border: 2px solid #FF8F00;
                border-radius: 6px;
                padding: 2px;
            }
            QPushButton:hover {
                background-color: #FF8F00;
                color: #0B1D3A;
            }
            QPushButton:checked {
                background-color: #4CAF50;
                color: #FFFFFF;
                border: 2px solid #FFFFFF;
            }
        """)
        self.info_btn.clicked.connect(
            lambda: self.info_clicked.emit(self.section_id)
        )
        head.addWidget(self.info_btn)

        layout.addLayout(head)

        # ردیف تخصیص
        alloc_row = QHBoxLayout()
        alloc_row.setSpacing(6)

        self.resource_lbl = QLabel("[—]")
        self.resource_lbl.setFont(QFont(FONT_FAMILY, 11))
        self.resource_lbl.setStyleSheet(
            "color: #666666; border: none; "
            "font-style: italic;"
        )
        self.resource_lbl.setLayoutDirection(
            Qt.LayoutDirection.RightToLeft
        )
        self.resource_lbl.setAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignAbsolute
        )
        self.resource_lbl.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents, True
        )
        alloc_row.addWidget(self.resource_lbl, 1)

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
        self.clear_btn.clicked.connect(self._on_clear_clicked)
        alloc_row.addWidget(self.clear_btn)

        layout.addLayout(alloc_row)

    # ----------------------------------------------------------------
    def _apply_style(self):
        if self._is_highlighted:
            self.setStyleSheet("""
                QFrame#sectionCard {
                    background-color: rgba(79, 195, 247, 0.20);
                    border: 2px solid #FFFFFF;
                    border-radius: 8px;
                }
            """)
        elif self._allocated_resource is not None:
            self.setStyleSheet("""
                QFrame#sectionCard {
                    background-color: rgba(76, 175, 80, 0.10);
                    border: 2px solid #4CAF50;
                    border-radius: 8px;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame#sectionCard {
                    background-color: rgba(26, 42, 74, 0.7);
                    border: 2px solid #4FC3F7;
                    border-radius: 8px;
                }
            """)

    # ----------------------------------------------------------------
    def get_allocated_resource(self) -> str | None:
        return self._allocated_resource

    def set_allocated(self, resource_id: str):
        self._allocated_resource = resource_id
        icon = RESOURCE_ICONS.get(resource_id, "●")
        name = RESOURCE_NAMES.get(resource_id, resource_id)
        self.resource_lbl.setText(f"[{icon} {name}]")
        self.resource_lbl.setStyleSheet(
            "color: #4CAF50; border: none; "
            "font-weight: bold; font-style: normal;"
        )
        self.clear_btn.setVisible(True)
        self._apply_style()

    def clear_allocation(self):
        self._allocated_resource = None
        self.resource_lbl.setText("[—]")
        self.resource_lbl.setStyleSheet(
            "color: #666666; border: none; "
            "font-style: italic;"
        )
        self.clear_btn.setVisible(False)
        self._apply_style()

    def set_selected_border(self, selected: bool):
        """افزودن حاشیه‌ی نارنجی برای بخش انتخاب‌شده"""
        if selected:
            self.setStyleSheet("""
                QFrame#sectionCard {
                    background-color: rgba(26, 42, 74, 0.7);
                    border: 3px solid #FF8F00;
                    border-radius: 8px;
                }
            """)
        else:
            self._apply_style()

    # ----------------------------------------------------------------
    def mousePressEvent(self, event):  # type: ignore
        if event.button() == Qt.MouseButton.LeftButton:
            self.selected.emit(self.section_id)
        super().mousePressEvent(event)

    # ----------------------------------------------------------------
    def dragEnterEvent(self, event):  # type: ignore
        if event.mimeData().hasFormat(MIME_TYPE_RESOURCE):
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
        if event.mimeData().hasFormat(MIME_TYPE_RESOURCE):
            resource_id = bytes(
                event.mimeData().data(MIME_TYPE_RESOURCE)
            ).decode("utf-8")
            self.dropped.emit(self.section_id, resource_id)
            event.acceptProposedAction()
        else:
            event.ignore()

    def _on_clear_clicked(self):
        if self._allocated_resource is not None:
            self.cleared.emit(self.section_id)


# ====================================================================
# ویجت اصلی
# ====================================================================
class ResourceAllocationWidget(QWidget):
    """تخصیص منابع اضطراری — با Drag&Drop"""

    allocation_done = pyqtSignal(dict)

    def __init__(self, sections: list, resources: list,
                 time_limit_sec: int = 90, parent=None):
        super().__init__(parent)
        self.sections = sections
        self.resources = resources
        self.time_limit_sec = time_limit_sec

        self.start_time = int(time.time() * 1000)
        self.allocations: dict = {}
        self.info_checked: list = []
        self.info_check_times: dict = {}
        self._last_info_check_start = 0
        self._current_info_section: str | None = None
        self._selected_section: str | None = None
        self.allocation_order: list = []
        self.time_to_first_allocation_ms = 0
        self.timed_out = False
        self.submitted = False
        self.is_done = False

        self._remaining_sec = time_limit_sec
        self.countdown_timer = QTimer(self)
        self.countdown_timer.timeout.connect(self._tick)

        self.section_cards: dict = {}
        self.resource_cards: dict = {}

        self._setup_ui()
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

    # ================================================================
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 10, 20, 10)
        main_layout.setSpacing(8)

        # ============================================================
        # بخش ۱: سرصفحه‌ی ثابت (تایمر + راهنما + اطلاعات)
        # ============================================================
        header_widget = QWidget()
        header_layout = QVBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(6)

        # --- تایمر ---
        timer_frame = QFrame()
        timer_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(11, 29, 58, 0.95);
                border: 2px solid #4CAF50;
                border-radius: 8px;
                padding: 6px;
            }
        """)
        timer_layout = QVBoxLayout(timer_frame)
        timer_layout.setSpacing(4)
        timer_layout.setContentsMargins(10, 6, 10, 6)

        top = QHBoxLayout()
        title = QLabel("تخصیص منابع اضطراری")
        tf = QFont(FONT_FAMILY, 16)
        tf.setBold(True)
        title.setFont(tf)
        title.setStyleSheet("color: #4FC3F7; border: none;")
        top.addWidget(title)
        top.addStretch()

        self.timer_label = QLabel(f"⏱  {self.time_limit_sec}s")
        tlf = QFont(FONT_FAMILY, 20)
        tlf.setBold(True)
        self.timer_label.setFont(tlf)
        self.timer_label.setStyleSheet("color: #4CAF50; border: none;")
        top.addWidget(self.timer_label)
        timer_layout.addLayout(top)

        self.time_bar = QProgressBar()
        self.time_bar.setRange(0, 100)
        self.time_bar.setValue(100)
        self.time_bar.setTextVisible(False)
        self.time_bar.setFixedHeight(10)
        self.time_bar.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self.time_bar.setStyleSheet("""
            QProgressBar {
                background-color: #1A2A4A;
                border: 1px solid #4FC3F7;
                border-radius: 4px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """)
        timer_layout.addWidget(self.time_bar)
        header_layout.addWidget(timer_frame)

        # --- راهنما ---
        guide_frame = QFrame()
        guide_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 143, 0, 0.10);
                border: 2px solid #FF8F00;
                border-radius: 6px;
            }
        """)
        guide_layout = QHBoxLayout(guide_frame)
        guide_layout.setContentsMargins(12, 4, 12, 4)

        guide_lbl = QLabel(
            "ℹ️  ابتدا روی هر بخش کلیک کنید تا اطلاعاتش را "
            "بخوانید، سپس منبع را بکشید و روی آن رها کنید."
        )
        guide_lbl.setFont(QFont(FONT_FAMILY, 10, QFont.Weight.Bold))
        guide_lbl.setStyleSheet("color: #FF8F00; border: none;")
        guide_lbl.setWordWrap(True)
        guide_layout.addWidget(guide_lbl)
        header_layout.addWidget(guide_frame)

        # --- اطلاعات بخش انتخاب‌شده ---
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(79, 195, 247, 0.08);
                border: 1px dashed #4FC3F7;
                border-radius: 6px;
            }
        """)
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(12, 6, 12, 6)
        info_layout.setSpacing(2)

        info_title = QLabel("اطلاعات بخش انتخاب‌شده:")
        info_title.setFont(
            QFont(FONT_FAMILY, 11, QFont.Weight.Bold)
        )
        info_title.setStyleSheet("color: #4FC3F7; border: none;")
        info_layout.addWidget(info_title)

        self.info_text = QLabel(
            "برای دیدن اطلاعات هر بخش، روی «ℹ️» آن کلیک کنید."
        )
        self.info_text.setFont(QFont(FONT_FAMILY, 12))
        self.info_text.setStyleSheet("color: #FFFFFF; border: none;")
        self.info_text.setWordWrap(True)
        self.info_text.setMinimumHeight(55)
        self.info_text.setMaximumHeight(85)
        info_layout.addWidget(self.info_text)

        header_layout.addWidget(info_frame)

        main_layout.addWidget(header_widget)

        # ============================================================
        # بخش ۲: ناحیه‌ی اسکرول‌شونده (منابع + بخش‌ها)
        # ============================================================
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(
            "QScrollArea { background-color: transparent; "
            "border: none; }"
        )
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background-color: transparent;")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(4, 4, 4, 4)
        scroll_layout.setSpacing(8)

        # --- منابع موجود (بالای بخش‌ها) ---
        res_label = QLabel("منابع موجود (برای تخصیص بکشید):")
        res_label.setFont(
            QFont(FONT_FAMILY, 12, QFont.Weight.Bold)
        )
        res_label.setStyleSheet("color: #FFFFFF;")
        scroll_layout.addWidget(res_label)

        resources_layout = QHBoxLayout()
        resources_layout.setSpacing(8)

        for resource in self.resources:
            card = _DraggableResource(resource)
            resources_layout.addWidget(card, 1)
            self.resource_cards[resource["id"]] = card

        scroll_layout.addLayout(resources_layout)

        # --- بخش‌های ایستگاه ---
        sections_label = QLabel("بخش‌های ایستگاه:")
        sections_label.setFont(
            QFont(FONT_FAMILY, 12, QFont.Weight.Bold)
        )
        sections_label.setStyleSheet("color: #FFFFFF;")
        scroll_layout.addWidget(sections_label)

        sections_grid = QGridLayout()
        sections_grid.setHorizontalSpacing(8)
        sections_grid.setVerticalSpacing(8)

        for i, section in enumerate(self.sections):
            row = i // 2
            col = i % 2
            card = _SectionCard(section)
            card.dropped.connect(self._on_section_dropped)
            card.cleared.connect(self._on_section_cleared)
            card.info_clicked.connect(self._on_info_click)
            card.selected.connect(self._on_section_selected)
            sections_grid.addWidget(card, row, col)
            self.section_cards[section["id"]] = card

        scroll_layout.addLayout(sections_grid)
        scroll_layout.addStretch()

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll, stretch=1)

        # ============================================================
        # بخش ۳: دکمه‌ی ثبت (پایین ثابت)
        # ============================================================
        self.submit_btn = QPushButton("ثبت تخصیص و ادامه")
        bf = QFont(FONT_FAMILY, 14)
        bf.setBold(True)
        self.submit_btn.setFont(bf)
        self.submit_btn.setMinimumHeight(44)
        self.submit_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.submit_btn.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.submit_btn.setStyleSheet("""
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
                border: 2px solid #FFFFFF;
            }
            QPushButton:disabled {
                background-color: #1A2A4A;
                color: #888888;
                border: 2px solid #444444;
            }
        """)
        self.submit_btn.clicked.connect(self._on_submit)
        main_layout.addWidget(self.submit_btn)

        self.countdown_timer.start(1000)

    # ================================================================
    # Drop / Clear
    # ================================================================
    def _on_section_dropped(self, section_id: str,
                             resource_id: str):
        if self.is_done:
            return
        # اگر این منبع قبلاً در جای دیگری تخصیص یافته
        if resource_id in self.allocations.values():
            return
        # اگر این بخش قبلاً پر است
        if section_id in self.allocations:
            return

        self.allocations[section_id] = resource_id
        self.allocation_order.append((section_id, resource_id))

        if self.time_to_first_allocation_ms == 0:
            self.time_to_first_allocation_ms = (
                int(time.time() * 1000) - self.start_time
            )

        # به‌روزرسانی کارت بخش
        card = self.section_cards.get(section_id)
        if card is not None:
            card.set_allocated(resource_id)
            if self._selected_section == section_id:
                card.set_selected_border(True)

        # به‌روزرسانی کارت منبع
        res_card = self.resource_cards.get(resource_id)
        if res_card is not None:
            res_card.set_used(True)

        print(
            f"   [DEBUG] تخصیص: بخش {section_id} ← {resource_id}"
        )

    def _on_section_cleared(self, section_id: str):
        if self.is_done:
            return
        if section_id not in self.allocations:
            return

        resource_id = self.allocations.pop(section_id)
        # حذف از allocation_order
        self.allocation_order = [
            (s, r) for s, r in self.allocation_order
            if not (s == section_id and r == resource_id)
        ]

        card = self.section_cards.get(section_id)
        if card is not None:
            card.clear_allocation()
            if self._selected_section == section_id:
                card.set_selected_border(True)

        res_card = self.resource_cards.get(resource_id)
        if res_card is not None:
            res_card.set_used(False)

    # ================================================================
    # انتخاب و اطلاعات
    # ================================================================
    def _on_section_selected(self, section_id: str):
        # برداشتن انتخاب قبلی
        if self._selected_section is not None:
            old = self.section_cards.get(self._selected_section)
            if old is not None:
                old.set_selected_border(False)

        self._selected_section = section_id
        new_card = self.section_cards.get(section_id)
        if new_card is not None:
            new_card.set_selected_border(True)

        # اگر این بخش در info_checked نیست، اضافه کن
        if section_id not in self.info_checked:
            self.info_checked.append(section_id)
            print(
                f"   [DEBUG] اطلاعات بخش {section_id} خوانده شد"
            )
            # علامت ✓ روی دکمه‌ی ℹ️
            if new_card is not None:
                new_card.info_btn.setText("✓")

        self._track_info_time(section_id)

        # نمایش اطلاعات
        section = next(
            (s for s in self.sections if s["id"] == section_id),
            None,
        )
        if section is not None:
            self.info_text.setText(section["info"])

    def _on_info_click(self, section_id: str):
        """همان رفتار کلیک روی بدنه‌ی بخش"""
        self._on_section_selected(section_id)

    def _track_info_time(self, section_id: str):
        now = int(time.time() * 1000)

        # بستن محاسبه‌ی بخش قبلی
        if self._current_info_section is not None:
            elapsed = now - self._last_info_check_start
            self.info_check_times[self._current_info_section] = (
                self.info_check_times.get(
                    self._current_info_section, 0
                ) + elapsed
            )

        # شروع محاسبه‌ی بخش جدید
        self._current_info_section = section_id
        self._last_info_check_start = now

    # ================================================================
    # تایمر
    # ================================================================
    def _tick(self):
        self._remaining_sec -= 1
        if self._remaining_sec <= 0:
            self._remaining_sec = 0
            self.timer_label.setText("⏱  0s")
            self.timer_label.setStyleSheet(
                "color: #D32F2F; border: none;"
            )
            self.time_bar.setValue(0)
            self.countdown_timer.stop()
            self.timed_out = True
            print("   [DEBUG] تایمر تمام شد — ثبت خودکار")
            self._finalize(timed_out=True)
            return

        pct = int(
            (self._remaining_sec / self.time_limit_sec) * 100
        )
        self.time_bar.setValue(pct)

        if self._remaining_sec <= 15:
            color = "#D32F2F"
        elif self._remaining_sec <= 30:
            color = "#FF8F00"
        else:
            color = "#4CAF50"

        self.timer_label.setText(f"⏱  {self._remaining_sec}s")
        self.timer_label.setStyleSheet(
            f"color: {color}; border: none;"
        )
        self.time_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: #1A2A4A;
                border: 1px solid #4FC3F7;
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 3px;
            }}
        """)

    # ================================================================
    def _on_submit(self):
        if self.is_done:
            return
        if len(self.allocations) == 0:
            QMessageBox.warning(
                self,
                "تخصیص ناقص",
                "شما هنوز هیچ منبعی را به بخشی اختصاص نداده‌اید.\n"
                "یک منبع را بکشید و روی بخش موردنظر رها کنید.",
            )
            return
        self.submitted = True
        self._finalize(timed_out=False)

    def _finalize(self, timed_out: bool):
        if self.is_done:
            return
        self.is_done = True
        self.countdown_timer.stop()

        total_time = int(time.time() * 1000) - self.start_time

        # بستن محاسبه‌ی زمان اطلاعات
        if self._current_info_section is not None:
            now = int(time.time() * 1000)
            elapsed = now - self._last_info_check_start
            self.info_check_times[self._current_info_section] = (
                self.info_check_times.get(
                    self._current_info_section, 0
                ) + elapsed
            )

        self.submit_btn.setEnabled(False)
        self.submit_btn.setText("✓ ثبت شد")

        result = {
            "allocations": self.allocations.copy(),
            "info_checked": list(self.info_checked),
            "info_check_times_ms": dict(self.info_check_times),
            "allocation_order": list(self.allocation_order),
            "time_to_first_allocation_ms": (
                self.time_to_first_allocation_ms
            ),
            "total_time_ms": total_time,
            "timed_out": timed_out,
            "submitted": self.submitted,
        }
        print(f"   [DEBUG] نتیجه تخصیص: {result}")
        self.allocation_done.emit(result)