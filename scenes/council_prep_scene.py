"""
صحنه‌ی آماده‌سازی پیش از جلسه‌ی شورا
سه انتخاب روایی برای خلق حالت ذهنی
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from scenes.base_scene import BaseScene

FONT_FAMILY = "Vazirmatn"


class CouncilPrepScene(BaseScene):
    """آماده‌سازی در راهروی سالن جلسه"""

    def __init__(self, game_manager):
        super().__init__(game_manager)
        self._setup_ui()
        print("✓ CouncilPrepScene راه‌اندازی شد")

    def _setup_ui(self):
        main_layout = self.main_layout
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # پس‌زمینه
        center = QWidget()
        center.setStyleSheet(
            "background: qlineargradient("
            "x1:0, y1:0, x2:0.3, y2:1, "
            "stop:0 #1A0B0B, stop:1 #2A1015);"
        )
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(120, 60, 120, 60)
        center_layout.setSpacing(20)

        # عنوان
        title = QLabel("پیش از جلسه")
        tf = QFont(FONT_FAMILY, 32)
        tf.setBold(True)
        title.setFont(tf)
        title.setStyleSheet("color: #D32F2F;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(title)

        # زیرعنوان
        subtitle = QLabel("راهروی سالن جلسه")
        subtitle.setFont(QFont(FONT_FAMILY, 16))
        subtitle.setStyleSheet("color: #FF8F00;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(subtitle)

        # متن فضاسازی
        intro = QLabel(
            "راهروی منتهی به سالن جلسه، خالی و بی‌صدا. صدای "
            "قدم‌هایت، در سکوتی فلزی می‌پیچد. در انتهای راهرو، "
            "درِ چوبی سنگینی است که به سالن جلسه باز می‌شود.\n\n"
            "پنج دقیقه تا شروع جلسه فرصت داری. این پنج دقیقه، "
            "تنها زمانی است که فقط مال خودت است."
        )
        intro.setFont(QFont(FONT_FAMILY, 13))
        intro.setStyleSheet("color: #CCCCCC;")
        intro.setAlignment(Qt.AlignmentFlag.AlignCenter)
        intro.setWordWrap(True)
        center_layout.addWidget(intro)

        center_layout.addSpacing(20)

        # گزینه‌ها
        question = QLabel("این پنج دقیقه را چطور می‌گذرانی؟")
        qf = QFont(FONT_FAMILY, 14)
        qf.setBold(True)
        question.setFont(qf)
        question.setStyleSheet("color: #FFFFFF;")
        question.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(question)

        # سه دکمه
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(10)

        btn1 = self._make_choice_button(
            "📄  مرور گزارش نهایی", "روی جزئیات تمرکز می‌کنم."
        )
        btn1.clicked.connect(lambda: self._on_choice("report"))
        btn_layout.addWidget(btn1)

        btn2 = self._make_choice_button(
            "📱  تماس با لی برای آخرین هماهنگی",
            "می‌خواهم مطمئن شوم همه چیز مرتب است."
        )
        btn2.clicked.connect(lambda: self._on_choice("contact"))
        btn_layout.addWidget(btn2)

        btn3 = self._make_choice_button(
            "🧘  تمرکز در سکوت",
            "فقط چند نفس عمیق، بدون هیچ اقدامی."
        )
        btn3.clicked.connect(lambda: self._on_choice("silent"))
        btn_layout.addWidget(btn3)

        center_layout.addLayout(btn_layout)
        center_layout.addStretch()

        main_layout.addWidget(center)

    def _make_choice_button(self, title: str, hint: str) -> QPushButton:
        # ✅ RLM برای راست‌چین کردن متن چندخطی
        RLM = "\u200F"
        text = f"{RLM}{title}\n{RLM}{hint}"
        btn = QPushButton(text)
        btn.setFont(QFont(FONT_FAMILY, 13))
        btn.setMinimumHeight(72)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #1A2A4A;
                color: #FFFFFF;
                border: 2px solid #D32F2F;
                border-radius: 10px;
                padding: 12px;
            }
            QPushButton:hover {
                background-color: #D32F2F;
                color: #FFFFFF;
                border: 2px solid #FFFFFF;
            }
        """)
        return btn

    def _on_choice(self, choice_key: str):
        """ثبت انتخاب و رفتن به interlude کوتاه"""
        self.data_logger.log_event(
            scene_id="council_prep",
            scenario_id="council_prep",
            event_type="choice_made",
            metadata={"choice": choice_key}
        )

        # انتخاب متن بر اساس گزینه
        if choice_key == "report":
            text = (
                "(راوی) برگه‌های گزارش را روی میز کنار راهرو، "
                "یکی‌یکی ورق می‌زنی. اما چشم‌هایت، دیگر کلمات را "
                "نمی‌بیند. فقط به یاد می‌آوری که هر جمله، یک "
                "تصمیم بوده."
            )
        elif choice_key == "contact":
            text = (
                "(راوی) با گوشی، به لی پیام می‌دهی: «جلسه نزدیکه. "
                "مطمئنی همه‌چیز مرتبه؟» بعد از چند لحظه، یک پیام "
                "می‌رسد: «بله، فکر می‌کنم آماده‌ای.»"
            )
        else:  # silent
            text = (
                "(راوی) دست‌هایت را روی هم می‌گذاری و چشم‌ها را "
                "می‌بندی. نور قرمز روی پلک‌هایت، کمرنگ می‌شود. "
                "برای چند لحظه، ذهنت آرام می‌گیرد."
            )

        self.change_scene(
            "interlude",
            next_scene="phase4",
            title="لحظه‌ی ورود",
            subtitle="در آستانه",
            body_text=(
                "دستگیره‌ی در را می‌چرخانی. در با صدای خش‌داری "
                "باز می‌شود. سه چهره، پشت میز بلند، به سمت تو "
                "برمی‌گردند."
            ),
            dialogues=[
                {"speaker": "راوی", "text": text},
                {"speaker": "راوی", "text": (
                    "پیش از آنکه کسی حرفی بزند، تو در آستانه‌ی "
                    "دروازه ایستاده‌ای. جلسه شروع می‌شود."
                )},
            ],
            video_path="interlude_day4.png",
        )

    def on_enter(self, **kwargs):
        self.data_logger.log_event(
            scene_id="council_prep",
            scenario_id="council_prep_start",
            event_type="scene_enter",
            metadata={}
        )