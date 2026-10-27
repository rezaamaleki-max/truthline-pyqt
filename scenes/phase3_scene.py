"""
فاز ۳: حل مسئله
شامل PID-01, SPA-02 (تخصیص منابع), MR-02
"""
import os
import json
import re
import time
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QShortcut, QKeySequence

from scenes.base_scene import BaseScene
from widgets.dialogue_widget import DialogueWidget
from widgets.choice_widget import ChoiceWidget
from widgets.diagnostic_map_widget import DiagnosticMapWidget
from widgets.hud_widget import HUDWidget
from widgets.resource_allocation_widget import ResourceAllocationWidget
from widgets.toast_widget import show_toast
from widgets.particle_overlay import ParticleOverlay    
from widgets.procedural_background import ProceduralBackground
from config import DATA_DIR, PHASE_THEMES
from core.app_config import (
    is_section_enabled, is_phase_enabled, next_enabled_phase_after,
    is_theater_mode, theater_scenarios_for_phase
)
from core.flashback_helper import get_flashback_text
from core.multilayer_memory import get_multilayer_memory_text

class Phase3Scene(BaseScene):

    def __init__(self, game_manager):
        super().__init__(game_manager)

        # ✅ تم اختصاصی فاز — instance attribute (سازگار با Pylance)
        self.phase_num: int = 3
        self.theme: dict = PHASE_THEMES[self.phase_num]

        self.scenarios = []
        self.current_scenario_index = 0
        self.current_state = "dialogue"
        self.scenario_start_time = 0
        self.dialogue_index = 0

        # تخصیص منابع
        self.allocation_widget = None
        self.allocation_result = {}
        self.allocation_done = False

        # ✅ SPA-01: تخته وابستگی
        self.dependency_widget = None
        self.dependency_result = {}
        self.dependency_done = False

        # ✅ CFI-01: پازل ترکیب
        self.puzzle_widget = None
        self.puzzle_result = {}
        self.puzzle_done = False

        # دیالوگ‌های نتیجه
        self._result_dialogues = []
        self._result_dialogue_index = 0
        self._result_data = {}
        self._result_then_action = "show_choices"

        # ✅ وضعیت فلش‌بک
        self._flashback_shown_for_scenario: str = ""
        self._flashback_then_choices_scenario: dict | None = None

        self.dialogue_widget = DialogueWidget(data_logger=self.data_logger)
        # ✅ اتصال سیگنال کلیک به پیشروی دیالوگ
        self.dialogue_widget.advanced.connect(
            lambda: self._on_dialogue_click()
        )
        self.choice_widget = ChoiceWidget()
        self.hud = HUDWidget()

        self.choice_widget.choice_made.connect(self._on_choice_made)
        self._setup_ui()

        # مکانیک نقشه تشخیصی
        self.diagnostic_widget = None
        self.diagnostic_result = {}
        self.diagnostic_done = False

        # QShortcut
        self._space_shortcut = QShortcut(
            QKeySequence(Qt.Key.Key_Space), self
        )
        self._space_shortcut.setContext(
            Qt.ShortcutContext.WindowShortcut
        )
        self._space_shortcut.activated.connect(self._on_space_shortcut)

        print("✓ Phase3Scene راه‌اندازی شد")

    def _setup_ui(self):
        main_layout = self.main_layout
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.hud.set_mission("ایستگاه کاسپین")
        self.hud.set_phase("روز سوم: معمای داده‌ها")
        self.hud.set_phase_color("#9C27B0")
        self.hud.set_objective("تحلیل داده و یافتن ریشه بحران")
        main_layout.addWidget(self.hud)


        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(
            "QScrollArea { background-color: transparent; border: none; }"
        )

        # ✅ پس‌زمینه‌ی رویه‌ای اختصاصی — آزمایشگاه داده
        self.scroll_content = ProceduralBackground("data_lab")
        self.center_layout = QVBoxLayout(self.scroll_content)
        self.center_layout.setContentsMargins(20, 20, 20, 20)
        self.center_layout.setSpacing(15)

        self.scenario_title = QLabel()
        self.scenario_title.setStyleSheet(
            f"color: {self.theme['accent']}; "
            f"font-size: 28px; font-weight: bold;"
        )
        self.scenario_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.center_layout.addWidget(self.scenario_title)

        self.center_layout.addWidget(self.dialogue_widget)
        self.choice_widget.setVisible(False)
        self.center_layout.addWidget(self.choice_widget)

        scroll.setWidget(self.scroll_content)
        main_layout.addWidget(scroll, stretch=1)

        # ✅ لایه‌ی ذرات (فقط اگر حالت سریع خاموش باشد)
        from core.app_config import get_fast_mode
        if not get_fast_mode():
            self._particles = ParticleOverlay(
                "phase3", self.scroll_content
            )
            self._particles.setGeometry(self.scroll_content.rect())
            self._particles.lower()
        else:
            self._particles = None

    # ================================================================
    def on_enter(self, **kwargs):
        print("✓ ورود به فاز ۳")
        self.data_logger.log_event(
            scene_id="phase3", scenario_id="phase3_start",
            event_type="scene_enter", metadata={}
        )
        self._load_scenarios()

        # ✅ پیش‌ساخت نقشه‌ی تصمیم بر اساس تعداد سناریوها
        self.hud.initialize_decision_trail(len(self.scenarios))

        # ✅ بازیابی ایندکس از game_manager
        gm = self.game_manager
        idx = 0
        if hasattr(gm, "_scenario_indices"):
            idx = int(gm._scenario_indices.get("phase3", 0))
        idx = min(idx, len(self.scenarios))
        print(f"   [RESUME] شروع فاز ۳ از ایندکس {idx}")
        self.current_scenario_index = idx
        self._start_scenario()

    def _load_scenarios(self):
        self.scenarios.clear()
        scenarios_dir = os.path.join(DATA_DIR, "scenarios", "phase3")

        # ✅ انتخاب نسخه بر اساس حالت دیالوگ درونی
        from core.app_config import should_use_inner_dialogue
        use_inner = should_use_inner_dialogue(
            self.data_logger.random_seed
        )
        suffix = "_inner" if use_inner else ""
        print(
            f"   [INNER] حالت دیالوگ: "
            f"{'با توجیه' if use_inner else 'ساده'}"
        )

        # ✅ در حالت نمایش، فقط سناریوهای منتخب
        theater_list = theater_scenarios_for_phase("phase3")
        if theater_list is not None:
            base_list = theater_list
        else:
            base_list = [
                "PID-01.json", "MC-02.json",
                "PID-02.json", "SPA-01.json",
                "CFI-01.json", "MR-01.json",
                "SPA-02.json", "MR-02.json",
            ]

        # ✅ ساخت لیست نهایی با suffix و fallback
        file_list: list = []
        for base in base_list:
            if suffix:
                name_with_suffix = base.replace(
                    ".json", f"{suffix}.json"
                )
                if os.path.exists(
                    os.path.join(scenarios_dir, name_with_suffix)
                ):
                    file_list.append(name_with_suffix)
                else:
                    file_list.append(base)  # fallback
            else:
                file_list.append(base)

        # ✅ بارگذاری
        for filename in file_list:
            path = os.path.join(scenarios_dir, filename)
            if os.path.exists(path):
                try:
                    with open(
                        path, "r", encoding="utf-8"
                    ) as f:
                        self.scenarios.append(json.load(f))
                    print(f"✓ سناریو بارگذاری شد: {filename}")
                except Exception as e:
                    print(
                        f"❌ خطا در بارگذاری {filename}: {e}"
                    )
            else:
                print(f"⚠️ فایل یافت نشد: {path}")
        print(
            f"✓ تعداد سناریوهای فاز ۳: {len(self.scenarios)}"
        )

    def _parse_inner_thoughts(self, scenario: dict):
        """
        اگر سناریو شامل 'توجیه منطقی:' در گزینه‌ها است، آن را
        به فیلد 'thought' جدا می‌کند.
        """
        import re
        pattern = re.compile(
            r"\n\n\(توجیه منطقی:\s*(.+?)\)\s*$",
            re.DOTALL
        )

        for choice in scenario.get("choices", []):
            text = choice.get("text_fa", "")
            if not text:
                continue
            m = pattern.search(text)
            if m:
                thought = m.group(1).strip()
                # ✅ حذف بخش توجیه از متن اصلی
                new_text = pattern.sub("", text).strip()
                choice["thought"] = thought
                choice["text_fa"] = new_text
            else:
                choice.setdefault("thought", "")

    def _start_scenario(self):
        if self.current_scenario_index >= len(self.scenarios):
            print("✓ فاز ۳ تمام شد. انتقال به میان‌پرده روز چهارم...")


            # ✅ اطلاع‌رسانی پایان فاز
            show_toast(
                self,
                "پایان روز سوم — معمای حل شد، اما نه کامل",
                kind="success",
                duration_ms=3000,
            )

            # ✅ تشخیص فاز بعدی فعال
            next_phase = next_enabled_phase_after("phase3") or "results"

            if not is_section_enabled("interludes_extended"):
                self.change_scene(next_phase)
                return

            # ✅ دیالوگ میان‌پرده بر اساس رابطه‌ی بازیکن با رحیمی
            rahimi_relation = self.data_logger.get_relationship("rahimi")

            # فضاسازی حسی — راوی
            intro_line = (
                "ساعت ۱۴:۵۰ به وقت ایستگاه. بوی سوخت سوخته، هنوز "
                "از بخش مهندسی می‌آید و در راهروی باریک پیچیده. "
                "لوله‌های بخار، تیک‌تیک نامنظمی می‌کنند. کسی در "
                "راهرو نیست، جز رحیمی."
            )

            # دیالوگ اصلی — رحیمی
            if rahimi_relation >= 2:
                rahimi_text = (
                    "(آرام، دست روی شانه‌ات می‌گذارد) تکنسین. توی "
                    "این چهار روز، من بارها دیدم که تو راهی رو رفتی "
                    "که من از خودم انتظار نداشتم."
                )
                rahimi_follow = (
                    "(نگاهی به راکتور می‌اندازد) اگه فردا شورا ازم "
                    "بپرسه که کی می‌تونه این ایستگاه رو بچرخونه، "
                    "بدون ذره‌ای تردید اسم تو رو می‌گم."
                )
            elif rahimi_relation <= -2:
                rahimi_text = (
                    "(با لحن خشک، بدون نگاه مستقیم. دست‌هایش را "
                    "در جیب فرو کرده) تکنسین. جلسه‌ی شورا فردا "
                    "برگزار می‌شه. من چیزی برای اضافه کردن ندارم."
                )
                rahimi_follow = (
                    "(آرام‌تر) تو گزارش‌های من رو هم دیدی، پس "
                    "خودت می‌دونی باید چی بگی."
                )
            elif rahimi_relation <= -1:
                rahimi_text = (
                    "(با لحن محتاط، کنار دیوار ایستاده) تکنسین. "
                    "جلسه‌ی شورا فردا برگزار می‌شه."
                )
                rahimi_follow = (
                    "(صدایش پایین‌تر می‌رود) من... نمی‌دونم چقدر "
                    "می‌تونم کمکت کنم. بعضی چیزها رو نمی‌شه به همین "
                    "راحتی گفت."
                )
            else:
                rahimi_text = (
                    "(آرام، در حالی که از پشت به تو نگاه می‌کند) "
                    "جلسه‌ی شورا... یه چیزی رو بگم. توی این چهار "
                    "روز، من بارها دیدم که تو راهی رو رفتی که من "
                    "رفتم یا نرفتم."
                )
                rahimi_follow = (
                    "(سرش را به سمت راکتور می‌چرخاند) فردا "
                    "هیچ‌کدوم از اینها مهم نیست. اون چیزی که مهمه، "
                    "اینه که وقتی شورا ازت پرسید، با خودت روراست "
                    "باشی. حتی اگه جوابت، منو ناراحت کنه."
                )

            # بازتاب پایانی — راوی
            outro_line = (
                "رحیمی به سمت راکتور راه می‌افتد. صدای قدم‌هایش "
                "در راهروی خالی می‌پیچد. تنها صدای باقی‌مانده، "
                "تیک‌تیک لوله‌های بخار است."
            )

            # ✅ ساخت kwargs میان‌پرده
            interlude_kwargs = {
                "next_scene": next_phase,
                "title": "روز چهارم",
                "subtitle": "آستانه‌ی شورا",
                "body_text": (
                    "روز چهارم. بحران فروکش کرده، اما زخم‌هایش "
                    "باقی است. سایه‌ی یک عملیات نافرجام روی ایستگاه "
                    "سنگینی می‌کند. امشب، جلسه‌ی شورای عالی "
                    "برگزار می‌شود."
                ),
                "dialogues": [
                    {"speaker": "راوی", "text": intro_line},
                    {"speaker": "مهندس رحیمی", "text": rahimi_text},
                    {"speaker": "مهندس رحیمی", "text": rahimi_follow},
                    {"speaker": "راوی", "text": outro_line},
                ],
                "video_path": "interlude_day4.png",
            }

            # ✅ اگر شب‌ها فعال است، اول شب برو
            if is_section_enabled("nights"):
                self.change_scene(
                    "night",
                    night_number=3,
                    next_scene="interlude",
                    next_scene_kwargs=interlude_kwargs,
                )
                return

            # حالت بدون شب
            self.change_scene("interlude", **interlude_kwargs)
            return

        scenario = self.scenarios[self.current_scenario_index]

        self._parse_inner_thoughts(scenario)

        # ✅ ذخیره‌ی ایندکس در game_manager (auto_resume)
        if hasattr(self.game_manager, "update_scenario_index"):
            self.game_manager.update_scenario_index(
                "phase3", self.current_scenario_index
            )

        self.scenario_start_time = time.time()
        self.dialogue_index = 0
        self.current_state = "dialogue"

        # ✅ شمارنده سناریو در HUD
        self.hud.set_scenario_progress(
            self.current_scenario_index + 1,
            len(self.scenarios)
        )
        # ✅ به‌روزرسانی نوار پیشرفت کل
        self.hud.set_progress_from_scenario(
            "phase3",
            self.current_scenario_index,
            len(self.scenarios)
        )

        # ✅ ذخیره برای استفاده در scene بعدی
        self.game_manager._last_progress_pct = (
            self.hud.progress_bar.value()
        )

        # بازنشانی
        self.allocation_done = False
        self.allocation_result = {}
        if self.allocation_widget is not None:
            self.allocation_widget.setVisible(False)

        # ✅ ریست SPA-01
        self.dependency_done = False
        self.dependency_result = {}
        if self.dependency_widget is not None:
            self.dependency_widget.setVisible(False)

        # ✅ ریست CFI-01
        self.puzzle_done = False
        self.puzzle_result = {}
        if self.puzzle_widget is not None:
            self.puzzle_widget.setVisible(False)

        self.diagnostic_done = False
        self.diagnostic_result = {}
        if self.diagnostic_widget is not None:
            self.diagnostic_widget.setVisible(False)

        self._result_dialogues = []
        self._result_dialogue_index = 0
        self._result_data = {}
        self._result_then_action = "show_choices"

        # ✅ بازنشانی وضعیت فلش‌بک
        self._flashback_then_choices_scenario = None

        self.hud.set_objective(scenario.get("title_fa", "مأموریت جاری"))
        self.scenario_title.setText(scenario.get("title_fa", ""))

        self.data_logger.log_event(
            scene_id="phase3", scenario_id=scenario["scenario_id"],
            event_type="scenario_start",
            metadata={"title": scenario.get("title_fa", "")}
        )
        print(f"→ شروع سناریو: {scenario.get('scenario_id')} - "
              f"{scenario.get('title_fa')}")
        self._show_dialogue()

    # ================================================================
    def _show_dialogue(self):
        scenario = self.scenarios[self.current_scenario_index]
        # ✅ ترکیب intro_sequence + dialogue_sequence
        intro_dlg = scenario.get("intro_sequence", [])
        main_dlg = scenario.get("dialogue_sequence", [])
        dialogues = intro_dlg + main_dlg

        if self.dialogue_index < len(dialogues):
            dlg = dialogues[self.dialogue_index]
            txt = dlg.get("text_fa", dlg.get("text", ""))
            self.dialogue_widget.show_dialogue(
                speaker_name=dlg.get("speaker", ""), 
                text=txt,
                emotion=dlg.get("emotion")  # ✅
            )
            self.dialogue_widget.setVisible(True)
            self.choice_widget.setVisible(False)
            self.hud.set_dimmed(False)   # HUD روشن — خواندن دیالوگ
            self.setFocus()
        else:
            # ✅ در حالت نمایش، مکانیک‌ها رد می‌شوند
            if is_theater_mode():
                self.current_state = "choice"
                self._show_choices()
                return

            mechanic = scenario.get("special_mechanic")
            if (mechanic == "resource_allocation"
                    and not self.allocation_done):
                self._show_allocation_widget(scenario)
            elif (mechanic == "diagnostic_map"
                    and not self.diagnostic_done):
                self._show_diagnostic_widget(scenario)
            elif (mechanic == "dependency_board"
                    and not self.dependency_done):
                self._show_dependency_widget(scenario)
            elif (mechanic == "innovation_puzzle"
                    and not self.puzzle_done):
                self._show_puzzle_widget(scenario)
            else:
                self.current_state = "choice"
                self._show_choices()

    # ================================================================
    def _show_allocation_widget(self, scenario):
        self.dialogue_widget.setVisible(False)
        self.choice_widget.setVisible(False)
        self.current_state = "allocation"

        if self.allocation_widget is not None:
            self.center_layout.removeWidget(self.allocation_widget)
            self.allocation_widget.setParent(None)
            self.allocation_widget = None

        cfg = scenario.get("allocation_config", {})
        self.allocation_widget = ResourceAllocationWidget(
            sections=cfg.get("sections", []),
            resources=cfg.get("resources", []),
            time_limit_sec=cfg.get("time_limit_sec", 45),
        )
        self.allocation_widget.allocation_done.connect(
            self._on_allocation_completed
        )
        self.center_layout.addWidget(self.allocation_widget)
        self.allocation_widget.setVisible(True)
        self.hud.set_dimmed(True)    # HUD کم‌رنگ — تمرکز روی ویجت
        print("   [DEBUG] ویجت تخصیص منابع نمایش داده شد")

    def _on_allocation_completed(self, result: dict):
        self.allocation_result = result
        self.allocation_done = True

        scenario = self.scenarios[self.current_scenario_index]

        self.data_logger.log_event(
            scene_id="phase3", scenario_id=scenario["scenario_id"],
            event_type="allocation_completed",
            metadata=result
        )

        # ✅ انتقال زمان واقعی تخصیص به عنوان decision_time
        #    (رفع باگ: E_SPA3_decision_time قبلاً همیشه ۱.۰ می‌شد
        #     چون مقدار پیش‌فرض ۰ پاس داده می‌شد)
        total_time_ms = int(result.get("total_time_ms", 0))
        self._record_mechanic_evidence(
            scenario, decision_time=total_time_ms
        )

        if self.allocation_widget is not None:
            self.allocation_widget.setVisible(False)

        self._result_dialogues = scenario.get("result_dialogue", [])
        self._result_dialogue_index = 0
        self._result_data = result
        self._result_then_action = "next_scenario"

        QTimer.singleShot(80, self._after_allocation)

    def _after_allocation(self):
        if self._result_dialogues:
            self.dialogue_widget.setVisible(True)
            self.choice_widget.setVisible(False)
            self.current_state = "result_dialogue"
            self._show_next_result_dialogue()
        else:
            self._advance_after_mechanic()

    def _show_diagnostic_widget(self, scenario):
        """نمایش ویجت نقشه تشخیصی"""
        self.dialogue_widget.setVisible(False)
        self.choice_widget.setVisible(False)
        self.current_state = "diagnostic"

        if self.diagnostic_widget is not None:
            self.center_layout.removeWidget(self.diagnostic_widget)
            self.diagnostic_widget.setParent(None)
            self.diagnostic_widget = None

        cfg = scenario.get("diagnostic_config", {})
        self.diagnostic_widget = DiagnosticMapWidget(
            systems=cfg.get("systems", []),
            npc_hint=cfg.get("npc_hint", ""),
            investigation_time_ms=cfg.get("investigation_time_ms", 1500),
        )
        self.diagnostic_widget.diagnosis_done.connect(
            self._on_diagnosis_completed
        )
        self.center_layout.addWidget(self.diagnostic_widget)
        self.diagnostic_widget.setVisible(True)
        self.hud.set_dimmed(True)    # HUD کم‌رنگ — تمرکز روی ویجت
        print("   [DEBUG] ویجت نقشه تشخیصی نمایش داده شد")

    # ================================================================
    def _show_dependency_widget(self, scenario):
        """نمایش ویجت تخته وابستگی SPA-01"""
        self.dialogue_widget.setVisible(False)
        self.choice_widget.setVisible(False)
        self.current_state = "dependency"

        if self.dependency_widget is not None:
            self.center_layout.removeWidget(self.dependency_widget)
            self.dependency_widget.setParent(None)
            self.dependency_widget = None

        cfg = scenario.get("dependency_config", {})
        actions = cfg.get("actions", [])
        correct_order = cfg.get("correct_order", [])

        from widgets.dependency_board_widget import DependencyBoardWidget
        self.dependency_widget = DependencyBoardWidget(
            actions=actions,
            correct_order=correct_order,
        )
        self.dependency_widget.board_done.connect(
            self._on_dependency_completed
        )
        self.center_layout.addWidget(self.dependency_widget)
        self.dependency_widget.setVisible(True)
        self.hud.set_dimmed(True)    # HUD کم‌رنگ — تمرکز روی ویجت
        print("   [DEBUG] ویجت تخته وابستگی نمایش داده شد")

    def _on_dependency_completed(self, result: dict):
        """پایان SPA-01"""
        self.dependency_result = result
        self.dependency_done = True

        scenario = self.scenarios[self.current_scenario_index]
        self.data_logger.log_event(
            scene_id="phase3", scenario_id=scenario["scenario_id"],
            event_type="dependency_board_completed",
            metadata=result
        )
        self._record_dependency_evidence(scenario, result)

        if self.dependency_widget is not None:
            self.dependency_widget.setVisible(False)

        # دیالوگ نتیجه
        self._result_dialogues = scenario.get("result_dialogue", [])
        self._result_dialogue_index = 0
        self._result_data = result
        self._result_then_action = "next_scenario"

        if self._result_dialogues:
            self.dialogue_widget.setVisible(True)
            self.choice_widget.setVisible(False)
            self.current_state = "result_dialogue"
            self._show_next_result_dialogue()
        else:
            self.current_scenario_index += 1
            self._start_scenario()

    def _record_dependency_evidence(self, scenario, result) -> float:
        scenario_id = scenario["scenario_id"]
        competency = "problem_solving"
        evidence_model = scenario.get("evidence_model", {})

        planning_time = result.get("planning_time_ms", 0)
        if 5000 <= planning_time <= 30000:
            planning_score = 1.0
        elif planning_time < 5000:
            planning_score = 0.4
        elif planning_time <= 60000:
            planning_score = 0.6
        else:
            planning_score = 0.3

        # ✅ امتیاز نهایی از client (شامل جریمه‌ی distractor)
        seq_score = float(result.get("sequence_score", 0))

        value_map = {
            "E_SPA1_sequence_score": seq_score,
            "E_SPA1_planning_time": planning_score,
            "E_SPA1_efficiency": seq_score,
        }

        # ✅ لاگ distractor
        distractor_used = result.get("distractor_used", [])
        if distractor_used:
            print(
                f"   [SPA-01] ⚠️ بازیکن "
                f"{len(distractor_used)} گزینه‌ی بی‌ربط "
                f"انتخاب کرد: {distractor_used}"
            )

        values: list = []
        weights: list = []

        for ev_id, ev_def in evidence_model.items():
            weight = ev_def.get("weight", 1.0)
            value = value_map.get(ev_id, 0.0)
            values.append(value)
            weights.append(weight)
            print(f"   [SPA-01] {ev_id} = {value:.2f} (weight={weight})")

            self.game_manager.data_logger.log_evidence(
                scenario_id=scenario_id, competency=competency,
                subcomponent=ev_def.get("description", ""),
                evidence_key=ev_id, evidence_value=value, weight=weight
            )

        total_w = sum(weights)
        avg = (
            sum(v * w for v, w in zip(values, weights)) / total_w
            if total_w > 0 else 0.5
        )
        self.hud.record_decision(
            avg, scenario.get("title_fa", "")
        )
        return avg

    # ================================================================
    def _show_puzzle_widget(self, scenario):
        """نمایش ویجت پازل ترکیب CFI-01"""
        self.dialogue_widget.setVisible(False)
        self.choice_widget.setVisible(False)
        self.current_state = "puzzle"

        if self.puzzle_widget is not None:
            self.center_layout.removeWidget(self.puzzle_widget)
            self.puzzle_widget.setParent(None)
            self.puzzle_widget = None

        cfg = scenario.get("puzzle_config", {})
        from widgets.puzzle_widget import PuzzleWidget
        self.puzzle_widget = PuzzleWidget(
            items=cfg.get("items", []),
            valid_combinations=cfg.get("valid_combinations", []),
            solution_hint=cfg.get("solution_hint", ""),
        )
        self.puzzle_widget.puzzle_done.connect(
            self._on_puzzle_completed
        )
        self.center_layout.addWidget(self.puzzle_widget)
        self.puzzle_widget.setVisible(True)
        self.hud.set_dimmed(True)    # HUD کم‌رنگ — تمرکز روی ویجت
        print("   [DEBUG] ویجت پازل نمایش داده شد")

    def _on_puzzle_completed(self, result: dict):
        """پایان CFI-01"""
        self.puzzle_result = result
        self.puzzle_done = True

        scenario = self.scenarios[self.current_scenario_index]
        self.data_logger.log_event(
            scene_id="phase3", scenario_id=scenario["scenario_id"],
            event_type="puzzle_completed",
            metadata=result
        )
        self._record_puzzle_evidence(scenario, result)

        if self.puzzle_widget is not None:
            self.puzzle_widget.setVisible(False)

        self._result_dialogues = scenario.get("result_dialogue", [])
        self._result_dialogue_index = 0
        self._result_data = result
        self._result_then_action = "next_scenario"

        if self._result_dialogues:
            self.dialogue_widget.setVisible(True)
            self.choice_widget.setVisible(False)
            self.current_state = "result_dialogue"
            self._show_next_result_dialogue()
        else:
            self.current_scenario_index += 1
            self._start_scenario()

    def _record_puzzle_evidence(self, scenario, result) -> float:
        scenario_id = scenario["scenario_id"]
        competency = "problem_solving"
        evidence_model = scenario.get("evidence_model", {})

        old_attempts = result.get("old_solution_attempts", 0)
        unique = result.get("unique_attempts", 0)
        total_attempts = result.get("total_attempts", 0)
        sol_time = result.get("solution_time_ms", 0)

        is_guessing = (total_attempts == 1 and sol_time < 10000)
        old_score = max(0.0, 1.0 - (old_attempts * 0.15))
        unique_score = 0.15 if is_guessing else min(1.0, unique * 0.15)

        if sol_time <= 15000:
            time_score = 0.7
        elif sol_time <= 60000:
            time_score = 1.0
        elif sol_time <= 120000:
            time_score = 0.6
        else:
            time_score = 0.3

        value_map = {
            "E_CFI1_old_attempts": old_score,
            "E_CFI1_unique_combinations": unique_score,
            "E_CFI1_solution_time": time_score,
        }

        values: list = []
        weights: list = []

        for ev_id, ev_def in evidence_model.items():
            weight = ev_def.get("weight", 1.0)
            value = value_map.get(ev_id, 0.0)
            values.append(value)
            weights.append(weight)
            print(f"   [CFI-01] {ev_id} = {value:.2f} (weight={weight})")

            self.game_manager.data_logger.log_evidence(
                scenario_id=scenario_id, competency=competency,
                subcomponent=ev_def.get("description", ""),
                evidence_key=ev_id, evidence_value=value, weight=weight
            )

        total_w = sum(weights)
        avg = (
            sum(v * w for v, w in zip(values, weights)) / total_w
            if total_w > 0 else 0.5
        )
        self.hud.record_decision(
            avg, scenario.get("title_fa", "")
        )
        return avg

    def _on_diagnosis_completed(self, result: dict):
        """پایان تشخیص"""
        self.diagnostic_result = result
        self.diagnostic_done = True

        scenario = self.scenarios[self.current_scenario_index]
        self.data_logger.log_event(
            scene_id="phase3", scenario_id=scenario["scenario_id"],
            event_type="diagnosis_completed",
            metadata=result
        )
        self._record_mechanic_evidence(scenario)

        if self.diagnostic_widget is not None:
            self.diagnostic_widget.setVisible(False)

        # ✅ انتخاب دیالوگ نتیجه بر اساس علت انتخابی
        chosen = result.get("chosen_root_cause", "")
        result_map = scenario.get("result_dialogue_by_root_cause", {})
        if chosen in result_map:
            self._result_dialogues = result_map[chosen]
        else:
            self._result_dialogues = scenario.get("result_dialogue", [])

        self._result_dialogue_index = 0
        self._result_data = result
        self._result_then_action = "next_scenario"

        QTimer.singleShot(80, self._after_diagnostic)

    def _after_diagnostic(self):
        """پس از تشخیص"""
        if self._result_dialogues:
            self.dialogue_widget.setVisible(True)
            self.choice_widget.setVisible(False)
            self.current_state = "result_dialogue"
            self._show_next_result_dialogue()
        else:
            self._advance_after_mechanic()

    def _advance_after_mechanic(self):
        """تصمیم بگیر که برویم گزینه‌ها یا سناریوی بعد"""
        scenario = self.scenarios[self.current_scenario_index]
        if scenario.get("choices"):
            self.current_state = "choice"
            self._show_choices()
        else:
            print("   [DEBUG] سناریو بدون گزینه — انتقال به سناریوی بعدی")
            self.current_scenario_index += 1
            self._start_scenario()

    def _show_next_result_dialogue(self):
        if self._result_dialogue_index < len(self._result_dialogues):
            dlg = self._result_dialogues[self._result_dialogue_index]
            text = dlg.get("text_fa", "")

            # ✅ جایگزینی placeholder ها + محاسبه کلیدهای مشتق
            data = dict(self._result_data)
            if "total_count" in data and "in_zone_count" in data:
                data.setdefault(
                    "out_zone_count",
                    data["total_count"] - data["in_zone_count"]
                )
            for key, val in data.items():
                text = text.replace("{" + key + "}", str(val))

            self.dialogue_widget.show_dialogue(
                speaker_name=dlg.get("speaker", ""), 
                text=text,
                emotion=dlg.get("emotion")  # ✅
            )
            self.dialogue_widget.setVisible(True)
            self.hud.set_dimmed(False)   # HUD روشن — خواندن نتیجه
            self.setFocus()
        else:
            action = getattr(self, "_result_then_action", "show_choices")
            if action == "next_scenario":
                print("   [DEBUG] پایان دیالوگ نتیجه → سناریوی بعدی")
                self.current_scenario_index += 1
                self._start_scenario()
            else:
                self._advance_after_mechanic()

    # ================================================================
    def _show_choices(self):
        scenario = self.scenarios[self.current_scenario_index]
        scenario_id = scenario.get("scenario_id", "")

        # ✅ اول: خاطرات چندلایه (اگر فعال باشد)
        if (
            is_section_enabled("multilayer_memory")
            and scenario_id != self._flashback_shown_for_scenario
        ):
            ml_text = get_multilayer_memory_text(
                scenario_id, self.data_logger
            )
            if ml_text:
                self._flashback_shown_for_scenario = scenario_id
                self._show_flashback_then_choices(ml_text, scenario)
                print("   [MULTILAYER] نمایش الگوی تصمیم‌ها")
                return

        # ✅ دوم: فلش‌بک ساده
        if (
            is_section_enabled("flashbacks")
            and scenario_id != self._flashback_shown_for_scenario
        ):
            fb_text = get_flashback_text(scenario_id, self.data_logger)
            if fb_text:
                self._flashback_shown_for_scenario = scenario_id
                self._show_flashback_then_choices(fb_text, scenario)
                return

        # نمایش مستقیم گزینه‌ها
        choices = scenario.get("choices", [])
        self.dialogue_widget.setVisible(False)
        self.choice_widget.setVisible(True)
        self.choice_widget.show_choices(
            choices, scenario.get("scenario_id", "")
        )
        self.hud.set_dimmed(True)    # HUD کم‌رنگ — انتخاب گزینه
        self.setFocus()
        print(f"   [DEBUG] {len(choices)} گزینه نمایش داده شد")

    def _show_flashback_then_choices(self, fb_text: str,
                                      scenario: dict):
        """نمایش فلش‌بک، سپس گزینه‌ها"""
        self.dialogue_widget.setVisible(True)
        self.choice_widget.setVisible(False)
        self.dialogue_widget.show_dialogue(
            speaker_name="راوی", text=fb_text
        )
        self.hud.set_dimmed(False)   # HUD روشن — خواندن فلش‌بک
        self.setFocus()
        self.current_state = "flashback"
        self._flashback_then_choices_scenario = scenario
        print("   [FLASHBACK] نمایش خاطره")
    # ================================================================
    def _on_choice_made(self, choice: dict, decision_time: int):
        scenario = self.scenarios[self.current_scenario_index]
        print(f"   [DEBUG] انتخاب دریافت شد: {choice.get('id')}")

        extra = {}
        if scenario.get("special_mechanic") == "resource_allocation":
            extra = {"allocation_result": self.allocation_result}
        elif scenario.get("special_mechanic") == "diagnostic_map":
            extra = {"diagnostic_result": self.diagnostic_result}

        self.data_logger.log_event(
            scene_id="phase3", scenario_id=scenario["scenario_id"],
            event_type="choice_made",
            metadata={
                "choice_id": choice.get("id"),
                "choice_text": choice.get("text_fa"),
                "decision_time_ms": decision_time,
                **extra,
            }
        )
        self._record_evidence(scenario, choice, decision_time)
        self._update_relationship(scenario, choice)

        # ✅ فاز B-3: ثبت طرح‌واره‌ی استدلالی (کلبرگ)
        schema = choice.get("schema")
        if schema and isinstance(schema, dict):
            self.data_logger.log_schema_evidence(
                scenario_id=scenario.get("scenario_id", ""),
                choice_id=choice.get("id", 0),
                schema_primary=schema.get("primary", ""),
                schema_secondary=schema.get("secondary") or "",
                reaction_time_ms=decision_time,
            )

        self.hud.show_save_indicator()

        # ✅ بازخورد فوری به بازیکن (فاز حل مسئله)
        show_toast(
            self,
            "✓  ثبت شد",
            kind="info",
            duration_ms=1500,
        )

        # ✅ بررسی وجود دیالوگ نتیجه پس از انتخاب
        result_dlg_map = scenario.get("result_dialogue_by_choice", {})
        choice_id_str = str(choice.get("id", 0))

        if choice_id_str in result_dlg_map:
            self._result_dialogues = result_dlg_map[choice_id_str]
            self._result_dialogue_index = 0
            self._result_data = {"decision_time_ms": decision_time}
            self._result_then_action = "next_scenario"
            self.dialogue_widget.setVisible(True)
            self.choice_widget.setVisible(False)
            self.current_state = "result_dialogue"
            self._show_next_result_dialogue()
        else:
            self.current_scenario_index += 1
            self._start_scenario()

    # ================================================================
    def _record_evidence(self, scenario: dict, choice: dict,
                          decision_time: int) -> float:
        # ✅ در حالت نمایش، هیچ شاهدی ثبت نمی‌شود
        if is_theater_mode():
            return 0.0

        scenario_id = scenario["scenario_id"]
        competency = scenario.get("competency_override", "problem_solving")
        evidence_model = scenario.get("evidence_model", {})

        values: list = []
        weights: list = []

        for ev_id, ev_def in evidence_model.items():
            weight = ev_def.get("weight", 1.0)
            formula = ev_def.get("formula", "")
            value = self._calculate_evidence_value(
                formula, choice, decision_time, scenario
            )
            values.append(value)
            weights.append(weight)

            self.game_manager.data_logger.log_evidence(
                scenario_id=scenario_id, competency=competency,
                subcomponent=ev_def.get("description", ""),
                evidence_key=ev_id, evidence_value=value, weight=weight
            )

        total_w = sum(weights)
        avg = (
            sum(v * w for v, w in zip(values, weights)) / total_w
            if total_w > 0 else 0.5
        )
        self.hud.record_decision(
            avg, scenario.get("title_fa", "")
        )
        return avg

    def _calculate_evidence_value(self, formula: str, choice: dict,
                                   decision_time: int,
                                   scenario: dict) -> float:
        """
        محاسبه مقدار شاهد از فرمول‌های تعریف‌شده در evidence_model سناریو.

        فرمول‌های پشتیبانی‌شده:

        ┌─────────────────────────────────────────────────────────────┐
        │ ۱. فرمول‌های معنایی:                                         │
        │    allocation_score, info_check_score,                       │
        │    fairness_under_pressure, investigation_depth,             │
        │    investigation_count, time_to_first_action,                │
        │    correct_root_cause, perseveration_score,                  │
        │    exploration_score                                         │
        │                                                              │
        │ ۲. زمان تصمیم:                                               │
        │    decision_time  →  کاهش خطی از ۱ به ۰ در ۶۰ ثانیه           │
        │                                                              │
        │ ۳. الگوی دو شرطی:                                            │
        │    1 if choice_id == A else (B if choice_id == C else D)    │
        │                                                              │
        │ ۴. الگوی تک‌شرطی:                                             │
        │    1 if choice_id == A else B                                │
        │                                                              │
        │ ۵. الگوی چندگزینه:                                            │
        │    1 if choice_id in (A, B) else C                           │
        └─────────────────────────────────────────────────────────────┘
        """
        from core.evidence_helpers import (
            evaluate_choice_formula, evaluate_time_formula
        )
        cid = choice.get("id", 0)
        formula = formula.strip()

        # ==========================================================
        # ۱. فرمول‌های معنایی (Semantic formulas)
        # ==========================================================
        semantic_handlers = {
            "allocation_score":        lambda: self._score_allocation(scenario),
            "info_check_score":        lambda: self._score_info_check(scenario),
            "fairness_under_pressure": lambda: self._score_fairness(),
            "investigation_depth":     lambda: self._score_investigation_depth(),
            "investigation_count":     lambda: self._score_investigation_count(),
            "time_to_first_action":    lambda: self._score_time_to_first_action(),
            "correct_root_cause":      lambda: self._score_correct_root(scenario),
            "perseveration_score":     lambda: self._score_perseveration(),
            "exploration_score":       lambda: self._score_exploration(),
        }
        if formula in semantic_handlers:
            return semantic_handlers[formula]()

        # ==========================================================
        # ۲. زمان تصمیم: کاهش خطی از ۱ به ۰ در ۶۰ ثانیه
        # ==========================================================
        if formula == "decision_time":
            return max(0.0, 1.0 - (decision_time / 60000.0))

        # ==========================================================
        # ۳. الگوی دو شرطی: 1 if choice_id == A else (B if choice_id == C else D)
        # ==========================================================
        m = re.match(
            r"^1 if choice_id == (\d+) "
            r"else \((\d+(?:\.\d+)?) if choice_id == (\d+) "
            r"else (\d+(?:\.\d+)?)\)$",
            formula
        )
        if m:
            best = int(m.group(1))            # گزینه‌ی بهترین (امتیاز ۱.۰)
            partial_score = float(m.group(2))  # امتیاز گزینه‌ی میانی
            partial_id = int(m.group(3))       # شناسه گزینه‌ی میانی
            default = float(m.group(4))        # امتیاز بقیه
            if cid == best:
                return 1.0
            if cid == partial_id:
                return partial_score
            return default

        # ==========================================================
        # ۴. الگوی تک‌شرطی: 1 if choice_id == A else B
        # ==========================================================
        m = re.match(
            r"^1 if choice_id == (\d+) else (\d+(?:\.\d+)?)$",
            formula
        )
        if m:
            best = int(m.group(1))
            default = float(m.group(2))
            return 1.0 if cid == best else default

        # ==========================================================
        # ۵. الگوی چندگزینه: 1 if choice_id in (A, B) else C
        # ==========================================================
        m = re.match(
            r"^1 if choice_id in \((\d+),\s*(\d+)\) "
            r"else (\d+(?:\.\d+)?)$",
            formula
        )
        if m:
            a = int(m.group(1))
            b = int(m.group(2))
            default = float(m.group(3))
            return 1.0 if cid in (a, b) else default

        # ==========================================================
        # ۶. Fallback — فرمول ناشناخته
        # ==========================================================
        print(f"   ⚠️ [phase3] فرمول ناشناخته: '{formula}'")
        return 1.0 if cid == 1 else (0.5 if cid == 2 else 0.0)

    def _score_allocation(self, scenario: dict) -> float:
        """نمره‌دهی بر اساس مطابقت با تخصیص بهینه.
        با ۶ بخش، بخش‌های غیربهینه جریمه‌ی متناسب می‌گیرند.
        """
        cfg = scenario.get("allocation_config", {})
        optimal = cfg.get("optimal_allocation", {})
        allocations = self.allocation_result.get("allocations", {})

        if not optimal:
            return 0.0

        # امتیاز تخصیص به بخش‌های بهینه
        correct = sum(
            1 for sec, res in optimal.items()
            if allocations.get(sec) == res
        )

        # جریمه برای تخصیص به بخش‌های غیربهینه
        # بخش‌های با اولویت بالاتر (engineering, command_center, science_lab)
        # جریمه‌ی کمتری می‌گیرند چون انتخاب‌های قابل توجیهی هستند
        penalty = 0
        for sec, res in allocations.items():
            if sec not in optimal:
                if sec == "engineering":
                    # فشار رحیمی — انتخاب قابل توجیه ولی باعث cascade failure
                    penalty += 0.5
                elif sec == "command_center":
                    # ارتباط مهم است ولی فوری نیست
                    penalty += 0.4
                elif sec == "science_lab":
                    # داده‌ی علمی ارزشمند ولی اولویت پایین
                    penalty += 0.4
                else:
                    penalty += 0.5

        score = (correct - penalty) / len(optimal)
        return max(0.0, min(1.0, score))

    def _score_info_check(self, scenario: dict) -> float:
        """نمره‌دهی بر اساس نسبت بخش‌های بررسی‌شده.
        با ۶ بخش، بازیکن باید حداقل ۵ بخش را بررسی کند تا امتیاز کامل بگیرد.
        """
        cfg = scenario.get("allocation_config", {})
        sections = cfg.get("sections", [])
        if not sections:
            return 0.0
        info_checked = self.allocation_result.get("info_checked", [])
        # با ۶ بخش، اگر ۵ بخش را بررسی کرده (۸۳٪)، امتیاز کامل می‌گیرد
        ratio = len(info_checked) / len(sections)
        if ratio >= 0.83:
            return 1.0
        return ratio * 1.2  # اجازه می‌دهد با ۵ از ۶، امتیاز کامل بگیرد

    def _score_investigation_depth(self) -> float:
        result = self.diagnostic_result
        total = result.get("total_systems", 6)
        investigated = result.get("total_investigated", 0)
        if total == 0:
            return 0.0
        ratio = min(1.0, investigated / max(1, total - 1))
        return ratio

    def _score_investigation_count(self) -> float:
        investigated = self.diagnostic_result.get("total_investigated", 0)
        if investigated >= 5:
            return 1.0
        elif investigated >= 3:
            return 0.7
        elif investigated >= 2:
            return 0.4
        elif investigated >= 1:
            return 0.2
        return 0.0

    def _score_time_to_first_action(self) -> float:
        t = self.diagnostic_result.get("time_to_first_action_ms", 0)
        if t == 0:
            return 0.0
        if t < 1000:
            return 0.3
        if t <= 8000:
            return 1.0
        if t <= 15000:
            return 0.7
        return 0.4

    def _score_correct_root(self, scenario: dict) -> float:
        chosen = self.diagnostic_result.get("chosen_root_cause")
        if chosen == "power_grid":
            return 1.0
        elif chosen == "cooling":
            return 0.1
        elif chosen == "communications":
            return 0.3
        return 0.2

    def _score_perseveration(self) -> float:
        """CFI-02: هرچه کلیک‌های تکراری کمتر، انعطاف بیشتر"""
        p = self.diagnostic_result.get("perseveration_count", 0)
        u = self.diagnostic_result.get("total_investigated", 0)
        if u == 0:
            return 0.0
        ratio = p / max(1, u)
        if ratio == 0:
            return 1.0
        if ratio <= 0.5:
            return 0.8
        if ratio <= 1.0:
            return 0.5
        return 0.2

    def _score_exploration(self) -> float:
        """CFI-02: هرچه سیستم‌های بیشتری بررسی شده، بهتر"""
        u = self.diagnostic_result.get("total_investigated", 0)
        t = self.diagnostic_result.get("total_systems", 6)
        return min(1.0, u / max(1, t))

    def _score_fairness(self) -> float:
        """
        انصاف تحت فشار اجتماعی — SPA-02.
        
        تست اصلی: رحیمی شخصاً درخواست باتری برای engineering کرده
        با وعده‌ی تعریف در گزارش نهایی. آیا بازیکن به این فشار تن داد
        یا بر اساس نیاز واقعی سیستم تصمیم گرفت؟
        
        سه لایه‌ی سنجش:
        ─────────────────────────────────────────
        ۱. تصمیم اصلی (۰.۵۰): به کدام بخش باتری داد؟
        ۲. فرآیند تصمیم (۰.۳۰): آیا قبل از تصمیم اطلاعات جمع کرد؟
        ۳. تأمین نیاز بحرانی (۰.۲۰): اکسیژن به بخش پزشکی؟
        """
        allocations = self.allocation_result.get("allocations", {})
        info_checked = self.allocation_result.get("info_checked", [])
        
        # =========================================================
        # لایه‌ی ۱: تصمیم اصلی — به کدام بخش باتری داد؟
        # =========================================================
        # ترتیب ترجیح:
        #   ۱. air_recycling: بهترین انتخاب (نجات cascade)
        #   ۲. engineering: تسلیم فشار (نه بحرانی، ولی مهم)
        #   ۳. command_center: انتخاب جایگزین (نه تسلیم، ولی ناقص)
        #   ۴. بخش‌های دیگر: انتخاب ضعیف
        if allocations.get("air_recycling") == "battery":
            decision_score = 1.00   # ✅ مقاومت کامل در برابر فشار
        elif allocations.get("engineering") == "battery":
            decision_score = 0.20   # ⚠️ تسلیم فشار اجتماعی
        elif allocations.get("command_center") == "battery":
            decision_score = 0.40   # ⚠️ انتخاب جایگزین — نه تسلیم، نه بهینه
        else:
            decision_score = 0.10   # ❌ انتخاب ضعیف
        
        # =========================================================
        # لایه‌ی ۲: فرآیند تصمیم — بررسی اطلاعات
        # =========================================================
        # کسی که بدون خواندن اطلاعات تصمیم گرفته، در تصمیمش
        # احتمالاً تحت تأثیر فشار بیرونی بوده است.
        total_sections = 6
        ratio = min(1.0, len(info_checked) / total_sections)
        # با ۵ از ۶ (۸۳٪)، امتیاز کامل
        if ratio >= 0.83:
            process_score = 1.00
        elif ratio >= 0.66:
            process_score = 0.70
        elif ratio >= 0.50:
            process_score = 0.40
        else:
            process_score = 0.10
        
        # =========================================================
        # لایه‌ی ۳: تأمین نیاز بحرانی — اکسیژن به پزشکی
        # =========================================================
        # این تصمیم اجباری است (سه نفر در ۴ ساعت می‌میرند)
        # اگر بازیکن این را ندهد، یک خطای بنیادی مرتکب شده
        medical_ok = allocations.get("medical") == "oxygen"
        medical_score = 1.0 if medical_ok else 0.0
        
        # =========================================================
        # ترکیب وزنی
        # =========================================================
        final = (
            decision_score * 0.50 +
            process_score * 0.30 +
            medical_score * 0.20
        )
        
        # print برای دیباگ
        print(f"   [FAIRNESS] decision={decision_score:.2f} "
            f"process={process_score:.2f} "
            f"medical={medical_score:.2f} "
            f"→ total={final:.2f}")
        
        return round(max(0.0, min(1.0, final)), 3)

    # ================================================================
    def _on_space_shortcut(self):
        if not self.isVisible():
            return
        state = self.current_state

        # ✅ مدیریت فلش‌بک
        if state == "flashback":
            if self.dialogue_widget.is_typing():
                self.dialogue_widget.advance()
            else:
                # بعد از خواندن فلش‌بک → نمایش گزینه‌ها
                self.current_state = "choice"
                scenario = getattr(
                    self, "_flashback_then_choices_scenario", None
                )
                if scenario is not None:
                    choices = scenario.get("choices", [])
                    self.dialogue_widget.setVisible(False)
                    self.choice_widget.setVisible(True)
                    self.choice_widget.show_choices(
                        choices, scenario.get("scenario_id", "")
                    )

                    self.setFocus()
            return

        if state == "allocation":
            if (self.allocation_widget is not None
                    and self.allocation_widget.submit_btn.isEnabled()):
                self.allocation_widget.submit_btn.click()
            return

        if state == "diagnostic":
            return

        if state == "result_dialogue":
            if self.dialogue_widget.is_typing():
                self.dialogue_widget.advance()
            else:
                self._result_dialogue_index += 1
                QTimer.singleShot(30, self._show_next_result_dialogue)
            return

        if state == "dialogue":
            if self.dialogue_widget.is_typing():
                self.dialogue_widget.advance()
            else:
                self.dialogue_index += 1
                self._show_dialogue()
            return

    def _on_dialogue_click(self):
        """کلیک کاربر = همان رفتار Space"""
        if not self.isVisible():
            return
        state = self.current_state

        # همان منطق _on_space_shortcut را دوباره اجرا می‌کنیم
        if state == "flashback":
            if self.dialogue_widget.is_typing():
                self.dialogue_widget.advance()
            else:
                self.current_state = "choice"
                scenario = self._flashback_then_choices_scenario
                if scenario is not None:
                    choices = scenario.get("choices", [])
                    self.dialogue_widget.setVisible(False)
                    self.choice_widget.setVisible(True)
                    self.choice_widget.show_choices(
                        choices, scenario.get("scenario_id", "")
                    )

                    self.setFocus()
            return

        if state == "result_dialogue":
            if self.dialogue_widget.is_typing():
                self.dialogue_widget.advance()
            else:
                self._result_dialogue_index += 1
                QTimer.singleShot(30, self._show_next_result_dialogue)
            return

        if state == "dialogue":
            if self.dialogue_widget.is_typing():
                self.dialogue_widget.advance()
            else:
                self.dialogue_index += 1
                self._show_dialogue()
            return

    def _record_mechanic_evidence(self, scenario: dict,
                                   decision_time: int = 0) -> float:
        scenario_id = scenario["scenario_id"]
        competency = "problem_solving"
        evidence_model = scenario.get("evidence_model", {})

        values: list = []
        weights: list = []

        print(f"   [DEBUG] ثبت شواهد مکانیک {scenario_id}:")
        for ev_id, ev_def in evidence_model.items():
            weight = ev_def.get("weight", 1.0)
            formula = ev_def.get("formula", "")
            value = self._calculate_evidence_value(
                formula, {"id": 0}, decision_time, scenario
            )
            values.append(value)
            weights.append(weight)
            print(f"      {ev_id} = {value:.2f} (weight={weight})")

            self.game_manager.data_logger.log_evidence(
                scenario_id=scenario_id, competency=competency,
                subcomponent=ev_def.get("description", ""),
                evidence_key=ev_id, evidence_value=value, weight=weight
            )

        total_w = sum(weights)
        avg = (
            sum(v * w for v, w in zip(values, weights)) / total_w
            if total_w > 0 else 0.5
        )
        self.hud.record_decision(
            avg, scenario.get("title_fa", "")
        )
        return avg

    def _update_relationship(self, scenario: dict, choice: dict):
        sid = scenario.get("scenario_id", "")
        cid = choice.get("id", 0)
        logger = self.data_logger

        logger.remember_choice(sid, cid)

        # ---------------- MC-02: خط نامرئی (افشای رحیمی) ----------------
        if sid == "MC-02":
            if cid == 1:      # افشا به مرکز
                logger.adjust_relationship("rahimi", -3)
                logger.adjust_relationship("artemis", +1)
            elif cid == 2:    # معامله
                logger.adjust_relationship("rahimi", +1)
            elif cid == 3:    # سکوت
                logger.adjust_relationship("rahimi", +2)

    def keyPressEvent(self, event):  # type: ignore[reportIncompatibleMethodOverride]
        super().keyPressEvent(event)

    def resizeEvent(self, event):  # type: ignore[reportIncompatibleMethodOverride]
        super().resizeEvent(event)
        if (hasattr(self, "_particles")
                and self._particles is not None
                and hasattr(self, "scroll_content")):
            self._particles.setGeometry(
                self.scroll_content.rect()
            )