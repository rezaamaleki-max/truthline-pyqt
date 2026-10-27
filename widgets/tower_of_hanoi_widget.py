"""
ویجت آزمون برج هانوی — نسخه‌ی دسکتاپ (PyQt6)
===============================================
- دیالوگ تمام‌صفحه با ۳ میله
- کلیک روی میله → انتخاب دیسک بالایی
- کلیک روی میله‌ی دوم → تلاش حرکت
- ذخیره‌ی metrics + move_log

نسخه: 1.0.0
"""
import time
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QMessageBox, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

from data.toh_items import ToHLogic, compute_toh_evidence

FONT_FAMILY = "Vazirmatn"


DISK_COLORS = {
    1: "#4FC3F7",
    2: "#FFB74D",
    3: "#9C27B0",
}
DISK_NAMES = {1: "کوچک", 2: "متوسط", 3: "بزرگ"}
PEG_LABELS = {"A": "میله‌ی چپ", "B": "میله‌ی وسط", "C": "میله‌ی راست"}


class TowerOfHanoiDialog(QDialog):
    """دیالوگ آزمون ToH."""

    finished_with_result = pyqtSignal(dict, list)  # metrics, moves

    def __init__(self, data_logger, parent=None):
        super().__init__(parent)
        self.data_logger = data_logger
        self.state = {
            "logic": ToHLogic(trial_id=1),
            "selected_peg": None,
            "attempts_used": 0,
            "completed": False,
        }

        self.setWindowTitle("آزمون برج هانوی")
        self.setMinimumSize(900, 720)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setStyleSheet(
            "QDialog { background-color: #0B1D3A; }"
        )

        self._peg_frames: dict = {}
        self._peg_disk_layouts: dict = {}

        self._setup_ui()
        self._render_pegs()
        self._update_progress()

        # ثبت رویداد شروع
        try:
            self.data_logger.log_event(
                scene_id="tower_of_hanoi",
                scenario_id="TOH-01",
                event_type="scene_enter",
                metadata={},
            )
        except Exception:
            pass

    # ============================================================
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        # ---- عنوان ----
        title = QLabel("آزمون برج هانوی")
        tf = QFont(FONT_FAMILY, 22)
        tf.setBold(True)
        title.setFont(tf)
        title.setStyleSheet("color: #4FC3F7;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # ---- دستور ----
        desc = QLabel(
            "همه‌ی دیسک‌ها را از میله‌ی چپ به میله‌ی راست "
            "منتقل کنید. فقط می‌توانید دیسک بالایی هر میله "
            "را بردارید و روی دیسک بزرگ‌تر بگذارید. "
            "حداقل ۷ حرکت لازم است.\n"
            "برای حرکت: ابتدا روی میله‌ی مبدأ کلیک کنید، "
            "سپس روی میله‌ی مقصد."
        )
        desc.setFont(QFont(FONT_FAMILY, 11))
        desc.setStyleSheet(
            "color: #CCCCCC; padding: 10px; "
            "background-color: rgba(26, 42, 74, 0.7); "
            "border-radius: 8px;"
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # ---- نوار پیشرفت ----
        progress_row = QHBoxLayout()
        self.progress_label = QLabel("0 حرکت معتبر")
        self.progress_label.setFont(QFont(FONT_FAMILY, 11))
        self.progress_label.setStyleSheet("color: #4FC3F7;")
        progress_row.addWidget(self.progress_label)

        progress_row.addStretch()

        self.attempt_label = QLabel(
            f"تلاش ۱ از {ToHLogic.MAX_ATTEMPTS}"
        )
        self.attempt_label.setFont(QFont(FONT_FAMILY, 11))
        self.attempt_label.setStyleSheet("color: #FF8F00;")
        progress_row.addWidget(self.attempt_label)
        layout.addLayout(progress_row)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 7)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #1A2A4A;
                border: 1px solid #4FC3F7;
                border-radius: 4px;
                height: 8px;
            }
            QProgressBar::chunk {
                background-color: #4FC3F7;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)

        # ---- میله‌ها ----
        pegs_row = QHBoxLayout()
        pegs_row.setSpacing(16)

        for peg_id in ("A", "B", "C"):
            frame = self._build_peg_frame(peg_id)
            pegs_row.addWidget(frame, 1)

        layout.addLayout(pegs_row, stretch=1)

        # ---- دکمه‌ها ----
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.retry_btn = QPushButton("🔄 شروع دوباره")
        self.retry_btn.setFont(QFont(FONT_FAMILY, 12))
        self.retry_btn.setMinimumHeight(42)
        self.retry_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.retry_btn.setStyleSheet("""
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
        """)
        self.retry_btn.clicked.connect(self._on_retry)
        btn_row.addWidget(self.retry_btn, 1)

        self.finish_btn = QPushButton("پایان آزمون")
        self.finish_btn.setFont(QFont(FONT_FAMILY, 12))
        self.finish_btn.setMinimumHeight(42)
        self.finish_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.finish_btn.setStyleSheet("""
            QPushButton {
                background-color: #4A3A2B;
                color: #FFB74D;
                border: 2px solid #FF8F00;
                border-radius: 8px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #FF8F00;
                color: #0B1D3A;
            }
        """)
        self.finish_btn.clicked.connect(self._on_finish)
        btn_row.addWidget(self.finish_btn, 1)

        layout.addLayout(btn_row)

    # ============================================================
    def _build_peg_frame(self, peg_id: str) -> QFrame:
        frame = QFrame()
        frame.setObjectName(f"peg_{peg_id}")
        frame.setStyleSheet("""
            QFrame {
                background-color: rgba(26, 42, 74, 0.5);
                border: 2px solid #2B4A6F;
                border-radius: 10px;
            }
        """)
        frame.mousePressEvent = (
            lambda a0, pid=peg_id: self._on_peg_click(pid)
        )

        v = QVBoxLayout(frame)
        v.setContentsMargins(8, 8, 8, 8)
        v.setSpacing(4)

        # برچسب
        lbl = QLabel(PEG_LABELS[peg_id])
        lbl.setFont(QFont(FONT_FAMILY, 11, QFont.Weight.Bold))
        lbl.setStyleSheet("color: #4FC3F7; border: none;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents, True
        )
        v.addWidget(lbl)

        # ناحیه‌ی دیسک‌ها
        disk_area = QFrame()
        disk_area.setStyleSheet(
            "background: transparent; border: none;"
        )
        disk_area.mousePressEvent = (
            lambda a0, pid=peg_id: self._on_peg_click(pid)
        )
        dl = QVBoxLayout(disk_area)
        dl.setContentsMargins(0, 0, 0, 0)
        dl.setSpacing(4)
        dl.setAlignment(Qt.AlignmentFlag.AlignBottom)
        v.addWidget(disk_area, stretch=1)

        self._peg_frames[peg_id] = frame
        self._peg_disk_layouts[peg_id] = dl
        return frame

    # ============================================================
    def _render_pegs(self):
        logic: ToHLogic = self.state["logic"]
        selected = self.state["selected_peg"]

        for peg_id in ("A", "B", "C"):
            frame = self._peg_frames[peg_id]
            dl = self._peg_disk_layouts[peg_id]

            # پاک کردن دیسک‌های قبلی
            while dl.count():
                item = dl.takeAt(0)
                if item and item.widget():
                    item.widget().deleteLater()

            # رنگ حاشیه
            if selected == peg_id:
                frame.setStyleSheet("""
                    QFrame {
                        background-color: rgba(255, 143, 0, 0.15);
                        border: 3px solid #FF8F00;
                        border-radius: 10px;
                    }
                """)
            else:
                frame.setStyleSheet("""
                    QFrame {
                        background-color: rgba(26, 42, 74, 0.5);
                        border: 2px solid #2B4A6F;
                        border-radius: 10px;
                    }
                """)

            # دیسک‌ها (از پایین به بالا در layout)
            disks = logic.pegs[peg_id]
            for disk in disks:  # [3,2,1] → 3 پایین، 1 بالا
                w = {1: 60, 2: 78, 3: 95}[disk]
                c = DISK_COLORS[disk]
                disk_widget = QFrame()
                disk_widget.setFixedHeight(34)
                disk_widget.setStyleSheet(f"""
                    QFrame {{
                        background-color: {c};
                        border-radius: 6px;
                        border: 2px solid rgba(255, 255, 255, 0.3);
                    }}
                """)
                disk_widget.setAttribute(
                    Qt.WidgetAttribute.WA_TransparentForMouseEvents,
                    True,
                )
                # عرض نسبی با spacer
                spacer = QHBoxLayout(disk_widget)
                spacer.setContentsMargins(0, 0, 0, 0)
                spacer.addStretch()
                disk_widget.setFixedWidth(w * 3)
                dl.addWidget(
                    disk_widget,
                    alignment=Qt.AlignmentFlag.AlignHCenter,
                )

    # ============================================================
    def _update_progress(self):
        logic: ToHLogic = self.state["logic"]
        metrics = logic.get_metrics()
        self.progress_label.setText(
            f"{metrics['valid_moves']} حرکت معتبر "
            f"• {metrics['invalid_attempts']} نامعتبر"
        )
        self.progress_bar.setValue(
            min(7, metrics["valid_moves"])
        )
        self.attempt_label.setText(
            f"تلاش {self.state['attempts_used'] + 1} "
            f"از {ToHLogic.MAX_ATTEMPTS}"
        )

    # ============================================================
    def _on_peg_click(self, peg_id: str):
        if self.state["completed"]:
            return

        logic: ToHLogic = self.state["logic"]

        # انتخاب اول
        if self.state["selected_peg"] is None:
            if not logic.pegs[peg_id]:
                QMessageBox.information(
                    self, "میله خالی",
                    "این میله خالی است. میله‌ی دیگری را "
                    "انتخاب کنید."
                )
                return
            self.state["selected_peg"] = peg_id
            self._render_pegs()
            return

        # لغو
        if self.state["selected_peg"] == peg_id:
            self.state["selected_peg"] = None
            self._render_pegs()
            return

        # حرکت
        source = self.state["selected_peg"]
        self.state["selected_peg"] = None
        moved, err = logic.try_move(source, peg_id)

        if not moved:
            QMessageBox.warning(
                self, "حرکت نامعتبر", err
            )
            self._render_pegs()
            self._update_progress()
            return

        self._render_pegs()
        self._update_progress()

        if logic.is_solved:
            self._on_solved()

    # ============================================================
    def _on_solved(self):
        self.state["completed"] = True
        QMessageBox.information(
            self, "🎉 موفقیت",
            f"برج هانوی را در {len(self.state['logic'].valid_move_count())} "
            f"حرکت حل کردید!"
        )
        metrics = self.state["logic"].get_metrics()
        moves = self.state["logic"].serialize_moves()
        self._emit_and_close(metrics, moves)

    # ============================================================
    def _on_retry(self):
        self.state["attempts_used"] += 1
        if self.state["attempts_used"] >= ToHLogic.MAX_ATTEMPTS:
            self._on_finish()
            return

        logic: ToHLogic = self.state["logic"]
        logic.reset()
        logic.trial_id = self.state["attempts_used"] + 1
        logic.attempt_number = self.state["attempts_used"] + 1
        self.state["selected_peg"] = None
        self._render_pegs()
        self._update_progress()

    # ============================================================
    def _on_finish(self):
        if self.state["completed"]:
            return
        self.state["completed"] = True
        metrics = self.state["logic"].get_metrics()
        moves = self.state["logic"].serialize_moves()
        self._emit_and_close(metrics, moves)

    # ============================================================
    def _emit_and_close(self, metrics: dict, moves: list):
        # ذخیره در DB
        try:
            self.data_logger.log_event(
                scene_id="tower_of_hanoi",
                scenario_id="TOH-01",
                event_type="tower_of_hanoi_completed",
                metadata=metrics,
            )
        except Exception as e:
            print(f"⚠️ log: {e}")

        # ثبت evidence
        evidence_items = compute_toh_evidence(metrics)
        try:
            for ev in evidence_items:
                self.data_logger.log_evidence(
                    scenario_id="TOH-01",
                    competency="problem_solving",
                    subcomponent="برنامه‌ریزی راهبردی",
                    evidence_key=ev["evidence_key"],
                    evidence_value=ev["evidence_value"],
                    weight=ev["weight"],
                )
        except Exception as e:
            print(f"⚠️ evidence: {e}")

        self.finished_with_result.emit(metrics, moves)
        QTimer.singleShot(50, self.accept)