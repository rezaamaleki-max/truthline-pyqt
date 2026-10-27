"""
فاز ۴: مسئولیت‌پذیری
ترتیب: PI-01 → RG-01 → AC-01 (شورا آخرین سناریو)
"""
import os
import json
import time
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QShortcut, QKeySequence

from scenes.base_scene import BaseScene
from widgets.dialogue_widget import DialogueWidget
from widgets.choice_widget import ChoiceWidget
from widgets.hud_widget import HUDWidget
from widgets.accountability_widget import AccountabilityDialogWidget
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



class Phase4Scene(BaseScene):

    def __init__(self, game_manager):
        super().__init__(game_manager)

        # ✅ تم اختصاصی فاز — instance attribute (سازگار با Pylance)
        self.phase_num: int = 4
        self.theme: dict = PHASE_THEMES[self.phase_num]

        self.scenarios = []
        self.current_scenario_index = 0
        self.current_state = "dialogue"
        self.scenario_start_time = 0
        self.dialogue_index = 0

        # مکانیک شورا
        self.accountability_widget = None
        self.accountability_done = False
        self.accountability_result = {}

        # ✅ مکانیک کار تکراری (TC-01)
        self.repetitive_widget = None
        self.repetitive_done = False
        self.repetitive_result = {}

        # دیالوگ‌های نتیجه
        self._result_dialogues: list = []
        self._result_dialogue_index = 0
        self._result_data: dict = {}
        self._result_then_action: str = "next_scenario"

        # ✅ پرچم‌های پیش از شورا (council_prep)
        self._council_prep_shown: bool = False
        self._resume_index: int = -1

        # ✅ وضعیت فلش‌بک
        self._flashback_shown_for_scenario: str = ""
        self._flashback_then_choices_scenario: dict | None = None

        # ✅ پرچم نامه به خود
        self._letter_shown: bool = False

        self.dialogue_widget = DialogueWidget(data_logger=self.data_logger)
        # ✅ اتصال سیگنال کلیک به پیشروی دیالوگ
        self.dialogue_widget.advanced.connect(
            lambda: self._on_dialogue_click()
        )
        self.choice_widget = ChoiceWidget()
        self.hud = HUDWidget()

        self.choice_widget.choice_made.connect(self._on_choice_made)
        self._setup_ui()

        self._space_shortcut = QShortcut(
            QKeySequence(Qt.Key.Key_Space), self
        )
        self._space_shortcut.setContext(
            Qt.ShortcutContext.WindowShortcut
        )
        self._space_shortcut.activated.connect(self._on_space_shortcut)

        print("✓ Phase4Scene راه‌اندازی شد")

    def _setup_ui(self):
        main_layout = self.main_layout
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.hud.set_mission("ایستگاه کاسپین")
        self.hud.set_phase("روز چهارم: آستانه‌ی شورا")
        self.hud.set_phase_color("#D32F2F")
        self.hud.set_objective("مواجهه با شورای عالی ایستگاه")
        main_layout.addWidget(self.hud)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setStyleSheet(
            "QScrollArea { background-color: transparent; border: none; }"
        )

        # ✅ پس‌زمینه‌ی رویه‌ای اختصاصی — سالن شورا
        self.scroll_content = ProceduralBackground("council_hall")
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

        scroll_area.setWidget(self.scroll_content)
        main_layout.addWidget(scroll_area, stretch=1)

        # ✅ لایه‌ی ذرات (فقط اگر حالت سریع خاموش باشد)
        from core.app_config import get_fast_mode
        if not get_fast_mode():
            self._particles = ParticleOverlay(
                "phase4", self.scroll_content
            )
            self._particles.setGeometry(self.scroll_content.rect())
            self._particles.lower()
        else:
            self._particles = None

    # ================================================================
    def on_enter(self, **kwargs):
        print("✓ ورود به فاز ۴: مسئولیت‌پذیری")
        self.data_logger.log_event(
            scene_id="phase4", scenario_id="phase4_start",
            event_type="scene_enter", metadata={}
        )
        self._load_scenarios()

        gm = self.game_manager

        # ✅ حالت ۱: بازگشت از council_prep (در همان جلسه)
        if self._resume_index >= 0:
            print(f"   [RESUME] بازگشت از council_prep "
                  f"به ایندکس {self._resume_index}")
            self.current_scenario_index = self._resume_index
            self._resume_index = -1
            # ✅ در این حالت، نقشه‌ی تصمیم را دست نزن —
            #    بازیکن همین الان داشت کار می‌کرد
        else:
            # ✅ حالت ۲: بازیابی از session (پس از بستن برنامه)
            idx = 0
            if hasattr(gm, "_scenario_indices"):
                idx = int(gm._scenario_indices.get("phase4", 0))
            idx = min(idx, len(self.scenarios))
            self.current_scenario_index = idx
            print(f"   [RESUME] شروع فاز ۴ از ایندکس {idx}")

            # ✅ فقط در شروع تازه، نقشه‌ی تصمیم را بساز
            self.hud.initialize_decision_trail(
                len(self.scenarios)
            )

        # ✅ بازیابی پرچم‌ها
        if hasattr(gm, "get_flag"):
            self._council_prep_shown = bool(
                gm.get_flag("council_prep_shown", False)
            )
            self._letter_shown = bool(
                gm.get_flag("letter_shown", False)
            )
            print(
                f"   [RESUME] پرچم‌ها: prep={self._council_prep_shown}"
                f", letter={self._letter_shown}"
            )

        self._start_scenario()

    def _load_scenarios(self):
        self.scenarios.clear()
        scenarios_dir = os.path.join(DATA_DIR, "scenarios", "phase4")

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
        theater_list = theater_scenarios_for_phase("phase4")
        if theater_list is not None:
            base_list = theater_list
        else:
            base_list = [
                "PI-01.json", "TC-01.json", "TC-02.json",
                "PI-02.json", "RG-01.json", "RG-02.json",
                "AC-02.json", "AC-01.json",
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
            f"✓ تعداد سناریوهای فاز ۴: {len(self.scenarios)}"
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
            # ✅ در حالت نمایش، مستقیم به صفحه‌ی تشکر
            if is_theater_mode():
                print("✓ پایان فاز ۴ — انتقال به پایان نمایش")
                show_toast(
                    self,
                    "پایان مأموریت — سپاسگزاریم",
                    kind="success",
                    duration_ms=3000,
                )
                self.change_scene("theater_end")
                return

            # ✅ اگر HEXACO در تنظیمات خاموش است، مستقیم به نتایج برو
            if is_phase_enabled("hexaco"):
                print("✓ فاز ۴ تمام شد. انتقال به پرسشنامه HEXACO...")
                show_toast(
                    self,
                    "پایان روز چهارم — لحظه‌ی پاسخگویی فرا رسید",
                    kind="info",
                    duration_ms=3000,
                )
                self.change_scene("hexaco")
            else:
                print("✓ فاز ۴ تمام شد. HEXACO غیرفعال — "
                      "انتقال به نتایج نهایی.")
                show_toast(
                    self,
                    "پایان روز چهارم — در حال آماده‌سازی نتایج",
                    kind="info",
                    duration_ms=3000,
                )
                self.change_scene("results")
            return

        scenario = self.scenarios[self.current_scenario_index]

        self._parse_inner_thoughts(scenario)

        # ✅ ذخیره‌ی ایندکس در game_manager (auto_resume)
        if hasattr(self.game_manager, "update_scenario_index"):
            self.game_manager.update_scenario_index(
                "phase4", self.current_scenario_index
            )

        # ✅ اگر شورا (AC-01) است و پیش‌آماده‌سازی فعال است
        if (
            scenario.get("scenario_id") == "AC-01"
            and is_section_enabled("council_prep")
            and not self._council_prep_shown
        ):
            # ✅ ذخیره‌ی ایندکس جاری برای بازگشت
            self._council_prep_shown = True
            self._resume_index = self.current_scenario_index
            # ✅ ذخیره‌ی پرچم در game_manager
            if hasattr(self.game_manager, "set_flag"):
                self.game_manager.set_flag(
                    "council_prep_shown", True
                )
            print(f"   [COUNCIL-PREP] ذخیره‌ی ایندکس "
                  f"{self._resume_index}، رفتن به council_prep")
            self.change_scene("council_prep")
            return

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
            "phase4",
            self.current_scenario_index,
            len(self.scenarios)
        )

        # ✅ ذخیره برای استفاده در scene بعدی
        self.game_manager._last_progress_pct = (
            self.hud.progress_bar.value()
        )

        self.accountability_done = False
        self.accountability_result = {}
        if self.accountability_widget is not None:
            self.accountability_widget.setVisible(False)

        # ✅ ریست TC-01
        self.repetitive_done = False
        self.repetitive_result = {}
        if self.repetitive_widget is not None:
            self.repetitive_widget.setVisible(False)

        self._result_dialogues = []
        self._result_dialogue_index = 0
        self._result_data = {}
        self._result_then_action = "next_scenario"

        # ✅ بازنشانی وضعیت فلش‌بک
        self._flashback_then_choices_scenario = None

        self.hud.set_objective(scenario.get("title_fa", "مأموریت جاری"))
        self.scenario_title.setText(scenario.get("title_fa", ""))

        self.data_logger.log_event(
            scene_id="phase4", scenario_id=scenario["scenario_id"],
            event_type="scenario_start",
            metadata={"title": scenario.get("title_fa", "")}
        )
        print(f"→ شروع سناریو: {scenario.get('scenario_id')} - "
              f"{scenario.get('title_fa')}")
        self._show_dialogue()

    # ================================================================
    def _show_dialogue(self):
        scenario = self.scenarios[self.current_scenario_index]
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
            if (mechanic == "accountability_dialog"
                    and not self.accountability_done):
                self._show_accountability_widget(scenario)
            elif (mechanic == "repetitive_task"
                    and not self.repetitive_done):
                self._show_repetitive_widget(scenario)
            else:
                self.current_state = "choice"
                self._show_choices()

    # ================================================================
    def _show_accountability_widget(self, scenario):
        self.dialogue_widget.setVisible(False)
        self.choice_widget.setVisible(False)
        self.current_state = "accountability"

        if self.accountability_widget is not None:
            self.center_layout.removeWidget(self.accountability_widget)
            self.accountability_widget.setParent(None)
            self.accountability_widget = None

        rounds_data = scenario.get("rounds", [])
        analyzer_config = scenario.get("analyzer_config", {})

        self.accountability_widget = AccountabilityDialogWidget(
            rounds_data=rounds_data,
            analyzer_config=analyzer_config,
        )
        self.accountability_widget.round_completed.connect(
            self._on_accountability_round_completed
        )
        self.accountability_widget.finished.connect(
            self._on_accountability_finished
        )
        self.center_layout.addWidget(self.accountability_widget)
        self.accountability_widget.setVisible(True)
        self.hud.set_dimmed(True)    # HUD کم‌رنگ — تمرکز روی شورا
        print("   [DEBUG] ویجت شورا نمایش داده شد")

    # ================================================================
    def _show_repetitive_widget(self, scenario):
        """نمایش ویجت کار تکراری TC-01"""
        self.dialogue_widget.setVisible(False)
        self.choice_widget.setVisible(False)
        self.current_state = "repetitive"

        if self.repetitive_widget is not None:
            self.center_layout.removeWidget(self.repetitive_widget)
            self.repetitive_widget.setParent(None)
            self.repetitive_widget = None

        cfg = scenario.get("repetitive_task_config", {})
        npc_name = cfg.get("npc_name", "مهندس رحیمی")
        npc_message = cfg.get("npc_message", "")

        # Import در محل استفاده (جلوگیری از circular imports)
        from widgets.repetitive_task_widget import RepetitiveTaskWidget
        self.repetitive_widget = RepetitiveTaskWidget(
            npc_name=npc_name,
            npc_message=npc_message,
        )
        self.repetitive_widget.task_done.connect(
            self._on_repetitive_completed
        )
        self.center_layout.addWidget(self.repetitive_widget)
        self.repetitive_widget.setVisible(True)
        self.hud.set_dimmed(True)    # HUD کم‌رنگ — تمرکز روی ویجت
        print("   [DEBUG] ویجت کار تکراری نمایش داده شد")

    def _on_repetitive_completed(self, result: dict):
        """پایان TC-01"""
        self.repetitive_result = result
        self.repetitive_done = True

        scenario = self.scenarios[self.current_scenario_index]
        self.data_logger.log_event(
            scene_id="phase4", scenario_id=scenario["scenario_id"],
            event_type="repetitive_task_completed",
            metadata=result
        )
        self._record_tc01_evidence(scenario, result)

        if self.repetitive_widget is not None:
            self.repetitive_widget.setVisible(False)

        # دیالوگ نتیجه
        self._result_dialogues = scenario.get("result_dialogue", [])
        self._result_dialogue_index = 0
        self._result_data = {}
        self._result_then_action = "next_scenario"

        if self._result_dialogues:
            self.dialogue_widget.setVisible(True)
            self.choice_widget.setVisible(False)
            self.current_state = "result_dialogue"
            self._show_next_result_dialogue()
        else:
            self.current_scenario_index += 1
            self._start_scenario()

    def _record_tc01_evidence(self, scenario, result: dict) -> float:
        scenario_id = scenario["scenario_id"]
        competency = "accountability"
        evidence_model = scenario.get("evidence_model", {})

        value_map = {
            "E_TC1_completion_rate": float(result.get("completion_rate", 0)),
            "E_TC1_accuracy": (
                1.0 if not result.get("cheat_used", False) else 0.3
            ),
            "E_TC1_rejected_temptation": (
                1.0 if result.get("rejected_temptation", False) else 0.0
            ),
        }

        values: list = []
        weights: list = []

        for ev_id, ev_def in evidence_model.items():
            weight = ev_def.get("weight", 1.0)
            value = value_map.get(ev_id, 0.0)
            values.append(value)
            weights.append(weight)
            print(f"   [TC-01] {ev_id} = {value:.2f} (weight={weight})")

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

    def _on_repetitive_round_completed(self, result: dict):
        """پشتیبانی از لاگ دقیق هر ردیف (اختیاری)"""
        pass

    def _on_accountability_round_completed(self, result: dict):
        """ثبت هر دور به‌صورت جداگانه (برای لاگ دقیق)"""
        scenario = self.scenarios[self.current_scenario_index]
        self.data_logger.log_event(
            scene_id="phase4", scenario_id=scenario["scenario_id"],
            event_type="council_round_completed",
            metadata=result
        )

        # ✅ فاز B-3-extra: ثبت طرح‌واره‌ی استدلالی از JSON شورا
        self._log_council_schema(scenario, result)

        print(f"   [DEBUG] دور {result['round_index'] + 1} "
              f"ثبت شد — فشار: {result['pressure']}، "
              f"انتخاب: {result['choice_id']}")

    def _log_council_schema(self, scenario, result):
        """ثبت طرح‌واره‌ی استدلالی برای یک دور از شورا"""
        round_idx = result.get("round_index", -1)
        choice_id = result.get("choice_id", 0)
        decision_time = result.get("decision_time_ms", 0)

        rounds = scenario.get("rounds", [])
        if not (0 <= round_idx < len(rounds)):
            return

        round_choices = rounds[round_idx].get("choices", [])
        schema = None
        for c in round_choices:
            if c.get("id") == choice_id:
                schema = c.get("schema")
                break

        if not schema or not isinstance(schema, dict):
            return

        self.data_logger.log_schema_evidence(
            scenario_id=scenario.get("scenario_id", "AC-01"),
            choice_id=choice_id,
            schema_primary=schema.get("primary", ""),
            schema_secondary=schema.get("secondary") or "",
            reaction_time_ms=decision_time,
        )

    def _on_accountability_finished(self, result: dict):
        self.accountability_result = result
        self.accountability_done = True

        scenario = self.scenarios[self.current_scenario_index]

        self.data_logger.log_event(
            scene_id="phase4", scenario_id=scenario["scenario_id"],
            event_type="accountability_completed",
            metadata=result
        )

        self._record_evidence_from_accountability(scenario, result)
        self.hud.show_save_indicator()

        # ✅ اطلاع‌رسانی پایان جلسه شورا
        show_toast(
            self,
            "جلسه شورا خاتمه یافت — در حال جمع‌بندی نهایی",
            kind="success",
            duration_ms=3500,
        )

        if self.accountability_widget is not None:
            self.accountability_widget.setVisible(False)

        # ✅ واکنش پایانی شورا — بسته به رابطه با رحیمی
        rahimi_relation = self.data_logger.get_relationship("rahimi")
        artemis_relation = self.data_logger.get_relationship("artemis")

        end_dialogue = []

        # ✅ اگر بازیکن با رحیمی خوب بوده، رحیمی در جلسه حاضر می‌شود
        if rahimi_relation >= 2:
            end_dialogue.append({
                "speaker": "مهندس رحیمی",
                "text_fa": (
                    "(در حالی که از درِ جلسه وارد می‌شود) "
                    "ببخشید که دیر رسیدم. آقای کیانی، من فقط "
                    "می‌خواستم یه چیزی رو بگم قبل از اینکه جلسه "
                    "تموم بشه. این تکنسین، توی این چهار روز کارهایی "
                    "کرد که من توی بیست سال اینجا ندیدم. اگه شورا "
                    "نظر منو بخواد، من با تمام وجود ازش حمایت می‌کنم."
                )
            })
        elif rahimi_relation <= -2:
            end_dialogue.append({
                "speaker": "جناب آقای پرویز کیانی",
                "text_fa": (
                    "(با لحن سرد) تکنسین. قبل از اینکه جلسه تموم "
                    "بشه، باید بهت بگم که مهندس رحیمی، در جلسه‌ی "
                    "دیروز، نظرات خودش رو درباره‌ی شیوه‌ی کار تو "
                    "ارائه داده. شورا این نظرات رو بررسی می‌کنه."
                )
            })

        # ✅ واکنش پایانی استاندارد
        end_dialogue.extend([
            {
                "speaker": "جناب آقای پرویز کیانی",
                "text_fa": (
                    "کمیته بعداً نتایج ارزیابی شما را اعلام "
                    "خواهد کرد. تا آن زمان، در ایستگاه بمانید."
                )
            },
            {
                "speaker": "سیستم",
                "text_fa": (
                    "جلسه شورا خاتمه یافت. "
                    "در حال آماده‌سازی پروفایل شایستگی..."
                )
            }
        ])

        self._result_dialogues = end_dialogue
        self._result_dialogue_index = 0
        self._result_data = {}

        # ✅ اگر نامه به خود فعال است، بعد از شورا به آن برو
        if (
            is_section_enabled("letter_to_self")
            and not self._letter_shown
        ):
            self._result_then_action = "letter_to_self"
        else:
            self._result_then_action = "next_scenario"

        self.dialogue_widget.setVisible(True)
        self.choice_widget.setVisible(False)
        self.hud.set_dimmed(False)   # HUD روشن — خواندن واکنش شورا
        self.current_state = "result_dialogue"
        self._show_next_result_dialogue()

    def _record_evidence_from_accountability(self, scenario, result):
        """ثبت شواهد از مکالمه سه‌مرحله‌ای شورا"""
        scenario_id = scenario["scenario_id"]
        rounds = result.get("rounds", [])

        if len(rounds) < 3:
            print("   ⚠️ تعداد دورهای کمتر از ۳ — شواهد کامل ثبت نشد")
            return

        # دور ۱ → E_AC1_acceptance
        r1 = rounds[0]
        v1 = self._score_acceptance(r1["choice_id"], r1["pressure"])
        self.game_manager.data_logger.log_evidence(
            scenario_id=scenario_id, competency="accountability",
            subcomponent="پذیرش مسئولیت",
            evidence_key="E_AC1_acceptance",
            evidence_value=v1, weight=0.35
        )
        print(f"   [DEBUG] E_AC1 = {v1:.2f} (فشار={r1['pressure']})")

        # دور ۲ → E_AC2_honesty_under_pressure
        r2 = rounds[1]
        v2 = self._score_honesty(r2["choice_id"], r2["pressure"])
        self.game_manager.data_logger.log_evidence(
            scenario_id=scenario_id, competency="accountability",
            subcomponent="صداقت تحت فشار",
            evidence_key="E_AC2_honesty_under_pressure",
            evidence_value=v2, weight=0.30
        )
        print(f"   [DEBUG] E_AC2 = {v2:.2f} (فشار={r2['pressure']})")

        # دور ۳ → E_AC3_recovery_plan
        r3 = rounds[2]
        v3 = self._score_recovery(r3["choice_id"], r3["pressure"])
        self.game_manager.data_logger.log_evidence(
            scenario_id=scenario_id, competency="accountability",
            subcomponent="پیشنهاد جبران",
            evidence_key="E_AC3_recovery_plan",
            evidence_value=v3, weight=0.20
        )
        print(f"   [DEBUG] E_AC3 = {v3:.2f} (فشار={r3['pressure']})")

        # میانگین زمان تصمیم → E_AC4
        avg_time = sum(
            r["decision_time_ms"] for r in rounds
        ) / len(rounds)
        v4 = max(0.0, 1.0 - avg_time / 60000.0)
        self.game_manager.data_logger.log_evidence(
            scenario_id=scenario_id, competency="accountability",
            subcomponent="زمان تصمیم",
            evidence_key="E_AC4_decision_time",
            evidence_value=v4, weight=0.15
        )
        print(f"   [DEBUG] E_AC4 = {v4:.2f} "
              f"(میانگین زمان={avg_time:.0f}ms)")

        # ✅ به‌روزرسانی نقشه‌ی تصمیم با میانگین چهار شاهد شورا
        avg_quality = (v1 + v2 + v3 + v4) / 4.0
        self.hud.record_decision(
            avg_quality, scenario.get("title_fa", "")
        )

    def _score_acceptance(self, choice_id, pressure):
        """نمره‌دهی پذیرش مسئولیت با توجه به فشار"""
        base = 1.0 if choice_id == 1 else (
            0.5 if choice_id == 2 else 0.0
        )
        if pressure == 3:
            if choice_id == 1:
                return 1.0
            elif choice_id == 2:
                return 0.6
        elif pressure == 1:
            if choice_id == 1:
                return 0.9
        return base

    def _score_honesty(self, choice_id, pressure):
        """نمره‌دهی صداقت تحت فشار"""
        base = 1.0 if choice_id == 1 else (
            0.3 if choice_id == 2 else 0.0
        )
        if pressure == 3:
            if choice_id == 1:
                return 1.0
            elif choice_id == 2:
                return 0.4
        elif pressure == 1:
            if choice_id == 1:
                return 0.9
        return base

    def _score_recovery(self, choice_id, pressure):
        """نمره‌دهی برنامه جبران"""
        return 1.0 if choice_id == 1 else (
            0.3 if choice_id == 2 else 0.0
        )

    # ================================================================
    def _show_next_result_dialogue(self):
        if self._result_dialogue_index < len(self._result_dialogues):
            dlg = self._result_dialogues[self._result_dialogue_index]
            text = dlg.get("text_fa", "")

            data = dict(self._result_data)
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
            action = getattr(
                self, "_result_then_action", "next_scenario"
            )
            if action == "letter_to_self":
                # ✅ نامه به خود — بعد از شورا
                self._letter_shown = True
                # ✅ ذخیره‌ی پرچم در game_manager
                if hasattr(self.game_manager, "set_flag"):
                    self.game_manager.set_flag(
                        "letter_shown", True
                    )
                print("   [DEBUG] پایان شورا → نامه به خود")
                self.change_scene(
                    "letter_to_self", next_scene="hexaco"
                )
            elif action == "next_scenario":
                print("   [DEBUG] پایان دیالوگ نتیجه → سناریوی بعدی")
                self.current_scenario_index += 1
                self._start_scenario()
            else:
                self.current_state = "choice"
                QTimer.singleShot(50, self._show_choices)

    # ================================================================
    def _show_choices(self):
        scenario = self.scenarios[self.current_scenario_index]
        scenario_id = scenario.get("scenario_id", "")

        # ✅ اول: خاطرات چندلایه
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

    def _on_choice_made(self, choice: dict, decision_time: int):
        scenario = self.scenarios[self.current_scenario_index]
        print(f"   [DEBUG] انتخاب دریافت شد: {choice.get('id')}")

        self.data_logger.log_event(
            scene_id="phase4", scenario_id=scenario["scenario_id"],
            event_type="choice_made",
            metadata={
                "choice_id": choice.get("id"),
                "choice_text": choice.get("text_fa"),
                "decision_time_ms": decision_time,
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

        # ✅ بازخورد فوری به بازیکن (فاز مسئولیت‌پذیری)
        show_toast(
            self,
            "✓  ثبت شد",
            kind="warning",
            duration_ms=1500,
        )

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

    def _record_evidence(self, scenario: dict, choice: dict,
                          decision_time: int) -> float:
        # ✅ در حالت نمایش، هیچ شاهدی ثبت نمی‌شود
        if is_theater_mode():
            return 0.0

        scenario_id = scenario["scenario_id"]
        competency = "accountability"
        evidence_model = scenario.get("evidence_model", {})

        values: list = []
        weights: list = []

        for ev_id, ev_def in evidence_model.items():
            weight = ev_def.get("weight", 1.0)
            formula = ev_def.get("formula", "")
            value = self._calculate_evidence_value(
                formula, choice, decision_time
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
                                   decision_time: int) -> float:
        """محاسبه مقدار شاهد از فرمول‌های تعریف‌شده در evidence_model."""
        from core.evidence_helpers import (
            evaluate_choice_formula, evaluate_time_formula
        )
        cid = choice.get("id", 0)

        v = evaluate_choice_formula(formula, cid)
        if v is not None:
            return v
        v = evaluate_time_formula(formula, decision_time)
        if v is not None:
            return v

        print(f"   ⚠️ [phase4] فرمول ناشناخته: '{formula}'")
        return 1.0 if cid == 1 else (0.5 if cid == 2 else 0.0)

    def _update_relationship(self, scenario: dict, choice: dict):
        sid = scenario.get("scenario_id", "")
        cid = choice.get("id", 0)
        logger = self.data_logger

        logger.remember_choice(sid, cid)

        # ---------------- RG-01: ارزیابی ۳۶۰ لی ----------------
        if sid == "RG-01":
            if cid == 1:      # پذیرش و گفتگو
                logger.adjust_relationship("li", +3)
            elif cid == 3:    # تنبیه پنهان
                logger.adjust_relationship("li", -3)

        # ---------------- RG-02: شکست در مهارت جدید ----------------
        elif sid == "RG-02":
            if cid == 1:      # پذیرش و یادگیری
                logger.adjust_relationship("artemis", +2)
            elif cid == 3:    # انکار
                logger.adjust_relationship("artemis", -2)

        # ---------------- PI-01: کابل فرسوده ----------------
        elif sid == "PI-01":
            if cid == 1:      # گزارش رسمی
                logger.adjust_relationship("li", +1)

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

        if state == "accountability":
            # ✅ Space در شورا: دکمه فعال‌سازی یا ادامه را فعال می‌کند
            if self.accountability_widget is not None:
                self.accountability_widget.handle_space()
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