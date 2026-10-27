
"""
منطق خالص آزمون برج هانوی — قابل استفاده در دسکتاپ و وب
==========================================================
کپی از web_app/engine/toh_logic.py
"""
"""
منطق خالص آزمون برج هانوی (Tower of Hanoi)
==============================================
- بدون هیچ وابستگی به NiceGUI یا PyQt
- کلاس ToHState با متدهای move_from، is_solved، validate
- کلاس ToHTrial برای نگه‌داری رویدادها

نسخه: 1.0.0
"""
import time
from dataclasses import dataclass, field


# ============================================================
# ساختار یک حرکت ثبت‌شده
# ============================================================
@dataclass
class ToHMove:
    trial_id: int
    move_number: int
    timestamp_ms: int
    disk_moved: int          # 1=کوچک، 2=متوسط، 3=بزرگ
    source_peg: str          # 'A' | 'B' | 'C'
    target_peg: str
    is_valid: bool
    reaction_time_ms: int = 0  # فاصله از حرکت قبلی


# ============================================================
# منطق آزمون
# ============================================================
class ToHLogic:
    """
    مدیریت وضعیت برج هانوی ۳ دیسکی.
    - start: A = [3,2,1]  (پایین به بالا)
    - goal:  C = [3,2,1]
    - min_moves = 7 = 2^3 - 1
    """
    MIN_MOVES = 7
    MAX_ATTEMPTS = 3

    def __init__(self, trial_id: int = 1):
        self.trial_id = trial_id
        self.reset()

    # ----------------------------------------------------------
    def reset(self):
        """بازنشانی به وضعیت شروع."""
        # pegs[peg_name] = [disk, ...] — آخر = دیسک بالایی
        self.pegs: dict = {
            "A": [3, 2, 1],
            "B": [],
            "C": [],
        }
        self.moves: list[ToHMove] = []
        self.invalid_attempts: int = 0
        self.is_solved: bool = False
        self.start_time_ms: int = int(time.time() * 1000)
        self.first_move_time_ms: int = 0
        self.last_move_time_ms: int = 0
        self.attempt_number: int = 1

    # ----------------------------------------------------------
    def get_top_disk(self, peg: str) -> int | None:
        """شماره‌ی دیسک بالایی میله یا None."""
        p = self.pegs.get(peg)
        if not p:
            return None
        return p[-1]

    # ----------------------------------------------------------
    def is_valid_move(
        self, source: str, target: str
    ) -> tuple[bool, str]:
        """
        بررسی اعتبار یک حرکت.
        Returns: (is_valid, error_message)
        """
        if source not in self.pegs or target not in self.pegs:
            return False, "میله‌ی نامعتبر"
        if source == target:
            return False, "مبدأ و مقصد یکی هستند"

        src_top = self.get_top_disk(source)
        if src_top is None:
            return False, "میله‌ی مبدأ خالی است"

        dst_top = self.get_top_disk(target)
        if dst_top is not None and src_top > dst_top:
            return (
                False,
                "دیسک بزرگ‌تر روی دیسک کوچک‌تر قرار نمی‌گیرد",
            )
        return True, ""

    # ----------------------------------------------------------
    def try_move(
        self, source: str, target: str
    ) -> tuple[bool, str]:
        """
        تلاش برای حرکت. اگر نامعتبر، فقط invalid را ثبت می‌کند.
        Returns: (moved, error_message)
        """
        if self.is_solved:
            return False, "آزمون حل شده است"

        now_ms = int(time.time() * 1000)
        is_valid, err = self.is_valid_move(source, target)

        # reaction time
        if self.moves:
            rt = now_ms - self.last_move_time_ms
        else:
            rt = now_ms - self.start_time_ms

        if not is_valid:
            self.invalid_attempts += 1
            self.moves.append(ToHMove(
                trial_id=self.trial_id,
                move_number=len(self.moves) + 1,
                timestamp_ms=now_ms,
                disk_moved=self.get_top_disk(source) or 0,
                source_peg=source,
                target_peg=target,
                is_valid=False,
                reaction_time_ms=rt,
            ))
            return False, err

        # انجام حرکت
        disk = self.pegs[source].pop()
        self.pegs[target].append(disk)

        if self.first_move_time_ms == 0:
            self.first_move_time_ms = now_ms
        self.last_move_time_ms = now_ms

        self.moves.append(ToHMove(
            trial_id=self.trial_id,
            move_number=len(self.valid_move_count()),
            timestamp_ms=now_ms,
            disk_moved=disk,
            source_peg=source,
            target_peg=target,
            is_valid=True,
            reaction_time_ms=rt,
        ))

        # بررسی حل
        if self.pegs["C"] == [3, 2, 1]:
            self.is_solved = True

        return True, ""

    # ----------------------------------------------------------
    def valid_move_count(self) -> list:
        """لیست حرکات معتبر."""
        return [m for m in self.moves if m.is_valid]

    # ----------------------------------------------------------
    def get_metrics(self) -> dict:
        """محاسبه‌ی شاخص‌های عملکردی."""
        valid_moves = len(self.valid_move_count())
        now_ms = int(time.time() * 1000)

        # planning_time: از شروع تا اولین حرکت معتبر
        if self.first_move_time_ms > 0:
            planning_ms = (
                self.first_move_time_ms - self.start_time_ms
            )
        else:
            planning_ms = now_ms - self.start_time_ms

        # execution_time: از اولین حرکت تا حل (یا الان)
        if self.first_move_time_ms > 0:
            end_ms = (
                self.last_move_time_ms
                if self.is_solved
                else now_ms
            )
            execution_ms = end_ms - self.first_move_time_ms
        else:
            execution_ms = 0

        efficiency = (
            self.MIN_MOVES / valid_moves
            if valid_moves > 0
            else 0.0
        )

        return {
            "solved": self.is_solved,
            "valid_moves": valid_moves,
            "invalid_attempts": self.invalid_attempts,
            "efficiency": round(
                min(1.0, efficiency), 3
            ),
            "planning_time_ms": planning_ms,
            "execution_time_ms": execution_ms,
            "total_time_ms": now_ms - self.start_time_ms,
            "attempt_number": self.attempt_number,
        }

    # ----------------------------------------------------------
    def serialize_moves(self) -> list[dict]:
        """لیست حرکات برای ذخیره در JSON."""
        return [
            {
                "trial_id": m.trial_id,
                "move_number": m.move_number,
                "timestamp_ms": m.timestamp_ms,
                "disk_moved": m.disk_moved,
                "source_peg": m.source_peg,
                "target_peg": m.target_peg,
                "is_valid": m.is_valid,
                "reaction_time_ms": m.reaction_time_ms,
            }
            for m in self.moves
        ]


# ============================================================
# محاسبه‌ی شواهد (Evidence Items)
# ============================================================
def compute_toh_evidence(metrics: dict) -> list[dict]:
    """
    محاسبه‌ی ۴ شاهد برای ثبت در web_evidence.
    """
    eff = float(metrics.get("efficiency", 0.0))
    invalid = int(metrics.get("invalid_attempts", 0))
    planning = int(metrics.get("planning_time_ms", 0))
    solved = bool(metrics.get("solved", False))

    # invalid_score: 0 invalid → 1.0، 10+ invalid → 0.0
    invalid_score = max(0.0, 1.0 - (invalid / 10.0))

    # planning_score: زمان ایده‌آل 3-15 ثانیه، خیلی کم/زیاد ضعیف
    if 3000 <= planning <= 15000:
        planning_score = 1.0
    elif 1500 <= planning <= 30000:
        planning_score = 0.7
    elif planning < 1500:
        planning_score = 0.3
    else:  # > 30s
        planning_score = 0.4

    return [
        {
            "evidence_key": "E_TOH_efficiency",
            "evidence_value": round(eff, 3),
            "weight": 0.40,
        },
        {
            "evidence_key": "E_TOH_invalid",
            "evidence_value": round(invalid_score, 3),
            "weight": 0.25,
        },
        {
            "evidence_key": "E_TOH_planning_time",
            "evidence_value": round(planning_score, 3),
            "weight": 0.20,
        },
        {
            "evidence_key": "E_TOH_solved",
            "evidence_value": 1.0 if solved else 0.0,
            "weight": 0.15,
        },
    ]