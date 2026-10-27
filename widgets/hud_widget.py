"""
ویجت HUD - نسخه 4.0
=====================================
تغییرات نسخه 4.0 (رفع کرش):
- حذف کامل QGraphicsOpacityEffect از set_dimmed — به‌جای آن
  از یک QFrame نیمه‌شفاف (overlay) استفاده می‌شود که بدون
  render به pixmap، ظاهر کم‌رنگ ایجاد می‌کند.
- حذف QGraphicsDropShadowEffect از فریم‌های mission/objective
  (دلیل اصلی خطاهای QPainter re-entrancy).
"""
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame,
    QProgressBar, QPushButton
)
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QFont

from config import SHOW_DECISION_TRAIL
from widgets.procedural_icons import get_icon

FONT_FAMILY = "Vazirmatn"


class HUDWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_saving = False
        self.save_timer = QTimer()
        self.save_timer.timeout.connect(self._hide_save_indicator)

        self._last_status: tuple = ("", "#4FC3F7")
        self._dim_anim = None  # برای سازگاری با نسخه‌ی قبل

        # ✅ overlay برای حالت dim — بدون QGraphicsEffect
        self._dim_overlay: QFrame | None = None

        self._setup_ui()
        self._setup_dim_overlay()
        print("✓ HUDWidget راه‌اندازی شد (نسخه 4.0 — بدون effect)")

    # ================================================================
    def _setup_dim_overlay(self):
        """ساخت لایه‌ی نیمه‌شفاف برای حالت کم‌رنگ"""
        overlay = QFrame(self)
        overlay.setStyleSheet("""
            QFrame {
                background-color: rgba(11, 29, 58, 0.55);
                border: none;
            }
        """)
        overlay.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents, True
        )
        overlay.setGeometry(self.rect())
        overlay.hide()
        self._dim_overlay = overlay

    def resizeEvent(self, event):  # type: ignore
        super().resizeEvent(event)
        if self._dim_overlay is not None:
            self._dim_overlay.setGeometry(self.rect())
            if self._dim_overlay.isVisible():
                self._dim_overlay.raise_()

    # ================================================================
    def set_dimmed(self, dimmed: bool):
        """
        حالت کم‌رنگ با overlay ساده (بدون QGraphicsEffect).
            dimmed=True  → HUD کم‌رنگ
            dimmed=False → HUD پررنگ
        """
        if self._dim_overlay is None:
            return
        if dimmed:
            self._dim_overlay.setGeometry(self.rect())
            self._dim_overlay.raise_()
            self._dim_overlay.show()
        else:
            self._dim_overlay.hide()

    # ================================================================
    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 10, 20, 10)
        main_layout.setSpacing(15)

        # --- بخش ۱: مأموریت ---
        # ✅ بدون add_shadow — سایه حذف شد
        mission_frame = QFrame()
        mission_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(11, 29, 58, 0.85);
                border: 1px solid #4FC3F7;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        mission_layout = QVBoxLayout(mission_frame)
        mission_layout.setSpacing(5)

        self.mission_label = QLabel("ایستگاه کاسپین")
        mf = QFont(FONT_FAMILY, 14)
        mf.setBold(True)
        self.mission_label.setFont(mf)
        self.mission_label.setStyleSheet("QLabel { color: #FFFFFF; }")
        self.mission_label.setToolTip("ایستگاه مداری کاسپین")
        mission_layout.addWidget(self.mission_label)

        self.phase_label = QLabel("آماده‌سازی")
        self.phase_label.setFont(QFont(FONT_FAMILY, 12))
        self.phase_label.setStyleSheet("QLabel { color: #4FC3F7; }")
        self.phase_label.setToolTip("روز جاری مأموریت")
        mission_layout.addWidget(self.phase_label)
        main_layout.addWidget(mission_frame)

        # --- بخش ۲: هدف ---
        objective_frame = QFrame()
        objective_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(26, 42, 74, 0.85);
                border: 1px solid #FF8F00;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        objective_layout = QHBoxLayout(objective_frame)

        self.objective_label = QLabel("شروع مأموریت")
        self.objective_label.setFont(QFont(FONT_FAMILY, 13))
        self.objective_label.setStyleSheet("QLabel { color: #FF8F00; }")
        self.objective_label.setToolTip("هدف اصلی این مرحله")
        # ✅ راست‌چین اجباری با Absolute — مستقل از layoutDirection
        self.objective_label.setLayoutDirection(
            Qt.LayoutDirection.RightToLeft
        )
        self.objective_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignVCenter
        )
        objective_layout.addWidget(self.objective_label)
        main_layout.addWidget(objective_frame, stretch=1)

        # --- بخش ۳: شمارنده سناریو ---
        self.scenario_frame = QFrame()
        self.scenario_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(11, 29, 58, 0.8);
                border: 1px solid #FF8F00;
                border-radius: 5px;
                padding: 8px;
            }
        """)
        scenario_layout = QVBoxLayout(self.scenario_frame)
        scenario_layout.setSpacing(3)

        self.scenario_title = QLabel("سناریو")
        self.scenario_title.setFont(QFont(FONT_FAMILY, 11))
        self.scenario_title.setStyleSheet("QLabel { color: #FF8F00; }")
        scenario_layout.addWidget(self.scenario_title)

        self.scenario_label = QLabel("— / —")
        scf = QFont(FONT_FAMILY, 14)
        scf.setBold(True)
        self.scenario_label.setFont(scf)
        self.scenario_label.setStyleSheet("QLabel { color: #FFFFFF; }")
        # ✅ در RTL، AlignLeft یعنی راست فیزیکی
        self.scenario_label.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.scenario_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignVCenter
        )
        self.scenario_label.setToolTip("سناریوی جاری از کل روز")
        scenario_layout.addWidget(self.scenario_label)

        main_layout.addWidget(self.scenario_frame)
        self.scenario_frame.setVisible(False)

        # --- بخش ۴: نوار پیشرفت ---
        progress_frame = QFrame()
        progress_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(11, 29, 58, 0.8);
                border: 1px solid #4FC3F7;
                border-radius: 5px;
                padding: 6px;
            }
        """)
        pf_layout = QVBoxLayout(progress_frame)
        pf_layout.setSpacing(2)

        self.progress_label = QLabel("پیشرفت مأموریت: ۰٪")
        self.progress_label.setFont(QFont(FONT_FAMILY, 10))
        self.progress_label.setStyleSheet("color: #FFFFFF;")
        self.progress_label.setToolTip("درصد پیشرفت کل مأموریت")
        pf_layout.addWidget(self.progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #1A2A4A;
                border: 1px solid #4FC3F7;
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background-color: #4FC3F7;
                border-radius: 2px;
            }
        """)
        pf_layout.addWidget(self.progress_bar)

        main_layout.addWidget(progress_frame)

        # --- بخش ۵: نقشه‌ی تصمیم ---
        from widgets.decision_trail_widget import DecisionTrailWidget

        self.trail_frame = QFrame()
        self.trail_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(11, 29, 58, 0.8);
                border: 1px solid #4FC3F7;
                border-radius: 5px;
                padding: 6px;
            }
        """)
        trail_layout = QVBoxLayout(self.trail_frame)
        trail_layout.setSpacing(3)

        self.trail_title = QLabel("مسیر تصمیم‌ها")
        self.trail_title.setFont(QFont(FONT_FAMILY, 10))
        self.trail_title.setStyleSheet("QLabel { color: #4FC3F7; }")
        self.trail_title.setToolTip(
            "هر دایره یک تصمیم — توپر: گرفته‌شده، خالی: در انتظار"
        )
        trail_layout.addWidget(self.trail_title)

        self.trail_widget = DecisionTrailWidget()
        trail_layout.addWidget(self.trail_widget)

        main_layout.addWidget(self.trail_frame)
        self.trail_frame.setVisible(False)

        # --- بخش ۶: دکمه‌ها ---
        tools_frame = QFrame()
        tools_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(11, 29, 58, 0.8);
                border: 1px solid #4FC3F7;
                border-radius: 5px;
                padding: 6px;
            }
        """)
        tools_layout = QHBoxLayout(tools_frame)
        tools_layout.setSpacing(6)

        self.log_btn = QPushButton("  L")
        self.log_btn.setIcon(get_icon("notebook", size=24, color="#FF8F00"))
        self.log_btn.setIconSize(QSize(18, 18))
        self.log_btn.setFont(QFont(FONT_FAMILY, 11))
        self.log_btn.setFixedHeight(28)
        self.log_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.log_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.log_btn.setToolTip("دفترچه‌ی مأموریت (کلید L)")
        self.log_btn.setStyleSheet("""
            QPushButton {
                background-color: #2B4A6F;
                color: #FF8F00;
                border: 1px solid #FF8F00;
                border-radius: 5px;
                padding: 2px 8px;
            }
            QPushButton:hover {
                background-color: #FF8F00;
                color: #0B1D3A;
            }
        """)
        self.log_btn.clicked.connect(self._on_log_clicked)
        tools_layout.addWidget(self.log_btn)

        self.dossier_btn = QPushButton("  C")
        self.dossier_btn.setIcon(get_icon("dossier", size=24, color="#4FC3F7"))
        self.dossier_btn.setIconSize(QSize(18, 18))
        self.dossier_btn.setFont(QFont(FONT_FAMILY, 11))
        self.dossier_btn.setFixedHeight(28)
        self.dossier_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.dossier_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.dossier_btn.setToolTip("پرونده‌ی شخصیت‌ها (کلید C)")
        self.dossier_btn.setStyleSheet("""
            QPushButton {
                background-color: #2B4A6F;
                color: #4FC3F7;
                border: 1px solid #4FC3F7;
                border-radius: 5px;
                padding: 2px 8px;
            }
            QPushButton:hover {
                background-color: #4FC3F7;
                color: #0B1D3A;
            }
        """)
        self.dossier_btn.clicked.connect(self._on_dossier_clicked)
        tools_layout.addWidget(self.dossier_btn)

        main_layout.addWidget(tools_frame)

        # ✅ در RTL، «AlignLeft» یعنی «leading» = سمت راست فیزیکی
        _R = (
            Qt.AlignmentFlag.AlignLeft
            | Qt.AlignmentFlag.AlignVCenter
        )
        for lbl in [
            self.mission_label,
            self.phase_label,
            self.objective_label,
            self.scenario_title,
            self.progress_label,
            self.trail_title,
        ]:
            lbl.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            lbl.setAlignment(_R)

        # ✅ راست‌چین کردن دکمه‌های HUD
        for btn in [self.log_btn, self.dossier_btn]:
            btn.setLayoutDirection(
                Qt.LayoutDirection.RightToLeft
            )

    # ================================================================
    # API عمومی
    # ================================================================
    def set_progress(self, percent: int):
        percent = max(0, min(100, percent))
        self.progress_label.setText(f"پیشرفت مأموریت: {percent}٪")
        self.progress_bar.setValue(percent)

    def set_mission(self, mission_name: str):
        self.mission_label.setText(mission_name)

    def set_phase(self, phase_name: str):
        self.phase_label.setText(phase_name)

    def set_objective(self, objective_text: str):
        self.objective_label.setText(objective_text)

    def set_status(self, status_text: str, color: str = "#4FC3F7"):
        self._last_status = (status_text, color)

    def set_scenario_progress(self, current: int, total: int):
        self.scenario_label.setText(f"{current} / {total}")
        self.scenario_frame.setVisible(True)

    def hide_scenario_progress(self):
        self.scenario_frame.setVisible(False)

    def set_phase_color(self, color: str):
        self.phase_label.setStyleSheet(f"QLabel {{ color: {color}; }}")

    def show_save_indicator(self):
        self.is_saving = True
        self.save_timer.start(2000)

    def _hide_save_indicator(self):
        self.is_saving = False
        self.save_timer.stop()

    def _on_log_clicked(self):
        try:
            main_window = self.window()
            open_log = getattr(main_window, "_open_mission_log", None)
            if callable(open_log):
                open_log()
        except Exception as e:
            print(f"⚠️ خطا در باز کردن دفترچه: {e}")

    def _on_dossier_clicked(self):
        try:
            main_window = self.window()
            open_dossier = getattr(
                main_window, "_open_character_dossier", None
            )
            if callable(open_dossier):
                open_dossier()
        except Exception as e:
            print(f"⚠️ خطا در باز کردن پرونده: {e}")

    # ================================================================
    # نقشه‌ی تصمیم
    # ================================================================
    def record_decision(self, quality: float, label: str = ""):
        if not SHOW_DECISION_TRAIL:
            return
        self.trail_widget.mark_next()
        if not self.trail_frame.isVisible():
            self.trail_frame.setVisible(True)

    def reset_trail(self):
        self.trail_widget.reset()
        self.trail_frame.setVisible(False)

    def set_progress_from_scenario(self, phase_key: str,
                                     current: int, total_in_phase: int):
        phase_order = ["phase1", "phase2", "phase3", "phase4", "hexaco"]
        if phase_key not in phase_order:
            return
        phase_index = phase_order.index(phase_key)
        total_phases = len(phase_order)
        phase_weight = 100.0 / total_phases
        in_phase_pct = (
            (current / max(1, total_in_phase)) if total_in_phase > 0 else 0.0
        )
        total_pct = int(
            phase_index * phase_weight + in_phase_pct * phase_weight
        )
        self.progress_label.setText(f"پیشرفت مأموریت: {total_pct}٪")
        self.progress_bar.setValue(total_pct)

    def initialize_decision_trail(self, total_scenarios: int):
        if not SHOW_DECISION_TRAIL:
            return
        self.trail_widget.set_total(total_scenarios)
        self.trail_frame.setVisible(True)