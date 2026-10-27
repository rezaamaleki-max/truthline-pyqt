"""
ویرایش‌گر گرافیکی سناریوها — Truthline
=========================================
پنجره‌ی مستقل برای مشاهده و ویرایش متن سناریوها.

نحوه استفاده:
    python analysis/scenario_editor.py

ویژگی‌ها:
- لیست درختی همه‌ی سناریوها (بر اساس فاز)
- نمایش و ویرایش عنوان، دیالوگ‌ها، گزینه‌ها
- نمایش evidence_model برای اطلاع
- ذخیره‌ی امن با پشتیبان‌گیری خودکار
"""
import os
import sys
import json
import shutil
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QTreeWidget, QTreeWidgetItem,
    QTextEdit, QLineEdit, QMessageBox, QSplitter, QTabWidget,
    QListWidget, QListWidgetItem, QScrollArea, QFileDialog,
    QAbstractItemView, QComboBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from config import SCENARIOS_DIR
except ImportError:
    SCENARIOS_DIR = os.path.join(
        PROJECT_ROOT, "data", "scenarios"
    )

FONT_FAMILY = "Vazirmatn"


# ====================================================================
# پنجره‌ی اصلی
# ====================================================================
class ScenarioEditorWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle(
            "Truthline — ویرایش‌گر سناریوها"
        )
        self.resize(1400, 820)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        self._current_path: str = ""
        self._current_data: dict = {}
        self._dirty: bool = False

        self._build_ui()
        self._load_tree()

    # ================================================================
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        central.setStyleSheet("background-color: #0B1D3A;")

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        # ---------- ستون چپ: درخت سناریوها ----------
        tree_frame = QFrame()
        tree_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(11, 29, 58, 0.7);
                border: 2px solid #2B4A6F;
                border-radius: 10px;
            }
        """)
        tree_layout = QVBoxLayout(tree_frame)
        tree_layout.setContentsMargins(8, 8, 8, 8)
        tree_layout.setSpacing(6)

        tree_header = QLabel("سناریوها")
        tree_header.setFont(
            QFont(FONT_FAMILY, 13, QFont.Weight.Bold)
        )
        tree_header.setStyleSheet(
            "color: #4FC3F7; border: none;"
        )
        tree_layout.addWidget(tree_header)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.tree.setStyleSheet("""
            QTreeWidget {
                background-color: transparent;
                color: #FFFFFF;
                border: none;
                font-family: 'Vazirmatn';
                font-size: 12px;
            }
            QTreeWidget::item {
                padding: 5px;
                border-radius: 4px;
            }
            QTreeWidget::item:selected {
                background-color: #2B4A6F;
                color: #FFFFFF;
            }
            QTreeWidget::item:hover {
                background-color: rgba(43, 74, 111, 0.6);
            }
        """)
        self.tree.itemClicked.connect(self._on_tree_item_clicked)
        tree_layout.addWidget(self.tree)

        tree_frame.setMinimumWidth(280)
        tree_frame.setMaximumWidth(360)
        main_layout.addWidget(tree_frame)

        # ---------- ستون راست: ویرایش‌گر ----------
        editor_frame = QFrame()
        editor_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(11, 29, 58, 0.7);
                border: 2px solid #2B4A6F;
                border-radius: 10px;
            }
        """)
        editor_layout = QVBoxLayout(editor_frame)
        editor_layout.setContentsMargins(12, 12, 12, 12)
        editor_layout.setSpacing(8)

        # نوار ابزار
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        self.file_label = QLabel("—")
        self.file_label.setFont(QFont(FONT_FAMILY, 11))
        self.file_label.setStyleSheet(
            "color: #B0BEC5; border: none;"
        )
        toolbar.addWidget(self.file_label)
        toolbar.addStretch()

        self.save_btn = QPushButton("💾 ذخیره")
        self.save_btn.setFont(QFont(FONT_FAMILY, 12))
        self.save_btn.setMinimumHeight(34)
        self.save_btn.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.save_btn.setEnabled(False)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #2B4A6F;
                color: #FFFFFF;
                border: 2px solid #4CAF50;
                border-radius: 6px;
                padding: 6px 14px;
            }
            QPushButton:hover {
                background-color: #4CAF50;
                color: #FFFFFF;
            }
            QPushButton:disabled {
                background-color: #1A2A4A;
                color: #666666;
                border: 2px solid #444444;
            }
        """)
        self.save_btn.clicked.connect(self._save)
        toolbar.addWidget(self.save_btn)

        self.revert_btn = QPushButton("↶ بازگردانی")
        self.revert_btn.setFont(QFont(FONT_FAMILY, 12))
        self.revert_btn.setMinimumHeight(34)
        self.revert_btn.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.revert_btn.setEnabled(False)
        self.revert_btn.setStyleSheet("""
            QPushButton {
                background-color: #2B4A6F;
                color: #FFFFFF;
                border: 2px solid #FF8F00;
                border-radius: 6px;
                padding: 6px 14px;
            }
            QPushButton:hover {
                background-color: #FF8F00;
                color: #FFFFFF;
            }
            QPushButton:disabled {
                background-color: #1A2A4A;
                color: #666666;
                border: 2px solid #444444;
            }
        """)
        self.revert_btn.clicked.connect(self._revert)
        toolbar.addWidget(self.revert_btn)

        editor_layout.addLayout(toolbar)

        # تب‌ها
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                background-color: transparent;
                border: none;
            }
            QTabBar::tab {
                background-color: #1A2A4A;
                color: #FFFFFF;
                padding: 8px 18px;
                border: 1px solid #2B4A6F;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-family: 'Vazirmatn';
                font-size: 12px;
            }
            QTabBar::tab:selected {
                background-color: #2B4A6F;
                color: #4FC3F7;
                border: 2px solid #4FC3F7;
            }
        """)

        # تب ۱: اطلاعات پایه
        self._build_tab_info()

        # تب ۲: دیالوگ‌ها
        self._build_tab_dialogues()

        # تب ۳: گزینه‌ها
        self._build_tab_choices()

        # تب ۴: شواهد (فقط خواندنی)
        self._build_tab_evidence()

        # تب ۵: JSON خام
        self._build_tab_raw()

        editor_layout.addWidget(self.tabs, stretch=1)

        main_layout.addWidget(editor_frame, stretch=1)

    # ================================================================
    # تب ۱ — اطلاعات پایه
    # ================================================================
    def _build_tab_info(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(10, 15, 10, 10)
        layout.setSpacing(12)

        # شناسه
        id_row = QHBoxLayout()
        id_row.addWidget(self._lbl("شناسه:"))
        self.id_edit = QLineEdit()
        self.id_edit.setReadOnly(True)
        self.id_edit.setFont(QFont("Consolas", 11))
        self._style_line_edit(self.id_edit, readonly=True)
        id_row.addWidget(self.id_edit, 1)
        layout.addLayout(id_row)

        # فاز
        phase_row = QHBoxLayout()
        phase_row.addWidget(self._lbl("فاز:"))
        self.phase_edit = QLineEdit()
        self.phase_edit.setReadOnly(True)
        self.phase_edit.setFont(QFont(FONT_FAMILY, 11))
        self._style_line_edit(self.phase_edit, readonly=True)
        phase_row.addWidget(self.phase_edit, 1)
        layout.addLayout(phase_row)

        # عنوان
        title_row = QHBoxLayout()
        title_row.addWidget(self._lbl("عنوان:"))
        self.title_edit = QLineEdit()
        self.title_edit.setFont(QFont(FONT_FAMILY, 12))
        self._style_line_edit(self.title_edit)
        self.title_edit.textChanged.connect(
            lambda: self._mark_dirty()
        )
        title_row.addWidget(self.title_edit, 1)
        layout.addLayout(title_row)

        layout.addStretch()

        self.tabs.addTab(page, "اطلاعات پایه")

    # ================================================================
    # تب ۲ — دیالوگ‌ها
    # ================================================================
    def _build_tab_dialogues(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(10, 15, 10, 10)
        layout.setSpacing(8)

        # انتخاب نوع دیالوگ
        selector_row = QHBoxLayout()
        selector_row.addWidget(self._lbl("نوع:"))
        self.dialogue_type_combo = QComboBox()
        self.dialogue_type_combo.addItems(
            ["intro_sequence", "dialogue_sequence"]
        )
        self.dialogue_type_combo.setFont(QFont(FONT_FAMILY, 11))
        self._style_combo(self.dialogue_type_combo)
        self.dialogue_type_combo.currentIndexChanged.connect(
            self._refresh_dialogue_list
        )
        selector_row.addWidget(self.dialogue_type_combo)
        selector_row.addStretch()
        layout.addLayout(selector_row)

        # splitter: لیست + ویرایشگر
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # لیست دیالوگ‌ها
        list_frame = QFrame()
        list_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(26, 42, 74, 0.5);
                border: 1px solid #2B4A6F;
                border-radius: 6px;
            }
        """)
        list_layout = QVBoxLayout(list_frame)
        list_layout.setContentsMargins(6, 6, 6, 6)

        self.dialogue_list = QListWidget()
        self.dialogue_list.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                color: #FFFFFF;
                border: none;
                font-family: 'Vazirmatn';
                font-size: 11px;
            }
            QListWidget::item {
                padding: 6px;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background-color: #2B4A6F;
            }
        """)
        self.dialogue_list.currentRowChanged.connect(
            self._on_dialogue_selected
        )
        list_layout.addWidget(self.dialogue_list)
        splitter.addWidget(list_frame)

        # ویرایشگر
        editor_w = QWidget()
        editor_l = QVBoxLayout(editor_w)
        editor_l.setContentsMargins(0, 0, 0, 0)
        editor_l.setSpacing(8)

        speaker_row = QHBoxLayout()
        speaker_row.addWidget(self._lbl("گوینده:"))
        self.speaker_edit = QLineEdit()
        self.speaker_edit.setFont(QFont(FONT_FAMILY, 11))
        self._style_line_edit(self.speaker_edit)
        self.speaker_edit.textChanged.connect(
            lambda: self._mark_dirty()
        )
        speaker_row.addWidget(self.speaker_edit, 1)
        editor_l.addLayout(speaker_row)

        editor_l.addWidget(self._lbl("متن:"))
        self.dialogue_text_edit = QTextEdit()
        self.dialogue_text_edit.setFont(QFont(FONT_FAMILY, 12))
        self.dialogue_text_edit.setLayoutDirection(
            Qt.LayoutDirection.RightToLeft
        )
        self._style_text_edit(self.dialogue_text_edit)
        self.dialogue_text_edit.textChanged.connect(
            lambda: self._mark_dirty()
        )
        editor_l.addWidget(self.dialogue_text_edit, stretch=1)

        splitter.addWidget(editor_w)
        splitter.setSizes([300, 600])

        layout.addWidget(splitter, stretch=1)

        self.tabs.addTab(page, "دیالوگ‌ها")

    # ================================================================
    # تب ۳ — گزینه‌ها
    # ================================================================
    def _build_tab_choices(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(10, 15, 10, 10)
        layout.setSpacing(8)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # لیست گزینه‌ها
        list_frame = QFrame()
        list_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(26, 42, 74, 0.5);
                border: 1px solid #2B4A6F;
                border-radius: 6px;
            }
        """)
        list_layout = QVBoxLayout(list_frame)
        list_layout.setContentsMargins(6, 6, 6, 6)

        self.choices_list = QListWidget()
        self.choices_list.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                color: #FFFFFF;
                border: none;
                font-family: 'Vazirmatn';
                font-size: 11px;
            }
            QListWidget::item {
                padding: 6px;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background-color: #2B4A6F;
            }
        """)
        self.choices_list.currentRowChanged.connect(
            self._on_choice_selected
        )
        list_layout.addWidget(self.choices_list)
        splitter.addWidget(list_frame)

        # ویرایشگر گزینه
        editor_w = QWidget()
        editor_l = QVBoxLayout(editor_w)
        editor_l.setContentsMargins(0, 0, 0, 0)
        editor_l.setSpacing(8)

        id_row = QHBoxLayout()
        id_row.addWidget(self._lbl("id:"))
        self.choice_id_edit = QLineEdit()
        self.choice_id_edit.setFont(QFont("Consolas", 11))
        self._style_line_edit(self.choice_id_edit)
        self.choice_id_edit.textChanged.connect(
            lambda: self._mark_dirty()
        )
        id_row.addWidget(self.choice_id_edit, 1)

        id_row.addWidget(self._lbl("خروجی:"))
        self.choice_outcome_edit = QLineEdit()
        self.choice_outcome_edit.setFont(QFont("Consolas", 11))
        self._style_line_edit(self.choice_outcome_edit)
        self.choice_outcome_edit.textChanged.connect(
            lambda: self._mark_dirty()
        )
        id_row.addWidget(self.choice_outcome_edit, 1)

        editor_l.addLayout(id_row)

        editor_l.addWidget(self._lbl("متن گزینه:"))
        self.choice_text_edit = QTextEdit()
        self.choice_text_edit.setFont(QFont(FONT_FAMILY, 12))
        self.choice_text_edit.setLayoutDirection(
            Qt.LayoutDirection.RightToLeft
        )
        self._style_text_edit(self.choice_text_edit)
        self.choice_text_edit.textChanged.connect(
            lambda: self._mark_dirty()
        )
        editor_l.addWidget(self.choice_text_edit, stretch=1)

        splitter.addWidget(editor_w)
        splitter.setSizes([300, 600])

        layout.addWidget(splitter, stretch=1)

        self.tabs.addTab(page, "گزینه‌ها")

    # ================================================================
    # تب ۴ — شواهد
    # ================================================================
    def _build_tab_evidence(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(10, 15, 10, 10)

        info = QLabel(
            "این بخش فقط برای اطلاع است. برای ویرایش، فایل JSON "
            "را مستقیماً باز کنید."
        )
        info.setFont(QFont(FONT_FAMILY, 11))
        info.setStyleSheet(
            "color: #FF8F00; border: none; padding: 8px;"
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        self.evidence_view = QTextEdit()
        self.evidence_view.setReadOnly(True)
        self.evidence_view.setFont(QFont("Consolas", 11))
        self.evidence_view.setLayoutDirection(
            Qt.LayoutDirection.LeftToRight
        )
        self._style_text_edit(self.evidence_view, readonly=True)
        layout.addWidget(self.evidence_view)

        self.tabs.addTab(page, "شواهد")

    # ================================================================
    # تب ۵ — JSON خام
    # ================================================================
    def _build_tab_raw(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(10, 15, 10, 10)

        self.raw_view = QTextEdit()
        self.raw_view.setReadOnly(True)
        self.raw_view.setFont(QFont("Consolas", 10))
        self.raw_view.setLayoutDirection(
            Qt.LayoutDirection.LeftToRight
        )
        self._style_text_edit(self.raw_view, readonly=True)
        layout.addWidget(self.raw_view)

        self.tabs.addTab(page, "JSON خام")

    # ================================================================
    # استایل‌دهی
    # ================================================================
    @staticmethod
    def _lbl(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setFont(QFont(FONT_FAMILY, 11))
        lbl.setStyleSheet("color: #FFFFFF; border: none;")
        lbl.setMinimumWidth(70)
        return lbl

    @staticmethod
    def _style_line_edit(edit: QLineEdit, readonly: bool = False):
        bg = "#0B1D3A" if readonly else "#1A2A4A"
        border = "#2B4A6F" if readonly else "#4FC3F7"
        edit.setStyleSheet(f"""
            QLineEdit {{
                background-color: {bg};
                color: #FFFFFF;
                border: 2px solid {border};
                border-radius: 6px;
                padding: 6px;
            }}
            QLineEdit:focus {{
                border: 2px solid #FF8F00;
            }}
        """)

    @staticmethod
    def _style_text_edit(edit: QTextEdit, readonly: bool = False):
        bg = "#0B1D3A" if readonly else "#1A2A4A"
        border = "#2B4A6F" if readonly else "#4FC3F7"
        edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {bg};
                color: #FFFFFF;
                border: 2px solid {border};
                border-radius: 6px;
                padding: 8px;
            }}
            QTextEdit:focus {{
                border: 2px solid #FF8F00;
            }}
        """)

    @staticmethod
    def _style_combo(combo: QComboBox):
        combo.setStyleSheet("""
            QComboBox {
                background-color: #1A2A4A;
                color: #FFFFFF;
                border: 2px solid #4FC3F7;
                border-radius: 6px;
                padding: 6px;
            }
            QComboBox QAbstractItemView {
                background-color: #1A2A4A;
                color: #FFFFFF;
                selection-background-color: #4FC3F7;
                selection-color: #0B1D3A;
            }
        """)

    # ================================================================
    # درخت سناریوها
    # ================================================================
    def _load_tree(self):
        self.tree.clear()
        self._path_map: dict = {}

        if not os.path.isdir(SCENARIOS_DIR):
            print(f"❌ پوشه‌ی سناریوها یافت نشد: {SCENARIOS_DIR}")
            return

        for phase_name in sorted(os.listdir(SCENARIOS_DIR)):
            phase_dir = os.path.join(SCENARIOS_DIR, phase_name)
            if not os.path.isdir(phase_dir):
                continue

            # آیتم والد
            phase_item = QTreeWidgetItem([phase_name])
            phase_item.setFont(
                0, QFont(FONT_FAMILY, 12, QFont.Weight.Bold)
            )
            phase_item.setForeground(0, QColor("#FF8F00"))
            self.tree.addTopLevelItem(phase_item)

            json_files = sorted([
                f for f in os.listdir(phase_dir)
                if f.endswith(".json")
            ])

            for fname in json_files:
                path = os.path.join(phase_dir, fname)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    sid = data.get("scenario_id", "?")
                    title = data.get("title_fa", "")
                    is_inner = fname.endswith("_inner.json")
                    suffix = "  [inner]" if is_inner else ""
                    label = f"{sid}{suffix}\n{title}"
                except Exception:
                    label = fname
                    sid = "?"

                child = QTreeWidgetItem([label])
                child.setFont(0, QFont(FONT_FAMILY, 11))
                if fname.endswith("_inner.json"):
                    child.setForeground(0, QColor("#B0BEC5"))
                phase_item.addChild(child)
                self._path_map[id(child)] = path

            phase_item.setExpanded(True)

    # ================================================================
    # انتخاب سناریو
    # ================================================================
    def _on_tree_item_clicked(self, item, column):
        path = self._path_map.get(id(item))
        if path is None:
            return

        # اگر تغییرات ذخیره‌نشده داریم، بپرس
        if self._dirty:
            reply = QMessageBox.question(
                self, "تغییرات ذخیره‌نشده",
                "تغییرات فعلی ذخیره نشده‌اند. ادامه می‌دهید؟",
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        self._load_scenario(path)

    def _load_scenario(self, path: str):
        try:
            with open(path, "r", encoding="utf-8") as f:
                self._current_data = json.load(f)
        except Exception as e:
            QMessageBox.critical(
                self, "خطا در بارگذاری",
                f"فایل بارگذاری نشد:\n{e}",
            )
            return

        self._current_path = path
        self._dirty = False

        self.file_label.setText(
            os.path.relpath(path, SCENARIOS_DIR)
        )

        data = self._current_data

        # تب ۱
        self.id_edit.setText(data.get("scenario_id", ""))
        self.phase_edit.setText(str(data.get("phase", "")))
        self.title_edit.blockSignals(True)
        self.title_edit.setText(data.get("title_fa", ""))
        self.title_edit.blockSignals(False)

        # تب ۲
        self._refresh_dialogue_list()

        # تب ۳
        self._refresh_choices_list()

        # تب ۴
        em = data.get("evidence_model", {})
        self.evidence_view.setPlainText(
            json.dumps(em, ensure_ascii=False, indent=2)
        )

        # تب ۵
        self.raw_view.setPlainText(
            json.dumps(data, ensure_ascii=False, indent=2)
        )

        # دکمه‌ها
        self.save_btn.setEnabled(False)
        self.revert_btn.setEnabled(False)

    # ================================================================
    def _refresh_dialogue_list(self):
        self.dialogue_list.clear()
        data = self._current_data
        dlg_type = self.dialogue_type_combo.currentText()
        dialogues = data.get(dlg_type, [])

        for i, dlg in enumerate(dialogues):
            speaker = dlg.get("speaker", "?")
            text = dlg.get("text_fa", dlg.get("text", ""))
            preview = text[:50] + ("..." if len(text) > 50 else "")
            item = QListWidgetItem(f"{i+1}. {speaker}\n{preview}")
            item.setFont(QFont(FONT_FAMILY, 10))
            self.dialogue_list.addItem(item)

        # پاک کردن ویرایشگر
        self.speaker_edit.blockSignals(True)
        self.speaker_edit.setText("")
        self.speaker_edit.blockSignals(False)
        self.dialogue_text_edit.blockSignals(True)
        self.dialogue_text_edit.setPlainText("")
        self.dialogue_text_edit.blockSignals(False)

    def _on_dialogue_selected(self, row):
        if row < 0:
            return
        data = self._current_data
        dlg_type = self.dialogue_type_combo.currentText()
        dialogues = data.get(dlg_type, [])
        if row >= len(dialogues):
            return
        dlg = dialogues[row]
        self.speaker_edit.blockSignals(True)
        self.speaker_edit.setText(dlg.get("speaker", ""))
        self.speaker_edit.blockSignals(False)
        self.dialogue_text_edit.blockSignals(True)
        self.dialogue_text_edit.setPlainText(
            dlg.get("text_fa", dlg.get("text", ""))
        )
        self.dialogue_text_edit.blockSignals(False)

    # ================================================================
    def _refresh_choices_list(self):
        self.choices_list.clear()
        data = self._current_data
        choices = data.get("choices", [])

        for i, ch in enumerate(choices):
            cid = ch.get("id", "?")
            text = ch.get("text_fa", ch.get("text", ""))
            preview = text[:50] + ("..." if len(text) > 50 else "")
            item = QListWidgetItem(f"[{cid}]  {preview}")
            item.setFont(QFont(FONT_FAMILY, 10))
            self.choices_list.addItem(item)

        # پاک کردن ویرایشگر
        self.choice_id_edit.blockSignals(True)
        self.choice_id_edit.setText("")
        self.choice_id_edit.blockSignals(False)
        self.choice_outcome_edit.blockSignals(True)
        self.choice_outcome_edit.setText("")
        self.choice_outcome_edit.blockSignals(False)
        self.choice_text_edit.blockSignals(True)
        self.choice_text_edit.setPlainText("")
        self.choice_text_edit.blockSignals(False)

    def _on_choice_selected(self, row):
        if row < 0:
            return
        data = self._current_data
        choices = data.get("choices", [])
        if row >= len(choices):
            return
        ch = choices[row]
        self.choice_id_edit.blockSignals(True)
        self.choice_id_edit.setText(str(ch.get("id", "")))
        self.choice_id_edit.blockSignals(False)
        self.choice_outcome_edit.blockSignals(True)
        self.choice_outcome_edit.setText(ch.get("outcome", ""))
        self.choice_outcome_edit.blockSignals(False)
        self.choice_text_edit.blockSignals(True)
        self.choice_text_edit.setPlainText(
            ch.get("text_fa", ch.get("text", ""))
        )
        self.choice_text_edit.blockSignals(False)

    # ================================================================
    # تغییرات
    # ================================================================
    def _mark_dirty(self):
        self._dirty = True
        self.save_btn.setEnabled(True)
        self.revert_btn.setEnabled(True)

    def _revert(self):
        if not self._current_path:
            return
        self._load_scenario(self._current_path)

    # ================================================================
    # ذخیره
    # ================================================================
    def _save(self):
        if not self._current_path:
            return

        # جمع‌آوری تغییرات
        data = dict(self._current_data)

        # تب ۱
        data["title_fa"] = self.title_edit.text()

        # تب ۲ (فقط دیالوگ انتخاب‌شده)
        dlg_type = self.dialogue_type_combo.currentText()
        row = self.dialogue_list.currentRow()
        if row >= 0:
            dialogues = list(data.get(dlg_type, []))
            if row < len(dialogues):
                dlg = dict(dialogues[row])
                dlg["speaker"] = self.speaker_edit.text()
                dlg["text_fa"] = self.dialogue_text_edit.toPlainText()
                dialogues[row] = dlg
                data[dlg_type] = dialogues

        # تب ۳
        row = self.choices_list.currentRow()
        if row >= 0:
            choices = list(data.get("choices", []))
            if row < len(choices):
                ch = dict(choices[row])
                try:
                    ch["id"] = int(self.choice_id_edit.text())
                except ValueError:
                    pass
                ch["outcome"] = self.choice_outcome_edit.text()
                ch["text_fa"] = self.choice_text_edit.toPlainText()
                choices[row] = ch
                data["choices"] = choices

        # پشتیبان‌گیری
        try:
            backup_path = self._current_path + ".bak"
            shutil.copy2(self._current_path, backup_path)
        except Exception as e:
            print(f"⚠️ خطا در پشتیبان: {e}")

        # ذخیره
        try:
            with open(self._current_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self._current_data = data
            self._dirty = False
            self.save_btn.setEnabled(False)
            self.revert_btn.setEnabled(False)

            # بازخوانی JSON خام
            self.raw_view.setPlainText(
                json.dumps(data, ensure_ascii=False, indent=2)
            )

            QMessageBox.information(
                self, "ذخیره شد",
                "✓ تغییرات ذخیره شد.\n"
                "پشتیبان در همان پوشه با پسوند .bak ساخته شد.",
            )
        except Exception as e:
            QMessageBox.critical(
                self, "خطا",
                f"ذخیره ناموفق:\n{e}",
            )

    # ================================================================
    def closeEvent(self, event):  # type: ignore
        if self._dirty:
            reply = QMessageBox.question(
                self, "تغییرات ذخیره‌نشده",
                "تغییرات ذخیره نشده‌اند. بستن؟",
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
        event.accept()


# ====================================================================
def main():
    print("=" * 60)
    print("  Truthline — ویرایش‌گر سناریوها")
    print("=" * 60)
    print(f"  SCENARIOS: {SCENARIOS_DIR}")

    app = QApplication(sys.argv)

    # فونت
    try:
        from config import FONT_PATH
        if os.path.exists(FONT_PATH):
            from PyQt6.QtGui import QFontDatabase
            fid = QFontDatabase.addApplicationFont(FONT_PATH)
            if fid != -1:
                families = QFontDatabase.applicationFontFamilies(
                    fid
                )
                if families:
                    app.setFont(QFont(families[0], 11))
                    print(f"✓ فونت: {families[0]}")
    except Exception as e:
        print(f"⚠️ فونت: {e}")

    window = ScenarioEditorWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()