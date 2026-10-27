"""
مدیریت ثبت داده‌های رفتاری بازیکن در SQLite
مطابق با چارچوب Evidence-Centered Design (ECD)

این فایل از پروژه قبلی (Pygame) کپی شده و بدون تغییر کار می‌کند.
"""
import sqlite3
import json
import time
from datetime import datetime
from typing import Optional
from config import DB_PATH


class DataLogger:
    """ثبت‌کننده مرکزی داده‌های رفتاری"""

    def __init__(self, participant_id: str, random_seed: int = 0):
        self.participant_id = participant_id
        self.random_seed = random_seed
        self.session_start = time.time()
        self.conn = sqlite3.connect(DB_PATH)
        self.is_closed = False

        # ✅ سیستم رابطه با شخصیت‌ها (لایه‌ی روایی — مستقل از ECD)
        # مقدار بین -3 (سرد) تا +3 (گرم)
        self.relationships: dict = {
            "li": 0,
            "rahimi": 0,
            "artemis": 0,
        }

        # ✅ حافظه‌ی تصمیم‌های قبلی (برای پیشنهاد ۲ در آینده)
        self.choice_memory: dict = {}

        self._create_tables()
        self._start_session()

    # ================================================================
    # ساخت جداول
    # ================================================================
    def _create_tables(self):
        """ایجاد جداول پایگاه داده"""
        cursor = self.conn.cursor()

        # ۱. جدول شرکت‌کنندگان
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS participants (
                participant_id TEXT PRIMARY KEY,
                session_start REAL,
                session_end REAL,
                demographic_data TEXT,
                hexaco_scores TEXT,
                created_at TEXT
            )
        """)

        # Migration: ستون random_seed
        try:
            cursor.execute(
                "ALTER TABLE participants ADD COLUMN random_seed INTEGER"
            )
        except sqlite3.OperationalError:
            pass

        # ۲. جدول رویدادهای خام
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                participant_id TEXT,
                scene_id TEXT,
                scenario_id TEXT,
                event_type TEXT,
                timestamp REAL,
                reaction_time_ms INTEGER,
                metadata TEXT,
                FOREIGN KEY (participant_id) REFERENCES participants(participant_id)
            )
        """)

        # ✅ فاز A-2: Migration ستون sub_competency
        try:
            cursor.execute(
                "ALTER TABLE events ADD COLUMN sub_competency TEXT"
            )
        except sqlite3.OperationalError:
            pass

        # ۳. جدول شواهد رفتاری
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS evidence (
                evidence_id INTEGER PRIMARY KEY AUTOINCREMENT,
                participant_id TEXT,
                scenario_id TEXT,
                competency TEXT,
                subcomponent TEXT,
                evidence_key TEXT,
                evidence_value REAL,
                weight REAL,
                FOREIGN KEY (participant_id) REFERENCES participants(participant_id)
            )
        """)

        # ۴. جدول نمرات نهایی شایستگی
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS competency_scores (
                participant_id TEXT,
                competency TEXT,
                score REAL,
                confidence REAL,
                evidence_count INTEGER,
                PRIMARY KEY (participant_id, competency),
                FOREIGN KEY (participant_id) REFERENCES participants(participant_id)
            )
        """)

        # ۵. جدول نامه به خود
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS self_letters (
                letter_id INTEGER PRIMARY KEY AUTOINCREMENT,
                participant_id TEXT,
                content TEXT,
                word_count INTEGER,
                created_at REAL,
                FOREIGN KEY (participant_id) REFERENCES participants(participant_id)
            )
        """)

        # ۶. جدول پرسشنامه‌های تکمیلی
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS extended_questionnaires (
                participant_id TEXT PRIMARY KEY,
                hexaco_scores TEXT,
                crt_data TEXT,
                sd3_scores TEXT,
                social_desirability TEXT,
                created_at REAL,
                FOREIGN KEY (participant_id) REFERENCES participants(participant_id)
            )
        """)

        # ۷. جدول پرسشنامه‌ی پس‌نگر
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS postgame_feedback (
                participant_id TEXT PRIMARY KEY,
                close_answers TEXT,
                open_answers TEXT,
                demographic_extra TEXT,
                subscale_scores TEXT,
                overall_score REAL,
                created_at REAL,
                FOREIGN KEY (participant_id) REFERENCES participants(participant_id)
            )
        """)

        # ۸. جدول طرح‌واره‌های استدلالی (کلبرگ)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_evidence (
                evidence_id INTEGER PRIMARY KEY AUTOINCREMENT,
                participant_id TEXT,
                scenario_id TEXT,
                choice_id INTEGER,
                schema_primary TEXT,
                schema_secondary TEXT,
                reaction_time_ms INTEGER DEFAULT 0,
                created_at REAL,
                FOREIGN KEY (participant_id) REFERENCES participants(participant_id)
            )
        """)

        # ۹. جدول نمرات زیرمؤلفه‌ای (فاز E)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sub_competency_scores (
                participant_id TEXT,
                competency TEXT,
                sub_competency TEXT,
                score REAL,
                evidence_count INTEGER,
                PRIMARY KEY (
                    participant_id, competency, sub_competency
                ),
                FOREIGN KEY (participant_id)
                REFERENCES participants(participant_id)
            )
        """)

        self.conn.commit()

    # ================================================================
    # شروع جلسه
    # ================================================================
    def _start_session(self):
        """شروع جلسه شرکت‌کننده"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO participants
            (participant_id, session_start, created_at, random_seed)
            VALUES (?, ?, ?, ?)
        """, (
            self.participant_id, self.session_start,
            datetime.now().isoformat(), self.random_seed,
        ))
        self.conn.commit()

    # ================================================================
    # ثبت رویداد و شواهد
    # ================================================================
    def log_event(self, scene_id: str, scenario_id: str,
                  event_type: str, metadata: Optional[dict] = None):
        """ثبت یک رویداد رفتاری"""
        if self.is_closed:
            return
        cursor = self.conn.cursor()
        current_time = time.time()
        reaction_time = int((current_time - self.session_start) * 1000)

        cursor.execute("""
            INSERT INTO events
            (participant_id, scene_id, scenario_id, event_type,
             timestamp, reaction_time_ms, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            self.participant_id, scene_id, scenario_id,
            event_type, current_time, reaction_time,
            json.dumps(metadata or {}, ensure_ascii=False),
        ))
        self.conn.commit()

    def log_evidence(self, scenario_id: str, competency: str,
                     subcomponent: str, evidence_key: str,
                     evidence_value: float, weight: float = 1.0):
        """ثبت یک شاهد رفتاری"""
        if self.is_closed:
            return
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO evidence
            (participant_id, scenario_id, competency, subcomponent,
             evidence_key, evidence_value, weight)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            self.participant_id, scenario_id, competency,
            subcomponent, evidence_key, evidence_value, weight,
        ))
        self.conn.commit()

    def save_competency_score(self, competency: str, score: float,
                              confidence: float, evidence_count: int):
        """ذخیره نمره نهایی یک شایستگی"""
        if self.is_closed:
            return
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO competency_scores
            (participant_id, competency, score, confidence, evidence_count)
            VALUES (?, ?, ?, ?, ?)
        """, (
            self.participant_id, competency, score,
            confidence, evidence_count,
        ))
        self.conn.commit()

    def save_hexaco_scores(self, hexaco_data: dict):
        """ذخیره نمرات HEXACO برای روایی همگرا"""
        if self.is_closed:
            return
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE participants
            SET hexaco_scores = ?
            WHERE participant_id = ?
        """, (
            json.dumps(hexaco_data, ensure_ascii=False),
            self.participant_id,
        ))
        self.conn.commit()

    def save_demographic_data(self, demographic_data: dict):
        """ذخیره اطلاعات دموگرافیک شرکت‌کننده"""
        if self.is_closed:
            return
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE participants
            SET demographic_data = ?
            WHERE participant_id = ?
        """, (
            json.dumps(demographic_data, ensure_ascii=False),
            self.participant_id,
        ))
        self.conn.commit()

    def end_session(self, demographic_data: Optional[dict] = None):
        """پایان جلسه"""
        if self.is_closed:
            return
        cursor = self.conn.cursor()
        if demographic_data:
            cursor.execute("""
                UPDATE participants
                SET session_end = ?, demographic_data = ?
                WHERE participant_id = ?
            """, (
                time.time(),
                json.dumps(demographic_data, ensure_ascii=False),
                self.participant_id,
            ))
        else:
            cursor.execute("""
                UPDATE participants
                SET session_end = ?
                WHERE participant_id = ?
            """, (time.time(), self.participant_id))
        self.conn.commit()
        self.conn.close()
        self.is_closed = True

    # ================================================================
    # خواندن داده
    # ================================================================
    def get_all_events(self):
        """دریافت تمام رویدادهای شرکت‌کننده فعلی"""
        if self.is_closed:
            return []
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM events
            WHERE participant_id = ?
            ORDER BY timestamp
        """, (self.participant_id,))
        return cursor.fetchall()

    def get_evidence_by_competency(self, competency: str):
        """دریافت شواهد یک شایستگی"""
        if self.is_closed:
            return []
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM evidence
            WHERE participant_id = ? AND competency = ?
        """, (self.participant_id, competency))
        return cursor.fetchall()

    def get_evidence_by_key(self, scenario_id: str, evidence_key: str):
        """دریافت مقدار یک شاهد خاص بر اساس سناریو و کلید"""
        if self.is_closed:
            return None
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT evidence_value FROM evidence
            WHERE participant_id = ? AND scenario_id = ? AND evidence_key = ?
            LIMIT 1
        """, (self.participant_id, scenario_id, evidence_key))
        return cursor.fetchone()

    def get_all_evidence(self):
        """دریافت تمام شواهد شرکت‌کننده"""
        if self.is_closed:
            return []
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM evidence
            WHERE participant_id = ?
        """, (self.participant_id,))
        return cursor.fetchall()

    def get_competency_scores(self):
        """دریافت نمرات نهایی شایستگی‌ها"""
        if self.is_closed:
            return []
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT competency, score, confidence, evidence_count
            FROM competency_scores
            WHERE participant_id = ?
        """, (self.participant_id,))
        return cursor.fetchall()

    # ================================================================
    # بازیابی از session (resume)
    # ================================================================
    def restore_from_state(self, state: dict):
        """بازیابی روابط، حافظه و بذر تصادفی از state ذخیره‌شده."""
        saved_seed = state.get("random_seed", None)
        if saved_seed is not None:
            try:
                self.random_seed = int(saved_seed)
                print(
                    f"   [RESTORE] بذر تصادفی: {self.random_seed}"
                )
            except (TypeError, ValueError):
                pass

        rel = state.get("relationships", {}) or {}
        for key in ["li", "rahimi", "artemis"]:
            if key in rel:
                self.relationships[key] = int(rel[key])

        cm = state.get("choice_memory", {}) or {}
        self.choice_memory = dict(cm)

        print(
            f"   [RESTORE] روابط: {self.relationships}"
        )
        print(
            f"   [RESTORE] حافظه: {len(self.choice_memory)} تصمیم"
        )

    # ================================================================
    # پرسشنامه‌های تکمیلی (HEXACO + CRT + SD3 + SD)
    # ================================================================
    def save_extended_questionnaires(
        self,
        payload: dict | None = None,
        *,
        hexaco_scores: dict | None = None,
        crt_data: dict | None = None,
        sd3_scores: dict | None = None,
        social_desirability: dict | None = None,
    ):
        """
        ذخیره‌ی داده‌های پرسشنامه‌های تکمیلی.

        دو حالت فراخوانی:
          1. با یک دیکشنری واحد:
                save_extended_questionnaires({"hexaco_scores": ..., ...})
          2. با آرگومان‌های جداگانه:
                save_extended_questionnaires(hexaco_scores=..., crt_data=...)

        ترکیب هر دو مجاز است (kwargs بر payload اولویت دارد).
        """
        if self.is_closed:
            return

        data: dict = {}
        if isinstance(payload, dict):
            data.update(payload)
        data.update({
            k: v for k, v in {
                "hexaco_scores": hexaco_scores,
                "crt_data": crt_data,
                "sd3_scores": sd3_scores,
                "social_desirability": social_desirability,
            }.items() if v is not None
        })

        if not data:
            return

        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT participant_id FROM extended_questionnaires
            WHERE participant_id = ?
        """, (self.participant_id,))
        exists = cursor.fetchone() is not None

        def _dump(obj):
            if obj is None:
                return None
            return json.dumps(obj, ensure_ascii=False)

        if not exists:
            cursor.execute("""
                INSERT INTO extended_questionnaires
                (participant_id, hexaco_scores, crt_data,
                 sd3_scores, social_desirability, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                self.participant_id,
                _dump(data.get("hexaco_scores")),
                _dump(data.get("crt_data")),
                _dump(data.get("sd3_scores")),
                _dump(data.get("social_desirability")),
                time.time(),
            ))
        else:
            updates = []
            params = []
            for key in ("hexaco_scores", "crt_data",
                        "sd3_scores", "social_desirability"):
                if key in data:
                    updates.append(f"{key} = ?")
                    params.append(_dump(data[key]))

            if updates:
                params.append(self.participant_id)
                cursor.execute(
                    f"UPDATE extended_questionnaires SET "
                    f"{', '.join(updates)} "
                    f"WHERE participant_id = ?",
                    tuple(params),
                )

        self.conn.commit()

    # ================================================================
    # پرسشنامه‌ی پس‌نگر (Post-game Feedback)
    # ================================================================
    def save_postgame_feedback(
        self,
        payload: dict | None = None,
        *,
        close_answers: dict | None = None,
        open_answers: dict | None = None,
        demographic_extra: dict | None = None,
        subscale_scores: dict | None = None,
        overall_score: float | None = None,
    ):
        """
        ذخیره‌ی بازخورد پس از بازی.

        هم با یک دیکشنری واحد کار می‌کند و هم با آرگومان‌های جداگانه.
        کلیدهای شناخته‌شده: close_answers, open_answers,
        demographic_extra, subscale_scores, overall_score.
        کلید "overall" نیز به‌عنوان fallback برای overall_score پذیرفته می‌شود.
        """
        if self.is_closed:
            return

        data: dict = {}
        if isinstance(payload, dict):
            data.update(payload)
        data.update({
            k: v for k, v in {
                "close_answers": close_answers,
                "open_answers": open_answers,
                "demographic_extra": demographic_extra,
                "subscale_scores": subscale_scores,
                "overall_score": overall_score,
            }.items() if v is not None
        })

        if not data:
            return

        cursor = self.conn.cursor()

        def _dump(obj):
            if obj is None:
                return None
            return json.dumps(obj, ensure_ascii=False)

        raw_overall = data.get("overall_score")
        if raw_overall is None:
            raw_overall = data.get("overall")  # fallback
        try:
            overall_val = (
                float(raw_overall) if raw_overall is not None else None
            )
        except (TypeError, ValueError):
            overall_val = None

        cursor.execute("""
            INSERT OR REPLACE INTO postgame_feedback
            (participant_id, close_answers, open_answers,
             demographic_extra, subscale_scores, overall_score, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            self.participant_id,
            _dump(data.get("close_answers")),
            _dump(data.get("open_answers")),
            _dump(data.get("demographic_extra")),
            _dump(data.get("subscale_scores")),
            overall_val,
            time.time(),
        ))
        self.conn.commit()

    # ================================================================
    # سیستم رابطه با شخصیت‌ها (لایه‌ی روایی)
    # ================================================================
    def adjust_relationship(self, character_key: str, delta: int):
        """
        تنظیم رابطه با یک شخصیت.

        Args:
            character_key: یکی از "li"، "rahimi"، "artemis"
            delta: مقدار تغییر (معمولاً -2 تا +2)
        """
        if character_key not in self.relationships:
            return
        old = self.relationships[character_key]
        new = max(-3, min(3, old + delta))
        self.relationships[character_key] = new
        if old != new:
            print(f"   [REL] {character_key}: {old} → {new}")

    def get_relationship(self, character_key: str) -> int:
        """دریافت مقدار فعلی رابطه با یک شخصیت."""
        return self.relationships.get(character_key, 0)

    def remember_choice(self, scenario_id: str, choice_id: int):
        """ثبت تصمیم برای ارجاع در دیالوگ‌های آینده."""
        self.choice_memory[scenario_id] = choice_id

    def recall_choice(self, scenario_id: str) -> int:
        """به‌یاد آوردن تصمیم قبلی. اگر ثبت نشده باشد، -1 برمی‌گرداند."""
        return self.choice_memory.get(scenario_id, -1)

    # ================================================================
    # نامه به خود (لایه‌ی روایی — داده‌ی کیفی)
    # ================================================================
    def save_self_letter(self, content: str):
        """
        ذخیره‌ی نامه به خود.
        اگر content خالی باشد، یعنی بازیکن رد کرده.
        """
        if self.is_closed:
            return
        cursor = self.conn.cursor()
        word_count = len(content.split()) if content.strip() else 0
        cursor.execute("""
            INSERT INTO self_letters
            (participant_id, content, word_count, created_at)
            VALUES (?, ?, ?, ?)
        """, (
            self.participant_id, content, word_count, time.time()
        ))
        self.conn.commit()

    # ================================================================
    # فاز A-3: طرح‌واره‌های استدلالی (کلبرگ)
    # ================================================================
    def log_schema_evidence(
        self,
        scenario_id: str,
        choice_id: int,
        schema_primary: str,
        schema_secondary: str = "",
        reaction_time_ms: int = 0,
    ):
        """
        ثبت طرح‌واره‌ی استدلالی برای یک انتخاب.

        Args:
            scenario_id: شناسه‌ی سناریو (مثل "MC-01")
            choice_id: شماره‌ی گزینه‌ی انتخاب‌شده
            schema_primary: یکی از:
                - "personal_interest"
                - "maintaining_norms"
                - "postconventional"
            schema_secondary: طرح‌واره‌ی فرعی (اختیاری)
            reaction_time_ms: زمان تصمیم (اختیاری)
        """
        if self.is_closed:
            return
        valid_schemas = {
            "personal_interest",
            "maintaining_norms",
            "postconventional",
        }
        if schema_primary not in valid_schemas:
            print(
                f"⚠️ طرح‌واره‌ی نامعتبر: {schema_primary}"
            )
            return

        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO schema_evidence
            (participant_id, scenario_id, choice_id,
             schema_primary, schema_secondary,
             reaction_time_ms, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            self.participant_id,
            scenario_id,
            int(choice_id),
            schema_primary,
            schema_secondary or "",
            int(reaction_time_ms),
            time.time(),
        ))
        self.conn.commit()

    def get_schema_distribution(self) -> dict:
        """
        توزیع طرح‌واره‌ها در تمام سناریوها برای شرکت‌کننده‌ی فعلی.
        """
        if self.is_closed:
            return {}
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT schema_primary, COUNT(*)
            FROM schema_evidence
            WHERE participant_id = ?
            GROUP BY schema_primary
        """, (self.participant_id,))

        dist = {
            "personal_interest": 0,
            "maintaining_norms": 0,
            "postconventional": 0,
        }
        for row in cursor.fetchall():
            key, count = row[0], row[1]
            if key in dist:
                dist[key] = count
        dist["total"] = sum(
            dist[k] for k in [
                "personal_interest",
                "maintaining_norms",
                "postconventional",
            ]
        )
        return dist

    def get_schema_evidence_list(self) -> list:
        """لیست کامل شواهد طرح‌واره — برای تحلیل دقیق‌تر"""
        if self.is_closed:
            return []
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT scenario_id, choice_id,
                   schema_primary, schema_secondary,
                   reaction_time_ms, created_at
            FROM schema_evidence
            WHERE participant_id = ?
            ORDER BY created_at
        """, (self.participant_id,))
        return cursor.fetchall()

    # ================================================================
    # فاز E: نمرات زیرمؤلفه‌ای
    # ================================================================
    def save_sub_competency_scores(self, scores: dict):
        """
        ذخیره‌ی نمرات زیرمؤلفه‌ای.
        scores = {
            "honesty": {"transparency": {"score": 85.0, "count": 3}, ...},
            ...
        }
        """
        if self.is_closed:
            return
        cursor = self.conn.cursor()
        for competency, subs in scores.items():
            for sub_key, data in subs.items():
                score = data.get("score", 0.0)
                count = data.get("count", 0)
                cursor.execute("""
                    INSERT OR REPLACE INTO sub_competency_scores
                    (participant_id, competency, sub_competency,
                     score, evidence_count)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    self.participant_id, competency, sub_key,
                    float(score), int(count),
                ))
        self.conn.commit()

    # ================================================================
    # پایان روایی (Epilogue)
    # ================================================================
    def save_epilogue_summary(self, summary: dict):
        """
        ذخیره‌ی خلاصه‌ی پایان روایی.
        summary = {
            "code": "belonging" | "warm_farewell" | ...,
            "total": int,
            "relationships": {"li": int, "rahimi": int, "artemis": int},
        }
        """
        if self.is_closed:
            return
        try:
            self.log_event(
                scene_id="epilogue",
                scenario_id="epilogue_summary",
                event_type="epilogue_summary",
                metadata=summary,
            )
        except Exception as e:
            print(f"⚠️ save_epilogue_summary: {e}")
