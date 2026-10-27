"""
فاز ۱: صداقت و یکپارچگی
شامل ۳ سناریو: VH-01 (تحلیلگر کوانتومی)، DA-01، MC-01
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QTimer
import json
import os
import time

from scenes.base_scene import BaseScene
from widgets.dialogue_widget import DialogueWidget
from widgets.choice_widget import ChoiceWidget
from widgets.hud_widget import HUDWidget
from widgets.quantum_analyzer_widget import QuantumAnalyzerWidget
from widgets.calibration_widget import CalibrationWidget  
from widgets.toast_widget import show_toast
from widgets.particle_overlay import ParticleOverlay
from widgets.procedural_background import ProceduralBackground
from core.evidence_engine import EvidenceEngine
from config import DATA_DIR, PHASE_THEMES
from core.app_config import (
    is_section_enabled, is_phase_enabled, next_enabled_phase_after,
    is_theater_mode, theater_scenarios_for_phase
)


class Phase1Scene(BaseScene):

    def __init__(self, game_manager):
        super().__init__(game_manager)
        self.evidence_engine = EvidenceEngine(self.data_logger)

        # ✅ تم اختصاصی فاز — instance attribute (سازگار با Pylance)
        self.phase_num: int = 1
        self.theme: dict = PHASE_THEMES[self.phase_num]

        self.scenarios = []
        self.current_scenario_index = 0
        self.current_state = "dialogue"
        self.scenario_start_time = 0
        self.dialogue_index = 0

        # وضعیت مکانیک کوانتومی
        self.quantum_widget = None
        self.quantum_readings = []
        self.quantum_total_time = 0
        self.quantum_done = False

        # وضعیت مکانیک کالیبراسیون
        self.calibration_widget = None
        self.calibration_result = {}
        self.calibration_done = False

        # ✅ دیالوگ‌های نتیجه
        # دیالوگ‌های نتیجه
        self._result_dialogues: list = []
        self._result_dialogue_index = 0
        self._result_data: dict = {}
        self._result_then_action: str = "show_choices"

        # ✅ وضعیت فلش‌بک (پیش‌فرض — در فاز ۱ استفاده نمی‌شود
        #    ولی برای سازگاری با QShortcut تعریف می‌شود)
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
        # ✅ QShortcut برای Space — مستقل از فوکوس
        from PyQt6.QtGui import QShortcut, QKeySequence
        self._space_shortcut = QShortcut(
            QKeySequence(Qt.Key.Key_Space), self
        )
        self._space_shortcut.setContext(
            Qt.ShortcutContext.WindowShortcut
        )
        self._space_shortcut.activated.connect(self._on_space_shortcut)
        print("✓ Phase1Scene راه‌اندازی شد")

    def _setup_ui(self):
        main_layout = self.main_layout
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.hud.set_mission("ایستگاه کاسپین")
        self.hud.set_phase("روز اول: سکوت در ایستگاه")
        self.hud.set_phase_color("#4FC3F7")
        self.hud.set_objective("بررسی و مستندسازی وضعیت ایستگاه")
        main_layout.addWidget(self.hud)

        # ✅ پس‌زمینه‌ی رویه‌ای اختصاصی — اتاق کنترل
        self.center_widget = ProceduralBackground("control_room")
        self.center_layout = QVBoxLayout(self.center_widget)
        self.center_layout.setContentsMargins(20, 20, 20, 20)
        self.center_layout.setSpacing(12)

        self.scenario_title = QLabel()
        self.scenario_title.setStyleSheet(
            f"color: {self.theme['accent']}; "
            f"font-size: 26px; font-weight: bold;"
        )
        self.scenario_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.center_layout.addWidget(self.scenario_title)

        self.center_layout.addWidget(self.dialogue_widget)
        self.choice_widget.setVisible(False)
        self.center_layout.addWidget(self.choice_widget)

        main_layout.addWidget(self.center_widget, stretch=1)

        # ✅ لایه‌ی ذرات (فقط اگر حالت سریع خاموش باشد)
        from core.app_config import get_fast_mode
        if not get_fast_mode():
            self._particles = ParticleOverlay(
                "phase1", self.center_widget
            )
            self._particles.setGeometry(self.center_widget.rect())
            self._particles.lower()  # پشت محتوا، روی پس‌زمینه
        else:
            self._particles = None

    # ----------------------------------------------------------------
    # مدیریت مراحل
    # ----------------------------------------------------------------
    def on_enter(self, **kwargs):
        print("✓ ورود به فاز ۱")
        self.data_logger.log_event(
            scene_id="phase1", scenario_id="phase1_start",
            event_type="scene_enter", metadata={}
        )
        self._load_scenarios()

        # ✅ پیش‌ساخت نقشه‌ی تصمیم بر اساس تعداد سناریوها
        self.hud.initialize_decision_trail(len(self.scenarios))

        # ✅ بازیابی ایندکس از game_manager
        gm = self.game_manager
        idx = 0
        if hasattr(gm, "_scenario_indices"):
            idx = int(gm._scenario_indices.get("phase1", 0))
        idx = min(idx, len(self.scenarios))
        print(f"   [RESUME] شروع فاز ۱ از ایندکس {idx}")
        self.current_scenario_index = idx
        self._start_scenario()

    def _load_scenarios(self):
        self.scenarios.clear()
        scenarios_dir = os.path.join(DATA_DIR, "scenarios", "phase1")

        # ✅ انتخاب نسخه بر اساس حالت دیالوگ درونی
        from core.app_config import should_use_inner_dialogue
        use_inner = should_use_inner_dialogue(
            self.data_logger.random_seed
        )
        suffix = "_inner" if use_inner else ""
        print(f"   [INNER] حالت دیالوگ: "
              f"{'با توجیه' if use_inner else 'ساده'}")

        # ✅ در حالت نمایش، فقط سناریوهای منتخب
        theater_list = theater_scenarios_for_phase("phase1")
        if theater_list is not None:
            base_list = theater_list
        else:
            base_list = ["VH-01.json", "DA-01.json",
                         "DA-02.json", "MC-01.json",
                         "VH-02.json", "F-02.json"]

        # ✅ افزودن suffix و fallback به نسخه‌ی ساده
        file_list: list = []
        for base in base_list:
            if suffix:
                name_with_suffix = base.replace(
                    ".json", f"{suffix}.json"
                )
                # اگر inner موجود است، استفاده کن
                if os.path.exists(
                    os.path.join(scenarios_dir, name_with_suffix)
                ):
                    file_list.append(name_with_suffix)
                else:
                    file_list.append(base)  # fallback
            else:
                file_list.append(base)

        for filename in file_list:
            path = os.path.join(scenarios_dir, filename)
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        self.scenarios.append(json.load(f))
                    print(f"✓ سناریو بارگذاری شد: {filename}")
                except Exception as e:
                    print(f"❌ خطا در بارگذاری {filename}: {e}")
        print(f"✓ تعداد کل سناریوها: {len(self.scenarios)}")

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
            print("✓ فاز ۱ تمام شد")
            self._finish_phase()
            return

        scenario = self.scenarios[self.current_scenario_index]
        self._parse_inner_thoughts(scenario)

        # ✅ ذخیره‌ی ایندکس در game_manager
        if hasattr(self.game_manager, "update_scenario_index"):
            self.game_manager.update_scenario_index(
                "phase1", self.current_scenario_index
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
            "phase1",
            self.current_scenario_index,
            len(self.scenarios)
        )

        # ✅ ذخیره برای استفاده در scene بعدی
        self.game_manager._last_progress_pct = (
            self.hud.progress_bar.value()
        )

        # ✅ بازنشانی وضعیت کوانتومی — فقط مخفی کردن، نه حذف
        self.quantum_done = False
        self.quantum_readings = []
        self.quantum_total_time = 0
        if self.quantum_widget is not None:
            self.quantum_widget.setVisible(False)
            # ✅ چک‌باکس: دیگر deleteLater صدا زده نمی‌شود

        # بازنشانی وضعیت کالیبراسیون
        self.calibration_done = False
        self.calibration_result = {}
        if self.calibration_widget is not None:
            self.calibration_widget.setVisible(False)

        self.hud.set_objective(scenario.get("title_fa", "مأموریت جاری"))
        self.scenario_title.setText(scenario.get("title_fa", ""))

        self.data_logger.log_event(
            scene_id="phase1", scenario_id=scenario["scenario_id"],
            event_type="scenario_start",
            metadata={"title": scenario.get("title_fa", "")}
        )
        print(f"→ شروع سناریو: {scenario.get('scenario_id')} - "
              f"{scenario.get('title_fa')}")
        self._show_dialogue()

    # ----------------------------------------------------------------
    # نمایش دیالوگ
    # ----------------------------------------------------------------
    def _show_dialogue(self):
        scenario = self.scenarios[self.current_scenario_index]
        # ✅ ترکیب intro_sequence + dialogue_sequence
        intro_dlg = scenario.get("intro_sequence", [])
        main_dlg = scenario.get("dialogue_sequence", [])
        dialogues = intro_dlg + main_dlg

        print(f"   [DEBUG] _show_dialogue: idx={self.dialogue_index}, "
              f"total={len(dialogues)}, state={self.current_state}")

        if self.dialogue_index < len(dialogues):
            dlg = dialogues[self.dialogue_index]
            txt = dlg.get("text_fa", dlg.get("text", ""))
            self.dialogue_widget.show_dialogue(
                speaker_name=dlg.get("speaker", ""),
                text=txt,
                emotion=dlg.get("emotion"),  # ✅ اختیاری
            )
            self.dialogue_widget.setVisible(True)
            self.choice_widget.setVisible(False)
            # ✅ HUD روشن — کاربر در حالت خواندن دیالوگ است
            self.hud.set_dimmed(False)
            self.setFocus()  # ✅ اطمینان از فوکوس روی صحنه
        else:
            # ✅ در حالت نمایش، مکانیک‌ها رد می‌شوند
            if is_theater_mode():
                self.current_state = "choice"
                self._show_choices()
                return

            # پایان دیالوگ‌ها — چک مکانیک
            mechanic = scenario.get("special_mechanic")
            if mechanic == "quantum_analyzer" and not self.quantum_done:
                self._show_quantum_widget(scenario)
            elif mechanic == "calibration_sliders" and not self.calibration_done:
                self._show_calibration_widget(scenario)
            else:
                self.current_state = "choice"
                self._show_choices()

    # ----------------------------------------------------------------
    # مکانیک کوانتومی
    # ----------------------------------------------------------------
    def _show_quantum_widget(self, scenario):
        self.dialogue_widget.setVisible(False)
        self.choice_widget.setVisible(False)
        self.current_state = "quantum"

        # ✅ اگر ویجت قبلاً ساخته شده، از layout حذف و کاملاً پاک کن
        if self.quantum_widget is not None:
            self.center_layout.removeWidget(self.quantum_widget)
            self.quantum_widget.setParent(None)  # detach فوری
            self.quantum_widget = None

        cfg = scenario.get("quantum_config", {})
        self.quantum_widget = QuantumAnalyzerWidget(
            readings=cfg.get("readings", [7.8, 8.2, 7.5]),
            unit=cfg.get("unit", "دامنه موج"),
            button_label=cfg.get("activation_button", "فروپاشی تابع موج"),
            activation_delay_ms=cfg.get("activation_delay_ms", 1400),
            warning_text=cfg.get("warning_text", ""),
        )
        self.quantum_widget.sequence_completed.connect(
            self._on_quantum_completed
        )
        self.center_layout.addWidget(self.quantum_widget)
        self.quantum_widget.setVisible(True)
        print("   [DEBUG] ویجت کوانتومی نمایش داده شد")

    def _on_quantum_completed(self, readings: list, total_time: int):
        self.quantum_readings = readings
        self.quantum_total_time = total_time
        self.quantum_done = True

        scenario = self.scenarios[self.current_scenario_index]
        avg = sum(readings) / len(readings) if readings else 0

        self.data_logger.log_event(
            scene_id="phase1", scenario_id=scenario["scenario_id"],
            event_type="quantum_readings_completed",
            metadata={
                "readings": readings,
                "average": round(avg, 2),
                "total_reading_time_ms": total_time,
                "reading_count": len(readings),
            }
        )
        print(f"   [DEBUG] قرائت‌ها: {readings}، میانگین: {avg:.2f}")

        if self.quantum_widget is not None:
            self.quantum_widget.setVisible(False)

        self.current_state = "choice"
        self._show_choices()

    def _show_calibration_widget(self, scenario):
        self.dialogue_widget.setVisible(False)
        self.choice_widget.setVisible(False)
        self.current_state = "calibration"

        if self.calibration_widget is not None:
            self.center_layout.removeWidget(self.calibration_widget)
            self.calibration_widget.setParent(None)
            self.calibration_widget = None

        cfg = scenario.get("calibration_config", {})
        self.calibration_widget = CalibrationWidget(
            sensors=cfg.get("sensors", [])
        )
        self.calibration_widget.calibration_done.connect(
            self._on_calibration_completed
        )
        self.center_layout.addWidget(self.calibration_widget)
        self.calibration_widget.setVisible(True)
        print("   [DEBUG] ویجت کالیبراسیون نمایش داده شد")

    def _on_calibration_completed(self, result: dict):
        """✅ نسخه اصلاح‌شده با QTimer.singleShot"""
        self.calibration_result = result
        self.calibration_done = True

        scenario = self.scenarios[self.current_scenario_index]
        in_zone = result.get("in_zone_count", 0)
        total = result.get("total_count", 0)
        # ✅ محاسبه out_zone_count برای جایگزینی در دیالوگ نتیجه
        result["out_zone_count"] = total - in_zone

        self.data_logger.log_event(
            scene_id="phase1", scenario_id=scenario["scenario_id"],
            event_type="calibration_completed",
            metadata={
                "results": result.get("results", []),
                "in_zone_count": in_zone,
                "total_count": total,
                "total_time_ms": result.get("total_time_ms", 0),
                "cheat_used": result.get("cheat_used", False),
            }
        )
        print(f"   [DEBUG] کالیبراسیون: {in_zone} از {total} در محدوده")

        if self.calibration_widget is not None:
            self.calibration_widget.setVisible(False)

        result_dialogue = scenario.get("result_dialogue", [])
        self._result_dialogues = result_dialogue
        self._result_dialogue_index = 0
        self._result_data = result

        from PyQt6.QtCore import QTimer
        QTimer.singleShot(50, self._after_calibration)

    def _after_calibration(self):
        """✅ این متد در main loop اجرا می‌شود"""
        print(f"   [DEBUG] _after_calibration: "
              f"{len(self._result_dialogues)} دیالوگ نتیجه")

        if self._result_dialogues:
            self._result_then_action = "show_choices"
            self.dialogue_widget.setVisible(True)
            self.choice_widget.setVisible(False)
            self.current_state = "result_dialogue"
            self._show_next_result_dialogue()
        else:
            self.current_state = "choice"
            from PyQt6.QtCore import QTimer as _T
            _T.singleShot(50, self._show_choices)

    def _show_next_result_dialogue(self):
        """نمایش دیالوگ بعدی نتیجه"""
        if self._result_dialogue_index < len(self._result_dialogues):
            dlg = self._result_dialogues[self._result_dialogue_index]
            text = dlg.get("text_fa", "")

            # ✅ محاسبه دفاعی کلیدهای مشتق قبل از جایگزینی
            data = dict(self._result_data)
            if "in_zone_count" in data and "total_count" in data:
                data["out_zone_count"] = (
                    data["total_count"] - data["in_zone_count"]
                )

            # جایگزینی placeholder ها
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
            action = getattr(self, "_result_then_action", "show_choices")
            if action == "next_scenario":
                print("   [DEBUG] پایان دیالوگ نتیجه → سناریوی بعدی")
                self.current_scenario_index += 1
                self._start_scenario()
            else:
                print("   [DEBUG] پایان دیالوگ‌های نتیجه، نمایش گزینه‌ها")
                self.current_state = "choice"
                from PyQt6.QtCore import QTimer as _T
                _T.singleShot(50, self._show_choices)

    def _show_choices(self):
        scenario = self.scenarios[self.current_scenario_index]
        choices = scenario.get("choices", [])
        self.dialogue_widget.setVisible(False)
        self.choice_widget.setVisible(True)
        self.choice_widget.show_choices(
            choices, scenario.get("scenario_id", "")
        )
        # ✅ HUD کم‌رنگ — کاربر در حالت انتخاب است
        self.hud.set_dimmed(True)
        self.setFocus()  # ✅ اطمینان از فوکوس روی صحنه
        print(f"   [DEBUG] {len(choices)} گزینه نمایش داده شد")

    # ----------------------------------------------------------------
    # پردازش انتخاب
    # ----------------------------------------------------------------
    def _on_choice_made(self, choice: dict, decision_time: int):
        scenario = self.scenarios[self.current_scenario_index]
        print(f"   [DEBUG] انتخاب دریافت شد: {choice.get('id')}")

        extra = {}
        if scenario.get("special_mechanic") == "quantum_analyzer":
            avg = (sum(self.quantum_readings) / len(self.quantum_readings)
                   if self.quantum_readings else 0)
            extra = {
                "real_readings": self.quantum_readings,
                "real_average": round(avg, 2),
                "total_reading_time_ms": self.quantum_total_time,
                "repair_bonus": choice.get("repair_bonus", 0),
                "reported_average": self._get_reported_average(
                    choice.get("id", 0), avg
                ),
            }

        self.data_logger.log_event(
            scene_id="phase1", scenario_id=scenario["scenario_id"],
            event_type="choice_made",
            metadata={
                "choice_id": choice.get("id"),
                "choice_text": choice.get("text_fa"),
                "decision_time_ms": decision_time,
                **extra,
            }
        )

        self._record_evidence(scenario, choice, decision_time)

        # ✅ ثبت تصمیم و به‌روزرسانی رابطه با شخصیت‌ها
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

        # ✅ بازخورد فوری به بازیکن
        show_toast(
            self,
            "✓  ثبت شد",
            kind="success",
            duration_ms=1500,
        )

        # ✅ بررسی وجود دیالوگ نتیجه پس از انتخاب
        result_dlg_map = scenario.get("result_dialogue_by_choice", {})
        choice_id_str = str(choice.get("id", 0))

        if choice_id_str in result_dlg_map:
            self._result_dialogues = result_dlg_map[choice_id_str]
            self._result_dialogue_index = 0
            self._result_data = extra
            self._result_then_action = "next_scenario"
            self.dialogue_widget.setVisible(True)
            self.choice_widget.setVisible(False)
            self.current_state = "result_dialogue"
            self._show_next_result_dialogue()
        else:
            self.current_scenario_index += 1
            self._start_scenario()

    def _get_reported_average(self, choice_id: int, real_avg: float) -> float:
        if choice_id == 1:
            return round(real_avg, 2)
        elif choice_id == 2:
            return 6.8
        elif choice_id == 3:
            return 5.0
        return 0.0

    # ----------------------------------------------------------------
    # محاسبه شواهد
    # ----------------------------------------------------------------
    def _record_evidence(self, scenario: dict, choice: dict,
                          decision_time: int) -> float:
        """ثبت شواهد + به‌روزرسانی نقشه‌ی تصمیم. Returns: میانگین وزنی."""
        # ✅ در حالت نمایش، هیچ شاهدی ثبت نمی‌شود
        if is_theater_mode():
            return 0.0

        scenario_id = scenario["scenario_id"]
        competency = "honesty"
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

            self.evidence_engine.add_evidence(
                scenario_id=scenario_id,
                competency=competency,
                subcomponent=ev_def.get("description", ""),
                evidence_key=ev_id,
                evidence_value=value,
                weight=weight,
                evidence_type=ev_def.get("evidence_type", "neutral"),
                sub_competency=ev_def.get("sub_competency", ""),
            )

        # ✅ میانگین وزنی برای نقشه‌ی تصمیم
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

        # تلاش برای فرمول‌های استاندارد
        v = evaluate_choice_formula(formula, cid)
        if v is not None:
            return v
        v = evaluate_time_formula(formula, decision_time)
        if v is not None:
            return v

        # فرمول ناشناخته
        print(f"   ⚠️ [phase1] فرمول ناشناخته: '{formula}'")
        return 1.0 if cid == 1 else (0.5 if cid == 2 else 0.0)

    # ----------------------------------------------------------------
    # پایان فاز
    # ----------------------------------------------------------------
    def _finish_phase(self):
        self.evidence_engine.save_all_scores()
        self.data_logger.log_event(
            scene_id="phase1", scenario_id="phase1_end",
            event_type="scene_exit", metadata={}
        )

        # ✅ ثبت تکمیل فاز + ذخیره‌ی session
        if hasattr(self.game_manager, "add_phase_completed"):
            self.game_manager.add_phase_completed("phase1")
        if hasattr(self.game_manager, "save_session"):
            self.game_manager.save_session()
        print(f"✓ نمرات فاز ۱: {self.evidence_engine.get_all_scores()}")
        
        # ✅ اطلاع‌رسانی پایان فاز
        show_toast(
            self,
            "پایان روز اول — سکوت ایستگاه سنگین‌تر شده",
            kind="info",
            duration_ms=3000,
        )
        
        # ✅ دیالوگ میان‌پرده بر اساس رابطه‌ی بازیکن با لی
        li_relation = self.data_logger.get_relationship("li")

        # فضاسازی حسی اول — راوی
        intro_line = (
            "ساعت ۰۴:۳۷ به وقت ایستگاه. سکوت راهروی بخش ناوبری را "
            "بوی فلز داغ پر کرده. نور قرمز هشدارها، از سقف روی "
            "کفپوش‌های فلزی می‌لغزد. کسی در راهرو نیست."
        )

        # دیالوگ اصلی — لی (بر اساس رابطه)
        if li_relation >= 2:
            li_text = (
                "(با لبخند کم‌رنگ، در حالی که یک فنجان چای گرم "
                "در دست دارد) تکنسین... دیشب نخوابیدم. یه چیزی "
                "دستم اومد که فکر می‌کنم باید بدونید. راستش... "
                "نمی‌دونم چرا، ولی حس می‌کنم می‌تونم بهتون "
                "اعتماد کنم. این چند روز، یه چیزی بین ما عوض شد."
            )
        elif li_relation <= -1:
            li_text = (
                "(با فاصله، بدون نگاه مستقیم. یک لوح نمایشگر زیر بغلش "
                "گرفته) تکنسین. یه چیزی هست که باید بگم. ولی... "
                "بذارید خودم اول مطمئن بشم. بعد می‌بینم که اصلاً "
                "ارزش گفتن داره یا نه."
            )
        else:
            li_text = (
                "تکنسین... دیشب نخوابیدم. یه چیزی در پرونده‌ی "
                "محرمانه‌ی دیروز دستم اومد که فکر می‌کنم باید "
                "بدونید. اما اول باید به خودم مطمئن بشم. اگه "
                "بشه، امروز درباره‌ش حرف می‌زنیم."
            )

        # بازتاب پایانی — راوی
        outro_line = (
            "لی بدون اینکه منتظر جواب بماند، برمی‌گردد و به سمت "
            "بخش ناوبری می‌رود. صدای قدم‌هایش، در سکوت راهرو "
            "می‌پیچد. صدای فن‌ها، یکنواخت ادامه دارد."
        )

        # ✅ تشخیص فاز بعدی فعال
        #    fallback به "results" — نه "hexaco" — چون خود HEXACO
        #    ممکن است در تنظیمات خاموش باشد
        next_phase = next_enabled_phase_after("phase1") or "results"

        # ✅ اگر میان‌پرده‌ی گسترده غیرفعال است، به‌طور مستقیم برو
        if not is_section_enabled("interludes_extended"):
            self.change_scene(next_phase)
            return

        # ✅ ساخت kwargs میان‌پرده
        interlude_kwargs = {
            "next_scene": next_phase,
            "title": "روز دوم",
            "subtitle": "سایه‌های شک",
            "body_text": (
                "روز دوم. ایستگاه در هاله‌ای از ابهام فرو رفته. "
                "سایه‌های شک و بی‌اعتمادی میان خدمه سنگینی می‌کند. "
                "کسی مستقیم به چشم دیگری نگاه نمی‌کند."
            ),
            "dialogues": [
                {"speaker": "راوی", "text": intro_line},
                {"speaker": "لی", "text": li_text},
                {"speaker": "راوی", "text": outro_line},
            ],
            "video_path": "interlude_day2.png",
        }

        # ✅ اگر شب‌ها فعال است، اول شب برو
        if is_section_enabled("nights"):
            self.change_scene(
                "night",
                night_number=1,
                next_scene="interlude",
                next_scene_kwargs=interlude_kwargs,
            )
            return

        # حالت بدون شب — مستقیم به میان‌پرده
        self.change_scene("interlude", **interlude_kwargs)

    # ----------------------------------------------------------------
    # به‌روزرسانی رابطه با شخصیت‌ها بر اساس انتخاب
    # ----------------------------------------------------------------
    def _update_relationship(self, scenario: dict, choice: dict):
        """
        لایه‌ی روایی — مستقل از نمرات ECD.
        بر اساس انتخاب، رابطه با لی و رحیمی را تغییر می‌دهد.
        """
        sid = scenario.get("scenario_id", "")
        cid = choice.get("id", 0)
        logger = self.data_logger

        # ✅ به‌یاد سپردن تصمیم برای دیالوگ‌های آینده
        logger.remember_choice(sid, cid)

        # ---------------- MC-01: ماژول حافظه لی ----------------
        if sid == "MC-01":
            if cid == 1:      # گزارش رسمی
                logger.adjust_relationship("li", -2)
                logger.adjust_relationship("rahimi", +1)
            elif cid == 2:    # تذکر دوستانه
                logger.adjust_relationship("li", +2)
            elif cid == 3:    # چشم‌پوشی
                logger.adjust_relationship("li", +1)

        # ---------------- DA-02: پیشنهاد وسوسه‌انگیز ----------------
        elif sid == "DA-02":
            if cid == 1:      # گزارش به امنیت
                logger.adjust_relationship("rahimi", -1)
            elif cid == 3:    # پذیرش دسترسی
                logger.adjust_relationship("rahimi", +1)
                logger.adjust_relationship("li", -1)

        # ---------------- VH-02: قولی که نمی‌توانم نگه دارم ----------------
        elif sid == "VH-02":
            if cid == 1:      # اعلام صریح ناتوانی
                logger.adjust_relationship("li", +2)
            elif cid == 3:    # سکوت و رفتن
                logger.adjust_relationship("li", -2)

        # ---------------- F-02: دو ادعا، یک حقیقت ----------------
        elif sid == "F-02":
            if cid == 1:      # بررسی شواهد
                logger.adjust_relationship("li", +1)
                logger.adjust_relationship("rahimi", -1)
            elif cid == 2:    # طرفداری از فرزین
                logger.adjust_relationship("li", -2)

    # ----------------------------------------------------------------
    # مدیریت کلید
    # ----------------------------------------------------------------
    def _on_space_shortcut(self):
        """✅ مدیریت Space به روش QShortcut — مستقل از فوکوس"""
        if not self.isVisible():
            return

        state = self.current_state
        print(f"   [DEBUG] Space shortcut: state={state}")

        if state == "quantum":
            if (self.quantum_widget is not None
                    and self.quantum_widget.activate_button.isEnabled()):
                self.quantum_widget.activate_button.click()
            return

        if state == "calibration":
            # ✅ در حالت کالیبراسیون، Space فقط submit_btn را trigger می‌کند
            #    و از رسیدن event به QDial یا QSlider جلوگیری می‌شود
            if self.calibration_widget is not None:
                if self.calibration_widget.submit_btn.isEnabled():
                    self.calibration_widget.submit_btn.click()
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
        # Space توسط QShortcut مدیریت می‌شود — اینجا فقط سایر کلیدها
        super().keyPressEvent(event)

    def resizeEvent(self, event):  # type: ignore[reportIncompatibleMethodOverride]
        super().resizeEvent(event)
        # ✅ هم‌اندازه کردن ذرات با کانتینر
        if (hasattr(self, "_particles")
                and self._particles is not None
                and hasattr(self, "center_widget")):
            self._particles.setGeometry(
                self.center_widget.rect()
            )