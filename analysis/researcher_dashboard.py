"""
داشبورد پژوهشگر — Truthline
===============================
پنجره‌ی مستقل برای مرور داده‌های جمع‌آوری‌شده.

نحوه استفاده:
    python analysis/researcher_dashboard.py

ویژگی‌ها:
- جدول همه‌ی شرکت‌کنندگان با نمرات شایستگی
- آمار توصیفی (M، SD، Min، Max)
- نمودار توزیع نمرات
- فیلتر بر اساس حالت (Full / Short / Theater)
- صادرات CSV
"""
import os
import sys
import sqlite3
import json
from datetime import datetime

import pandas as pd
import numpy as np

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QComboBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QFileDialog,
    QSplitter, QAbstractItemView
)
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QFont, QPainter, QPen, QBrush, QColor

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from config import DB_PATH
except ImportError:
    DB_PATH = os.path.join(
        PROJECT_ROOT, "data", "participants.db"
    )

FONT_FAMILY = "Vazirmatn"


# ====================================================================
# داده‌ها
# ====================================================================
COMPETENCIES = [
    ("honesty", "صداقت"),
    ("trustworthiness", "اعتماد"),
    ("problem_solving", "حل مسئله"),
    ("accountability", "مسئولیت"),
]


def load_data() -> pd.DataFrame:
    """بارگذاری یک ردیف per participant"""
    if not os.path.exists(DB_PATH):
        return pd.DataFrame()

    conn = sqlite3.connect(DB_PATH)
    try:
        # Participants
        participants = pd.read_sql_query(
            "SELECT participant_id, session_start, session_end, "
            "demographic_data, hexaco_scores "
            "FROM participants ORDER BY session_start",
            conn,
        )
        # Competency scores (wide)
        scores = pd.read_sql_query(
            "SELECT participant_id, competency, score, "
            "confidence, evidence_count "
            "FROM competency_scores",
            conn,
        )
    finally:
        conn.close()

    if participants.empty:
        return pd.DataFrame()

    rows = []
    for _, p in participants.iterrows():
        pid = p["participant_id"]
        mode = _detect_mode(pid)

        # زمان
        ss = p.get("session_start") or 0
        se = p.get("session_end") or 0
        duration_min = (
            int((se - ss) / 60) if se > ss else 0
        )

        # دموگرافیک
        demo = _parse_json(p.get("demographic_data"))
        hexaco = _parse_json(p.get("hexaco_scores"))

        row = {
            "participant_id": pid,
            "mode": mode,
            "date": (
                datetime.fromtimestamp(ss).strftime(
                    "%Y-%m-%d %H:%M"
                )
                if ss > 0 else "—"
            ),
            "duration_min": duration_min,
            "age": demo.get("age"),
            "gender": demo.get("gender"),
            "education": demo.get("education"),
        }

        # HEXACO
        for code in ["H", "E", "X", "A", "C", "O"]:
            row[f"hexaco_{code}"] = hexaco.get(f"score_{code}")

        # Competency scores
        pid_scores = scores[scores["participant_id"] == pid]
        for comp_code, _ in COMPETENCIES:
            match = pid_scores[pid_scores["competency"] == comp_code]
            if not match.empty:
                row[f"score_{comp_code}"] = float(
                    match.iloc[0]["score"]
                )
                row[f"count_{comp_code}"] = int(
                    match.iloc[0]["evidence_count"]
                )
            else:
                row[f"score_{comp_code}"] = None
                row[f"count_{comp_code}"] = 0

        rows.append(row)

    return pd.DataFrame(rows)


def _detect_mode(pid: str) -> str:
    if pid.startswith("THEATER_"):
        return "Theater"
    return "Normal"


def _parse_json(s) -> dict:
    if not s:
        return {}
    if isinstance(s, dict):
        return s
    try:
        return json.loads(s)
    except Exception:
        return {}


# ====================================================================
# نمودار توزیع
# ====================================================================
class _HistogramWidget(QWidget):
    """نمودار میله‌ای ساده با QPainter"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: list = []
        self._label: str = ""
        self._bins: int = 10
        self.setMinimumHeight(160)
        self.setStyleSheet("background: transparent;")

    def set_data(self, values: list, label: str = ""):
        self._data = [v for v in values if v is not None]
        self._label = label
        self.update()

    def paintEvent(self, event):  # type: ignore
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # پس‌زمینه
        painter.setBrush(QBrush(QColor(11, 29, 58)))
        painter.setPen(QPen(QColor(43, 74, 111), 1))
        painter.drawRoundedRect(
            QRectF(0, 0, w - 1, h - 1), 8, 8
        )

        if not self._data:
            painter.setPen(QColor(176, 190, 197))
            painter.setFont(QFont(FONT_FAMILY, 11))
            painter.drawText(
                QRectF(0, 0, w, h),
                int(Qt.AlignmentFlag.AlignCenter),
                "داده‌ای برای نمایش نیست",
            )
            painter.end()
            return

        # label
        if self._label:
            painter.setPen(QColor(79, 195, 247))
            painter.setFont(QFont(FONT_FAMILY, 11, QFont.Weight.Bold))
            painter.drawText(
                QRectF(8, 4, w - 16, 20),
                int(
                    Qt.AlignmentFlag.AlignRight
                    | Qt.AlignmentFlag.AlignVCenter
                ),
                self._label,
            )

        # محاسبه‌ی bins
        margin_left = 30
        margin_right = 12
        margin_top = 28
        margin_bottom = 24

        plot_w = w - margin_left - margin_right
        plot_h = h - margin_top - margin_bottom

        values = np.array(self._data)
        vmin = 0.0
        vmax = 100.0

        # bins
        bins = np.linspace(vmin, vmax, self._bins + 1)
        counts, _ = np.histogram(values, bins=bins)

        if counts.max() == 0:
            counts_max = 1
        else:
            counts_max = counts.max()

        bar_gap = 3
        bar_w = (plot_w - (self._bins - 1) * bar_gap) / self._bins

        for i, c in enumerate(counts):
            bar_h = (c / counts_max) * plot_h
            x = margin_right + (self._bins - 1 - i) * (
                bar_w + bar_gap
            )
            # در RTL، ستون‌ها از راست به چپ
            x = margin_left + (self._bins - 1 - i) * (
                bar_w + bar_gap
            )
            y = margin_top + (plot_h - bar_h)

            # رنگ بر اساس جایگاه
            if c == 0:
                color = QColor(43, 74, 111)
            else:
                intensity = 0.4 + 0.6 * (c / counts_max)
                color = QColor(
                    int(79 * intensity + 30),
                    int(195 * intensity + 40),
                    int(247 * intensity + 5),
                )

            painter.setBrush(QBrush(color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(
                QRectF(x, y, bar_w, bar_h), 3, 3
            )

            # عدد بالای میله
            if c > 0:
                painter.setPen(QColor(255, 255, 255))
                painter.setFont(QFont(FONT_FAMILY, 9))
                painter.drawText(
                    QRectF(x, y - 16, bar_w, 14),
                    int(Qt.AlignmentFlag.AlignCenter),
                    str(c),
                )

        # محورها
        painter.setPen(QPen(QColor(79, 195, 247, 100), 1))
        painter.drawLine(
            int(margin_left), int(margin_top),
            int(margin_left), int(margin_top + plot_h),
        )
        painter.drawLine(
            int(margin_left), int(margin_top + plot_h),
            int(margin_left + plot_w), int(margin_top + plot_h),
        )

        # مقادیر محور X
        painter.setPen(QColor(176, 190, 197))
        painter.setFont(QFont(FONT_FAMILY, 8))
        for i in range(0, self._bins + 1, 2):
            val = int(vmin + (vmax - vmin) * i / self._bins)
            x = margin_left + (plot_w - i * plot_w / self._bins)
            painter.drawText(
                QRectF(x - 15, margin_top + plot_h + 2, 30, 16),
                int(Qt.AlignmentFlag.AlignCenter),
                str(val),
            )

        painter.end()


# ====================================================================
# پنجره‌ی اصلی
# ====================================================================
class DashboardWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Truthline — داشبورد پژوهشگر")
        self.resize(1280, 780)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        self._df = pd.DataFrame()

        self._build_ui()
        self._refresh_data()

    # ================================================================
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        central.setStyleSheet("background-color: #0B1D3A;")

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(20, 15, 20, 15)
        main_layout.setSpacing(12)

        # ---------- سرصفحه ----------
        header = QHBoxLayout()
        header.setSpacing(10)

        title = QLabel("داشبورد پژوهشگر")
        tf = QFont(FONT_FAMILY, 22, QFont.Weight.Bold)
        title.setFont(tf)
        title.setStyleSheet("color: #4FC3F7;")
        header.addWidget(title)

        header.addStretch()

        # فیلتر حالت
        header.addWidget(self._label("حالت:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(
            ["همه", "Normal", "Theater"]
        )
        self.mode_combo.setFont(QFont(FONT_FAMILY, 11))
        self.mode_combo.setMinimumWidth(140)
        self.mode_combo.setStyleSheet("""
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
        self.mode_combo.currentIndexChanged.connect(
            self._apply_filters
        )
        header.addWidget(self.mode_combo)

        # دکمه بروزرسانی
        refresh_btn = QPushButton("🔄 بروزرسانی")
        refresh_btn.setFont(QFont(FONT_FAMILY, 11))
        refresh_btn.setMinimumHeight(34)
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #2B4A6F;
                color: #FFFFFF;
                border: 2px solid #4FC3F7;
                border-radius: 6px;
                padding: 6px 14px;
            }
            QPushButton:hover {
                background-color: #4FC3F7;
                color: #0B1D3A;
            }
        """)
        refresh_btn.clicked.connect(self._refresh_data)
        header.addWidget(refresh_btn)

        main_layout.addLayout(header)

        # ---------- آمار توصیفی ----------
        self.stats_frame = QFrame()
        self.stats_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(26, 42, 74, 0.5);
                border: 2px solid #4FC3F7;
                border-radius: 10px;
            }
        """)
        self.stats_layout = QHBoxLayout(self.stats_frame)
        self.stats_layout.setContentsMargins(15, 10, 15, 10)
        self.stats_layout.setSpacing(20)
        main_layout.addWidget(self.stats_frame)

        # ---------- Splitter: جدول + نمودار ----------
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #2B4A6F;
                width: 4px;
            }
        """)

        # جدول
        table_frame = QFrame()
        table_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(11, 29, 58, 0.6);
                border: 2px solid #2B4A6F;
                border-radius: 10px;
            }
        """)
        tf_layout = QVBoxLayout(table_frame)
        tf_layout.setContentsMargins(8, 8, 8, 8)

        lbl = QLabel("لیست شرکت‌کنندگان")
        lbl.setFont(QFont(FONT_FAMILY, 13, QFont.Weight.Bold))
        lbl.setStyleSheet("color: #4FC3F7; border: none;")
        tf_layout.addWidget(lbl)

        self.table = QTableWidget()
        self.table.setLayoutDirection(
            Qt.LayoutDirection.RightToLeft
        )
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #0B1D3A;
                color: #FFFFFF;
                gridline-color: #2B4A6F;
                border: none;
                font-family: 'Vazirmatn';
                font-size: 11px;
            }
            QTableWidget::item {
                padding: 6px;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #2B4A6F;
            }
            QHeaderView::section {
                background-color: #1A2A4A;
                color: #4FC3F7;
                padding: 8px;
                border: none;
                border-bottom: 2px solid #4FC3F7;
                font-weight: bold;
                font-size: 11px;
            }
        """)
        # ✅ چک None برای verticalHeader
        v_header = self.table.verticalHeader()
        if v_header is not None:
            v_header.setVisible(False)
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table.setAlternatingRowColors(False)
        tf_layout.addWidget(self.table)

        splitter.addWidget(table_frame)

        # پنل نمودار
        chart_frame = QFrame()
        chart_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(11, 29, 58, 0.6);
                border: 2px solid #2B4A6F;
                border-radius: 10px;
            }
        """)
        cf_layout = QVBoxLayout(chart_frame)
        cf_layout.setContentsMargins(12, 12, 12, 12)
        cf_layout.setSpacing(10)

        chart_lbl = QLabel("نمودار توزیع")
        chart_lbl.setFont(
            QFont(FONT_FAMILY, 13, QFont.Weight.Bold)
        )
        chart_lbl.setStyleSheet(
            "color: #4FC3F7; border: none;"
        )
        cf_layout.addWidget(chart_lbl)

        # انتخاب شایستگی برای نمودار
        self.chart_combo = QComboBox()
        self.chart_combo.setFont(QFont(FONT_FAMILY, 11))
        for code, label in COMPETENCIES:
            self.chart_combo.addItem(label, code)
        self.chart_combo.setStyleSheet("""
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
        self.chart_combo.currentIndexChanged.connect(
            self._update_histogram
        )
        cf_layout.addWidget(self.chart_combo)

        self.histogram = _HistogramWidget()
        cf_layout.addWidget(self.histogram, stretch=1)

        # آمار شایستگی انتخاب‌شده
        self.chart_stats = QLabel("—")
        self.chart_stats.setFont(QFont(FONT_FAMILY, 11))
        self.chart_stats.setStyleSheet(
            "color: #B0BEC5; border: none;"
        )
        self.chart_stats.setWordWrap(True)
        cf_layout.addWidget(self.chart_stats)

        splitter.addWidget(chart_frame)
        splitter.setSizes([700, 500])

        main_layout.addWidget(splitter, stretch=1)

        # ---------- دکمه‌های پایین ----------
        bottom = QHBoxLayout()
        bottom.setSpacing(10)

        export_csv_btn = QPushButton("📄 صادرات CSV")
        export_csv_btn.setFont(QFont(FONT_FAMILY, 12))
        export_csv_btn.setMinimumHeight(40)
        export_csv_btn.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        export_csv_btn.setStyleSheet("""
            QPushButton {
                background-color: #2B4A6F;
                color: #FFFFFF;
                border: 2px solid #4FC3F7;
                border-radius: 8px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #4FC3F7;
                color: #0B1D3A;
            }
        """)
        export_csv_btn.clicked.connect(self._export_csv)
        bottom.addWidget(export_csv_btn)

        export_excel_btn = QPushButton("📊 صادرات Excel")
        export_excel_btn.setFont(QFont(FONT_FAMILY, 12))
        export_excel_btn.setMinimumHeight(40)
        export_excel_btn.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        export_excel_btn.setStyleSheet("""
            QPushButton {
                background-color: #2B4A6F;
                color: #FFFFFF;
                border: 2px solid #4CAF50;
                border-radius: 8px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #4CAF50;
                color: #FFFFFF;
            }
        """)
        export_excel_btn.clicked.connect(self._export_excel)
        bottom.addWidget(export_excel_btn)

        bottom.addStretch()

        close_btn = QPushButton("بستن")
        close_btn.setFont(QFont(FONT_FAMILY, 12))
        close_btn.setMinimumHeight(40)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #2B4A6F;
                color: #FFFFFF;
                border: 2px solid #666666;
                border-radius: 8px;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background-color: #666666;
            }
        """)
        close_btn.clicked.connect(self.close)
        bottom.addWidget(close_btn)

        main_layout.addLayout(bottom)

        # مسیر دیتابیس در پایین
        path_lbl = QLabel(f"مسیر پایگاه داده: {DB_PATH}")
        path_lbl.setFont(QFont(FONT_FAMILY, 9))
        path_lbl.setStyleSheet("color: #666666;")
        main_layout.addWidget(path_lbl)

    # ================================================================
    @staticmethod
    def _label(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setFont(QFont(FONT_FAMILY, 11))
        lbl.setStyleSheet("color: #FFFFFF;")
        return lbl

    # ================================================================
    def _refresh_data(self):
        print("🔄 بروزرسانی داده‌ها...")
        self._df = load_data()

        if self._df.empty:
            QMessageBox.information(
                self,
                "بدون داده",
                "هیچ شرکت‌کننده‌ای در پایگاه داده یافت نشد.",
            )
            return

        self._apply_filters()

    def _apply_filters(self):
        if self._df.empty:
            return

        mode = self.mode_combo.currentText()
        df = self._df.copy()

        if mode != "همه":
            df = df[df["mode"] == mode]

        self._update_table(df)
        self._update_stats(df)
        self._update_histogram()

    # ================================================================
    def _update_table(self, df: pd.DataFrame):
        headers = [
            "ID", "حالت", "تاریخ", "مدت (دقیقه)",
            "سن", "جنسیت",
            "صداقت", "اعتماد", "حل مسئله", "مسئولیت",
        ]

        self.table.setRowCount(len(df))
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)

        for r, (_, row) in enumerate(df.iterrows()):
            def _fmt(key):
                v = row.get(key)
                if v is None or pd.isna(v):
                    return "—"
                return f"{float(v):.1f}"

            items = [
                str(row["participant_id"]),
                str(row["mode"]),
                str(row["date"]),
                str(row["duration_min"]),
                str(row["age"]) if row["age"] is not None else "—",
                str(row["gender"]) if row["gender"] else "—",
                _fmt("score_honesty"),
                _fmt("score_trustworthiness"),
                _fmt("score_problem_solving"),
                _fmt("score_accountability"),
            ]

            for c, txt in enumerate(items):
                item = QTableWidgetItem(txt)
                item.setTextAlignment(
                    int(
                        Qt.AlignmentFlag.AlignRight
                        | Qt.AlignmentFlag.AlignVCenter
                    )
                )
                # رنگ‌بندی نمرات
                if c >= 6 and txt != "—":
                    try:
                        val = float(txt)
                        if val >= 70:
                            item.setForeground(
                                QColor("#4CAF50")
                            )
                        elif val >= 40:
                            item.setForeground(
                                QColor("#FF8F00")
                            )
                        else:
                            item.setForeground(
                                QColor("#D32F2F")
                            )
                    except ValueError:
                        pass

                self.table.setItem(r, c, item)

        self.table.resizeColumnsToContents()
        header = self.table.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(
                QHeaderView.ResizeMode.Stretch
            )

    # ================================================================
    def _update_stats(self, df: pd.DataFrame):
        # حذف فریم‌های قبلی
        while self.stats_layout.count():
            item = self.stats_layout.takeAt(0)
            if item is None:
                continue
            w = item.widget()
            if w is None:
                continue
            try:
                w.setParent(None)
                w.deleteLater()
            except RuntimeError:
                pass

        # عنوان
        n_total = len(df)
        title = QLabel(f"آمار توصیفی ({n_total} شرکت‌کننده)")
        title.setFont(QFont(FONT_FAMILY, 13, QFont.Weight.Bold))
        title.setStyleSheet("color: #4FC3F7; border: none;")
        self.stats_layout.addWidget(title)

        # برای هر شایستگی
        for comp_code, comp_label in COMPETENCIES:
            col = f"score_{comp_code}"
            values = df[col].dropna().tolist()

            box = QFrame()
            box.setStyleSheet("""
                QFrame {
                    background-color: rgba(11, 29, 58, 0.5);
                    border: 1px solid #2B4A6F;
                    border-radius: 8px;
                }
            """)
            box_layout = QVBoxLayout(box)
            box_layout.setSpacing(4)
            box_layout.setContentsMargins(10, 8, 10, 8)

            name = QLabel(comp_label)
            name.setFont(
                QFont(FONT_FAMILY, 11, QFont.Weight.Bold)
            )
            name.setStyleSheet(
                "color: #FFFFFF; border: none;"
            )
            name.setAlignment(Qt.AlignmentFlag.AlignCenter)
            box_layout.addWidget(name)

            if not values:
                stat_text = "—"
            else:
                arr = np.array(values)
                sd = arr.std(ddof=1) if len(arr) > 1 else 0.0
                stat_text = (
                    f"M = {arr.mean():.1f}\n"
                    f"SD = {sd:.1f}"
                )

            stat = QLabel(stat_text)
            stat.setFont(QFont(FONT_FAMILY, 10))
            stat.setStyleSheet(
                "color: #4FC3F7; border: none;"
            )
            stat.setAlignment(Qt.AlignmentFlag.AlignCenter)
            box_layout.addWidget(stat)

            self.stats_layout.addWidget(box)

        self.stats_layout.addStretch()

    # ================================================================
    def _update_histogram(self):
        if self._df.empty:
            return

        mode = self.mode_combo.currentText()
        df = self._df.copy()
        if mode != "همه":
            df = df[df["mode"] == mode]

        comp_code = self.chart_combo.currentData()
        comp_label = self.chart_combo.currentText()

        col = f"score_{comp_code}"
        if col not in df.columns:
            self.histogram.set_data([], comp_label)
            self.chart_stats.setText("—")
            return

        values = df[col].dropna().tolist()
        self.histogram.set_data(values, comp_label)

        if values:
            arr = np.array(values)
            self.chart_stats.setText(
                f"تعداد: {len(arr)}   |   "
                f"میانگین: {arr.mean():.1f}   |   "
                f"SD: {arr.std(ddof=1) if len(arr) > 1 else 0:.1f}   |   "
                f"کمینه: {arr.min():.1f}   |   "
                f"بیشینه: {arr.max():.1f}"
            )
        else:
            self.chart_stats.setText("داده‌ای برای نمایش نیست")

    # ================================================================
    def _export_csv(self):
        if self._df.empty:
            return
        mode = self.mode_combo.currentText()
        df = self._df.copy()
        if mode != "همه":
            df = df[df["mode"] == mode]

        path, _ = QFileDialog.getSaveFileName(
            self,
            "ذخیره‌ی CSV",
            "dashboard_export.csv",
            "CSV files (*.csv)",
        )
        if not path:
            return
        df.to_csv(path, index=False, encoding="utf-8-sig")
        QMessageBox.information(
            self, "ذخیره شد",
            f"✓ {len(df)} ردیف در:\n{path}",
        )

    def _export_excel(self):
        if self._df.empty:
            return
        mode = self.mode_combo.currentText()
        df = self._df.copy()
        if mode != "همه":
            df = df[df["mode"] == mode]

        path, _ = QFileDialog.getSaveFileName(
            self,
            "ذخیره‌ی Excel",
            "dashboard_export.xlsx",
            "Excel files (*.xlsx)",
        )
        if not path:
            return

        try:
            df.to_excel(path, index=False)
            QMessageBox.information(
                self, "ذخیره شد",
                f"✓ {len(df)} ردیف در:\n{path}",
            )
        except Exception as e:
            QMessageBox.warning(
                self,
                "خطا",
                f"Excel ذخیره نشد: {e}\n\n"
                "مطمئن شوید openpyxl نصب است:\n"
                "pip install openpyxl",
            )


# ====================================================================
def main():
    print("=" * 60)
    print("  Truthline — داشبورد پژوهشگر")
    print("=" * 60)
    print(f"  DB: {DB_PATH}")

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

    window = DashboardWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()