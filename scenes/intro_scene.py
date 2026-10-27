"""
صحنه مقدمه داستانی بازی — نسخه اصلاح‌شده
تغییر: حذف دکمه اضافه «ادامه»، افزودن setFocus برای Space
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt
from scenes.base_scene import BaseScene
from widgets.dialogue_widget import DialogueWidget
from widgets.hud_widget import HUDWidget


class IntroScene(BaseScene):
    """صحنه مقدمه داستانی"""

    def __init__(self, game_manager):
        super().__init__(game_manager)

        self.current_dialogue_index = 0

        self.dialogues = [
            # ---------------- پرولوگ شخصی ----------------
            {"speaker": "راوی", "text": "سه ماه پیش، پرونده‌ی بازرسی دوره‌ای ایستگاه کاسپین روی میزت قرار گرفت. اما این بار، درخواست از خودت بود.", "portrait": None},
            {"speaker": "راوی", "text": "تو داوطلب شدی؛ چون می‌دانستی این ایستگاه، و مردمی که در آن زندگی می‌کنند، تو را در موقعیت‌هایی قرار می‌دهند که هیچ شبیه‌ساز آموزشی نمی‌تواند بازسازی کند.", "portrait": None},
            {"speaker": "راوی", "text": "معیار ارتقاء تو، فقط گزارش فنی نیست. شیوه‌ی تصمیم‌گیری تو در بحران‌ها، همان چیزی است که تیم ارزیابی به دنبالش است.", "portrait": None},

            # ---------------- مقدمه‌ی موجود ----------------
            {"speaker": "راوی", "text": "سال ۲۱۴۸. ایستگاه پژوهشی مداری کاسپین.", "portrait": None},
            {"speaker": "راوی", "text": "هر تصمیم، یک ردپا بر جای می‌گذارد.", "portrait": None},
            {"speaker": "راوی", "text": "تو تکنسین ارشد هستی. برای بازرسی دوره‌ای به ایستگاه اعزام شده‌ای.", "portrait": None},
            {"speaker": "راوی", "text": "در این مأموریت، فقط یه چیز ازت می‌خوایم: خودت باش. همون‌طور که توی موقعیت‌های واقعی تصمیم می‌گیری، تصمیم بگیر. هوش و درایتت رو به کار بگیر و تا جایی که می‌تونی، مسائل رو حل کن.", "portrait": None},
            {"speaker": "مهندس رحیمی", "text": "به ایستگاه کاسپین خوش آمدید. من مهندس رحیمی هستم، مسئول نگهداری این ایستگاه.", "portrait": None},
            {"speaker": "مهندس رحیمی", "text": "بذار کسی رو معرفی کنم. این لی هست، کارآموز بخش ناوبری. چند ماه پیش اومده، سخت‌کوش و باانگیزه است.", "portrait": None},
            {"speaker": "لی", "text": "سلام! خوشحالم که می‌بینمتون. اگه در طول شیفت کمکی لازم داشتید، در خدمتم.", "portrait": None},
            {"speaker": "مهندس رحیمی", "text": "راستی تکنسین، لی این چند روز روی یه سری محاسبات ناوبری گیر کرده. اگه بعد از کارهای اولیه فرصتی داشتی، کمکش کن. لی تازه‌کاره ولی سخت‌کوشه.", "portrait": None},
            {"speaker": "لی", "text": "(با لبخند) ممنون مهندس. تکنسین، اگه بعد از کالیبراسیون فرصت کردید، من توی بخش ناوبری هستم. داده‌ها رو که آماده کردم، می‌تونم بیام پیش شما.", "portrait": None},
            {"speaker": "مهندس رحیمی", "text": "و این هم دکتر آرتمیس، مسئول تحلیل داده‌های علمی ایستگاه. یکی از دقیق‌ترین تحلیلگرهایی که توی این شبکه داریم.", "portrait": None},
            {"speaker": "دکتر آرتمیس", "text": "سلام... خوش آمدید. من راستش دارم روی چند آنومالی در داده‌های هفته گذشته کار می‌کنم. اگر بعد از جلسه فرصتی بود، می‌خواستم نظرتون رو بشنوم.", "portrait": None},
            {"speaker": "مهندس رحیمی", "text": "آرتمیس همیشه نگرانه، کارش همینه. اما جدی نگیر.", "portrait": None},
            {"speaker": "راوی", "text": "در راهروی منتهی به اتاق کنترل، مردی میانسال با دستکش‌های کار، مشغول تعمیر یک پنل برق است. با دیدن شما، سرش را بالا می‌آورد. لکه‌های روغن روی گونه‌اش، خط‌های عمیق کار را نشان می‌دهد.", "portrait": None},
            {"speaker": "مهندس رحیمی", "text": "این فرزین هست. تکنسین فنی ایستگاه. هر چی این‌جا برق مصرف می‌کنه، یه روزی از دست فرزین رد شده.", "portrait": None},
            {"speaker": "فرزین", "text": "(دستکش‌هایش را پایین می‌کشد، ولی دستش را برای دست دادن دراز نمی‌کند. لحنش صمیمی است، ولی نگاهش جای دیگری را می‌خواند) تکنسین. خوش آمدید. من این‌جا خیلی چیزها می‌دونم — شاید بیشتر از اون‌هایی که به‌نظر می‌رسه لازم باشه بدونن. اگه یه روزی کمکی خواستید... فقط یه اشاره کافیه.", "portrait": None},
            {"speaker": "راوی", "text": "فرزین بدون اینکه منتظر جواب بماند، به کار خودش برمی‌گردد. صدای پیچ‌گوشتی برقی، در راهرو می‌پیچد. مهندس رحیمی نگاهی کوتاه به او می‌اندازد، ولی چیزی نمی‌گوید.", "portrait": None},
            {"speaker": "مهندس رحیمی", "text": "حالا بذار بریم اتاق کنترل؛ دیروز چند ناهنجاری در سیستم‌ها ثبت شده.", "portrait": None},
            {"speaker": "سیستم", "text": "هشدار: افزایش دمای مدار خنک‌کننده. توصیه می‌شود فوراً بررسی شود.", "portrait": None},
            {"speaker": "مهندس رحیمی", "text": "مشکل جدی‌تر از اونیه که فکر می‌کردم. باید سریع به اتاق کنترل برویم.", "portrait": None},
        ]

        self._setup_ui()

        # ✅ اطمینان از دریافت کلید Space
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        print("✓ IntroScene راه‌اندازی شد")

    def _setup_ui(self):
        container = QWidget()
        container.setStyleSheet("background-color: #0B1D3A;")
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.hud = HUDWidget()
        self.hud.set_mission("ایستگاه کاسپین")
        self.hud.set_phase("پیش از مأموریت")
        self.hud.set_objective("آشنایی با ایستگاه و خدمه")
        main_layout.addWidget(self.hud)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setStyleSheet(
            "QScrollArea { background-color: #0B1D3A; border: none; }"
        )

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background-color: #0B1D3A;")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(20, 10, 20, 10)
        scroll_layout.setSpacing(15)

        background_frame = QFrame()
        background_frame.setStyleSheet("""
            QFrame {
                background-color: #0B1D3A;
                border: 1px solid #2B4A6F;
                border-radius: 10px;
            }
        """)
        background_frame.setMinimumHeight(250)

        bg_layout = QVBoxLayout(background_frame)
        bg_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        from PyQt6.QtGui import QPixmap
        from config import ASSETS_DIR
        import os as _os

        # ✅ اول تلاش برای بارگذاری تصویر
        _img_path = _os.path.join(
            ASSETS_DIR, "backgrounds", "caspian_station.png"
        )
        if not _os.path.exists(_img_path):
            # fallback به تصویر منو
            _img_path = _os.path.join(
                ASSETS_DIR, "backgrounds", "menu_hero_v01.png"
            )

        if _os.path.exists(_img_path):
            img_lbl = QLabel()
            pix = QPixmap(_img_path)
            if not pix.isNull():
                pix = pix.scaledToWidth(
                    380,   # ← از ۶۰۰ به ۳۸۰
                    Qt.TransformationMode.SmoothTransformation
                )
                img_lbl.setPixmap(pix)
            img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            img_lbl.setStyleSheet("background: transparent;")
            bg_layout.addWidget(img_lbl)
        else:
            # fallback: فقط متن
            title_lbl = QLabel("ایستگاه فضایی کاسپین")
            title_lbl.setStyleSheet("""
                QLabel {
                    color: #4FC3F7;
                    font-size: 36px;
                    font-weight: bold;
                    background: transparent;
                }
            """)
            title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            bg_layout.addWidget(title_lbl)

        scroll_layout.addWidget(background_frame)

        self.dialogue_box = DialogueWidget()
        scroll_layout.addWidget(self.dialogue_box)

        # ✅ دکمه‌ی «ادامه» حذف شد — Space و کلیک کافیست

        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area, stretch=1)

        self.main_layout.addWidget(container)

    def on_enter(self, **kwargs):
        print("✓ ورود به صحنه مقدمه")
        self.data_logger.log_event(
            scene_id="intro",
            scenario_id="intro_start",
            event_type="scene_enter",
            metadata={}
        )
        self.current_dialogue_index = 0
        self._show_current_dialogue()
        # ✅ گرفتن فوکوس برای دریافت Space
        self.setFocus()

    def _show_current_dialogue(self):
        if self.current_dialogue_index < len(self.dialogues):
            dialogue = self.dialogues[self.current_dialogue_index]
            portrait_val = dialogue.get("portrait")

            self.dialogue_box.show_dialogue(
                speaker_name=dialogue["speaker"],
                text=dialogue["text"],
                portrait_path=portrait_val
            )

            self.data_logger.log_event(
                scene_id="intro",
                scenario_id="intro_dialogue",
                event_type="dialogue_shown",
                metadata={
                    "dialogue_index": self.current_dialogue_index,
                    "speaker": dialogue["speaker"]
                }
            )
        else:
            print("✓ پایان مقدمه، انتقال به میان‌پرده روز اول")
            self._go_to_interlude_day1()

    def _go_to_interlude_day1(self):
        self.change_scene(
            "interlude",
            next_scene="phase1",
            title="روز اول",
            subtitle="سکوت در ایستگاه",
            body_text=(
                "ساعت ۰۶:۱۴ به وقت ایستگاه. چراغ‌های اضطراری اتاق کنترل "
                "می‌درخشند. رحیمی پشت کنسول اصلی نشسته و به صفحه‌نمایش‌های "
                "پر از هشدار خیره شده است."
            ),
            dialogue_speaker="مهندس رحیمی",
            dialogue_text=(
                "بیا اینجا. یه ناهنجاری توی مدار خنک‌کننده پیدا شده. "
                "قبل از اینکه مرکز خبردار بشه، باید خودمون بفهمیم چی داره می‌شه."
            ),
            video_path="interlude_day1.png",
        )

    def _on_continue_clicked(self):
        # اگر وسط تایپ بود، متن کامل شود
        if self.dialogue_box.is_typing():
            self.dialogue_box.advance()
            return
        # در غیر این صورت، دیالوگ بعدی
        self.current_dialogue_index += 1
        self._show_current_dialogue()

    def mousePressEvent(self, event):  # type: ignore[reportIncompatibleMethodOverride]
        """کلیک روی هرجای صحنه = ادامه"""
        self._on_continue_clicked()
        super().mousePressEvent(event)

    def keyPressEvent(self, event):    # type: ignore[reportIncompatibleMethodOverride]
        if event.key() in (Qt.Key.Key_Space, Qt.Key.Key_Return,
                            Qt.Key.Key_Enter):
            self._on_continue_clicked()
        elif event.key() == Qt.Key.Key_S:
            if self.dialogue_box.is_typing():
                self.dialogue_box.advance()
        else:
            super().keyPressEvent(event)

    def on_exit(self):
        print("✓ خروج از صحنه مقدمه")