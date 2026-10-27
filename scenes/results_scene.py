"""
صحنه نتایج نهایی:
- نمودار راداری چهار شایستگی
- پنل تفسیر کیفی بر اساس الگوی نمرات
"""
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QMessageBox, QFrame, QGraphicsOpacityEffect
)
from PyQt6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve
)
from PyQt6.QtGui import QFont
import os          # ✅ اضافه شد
import sys
import subprocess
import time

from scenes.base_scene import BaseScene
from widgets.radar_chart import RadarChart

FONT_FAMILY = "Vazirmatn"


# ============================================================
# برچسب فارسی هر شایستگی
# ============================================================
COMPETENCY_LABELS = [
    "صداقت و یکپارچگی",
    "قابلیت اعتماد",
    "حل مسئله",
    "مسئولیت‌پذیری",
]


# ============================================================
# متن تفسیر برای هر ترکیب (شاخص، سطح)
# سطوح: high (>=70)، mid (40..69)، low (<40)
# ============================================================
COMPETENCY_INTERPRETATIONS = {
    (0, "high"): "پایبندی استثنایی به حقیقت و اصول اخلاقی، حتی تحت فشار.",
    (0, "mid"): "صداقت شما موقعیت‌محور است و به شرایط وابسته می‌شود.",
    (0, "low"): "منافع شخصی معمولاً بر ملاحظات اخلاقی اولویت می‌یابد.",

    (1, "high"): "به شکلی قابل اتکا به تعهدات و وعده‌های خود پایبندید.",
    (1, "mid"): "قابلیت اعتماد شما در شرایط عادی خوب است اما در بحران نوسان دارد.",
    (1, "low"): "در حفظ تعهدات و شفافیت نیاز به تمرین و بازنگری دارید.",

    (2, "high"): "تحلیل‌گر نظام‌مندی هستید که مسائل پیچیده را ریشه‌ای حل می‌کنید.",
    (2, "mid"): "در حل مسائل توانمندید اما در شرایط ابهام گاهی عجولانه عمل می‌کنید.",
    (2, "low"): "در تشخیص ریشه مسائل و برنامه‌ریزی نظام‌مند نیاز به توسعه دارید.",

    (3, "high"): "مسئولیت‌پذیری بالایی دارید و از اشتباهات خود درس می‌گیرید.",
    (3, "mid"): "در پذیرش مسئولیت قابل اتکا هستید اما از مواجهه با بازخورد تلخ دوری می‌کنید.",
    (3, "low"): "در پاسخگویی و پذیرش پیامدها نیازمند تقویت هستید.",
}


def _classify(score: float) -> str:
    """تبدیل نمره عددی به سطح کیفی"""
    if score >= 70:
        return "high"
    if score >= 40:
        return "mid"
    return "low"


# ============================================================
# صحنه نتایج
# ============================================================
class ResultsScene(BaseScene):

    def __init__(self, game_manager):
        super().__init__(game_manager)
        self.radar_chart = RadarChart()
        self.radar_chart.setMinimumSize(360, 360)

        # ✅ پیش‌تعریف ویجت‌های تفسیر
        self.profile_badge: QLabel = QLabel()
        self.interp_avg: QLabel = QLabel()
        self.interp_strength: QLabel = QLabel()
        self.interp_weakness: QLabel = QLabel()
        self.interp_per_comp: QLabel = QLabel()
        self.interp_advice: QLabel = QLabel()
        self._sub_scores: dict = {}

        # ✅ فاز C: بج MRL
        self.mrl_badge: QLabel = QLabel()
        self.mrl_detail: QLabel = QLabel()

        self.typo_badge: QLabel = QLabel()
        self.typo_desc: QLabel = QLabel()

        self._session_lbl: QLabel | None = None

        # ✅ نگه‌داشتن مراجع انیمیشن‌ها (برای جلوگیری از GC)
        self._anim_refs: list = []

        # ✅ نگه‌داشتن مراجع عناصری که باید انیمیت شوند
        self._title_ref: QLabel | None = None
        self._subtitle_ref: QLabel | None = None
        self._interp_panel_ref: QFrame | None = None
        self._info_frame_ref: QFrame | None = None
        self._buttons_ref: list = []

        self._setup_ui()
        print("✓ ResultsScene راه‌اندازی شد")

    # ----------------------------------------------------------------
    def _setup_ui(self):
        main_layout = self.main_layout
        main_layout.setContentsMargins(30, 20, 30, 20)
        main_layout.setSpacing(12)

        # عنوان
        title = QLabel("نیمرخ شایستگی عملیاتی")
        tf = QFont(FONT_FAMILY, 26)
        tf.setBold(True)
        title.setFont(tf)
        title.setStyleSheet("color: #4FC3F7;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)
        # ✅ ذخیره‌ی مرجع برای انیمیشن
        self._title_ref = title

        # زیرعنوان
        subtitle = QLabel("بر اساس شواهد رفتاری ثبت‌شده در طول مأموریت")
        subtitle.setFont(QFont(FONT_FAMILY, 12))
        subtitle.setStyleSheet("color: #B0BEC5;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(subtitle)
        # ✅ ذخیره‌ی مرجع
        self._subtitle_ref = subtitle

        main_layout.addSpacing(8)

        # ---------------------------------------------------------
        # Layout افقی: رادار + تفسیر
        # ---------------------------------------------------------
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)

        content_layout.addWidget(self.radar_chart, stretch=3)
        interp_panel = self._build_interpretation_panel()
        content_layout.addWidget(interp_panel, stretch=2)
        # ✅ ذخیره‌ی مرجع
        self._interp_panel_ref = interp_panel

        main_layout.addLayout(content_layout, stretch=1)

        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(11, 29, 58, 0.6);
                border: 1px solid #2B4A6F;
                border-radius: 6px;
            }
        """)
        info_layout = QHBoxLayout(info_frame)
        info_layout.setContentsMargins(15, 8, 15, 8)

        logger = self.game_manager.data_logger
        participant_id = getattr(logger, "participant_id", "—")

        # ✅ محاسبه‌ی مطمئن مدت جلسه
        session_start = getattr(logger, "session_start", None)
        session_end = time.time()
        duration_min = 0

        if session_start is not None:
            try:
                delta = float(session_end) - float(session_start)
                if delta > 0:
                    duration_min = int(delta / 60)
            except (TypeError, ValueError):
                duration_min = 0

        # اگر session_start صفر بود، سعی کن از دیتابیس بخوانی
        if duration_min == 0:
            try:
                import sqlite3
                from config import DB_PATH
                conn = sqlite3.connect(DB_PATH)
                cur = conn.cursor()
                cur.execute(
                    "SELECT session_start, session_end FROM "
                    "participants WHERE participant_id = ?",
                    (participant_id,)
                )
                row = cur.fetchone()
                conn.close()
                if row and row[0]:
                    ss = float(row[0])
                    se = float(row[1]) if row[1] else float(session_end)
                    delta = se - ss
                    if delta > 0:
                        duration_min = int(delta / 60)
            except Exception as e:
                print(f"⚠️ خطا در خواندن مدت جلسه: {e}")

        # ✅ ذخیره به‌عنوان attribute برای به‌روزرسانی بعدی
        self._session_lbl = QLabel(
            f"⏱  مدت جلسه: ...    |    "
            f"👤  شناسه: {participant_id}"
        )
        self._session_lbl.setFont(QFont(FONT_FAMILY, 11))
        self._session_lbl.setStyleSheet(
            "color: #B0BEC5; border: none;"
        )
        self._session_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_layout.addWidget(self._session_lbl)

        main_layout.addWidget(info_frame)
        # ✅ ذخیره‌ی مرجع
        self._info_frame_ref = info_frame

        # ---------------------------------------------------------
        # دکمه‌های پایین
        # ---------------------------------------------------------
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)

        # ✅ دکمه‌ی PDF (قبل از restart)
        pdf_btn = QPushButton("📄 دریافت گزارش PDF")
        pdf_btn.setMinimumHeight(52)
        pdf_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        pdf_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        pdf_btn.setStyleSheet("""
            QPushButton {
                background-color: #2B4A6F;
                color: #FFFFFF;
                border: 2px solid #FF8F00;
                border-radius: 10px;
                font-size: 15px;
                font-weight: bold;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #FF8F00;
                color: #0B1D3A;
                border: 2px solid #FFFFFF;
            }
        """)
        pdf_btn.clicked.connect(self._on_pdf_clicked)
        buttons_layout.addWidget(pdf_btn, 1)

        restart_btn = QPushButton("شروع مأموریت جدید")
        restart_btn.setMinimumHeight(52)
        restart_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        restart_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        restart_btn.setStyleSheet("""
            QPushButton {
                background-color: #2B4A6F;
                color: #FFFFFF;
                border: 2px solid #4FC3F7;
                border-radius: 10px;
                font-size: 15px;
                font-weight: bold;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #4FC3F7;
                color: #0B1D3A;
                border: 2px solid #FFFFFF;
            }
        """)
        restart_btn.clicked.connect(self._on_restart)
        buttons_layout.addWidget(restart_btn, 1)

        exit_btn = QPushButton("خروج کامل")
        exit_btn.setMinimumHeight(52)
        exit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        exit_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        exit_btn.setStyleSheet("""
            QPushButton {
                background-color: #D32F2F;
                color: #FFFFFF;
                border: 2px solid #FFFFFF;
                border-radius: 10px;
                font-size: 15px;
                font-weight: bold;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #B71C1C;
            }
        """)
        exit_btn.clicked.connect(self._on_exit)
        buttons_layout.addWidget(exit_btn, 1)
        # ✅ ذخیره‌ی مراجع دکمه‌ها
        self._buttons_ref = [restart_btn, exit_btn]

        main_layout.addLayout(buttons_layout)

    # ----------------------------------------------------------------
    def _build_interpretation_panel(self) -> QFrame:
        """ساخت پنل تفسیر کیفی"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: rgba(26, 42, 74, 0.75);
                border: 2px solid #4FC3F7;
                border-radius: 12px;
            }
        """)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        # عنوان پنل
        hdr = QLabel("تفسیر تحلیلی")
        hf = QFont(FONT_FAMILY, 14)
        hf.setBold(True)
        hdr.setFont(hf)
        hdr.setStyleSheet("color: #4FC3F7; border: none;")
        hdr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hdr)

        # بج پروفایل (بازاستفاده از ویجت پیش‌تعریف‌شده)
        self.profile_badge.setText("—")
        self.profile_badge.setFont(QFont(FONT_FAMILY, 12, QFont.Weight.Bold))
        self.profile_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.profile_badge.setStyleSheet("""
            QLabel {
                color: #0B1D3A;
                background-color: #4FC3F7;
                border-radius: 14px;
                padding: 5px 12px;
                font-weight: bold;
                border: none;
            }
        """)
        self.profile_badge.setMaximumHeight(32)
        layout.addWidget(self.profile_badge, alignment=Qt.AlignmentFlag.AlignCenter)

        # ✅ فاز C: بج MRL (سطح استدلال اخلاقی)
        self.mrl_badge.setText("—")
        self.mrl_badge.setFont(
            QFont(FONT_FAMILY, 11, QFont.Weight.Bold)
        )
        self.mrl_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mrl_badge.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                background-color: #455A64;
                border-radius: 12px;
                padding: 4px 10px;
                font-weight: bold;
                border: none;
            }
        """)
        self.mrl_badge.setMaximumHeight(28)
        layout.addWidget(
            self.mrl_badge,
            alignment=Qt.AlignmentFlag.AlignCenter,
        )

        # خط توضیح کوچک
        self.mrl_detail.setText("")
        self.mrl_detail.setFont(QFont(FONT_FAMILY, 9))
        self.mrl_detail.setStyleSheet(
            "color: #90A4AE; border: none;"
        )
        self.mrl_detail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mrl_detail.setWordWrap(True)
        layout.addWidget(self.mrl_detail)

        # خط جداکننده
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background-color: #2B4A6F; max-height: 1px; border: none;")
        layout.addWidget(sep)

        # میانگین
        self.interp_avg.setText("—")
        self.interp_avg.setFont(QFont(FONT_FAMILY, 11))
        self.interp_avg.setStyleSheet("color: #B0BEC5; border: none;")
        self.interp_avg.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.interp_avg.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignAbsolute
        )
        layout.addWidget(self.interp_avg)

        # قوی‌ترین بُعد
        self.interp_strength.setText("—")
        self.interp_strength.setFont(QFont(FONT_FAMILY, 11, QFont.Weight.Bold))
        self.interp_strength.setStyleSheet(
            "color: #4CAF50; border: none; padding: 3px 0;"
        )
        self.interp_strength.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.interp_strength.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignAbsolute
        )
        self.interp_strength.setWordWrap(True)
        layout.addWidget(self.interp_strength)

        # نقطه قابل بهبود
        self.interp_weakness.setText("—")
        self.interp_weakness.setFont(QFont(FONT_FAMILY, 11, QFont.Weight.Bold))
        self.interp_weakness.setStyleSheet(
            "color: #FF8F00; border: none; padding: 3px 0;"
        )
        self.interp_weakness.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.interp_weakness.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignAbsolute
        )
        self.interp_weakness.setWordWrap(True)
        layout.addWidget(self.interp_weakness)

        # خط جداکننده دوم
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet(
            "background-color: #2B4A6F; max-height: 1px; border: none;"
        )
        layout.addWidget(sep2)

        # تفسیر هر شایستگی
        self.interp_per_comp.setText("—")
        self.interp_per_comp.setFont(QFont(FONT_FAMILY, 10))
        self.interp_per_comp.setStyleSheet("color: #CFD8DC; border: none;")
        self.interp_per_comp.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.interp_per_comp.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignAbsolute
        )
        self.interp_per_comp.setWordWrap(True)
        layout.addWidget(self.interp_per_comp)

        layout.addStretch()

        # کادر پیشنهاد
        self.interp_advice.setText("—")
        self.interp_advice.setFont(QFont(FONT_FAMILY, 11, QFont.Weight.Bold))
        self.interp_advice.setStyleSheet("""
            QLabel {
                color: #4FC3F7;
                background-color: rgba(79, 195, 247, 0.10);
                border: 1px dashed #4FC3F7;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        self.interp_advice.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.interp_advice.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignAbsolute
        )
        self.interp_advice.setWordWrap(True)
        self.interp_advice.setMinimumHeight(50)
        layout.addWidget(self.interp_advice)

        # ✅ فاز E: بج Typology
        self.typo_badge = QLabel()
        self.typo_badge.setText("—")
        self.typo_badge.setFont(
            QFont(FONT_FAMILY, 12, QFont.Weight.Bold)
        )
        self.typo_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.typo_badge.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                background-color: #455A64;
                border-radius: 14px;
                padding: 5px 12px;
                font-weight: bold;
                border: none;
            }
        """)
        self.typo_badge.setMaximumHeight(30)
        layout.addWidget(self.typo_badge)

        self.typo_desc = QLabel("")
        self.typo_desc.setFont(QFont(FONT_FAMILY, 10))
        self.typo_desc.setStyleSheet(
            "color: #90A4AE; border: none;"
        )
        self.typo_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.typo_desc.setWordWrap(True)
        layout.addWidget(self.typo_desc)

        return frame

    # ================================================================
    def on_enter(self, **kwargs):
        print("✓ ورود به صحنه نتایج")
        self.game_manager.data_logger.log_event(
            scene_id="results", scenario_id="results_start",
            event_type="scene_enter", metadata={}
        )
        self._compute_and_save_consistency()

        self._calculate_and_save_scores()
        scores = self._get_final_scores()
        self.radar_chart.set_scores(scores)
        self._apply_interpretation(scores)

        # ✅ به‌روزرسانی label مدت جلسه بعد از محاسبه
        self._refresh_session_duration()

        QTimer.singleShot(60, self._animate_entrance)

    def _refresh_session_duration(self):
        """محاسبه‌ی دقیق مدت جلسه از logger + دیتابیس"""
        try:
            logger = self.game_manager.data_logger
            participant_id = getattr(logger, "participant_id", "—")

            session_start = None
            session_end = None

            # از حافظه
            try:
                ss = getattr(logger, "session_start", None)
                if ss is not None and float(ss) > 0:
                    session_start = float(ss)
                    session_end = time.time()
            except (TypeError, ValueError):
                pass

            # از دیتابیس
            if session_start is None:
                import sqlite3
                from config import DB_PATH
                conn = sqlite3.connect(DB_PATH)
                cur = conn.cursor()
                cur.execute(
                    "SELECT session_start, session_end FROM "
                    "participants WHERE participant_id = ?",
                    (participant_id,)
                )
                row = cur.fetchone()
                conn.close()
                if row and row[0] is not None:
                    session_start = float(row[0])
                    session_end = (
                        float(row[1]) if row[1] is not None
                        else time.time()
                    )

            duration_min = 0
            if session_start and session_end and session_end > session_start:
                delta_sec = float(session_end) - float(session_start)
                duration_min = max(0, int(delta_sec / 60))
                if duration_min == 0 and delta_sec > 10:
                    duration_min = 1  # حداقل ۱ دقیقه

            print(f"   [INFO] session_start={session_start}")
            print(f"   [INFO] session_end={session_end}")
            print(f"   [INFO] مدت جلسه: {duration_min} دقیقه")

            # به‌روزرسانی label
            if hasattr(self, "_session_lbl") and self._session_lbl is not None:
                self._session_lbl.setText(
                    f"⏱  مدت جلسه: {duration_min} دقیقه    |    "
                    f"👤  شناسه: {participant_id}"
                )
        except Exception as e:
            print(f"⚠️ خطا در به‌روزرسانی مدت جلسه: {e}")
            import traceback
            traceback.print_exc()

    # ================================================================
    # انیمیشن ورودی سینمایی
    # ================================================================
    def _animate_entrance(self):
        """اجرای دنباله‌ی انیمیشن ورود برای عناصر صحنه"""
        # ✅ توقف انیمیشن‌های قبلی (در صورت ورود دوباره)
        self._stop_all_anims()

        # بازنشانی همه‌ی opacityها
        for widget in self._collect_animated_widgets():
            if widget is not None:
                try:
                    widget.setGraphicsEffect(None)
                except Exception:
                    pass

        # ---- ۱. عنوان (تأخیر ۰) ----
        self._fade_in(self._title_ref, delay_ms=0)

        # ---- ۲. زیرعنوان (۱۵۰ms) ----
        self._fade_in(self._subtitle_ref, delay_ms=150)

        # ---- ۳. نمودار راداری (۳۰۰ms) ----
        # ✅ نمودار راداری custom paintEvent دارد و نباید
        #    QGraphicsOpacityEffect بگیرد؛ وگرنه خطای
        #    "Painter not active" رخ می‌دهد.
        #    به‌جای fade، مستقیم نمایش داده می‌شود.
        try:
            self.radar_chart.setGraphicsEffect(None)
            self.radar_chart.setVisible(True)
            self.radar_chart.update()
        except Exception:
            pass

        # ---- ۴. پنل تفسیر (۴۵۰ms) ----
        self._fade_in(self._interp_panel_ref, delay_ms=450)

        # ---- ۵. عناصر داخل پنل تفسیر (پله‌ای) ----
        interp_elements = [
            self.profile_badge,     # 900ms
            self.interp_avg,        # 1000ms
            self.interp_strength,   # 1150ms
            self.interp_weakness,   # 1250ms
            self.interp_per_comp,   # 1400ms
            self.interp_advice,     # 1700ms
        ]
        delays = [900, 1000, 1150, 1250, 1400, 1700]
        for elem, delay in zip(interp_elements, delays):
            self._fade_in(elem, delay_ms=delay)

        # ---- ۶. کادر اطلاعات جلسه (۱۹۰۰ms) ----
        self._fade_in(self._info_frame_ref, delay_ms=1900)

        # ---- ۷. دکمه‌ها (۲۱۰۰ms و ۲۲۵۰ms) ----
        for i, btn in enumerate(self._buttons_ref):
            self._fade_in(btn, delay_ms=2100 + i * 150)

    # ================================================================
    def _fade_in(self, widget, delay_ms: int = 0, duration_ms: int = 400):
        """
        انیمیشن Fade-in با تأخیر.
        از QGraphicsOpacityEffect + QPropertyAnimation استفاده می‌کند.
        """
        if widget is None:
            return

        try:
            effect = QGraphicsOpacityEffect(widget)
            effect.setOpacity(0.0)
            widget.setGraphicsEffect(effect)
        except Exception as e:
            print(f"⚠️ خطا در ساخت effect: {e}")
            return

        def _start():
            try:
                # بررسی معتبر بودن widget (ممکن است حذف شده باشد)
                _ = widget.width()
            except RuntimeError:
                return

            try:
                anim = QPropertyAnimation(
                    effect, b"opacity", widget
                )
                anim.setDuration(duration_ms)
                anim.setStartValue(0.0)
                anim.setEndValue(1.0)
                anim.setEasingCurve(QEasingCurve.Type.OutCubic)

                # ✅ پاک کردن effect بعد از اتمام (تا با کلیک‌ها
                #    و hover تداخل نداشته باشد)
                anim.finished.connect(
                    lambda w=widget: self._clear_effect(w)
                )
                anim.start(
                    QPropertyAnimation.DeletionPolicy.DeleteWhenStopped
                )
                self._anim_refs.append(anim)
            except Exception as e:
                print(f"⚠️ خطا در شروع انیمیشن: {e}")

        QTimer.singleShot(delay_ms, _start)

    # ================================================================
    def _clear_effect(self, widget):
        """پاک کردن graphicsEffect پس از اتمام انیمیشن"""
        if widget is None:
            return
        try:
            widget.setGraphicsEffect(None)
        except RuntimeError:
            pass

    # ================================================================
    def _stop_all_anims(self):
        """توقف همه‌ی انیمیشن‌های در حال اجرا"""
        for anim in self._anim_refs:
            try:
                anim.stop()
            except RuntimeError:
                pass
        self._anim_refs.clear()

    # ================================================================
    def _collect_animated_widgets(self):
        """لیست همه‌ی ویجت‌هایی که انیمیت می‌شوند"""
        # ✅ توجه: radar_chart از این لیست حذف شده چون
        #    paintEvent دستی دارد و Effect روی آن خطا می‌دهد.
        result = [
            self._title_ref,
            self._subtitle_ref,
            self._interp_panel_ref,
            self.profile_badge,
            self.interp_avg,
            self.interp_strength,
            self.interp_weakness,
            self.interp_per_comp,
            self.interp_advice,
            self._info_frame_ref,
        ]
        result.extend(self._buttons_ref)
        return result

    # ----------------------------------------------------------------
    def _calculate_and_save_scores(self):
        """محاسبه میانگین وزنی شواهد و ذخیره در دیتابیس"""
        competencies = [
            "honesty", "trustworthiness",
            "problem_solving", "accountability"
        ]
        for comp in competencies:
            evidence = self.game_manager.data_logger.get_evidence_by_competency(comp)
            if evidence and len(evidence) > 0:
                total_weight = sum(float(e[7]) for e in evidence)
                weighted_sum = sum(float(e[6]) * float(e[7]) for e in evidence)
                score = (weighted_sum / total_weight * 100) if total_weight > 0 else 0.0

                # اطمینان بر اساس تعداد شواهد
                confidence = min(1.0, len(evidence) / 12.0)

                # ✅ هشدار روایی: اگر تعداد شواهد کمتر از ۳ باشد
                if len(evidence) < 3:
                    print(f"⚠️ هشدار روایی: شایستگی '{comp}' "
                        f"تنها {len(evidence)} شاهد دارد. "
                        f"پایایی نمره پایین است.")

                self.game_manager.data_logger.save_competency_score(
                    competency=comp, score=round(score, 2),
                    confidence=round(confidence, 2),
                    evidence_count=len(evidence)
                )
            else:
                self.game_manager.data_logger.save_competency_score(
                    competency=comp, score=0.0,
                    confidence=0.0, evidence_count=0
                )
        # ✅ فاز E: محاسبه و ذخیره‌ی نمرات زیرمؤلفه‌ای
        self._compute_sub_competencies()

        print("✓ نمرات نهایی محاسبه و در پایگاه داده ذخیره شدند.")

    def _compute_sub_competencies(self):
        """
        محاسبه‌ی نمره‌ی هر زیرمؤلفه از شواهد و ذخیره در دیتابیس.
        """
        all_evidence = self.game_manager.data_logger.get_all_evidence()
        # ساختار شواهد در DB:
        # (evidence_id, participant_id, scenario_id, competency,
        #  subcomponent, evidence_key, evidence_value, weight)

        # جمع‌بندی: {competency: {sub_competency: [values]}}
        # اما چون DB ستون sub_competency ندارد، از evidence_engine
        # موجود در memory استفاده می‌کنیم.
        # در واقع evidence_engine در حافظه‌ی همان جلسه است.

        # ساده‌تر: از evidence_buffer فعلی evidence_engine استفاده کن
        # اما در ResultsScene، EvidenceEngine ساخته نمی‌شود.
        # پس از DB می‌خوانیم و بر اساس evidence_key + نگاشت
        # SUB_COMP_MAP، زیرمؤلفه را استخراج می‌کنیم.

        from core.evidence_engine import EvidenceEngine
        # از یک map سراسری استفاده می‌کنیم
        try:
            from data.scenario_metadata import (
                COMPETENCY_DEFINITIONS
            )
        except Exception:
            pass

        # ما از یک نگاشت ساده استفاده می‌کنیم
        from collections import defaultdict
        sums = defaultdict(lambda: defaultdict(
            lambda: {"sum": 0.0, "weight": 0.0, "count": 0}
        ))

        # از data_logger.get_all_evidence می‌خوانیم
        # اما ستون sub_competency را ندارد، پس از evidence_key استفاده می‌کنیم
        # به همین منظور یک نگاشت ساده‌ی درون کد می‌سازیم
        # (در آینده می‌توانیم ستون sub_competency را هم اضافه کنیم)
        try:
            # ✅ از schema_evidence استفاده نمی‌کنیم؛
            #    از evidence واقعی که در جلسه ثبت شده
            evidence_list = all_evidence
        except Exception:
            return

        # نگاشت ساده (کپی از add_sub_competencies.py)
        # برای جلوگیری از import سنگین
        SUB_COMP_MAP = {
            # honesty
            "E_H1_transparency": "transparency",
            "E_H2_completeness": "transparency",
            "E_H3_pressure_resistance": "boundary_setting",
            "E_H4_decision_time": "transparency",
            "E_DA1_cheat_avoidance": "data_integrity",
            "E_DA2_refusal": "boundary_setting",
            "E_DA2_reporting": "boundary_setting",
            "E_MC1_action_type": "fair_judgment",
            "E_MC2_integrity": "moral_consistency",
            "E_MC2_pressure_resistance": "moral_consistency",
            "E_VH2_disclosure": "transparency",
            "E_F2_thorough_investigation": "fair_judgment",
            "E_F2_bias_resistance": "fair_judgment",
            # trustworthiness
            "E_CF1_delivery_success": "commitment_keeping",
            "E_CF2_quality": "autonomous_quality",
            "E_CF2_effort": "autonomous_quality",
            "E_TR1_disclosure_action": "responsible_disclosure",
            "E_TR2_disclosure_level": "responsible_disclosure",
            "E_BC1_decision": "resource_generosity",
            "E_BC2_sacrifice": "shared_responsibility",
            # problem_solving
            "E_PID1_systems_sequence": "root_cause_analysis",
            "E_PID4_correct_root": "root_cause_analysis",
            "E_PID2_coverage": "pattern_recognition",
            "E_SPA1_sequence_score": "sequence_planning",
            "E_CFI1_unique_combinations": "creative_thinking",
            "E_MR1_adjustment": "adaptive_revision",
            "E_SPA1_allocation_pattern": "resource_allocation",
            "E_F1_fairness_under_pressure": "resource_allocation",
            # accountability
            "E_PI1_reporting_delay": "hazard_reporting",
            "E_PI2_proposal": "proactive_improvement",
            "E_TC1_completion_rate": "resistance_to_temptation",
            "E_TC2_action_taken": "task_persistence",
            "E_RG1_initial_tone": "feedback_acceptance",
            "E_RG2_attitude": "growth_mindset",
            "E_AC1_acceptance": "formal_accountability",
            "E_AC2_ownership": "past_action_ownership",
        }

        # ساختار evidence row:
        # (id, participant_id, scenario_id, competency,
        #  subcomponent, evidence_key, value, weight)
        for row in evidence_list:
            competency = row[3]
            evidence_key = row[5]
            value = float(row[6])
            weight = float(row[7])

            sub = SUB_COMP_MAP.get(evidence_key, "")
            if not sub:
                continue

            d = sums[competency][sub]
            d["sum"] += value * weight
            d["weight"] += weight
            d["count"] += 1

        # تبدیل به دیکشنری نهایی
        final = {}
        for comp, subs in sums.items():
            final[comp] = {}
            for sub, d in subs.items():
                if d["weight"] > 0:
                    score = (d["sum"] / d["weight"]) * 100
                else:
                    score = 0.0
                final[comp][sub] = {
                    "score": round(score, 2),
                    "count": d["count"],
                }

        # ذخیره
        if final:
            try:
                self.game_manager.data_logger.save_sub_competency_scores(
                    final
                )
                print(f"✓ نمرات زیرمؤلفه‌ای ذخیره شد: {list(final.keys())}")
            except Exception as e:
                print(f"⚠️ خطا در ذخیره‌ی زیرمؤلفه‌ها: {e}")

        # ذخیره در self برای استفاده در Typology
        self._sub_scores = final

    @staticmethod
    def _compute_pair_score(v1: float, v2: float) -> float:
        """
        فرمول ترکیبی ثبات + کیفیت اخلاقی.

        similarity = 1 - |v1 - v2|       (0..1)
        quality    = (v1 + v2) / 2        (0..1)
        score      = 0.4 × similarity + 0.6 × quality

        نمونه‌ها:
            (1.0, 1.0) → 1.00  ثابت و خوب
            (0.9, 0.9) → 0.94  تقریباً ثابت و خوب
            (0.5, 0.5) → 0.70  ثابت ولی متوسط
            (0.0, 0.0) → 0.40  ثابت ولی ضعیف
            (1.0, 0.5) → 0.65  تا حدی ثابت
            (1.0, 0.0) → 0.30  ناسازگار
        """
        similarity = 1.0 - abs(v1 - v2)
        quality = (v1 + v2) / 2.0
        return round(0.4 * similarity + 0.6 * quality, 3)

    def _compute_and_save_consistency(self):
        """
        محاسبه‌ی سه شاخص ثبات بین جفت‌سناریوها:
        - CO-01: MC-01 vs MC-02   (صداقت)
        - CO-02: PI-01 vs RG-01   (مسئولیت‌پذیری)
        - CO-03: CF-01 vs CF-02   (قابلیت اعتماد)
        """
        logger = self.game_manager.data_logger

        # اگر قبلاً محاسبه شده، دوباره اجرا نکن
        already = logger.get_evidence_by_key(
            "CO-computed", "E_CO1_moral_consistency"
        )
        if already:
            print("   [CO] قبلاً محاسبه شده — پرش")
            return

        # ---------------------------------------------------------
        # CO-01: همسانی اخلاقی بین MC-01 (روز ۱) و MC-02 (روز ۳)
        # ---------------------------------------------------------
        mc1 = logger.get_evidence_by_key("MC-01", "E_MC1_action_type")
        mc2 = logger.get_evidence_by_key("MC-02", "E_MC2_integrity")

        if mc1 and mc2:
            v1, v2 = float(mc1[0]), float(mc2[0])
            co1 = self._compute_pair_score(v1, v2)

            logger.log_evidence(
                scenario_id="CO-computed",
                competency="honesty",
                subcomponent="ثبات اخلاقی در طول مأموریت",
                evidence_key="E_CO1_moral_consistency",
                evidence_value=co1,
                weight=0.8,
            )
            print(
                f"   [CO-01] MC-01={v1:.2f} vs MC-02={v2:.2f} "
                f"→ {co1:.3f}"
            )

        # ---------------------------------------------------------
        # CO-02: همسانی پاسخگویی بین PI-01 و RG-01
        # ---------------------------------------------------------
        pi1 = logger.get_evidence_by_key(
            "PI-01", "E_PI2_report_completeness"
        )
        rg1 = logger.get_evidence_by_key(
            "RG-01", "E_RG1_initial_tone"
        )

        if pi1 and rg1:
            v1, v2 = float(pi1[0]), float(rg1[0])
            co2 = self._compute_pair_score(v1, v2)

            logger.log_evidence(
                scenario_id="CO-computed",
                competency="accountability",
                subcomponent="ثبات پاسخگویی",
                evidence_key="E_CO2_accountability_consistency",
                evidence_value=co2,
                weight=0.8,
            )
            print(
                f"   [CO-02] PI-01={v1:.2f} vs RG-01={v2:.2f} "
                f"→ {co2:.3f}"
            )

        # ---------------------------------------------------------
        # CO-03: ثبات رفتاری در قابلیت اعتماد — CF-01 vs CF-02
        # ---------------------------------------------------------
        cf1 = logger.get_evidence_by_key(
            "CF-01", "E_CF1_delivery_success"
        )
        cf2 = logger.get_evidence_by_key("CF-02", "E_CF2_quality")

        if cf1 and cf2:
            v1, v2 = float(cf1[0]), float(cf2[0])
            co3 = self._compute_pair_score(v1, v2)

            logger.log_evidence(
                scenario_id="CO-computed",
                competency="trustworthiness",
                subcomponent="ثبات رفتاری در وفاداری به تعهد",
                evidence_key="E_CO3_behavioral_consistency",
                evidence_value=co3,
                weight=0.8,
            )
            print(
                f"   [CO-03] CF-01={v1:.2f} vs CF-02={v2:.2f} "
                f"→ {co3:.3f}"
            )

    # ----------------------------------------------------------------
    def _get_final_scores(self) -> list:
        scores_data = self.game_manager.data_logger.get_competency_scores()
        scores_dict = {row[0]: row[1] for row in scores_data}
        return [
            scores_dict.get("honesty", 0.0),
            scores_dict.get("trustworthiness", 0.0),
            scores_dict.get("problem_solving", 0.0),
            scores_dict.get("accountability", 0.0),
        ]

    # ----------------------------------------------------------------
    # ✅ فاز C: شاخص MRL (Moral Reasoning Level)
    # ----------------------------------------------------------------
    def _compute_mrl(self) -> dict:
        """
        محاسبه‌ی شاخص استدلال اخلاقی از توزیع طرح‌واره‌ها.

        فرمول:
            MRL = (PC×2 − PI×1 + MN×0.5) / (total×2)

        Returns:
            {
                "level": "postconventional" | "maintaining_norms"
                         | "personal_interest" | "unknown",
                "score": float in [-1, 1],
                "pi": int, "mn": int, "pc": int, "total": int,
            }
        """
        dist = self.game_manager.data_logger.get_schema_distribution()

        pi = dist.get("personal_interest", 0)
        mn = dist.get("maintaining_norms", 0)
        pc = dist.get("postconventional", 0)
        total = pi + mn + pc

        if total == 0:
            return {
                "level": "unknown",
                "score": 0.0,
                "pi": 0, "mn": 0, "pc": 0, "total": 0,
            }

        raw = (pc * 2) - (pi * 1) + (mn * 0.5)
        normalized = raw / (total * 2)

        if normalized > 0.25:
            level = "postconventional"
        elif normalized > -0.25:
            level = "maintaining_norms"
        else:
            level = "personal_interest"

        return {
            "level": level,
            "score": round(normalized, 3),
            "pi": pi, "mn": mn, "pc": pc, "total": total,
        }

    def _compute_typology(self) -> dict:
        """
        تشخیص پروفایل ترکیبی بر اساس نمرات زیرمؤلفه‌ای.

        Returns:
            {
                "code": str,
                "label_fa": str,
                "color": str,
                "description": str,
            }
        """
        sub = self._sub_scores
        if not sub:
            return {
                "code": "unknown",
                "label_fa": "پروفایل نامشخص",
                "color": "#546E7A",
                "description": "داده‌ی کافی برای شناسایی پروفایل نیست.",
            }

        def get(comp, key):
            return sub.get(comp, {}).get(key, {}).get("score", 0.0)

        # --- استخراج نمرات کلیدی ---
        pid = get("problem_solving", "root_cause_analysis")
        spa = get("problem_solving", "sequence_planning")
        cfi = get("problem_solving", "creative_thinking")
        mr = get("problem_solving", "adaptive_revision")
        ac = get("accountability", "formal_accountability")
        pi = get("accountability", "proactive_improvement")
        tc = get("accountability", "resistance_to_temptation")
        rg = get("accountability", "growth_mindset")
        transparency = get("honesty", "transparency")
        integrity = get("honesty", "data_integrity")

        # --- قواعد تشخیص ---
        profiles = []

        # الگوی تحلیلگر نظام‌مند
        if pid >= 60 and spa >= 60:
            profiles.append({
                "code": "systematic_analyst",
                "label_fa": "تحلیلگر نظام‌مند",
                "color": "#4FC3F7",
                "description": "مشکل‌یاب دقیق با توانایی برنامه‌ریزی مرحله‌ای",
            })

        # الگوی نوآور چابک
        if cfi >= 60 and mr >= 60:
            profiles.append({
                "code": "agile_innovator",
                "label_fa": "نوآور چابک",
                "color": "#9C27B0",
                "description": "انعطاف‌پذیر و یادگیرنده‌ی سریع از بازخورد",
            })

        # الگوی رهبر پاسخگو
        if ac >= 60 and pi >= 60:
            profiles.append({
                "code": "accountable_leader",
                "label_fa": "رهبر پاسخگو",
                "color": "#4CAF50",
                "description": "مسئولیت‌پذیر در قبال اشتباهات و پیش‌دست در بهبود",
            })

        # الگوی اجراکننده متعهد
        if tc >= 60 and rg < 50:
            profiles.append({
                "code": "committed_executor",
                "label_fa": "اجراکننده‌ی متعهد",
                "color": "#FF8F00",
                "description": "قابل اتکا در انجام وظایف، اما کم‌علاقه به بازخورد",
            })

        # الگوی شفاف
        if transparency >= 60 and integrity >= 60:
            profiles.append({
                "code": "transparent_operator",
                "label_fa": "عمل‌کننده‌ی شفاف",
                "color": "#4CAF50",
                "description": "شفافیت بالا در گزارش‌دهی و یکپارچگی داده",
            })

        # الگوی مصلحت‌گرا
        if ac < 40 and pi < 40:
            profiles.append({
                "code": "pragmatic_passive",
                "label_fa": "مصلحت‌گرا",
                "color": "#D32F2F",
                "description": "پرهیز از مسئولیت و اجتناب از ابتکار عمل",
            })

        # انتخاب اولین پروفایل منطبق، یا پیش‌فرض
        if profiles:
            return profiles[0]

        return {
            "code": "balanced",
            "label_fa": "متعادل",
            "color": "#B0BEC5",
            "description": "پروفایلی بدون الگوی غالب مشخص",
        }

    # ================================================================
    # تفسیر کیفی
    # ================================================================
    def _apply_interpretation(self, scores: list):
        """پر کردن ویجت‌های تفسیر بر اساس نمرات"""
        if len(scores) != 4:
            return

        avg = sum(scores) / 4.0

        # اگر داده کافی نبود
        if avg < 3.0 and max(scores) < 5.0:
            self._set_empty_interpretation()
            return

        # ---------------------------------------------------------
        # تعیین نوع پروفایل کلی
        # ---------------------------------------------------------
        if avg >= 80:
            badge_text = "الگوی متعالی"
            badge_color = "#4CAF50"
            summary = (
                "شما در تمامی ابعاد شایستگی، عملکردی درخشان و پایدار "
                "نشان داده‌اید."
            )
        elif avg >= 65:
            badge_text = "الگوی متعادل"
            badge_color = "#4FC3F7"
            summary = (
                "پروفایل شما متعادل و قابل اتکا است. در موقعیت‌های "
                "حساس عملکرد مناسبی دارید."
            )
        elif avg >= 45:
            badge_text = "در حال توسعه"
            badge_color = "#FF8F00"
            summary = (
                "شما در برخی ابعاد عملکرد خوبی دارید اما در برخی "
                "موقعیت‌ها نیاز به تأمل بیشتری دارید."
            )
        else:
            badge_text = "نیازمند بازنگری"
            badge_color = "#D32F2F"
            summary = (
                "الگوی رفتاری شما در شرایط بحرانی نیازمند بازنگری "
                "جدی و تمرین هدفمند است."
            )

        self.profile_badge.setText(badge_text)
        self.profile_badge.setStyleSheet(f"""
            QLabel {{
                color: #0B1D3A;
                background-color: {badge_color};
                border-radius: 14px;
                padding: 5px 12px;
                font-weight: bold;
                border: none;
            }}
        """)

        self.interp_avg.setText(f"میانگین کل: {avg:.1f} از ۱۰۰")

        # ---------------------------------------------------------
        # قوی‌ترین و ضعیف‌ترین بُعد
        # ---------------------------------------------------------
        sorted_idx = sorted(range(4), key=lambda i: scores[i], reverse=True)
        si, wi = sorted_idx[0], sorted_idx[-1]

        self.interp_strength.setText(
            f"✓ قوی‌ترین بُعد: {COMPETENCY_LABELS[si]}  ({scores[si]:.0f})"
        )
        self.interp_weakness.setText(
            f"△ نقطه قابل بهبود: {COMPETENCY_LABELS[wi]}  ({scores[wi]:.0f})"
        )

        # ---------------------------------------------------------
        # تفسیر هر شایستگی
        # ---------------------------------------------------------
        lines = [summary, ""]
        for i, s in enumerate(scores):
            level = _classify(s)
            text = COMPETENCY_INTERPRETATIONS.get((i, level), "")
            if text:
                lines.append(f"• {COMPETENCY_LABELS[i]}: {text}")
        self.interp_per_comp.setText("\n".join(lines))

        # ---------------------------------------------------------
        # پیشنهاد
        # ---------------------------------------------------------
        if scores[wi] < 40:
            advice = (
                f"پیشنهاد: در موقعیت‌های مرتبط با «{COMPETENCY_LABELS[wi]}»، "
                f"پیش از تصمیم‌گیری زمانی برای تأمل و مشورت با همکاران "
                f"اختصاص دهید."
            )
        elif scores[wi] < 60:
            advice = (
                f"پیشنهاد: «{COMPETENCY_LABELS[wi]}» نقطه قابل بهبود "
                f"شماست؛ بازخورد فعالانه از همکاران دریافت کنید."
            )
        else:
            advice = (
                "پیشنهاد: پروفایل شما متعادل است؛ تداوم این الگو "
                "و به اشتراک گذاشتن تجربه‌هایتان با همکاران توصیه می‌شود."
            )

        self.interp_advice.setText(advice)

        # ✅ فاز C: به‌روزرسانی بج MRL
        self._apply_mrl_interpretation()

        # ✅ فاز E: به‌روزرسانی Typology
        self._apply_typology_interpretation()

        # ✅ فاز F: ارجاع به سه ثبات
        cons = self._get_consistency_summary()
        if cons:
            cons_lines = []
            for name, val in cons.items():
                cons_lines.append(f"{name}: {val:.0%}")
            self.interp_advice.setText(
                advice + "\n\n— ثبات رفتار —\n" +
                " | ".join(cons_lines)
            )

    def _get_consistency_summary(self) -> dict:
        """خلاصه‌ی سه شاخص ثبات"""
        logger = self.game_manager.data_logger
        keys = {
            "صداقت": "E_CO1_moral_consistency",
            "پاسخگویی": "E_CO2_accountability_consistency",
            "قرارداد": "E_CO3_behavioral_consistency",
        }
        result = {}
        for name, key in keys.items():
            row = logger.get_evidence_by_key("CO-computed", key)
            if row:
                result[name] = float(row[0])
        return result

    def _apply_typology_interpretation(self):
        """به‌روزرسانی بج Typology"""
        typo = self._compute_typology()
        self.typo_badge.setText(f"🎯 {typo['label_fa']}")
        self.typo_badge.setStyleSheet(f"""
            QLabel {{
                color: #FFFFFF;
                background-color: {typo['color']};
                border-radius: 14px;
                padding: 5px 12px;
                font-weight: bold;
                border: none;
            }}
        """)
        self.typo_desc.setText(typo["description"])

    def _apply_mrl_interpretation(self):
        """به‌روزرسانی بج MRL بر اساس توزیع طرح‌واره‌ها"""
        mrl = self._compute_mrl()

        if mrl["level"] == "unknown":
            self.mrl_badge.setText("— استدلال نامشخص")
            self.mrl_badge.setStyleSheet("""
                QLabel {
                    color: #FFFFFF;
                    background-color: #546E7A;
                    border-radius: 12px;
                    padding: 4px 10px;
                    font-weight: bold;
                    border: none;
                }
            """)
            self.mrl_detail.setText(
                "داده‌ی کافی برای ارزیابی سطح استدلال ثبت نشده."
            )
            return

        level_map = {
            "postconventional": (
                "🧭 استدلال پسافرا قراردادی",
                "#4CAF50",   # سبز
                "تصمیم‌هایت را بر اساس اصول جهان‌شمول و عدالت "
                "گرفته‌ای — حتی وقتی هزینه داشته.",
            ),
            "maintaining_norms": (
                "⚖️ استدلال هنجارمحور",
                "#4FC3F7",   # فیروزه‌ای
                "پایبندی به قواعد و رویه‌های سازمانی، محور "
                "تصمیم‌های تو بوده است.",
            ),
            "personal_interest": (
                "⚠️ استدلال منفعت‌محور",
                "#FF8F00",   # نارنجی
                "در برخی تصمیم‌ها، منافع شخصی یا اجتناب از "
                "دردسر، اولویت داشته است.",
            ),
        }

        label, color, detail = level_map.get(
            mrl["level"], ("—", "#546E7A", "")
        )

        self.mrl_badge.setText(label)
        self.mrl_badge.setStyleSheet(f"""
            QLabel {{
                color: #FFFFFF;
                background-color: {color};
                border-radius: 12px;
                padding: 4px 10px;
                font-weight: bold;
                border: none;
            }}
        """)
        self.mrl_detail.setText(detail)

    def _set_empty_interpretation(self):
        """حالت بدون داده"""
        self.profile_badge.setText("داده کافی نیست")
        self.profile_badge.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                background-color: #666666;
                border-radius: 14px;
                padding: 5px 12px;
                font-weight: bold;
                border: none;
            }
        """)
        self.interp_avg.setText("میانگین کل: —")
        self.interp_strength.setText("✓ قوی‌ترین بُعد: —")
        self.interp_weakness.setText("△ نقطه قابل بهبود: —")
        self.interp_per_comp.setText(
            "برای تحلیل، نیاز به داده‌های رفتاری کافی است."
        )
        self.interp_advice.setText(
            "لطفاً یک مأموریت کامل را انجام دهید تا پروفایل شما محاسبه شود."
        )

    def _on_pdf_clicked(self):
        """تولید PDF گزارش فردی و نمایش مسیر فایل"""
        try:
            from analysis.pdf_report import generate_pdf_report
        except Exception as e:
            QMessageBox.warning(
                self, "خطا",
                f"ماژول گزارش PDF در دسترس نیست:\n{e}",
            )
            return

        logger = self.game_manager.data_logger
        pid = getattr(logger, "participant_id", "")
        if not pid:
            QMessageBox.warning(
                self, "خطا",
                "شناسه‌ی شرکت‌کننده یافت نشد.",
            )
            return

        try:
            out_path = generate_pdf_report(pid)
            if out_path and os.path.exists(out_path):
                QMessageBox.information(
                    self, "موفق",
                    f"✓ گزارش PDF ساخته شد:\n\n{out_path}",
                )
            else:
                QMessageBox.warning(
                    self, "خطا",
                    "تولید PDF ناموفق بود.",
                )
        except Exception as e:
            QMessageBox.warning(
                self, "خطا",
                f"تولید PDF ناموفق بود:\n{e}",
            )

    # ================================================================
    def _on_restart(self):
        """شروع مجدد کامل بازی با فرآیند جدید"""
        print("✓ شروع مجدد بازی...")

        # ✅ ابتدا مسیر مطلق فایل اصلی را می‌سازیم
        #    (پروسه‌ی جدید باید بعد از بسته شدن کامل این پروسه
        #     اجرا شود تا تداخل دیتابیس پیش نیاید)
        main_script = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__), "..", "main.py"
            )
        )

        # ✅ پنجره را می‌بندیم (closeEvent خودش end_session
        #    و backup می‌گیرد)، سپس پروسه‌ی جدید را با تاخیر کوتاه
        #    اجرا می‌کنیم
        from PyQt6.QtCore import QTimer

        def _spawn_new():
            try:
                subprocess.Popen(
                    [sys.executable, main_script],
                    cwd=os.path.dirname(main_script),
                )
            except Exception as e:
                print(f"⚠️ خطا در اجرای مجدد: {e}")

        QTimer.singleShot(300, _spawn_new)
        self.game_manager.main_window.close()

    def _on_exit(self):
        """خروج کامل از برنامه با تأیید کاربر"""
        reply = QMessageBox.question(
            self, "خروج از برنامه",
            "آیا از بستن برنامه مطمئن هستید؟\n"
            "داده‌های شما ذخیره شده است.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            print("✓ پایان بازی. بستن پنجره...")
            self.game_manager.main_window.close()

    def on_exit(self):
        """پاکسازی هنگام خروج از صحنه"""
        self._stop_all_anims()
        # پاک کردن effectهای باقی‌مانده
        for widget in self._collect_animated_widgets():
            if widget is not None:
                try:
                    widget.setGraphicsEffect(None)
                except Exception:
                    pass

    def keyPressEvent(self, event):  # type: ignore[reportIncompatibleMethodOverride]
        if event.key() == Qt.Key.Key_Escape:
            self._on_exit()
        else:
            super().keyPressEvent(event)