"""
فاز ۲: قابلیت اعتماد (Trustworthiness)
شامل سناریوهای: CF-01, TR-01, BC-01
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
from widgets.toast_widget import show_toast
from widgets.particle_overlay import ParticleOverlay
from widgets.procedural_background import ProceduralBackground
from config import DATA_DIR, PHASE_THEMES
from core.app_config import (
    is_section_enabled, is_phase_enabled, next_enabled_phase_after,
    is_theater_mode, theater_scenarios_for_phase
)
from core.flashback_helper import get_flashback_text


class Phase2Scene(BaseScene):
    def __init__(self, game_manager):
        super().__init__(game_manager)

        # ✅ تم اختصاصی فاز — instance attribute
        self.phase_num: int = 2
        self.theme: dict = PHASE_THEMES[self.phase_num]

        self.scenarios = []
        self.current_scenario_index = 0
        self.current_state = "dialogue"
        self.scenario_start_time = 0
        self.dialogue_index = 0

        # ✅ دیالوگ‌های نتیجه
        self._result_dialogues: list = []
        self._result_dialogue_index = 0
        self._result_data: dict = {}
        self._result_then_action: str = "next_scenario"

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

        # QShortcut برای Space
        self._space_shortcut = QShortcut(
            QKeySequence(Qt.Key.Key_Space), self
        )
        self._space_shortcut.setContext(
            Qt.ShortcutContext.WindowShortcut
        )
        self._space_shortcut.activated.connect(self._on_space_shortcut)

        print("✓ Phase2Scene راه‌اندازی شد")

    def _setup_ui(self):
        main_layout = self.main_layout
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # HUD (ثابت در بالا)
        self.hud.set_mission("ایستگاه کاسپین")
        self.hud.set_phase("روز دوم: سایه‌های شک")
        self.hud.set_phase_color("#FF8F00")
        self.hud.set_objective("تحویل محموله در طوفان خورشیدی")
        main_layout.addWidget(self.hud)

        # QScrollArea برای محتوای قابل اسکرول
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setStyleSheet(
            "QScrollArea { background-color: transparent; border: none; }"
        )

        # ✅ پس‌زمینه‌ی رویه‌ای اختصاصی — راهرو
        scroll_content = ProceduralBackground("corridor")
        center_layout = QVBoxLayout(scroll_content)
        center_layout.setContentsMargins(20, 20, 20, 20)
        center_layout.setSpacing(15)

        self.scenario_title = QLabel()
        self.scenario_title.setStyleSheet(
            f"color: {self.theme['accent']}; "
            f"font-size: 28px; font-weight: bold;"
        )
        self.scenario_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(self.scenario_title)

        center_layout.addWidget(self.dialogue_widget)
        self.choice_widget.setVisible(False)
        center_layout.addWidget(self.choice_widget)

        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area, stretch=1)

        # ✅ لایه‌ی ذرات (فقط اگر حالت سریع خاموش باشد)
        from core.app_config import get_fast_mode
        if not get_fast_mode():
            self._particles = ParticleOverlay(
                "phase2", scroll_content
            )
            self._particles.setGeometry(scroll_content.rect())
            self._particles.lower()
        else:
            self._particles = None

    def on_enter(self, **kwargs):
        print("✓ ورود به فاز ۲: قابلیت اعتماد")
        self.data_logger.log_event(
            scene_id="phase2", scenario_id="phase2_start",
            event_type="scene_enter", metadata={}
        )
        self._load_scenarios()

        # ✅ پیش‌ساخت نقشه‌ی تصمیم بر اساس تعداد سناریوها
        self.hud.initialize_decision_trail(len(self.scenarios))

        # ✅ بازیابی ایندکس از game_manager
        gm = self.game_manager
        idx = 0
        if hasattr(gm, "_scenario_indices"):
            idx = int(gm._scenario_indices.get("phase2", 0))
        idx = min(idx, len(self.scenarios))
        print(f"   [RESUME] شروع فاز ۲ از ایندکس {idx}")
        self.current_scenario_index = idx
        self._start_scenario()

    def _load_scenarios(self):
        self.scenarios.clear()
        scenarios_dir = os.path.join(DATA_DIR, "scenarios", "phase2")

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
        theater_list = theater_scenarios_for_phase("phase2")
        if theater_list is not None:
            base_list = theater_list
        else:
            base_list = [
                "CF-01.json", "TR-01.json",
                "TR-02.json", "BC-01.json",
                "BC-02.json", "CF-02.json",
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
                    file_list.append(base)  # fallback به نسخه‌ی ساده
            else:
                file_list.append(base)

        # ✅ بارگذاری
        for filename in file_list:
            filepath = os.path.join(scenarios_dir, filename)
            if os.path.exists(filepath):
                try:
                    with open(
                        filepath, 'r', encoding='utf-8'
                    ) as f:
                        self.scenarios.append(json.load(f))
                    print(f"✓ سناریو بارگذاری شد: {filename}")
                except Exception as e:
                    print(
                        f"❌ خطا در بارگذاری {filename}: {e}"
                    )
            else:
                print(f"⚠️ فایل یافت نشد: {filepath}")
        print(
            f"✓ تعداد سناریوهای فاز ۲: {len(self.scenarios)}"
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
            print("✓ فاز ۲ تمام شد. انتقال به میان‌پرده روز سوم...")

            # ✅ اطلاع‌رسانی پایان فاز
            show_toast(
                self,
                "پایان روز دوم — سایه‌ها بلندتر شده‌اند",
                kind="success",
                duration_ms=3000,
            )

            # ✅ دیالوگ میان‌پرده بر اساس رابطه‌ی بازیکن با آرتمیس
            artemis_relation = self.data_logger.get_relationship("artemis")
            li_relation = self.data_logger.get_relationship("li")

            # فضاسازی حسی — راوی
            intro_line = (
                "ساعت ۰۹:۱۵ به وقت ایستگاه. آفتاب مصنوعی از پنجره‌ی "
                "باریک اتاق تحلیل می‌تابد و روی کاغذهای سفید، سایه‌های "
                "کشیده می‌اندازد. یک ماگ چای سرد، کنار ترمینال مانده."
            )

            # دیالوگ اصلی — آرتمیس
            if artemis_relation >= 2:
                artemis_text = (
                    "(با نگاهی صمیمانه، در حالی که پرونده‌ای را روی "
                    "میز می‌گذارد) خوب شد که هستی. راستش، این چند "
                    "روز که با هم کار کردیم، فهمیدم که می‌تونم روی "
                    "قضاوتت حساب کنم. این پرونده رو کسی جز تو نباید "
                    "ببینه."
                )
            elif artemis_relation <= -1:
                artemis_text = (
                    "(با لحن رسمی و فاصله‌دار، پرونده را روی میز "
                    "می‌گذارد) تکنسین. پرونده‌ی جدیدی روی میزه. "
                    "روش‌شناسی تحلیل رو من تعیین می‌کنم و لطفاً قبل "
                    "از هر اقدامی، با من هماهنگ کنید."
                )
            else:
                artemis_text = (
                    "باید علت ریشه‌ای رو پیدا کنیم. وگرنه این فاجعه "
                    "تکرار می‌شه. من با تو هستم، ولی زمان کمی داریم."
                )

            # دیالوگ دوم — اشاره به لی
            if li_relation >= 2:
                li_reference = (
                    "(آرتمیس، آرام‌تر) راستی، لی هم اصرار داشت توی "
                    "این مرحله کنارت باشه. گفت که بهت اعتماد داره."
                )
            elif li_relation <= -2:
                li_reference = (
                    "(آرتمیس مکث می‌کند. صدایش پایین‌تر می‌آید) "
                    "لی دیروز درخواست کرد که از تیم تحلیل منتقل "
                    "بشه. نمی‌دونم چرا، ولی فکر می‌کنم بهتره خودت "
                    "باهاش حرف بزنی."
                )
            else:
                li_reference = None

            # بازتاب پایانی — راوی
            outro_line = (
                "آرتمیس به سمت ترمینال برمی‌گردد و شروع می‌کند به "
                "کشیدن نمودارها. صدای تایپ، تنها صدایی است که در "
                "اتاق می‌پیچد."
            )

            # ساخت دنباله‌ی دیالوگ
            dialogue_seq = [
                {"speaker": "راوی", "text": intro_line},
                {"speaker": "دکتر آرتمیس", "text": artemis_text},
            ]
            if li_reference:
                dialogue_seq.append(
                    {"speaker": "دکتر آرتمیس", "text": li_reference}
                )
            dialogue_seq.append(
                {"speaker": "راوی", "text": outro_line}
            )

            # ✅ تشخیص فاز بعدی فعال
            next_phase = next_enabled_phase_after("phase2") or "results"

            # ✅ اگر میان‌پرده غیرفعال است، مستقیم برو
            if not is_section_enabled("interludes_extended"):
                self.change_scene(next_phase)
                return

            # ✅ ساخت kwargs میان‌پرده
            interlude_kwargs = {
                "next_scene": next_phase,
                "title": "روز سوم",
                "subtitle": "معمای داده‌ها",
                "body_text": (
                    "روز سوم. ایستگاه تثبیت شده، اما سؤالات بی‌پاسخ "
                    "باقی مانده‌اند. شش فایل لاگ روی میز پراکنده‌اند — "
                    "داده‌ها متناقض‌اند و ریشه‌ی واقعی بحران باید "
                    "پیدا شود."
                ),
                "dialogues": dialogue_seq,
                "video_path": "interlude_day3.png",
            }

            # ✅ اگر شب‌ها فعال است، اول شب برو
            if is_section_enabled("nights"):
                self.change_scene(
                    "night",
                    night_number=2,
                    next_scene="interlude",
                    next_scene_kwargs=interlude_kwargs,
                )
                return

            # حالت بدون شب
            self.change_scene("interlude", **interlude_kwargs)
            return

        scenario = self.scenarios[self.current_scenario_index]

        self._parse_inner_thoughts(scenario)

        # ✅ ذخیره‌ی ایندکس
        if hasattr(self.game_manager, "update_scenario_index"):
            self.game_manager.update_scenario_index(
                "phase2", self.current_scenario_index
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
            "phase2",
            self.current_scenario_index,
            len(self.scenarios)
        )

        # ✅ ذخیره برای استفاده در scene بعدی
        self.game_manager._last_progress_pct = (
            self.hud.progress_bar.value()
        )

        # بازنشانی دیالوگ‌های نتیجه
        self._result_dialogues = []
        self._result_dialogue_index = 0
        self._result_data = {}
        self._result_then_action = "next_scenario"

        # ✅ بازنشانی وضعیت فلش‌بک
        self._flashback_then_choices_scenario = None

        print(f"→ شروع سناریو: {scenario.get('scenario_id')} - {scenario.get('title_fa')}")

        self.hud.set_objective(scenario.get("title_fa", "مأموریت جاری"))
        self.scenario_title.setText(scenario.get("title_fa", ""))

        self.data_logger.log_event(
            scene_id="phase2", scenario_id=scenario["scenario_id"],
            event_type="scenario_start", metadata={"title": scenario.get("title_fa", "")}
        )
        self._show_dialogue()

    def _show_dialogue(self):
        scenario = self.scenarios[self.current_scenario_index]
        # ✅ ترکیب intro_sequence + dialogue_sequence
        intro_dlg = scenario.get("intro_sequence", [])
        main_dlg = scenario.get("dialogue_sequence", [])
        dialogues = intro_dlg + main_dlg

        if self.dialogue_index < len(dialogues):
            dlg = dialogues[self.dialogue_index]
            dialogue_text = dlg.get("text_fa", dlg.get("text", ""))

            print(f"   دیالوگ {self.dialogue_index + 1}/{len(dialogues)} - گوینده: {dlg.get('speaker', '')}")

            self.dialogue_widget.show_dialogue(
                speaker_name=dlg.get("speaker", ""),
                text=dialogue_text,
                emotion=dlg.get("emotion")  # ✅
            )
            self.dialogue_widget.setVisible(True)
            self.choice_widget.setVisible(False)
            self.hud.set_dimmed(False)   # HUD روشن — خواندن دیالوگ
            self.setFocus()
        else:
            # ✅ در حالت نمایش، مستقیم به گزینه‌ها (بدون مکانیک)
            print(f"   → پایان دیالوگ‌های سناریو، نمایش گزینه‌ها")
            self.current_state = "choice"
            self._show_choices()

    def _show_choices(self):
        scenario = self.scenarios[self.current_scenario_index]
        scenario_id = scenario.get("scenario_id", "")

        # ✅ بررسی فلش‌بک (فقط یک بار برای هر سناریو)
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
        print(f"   → {len(choices)} گزینه نمایش داده می‌شود")

        self.dialogue_widget.setVisible(False)
        self.choice_widget.setVisible(True)
        self.choice_widget.show_choices(
            choices, scenario.get("scenario_id", "")
        )

        self.hud.set_dimmed(True)    # HUD کم‌رنگ — انتخاب گزینه
        self.setFocus()

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
        print("   [FLASHBACK] نمایش خاطره‌ی تصمیم قبلی")

    def _on_choice_made(self, choice: dict, decision_time: int):
        scenario = self.scenarios[self.current_scenario_index]
        print(f"   ✓ انتخاب: {choice.get('text_fa', choice.get('text', ''))[:50]}...")

        self.data_logger.log_event(
            scene_id="phase2", scenario_id=scenario["scenario_id"],
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

        # ✅ بازخورد فوری به بازیکن (فاز قابلیت اعتماد)
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
            self.choice_widget.hide_choices()
            self.current_scenario_index += 1
            self._start_scenario()

    def _show_next_result_dialogue(self):
        """نمایش دیالوگ نتیجه بعدی"""
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

            print(f"   [DEBUG] دیالوگ نتیجه "
                  f"{self._result_dialogue_index + 1}/"
                  f"{len(self._result_dialogues)}")
            self.dialogue_widget.show_dialogue(
                speaker_name=dlg.get("speaker", ""), text=text
            )
            self.dialogue_widget.setVisible(True)
            self.hud.set_dimmed(False)   # HUD روشن — خواندن نتیجه
            self.setFocus()
        else:
            action = getattr(self, "_result_then_action", "next_scenario")
            if action == "next_scenario":
                print("   [DEBUG] پایان دیالوگ نتیجه → سناریوی بعدی")
                self.choice_widget.hide_choices()
                self.current_scenario_index += 1
                self._start_scenario()
            else:
                self.current_state = "choice"
                QTimer.singleShot(50, self._show_choices)

    def _record_evidence(self, scenario: dict, choice: dict,
                          decision_time: int) -> float:
        """ثبت شواهد + به‌روزرسانی نقشه‌ی تصمیم."""
        # ✅ در حالت نمایش، هیچ شاهدی ثبت نمی‌شود
        if is_theater_mode():
            return 0.0

        scenario_id = scenario["scenario_id"]
        competency = "trustworthiness"
        evidence_model = scenario.get("evidence_model", {})

        values: list = []
        weights: list = []

        # ✅ فرمول‌های deferred — در ResultsScene محاسبه می‌شوند
        DEFERRED_FORMULAS = {
            "consistency_computed",
            "deferred",
            "deferred_consistency",
        }

        for evidence_id, evidence_def in evidence_model.items():
            weight = evidence_def.get("weight", 1.0)
            formula = evidence_def.get("formula", "")

            # ✅ رد کردن فرمول‌های deferred
            if formula in DEFERRED_FORMULAS:
                print(
                    f"   [SKIP] {evidence_id}: فرمول deferred — "
                    f"در ResultsScene محاسبه می‌شود"
                )
                continue

            value = self._calculate_evidence_value(
                formula, choice, decision_time
            )
            values.append(value)
            weights.append(weight)

            self.game_manager.data_logger.log_evidence(
                scenario_id=scenario_id, competency=competency,
                subcomponent=evidence_def.get("description", ""),
                evidence_key=evidence_id, evidence_value=value,
                weight=weight
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

        print(f"   ⚠️ [phase2] فرمول ناشناخته: '{formula}'")
        return 1.0 if cid == 1 else (0.5 if cid == 2 else 0.0)

    def _update_relationship(self, scenario: dict, choice: dict):
        sid = scenario.get("scenario_id", "")
        cid = choice.get("id", 0)
        logger = self.data_logger

        logger.remember_choice(sid, cid)

        # ---------------- CF-01: تحویل محموله ----------------
        if sid == "CF-01":
            if cid == 1:      # رفتن از مسیر پرخطر
                logger.adjust_relationship("li", +2)
            elif cid == 3:    # منصرف شدن
                logger.adjust_relationship("li", -2)

        # ---------------- TR-01: نقص عایق سوخت ----------------
        elif sid == "TR-01":
            if cid == 1:      # گزارش فوری به مرکز
                logger.adjust_relationship("rahimi", -2)
                logger.adjust_relationship("artemis", +2)
            elif cid == 3:    # سکوت
                logger.adjust_relationship("artemis", -2)

        # ---------------- BC-01: اعتبار ویژه ----------------
        elif sid == "BC-01":
            if cid == 1:      # بخشیدن کل اعتبار
                logger.adjust_relationship("li", +3)
            elif cid == 3:    # نگه داشتن
                logger.adjust_relationship("li", -2)

        # ---------------- BC-02: سایه‌ی همکار ----------------
        elif sid == "BC-02":
            if cid == 1:      # پذیرش مسئولیت
                logger.adjust_relationship("li", +3)
            elif cid == 3:    # رد مسئولیت
                logger.adjust_relationship("li", -3)

        # ---------------- TR-02: سند پنهان ----------------
        elif sid == "TR-02":
            if cid == 1:      # افشای کامل
                logger.adjust_relationship("rahimi", -1)
                logger.adjust_relationship("artemis", +2)
            elif cid == 3:    # سکوت
                logger.adjust_relationship("artemis", -1)

    def _on_space_shortcut(self):
        if not self.isVisible():
            return
        state = self.current_state

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
                and self._particles is not None):
            # resize با scroll_content هم‌اندازه شود
            scroll_content = self._particles.parentWidget()
            if scroll_content is not None:
                self._particles.setGeometry(
                    scroll_content.rect()
                )