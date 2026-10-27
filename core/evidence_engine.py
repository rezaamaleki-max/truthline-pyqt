"""
موتور محاسبه شواهد و نمرات شایستگی (Evidence-Centered Design)
این کلاس مسئول تبدیل رفتارهای بازیکن به نمرات کمی برای هر شایستگی است.

نسخه: 2.0.0
"""
from typing import Dict, List, Optional
import time


class EvidenceEngine:
    """موتور محاسبه شواهد و نمرات شایستگی"""
    
    # چهار شایستگی اصلی بازی
    COMPETENCIES = [
        "honesty",           # صداقت و یکپارچگی
        "trustworthiness",   # قابلیت اعتماد
        "problem_solving",   # حل مسئله
        "accountability"     # مسئولیت‌پذیری
    ]
    
    # نام‌های فارسی برای نمایش
    COMPETENCY_NAMES_FA = {
        "honesty": "صداقت و یکپارچگی",
        "trustworthiness": "قابلیت اعتماد",
        "problem_solving": "حل مسئله",
        "accountability": "مسئولیت‌پذیری"
    }
    
    def __init__(self, data_logger):
        """
        مقداردهی اولیه موتور شواهد
        
        Args:
            data_logger: نمونه DataLogger برای ثبت داده‌ها
        """
        self.data_logger = data_logger
        
        # ذخیره موقت شواهد جمع‌آوری‌شده برای هر شایستگی
        # ساختار: {"honesty": [{"key": "...", "value": 0.8, "weight": 0.5}, ...]}
        self.evidence_buffer: Dict[str, List[dict]] = {
            comp: [] for comp in self.COMPETENCIES
        }
        
        # نمرات تجمعی هر شایستگی (بین ۰ تا ۱۰۰)
        self.competency_scores: Dict[str, float] = {
            comp: 0.0 for comp in self.COMPETENCIES
        }
        
        # تعداد شواهد ثبت‌شده برای هر شایستگی
        self.evidence_counts: Dict[str, int] = {
            comp: 0 for comp in self.COMPETENCIES
        }
        
        print("✓ EvidenceEngine راه‌اندازی شد")
    
    def add_evidence(self, scenario_id: str, competency: str,
                     subcomponent: str, evidence_key: str,
                     evidence_value: float, weight: float = 1.0,
                     evidence_type: str = "neutral",
                     sub_competency: str = ""):
        """
        افزودن یک شاهد رفتاری جدید

        Args:
            scenario_id: شناسه سناریو
            competency: نام شایستگی (یکی از COMPETENCIES)
            subcomponent: زیرمؤلفه شایستگی (برای سازگاری با کد قدیم)
            evidence_key: کلید شاهد
            evidence_value: مقدار شاهد (بین ۰ تا ۱)
            weight: وزن شاهد
            evidence_type: "outcome" | "process" | "neutral"
            sub_competency: کلید زیرمؤلفه‌ی ساختاری (فاز E)
        """
        if competency not in self.COMPETENCIES:
            print(f"⚠️ شایستگی نامعتبر: {competency}")
            return

        # محدود کردن مقدار
        evidence_value = max(0.0, min(1.0, evidence_value))

        # اعتبارسنجی نوع
        if evidence_type not in ("outcome", "process", "neutral"):
            evidence_type = "neutral"

        self.evidence_buffer[competency].append({
            "scenario_id": scenario_id,
            "subcomponent": subcomponent,
            "sub_competency": sub_competency,  # ✅ فاز E
            "key": evidence_key,
            "value": evidence_value,
            "weight": weight,
            "evidence_type": evidence_type,   # ✅ فاز D
            "timestamp": time.time(),
        })
        
        # به‌روزرسانی تعداد شواهد
        self.evidence_counts[competency] += 1
        
        # ثبت در پایگاه داده
        self.data_logger.log_evidence(
            scenario_id=scenario_id,
            competency=competency,
            subcomponent=subcomponent,
            evidence_key=evidence_key,
            evidence_value=evidence_value,
            weight=weight
        )
        
        # محاسبه مجدد نمره تجمعی
        self._recalculate_score(competency)
    
    def _recalculate_score(self, competency: str):
        """
        محاسبه مجدد نمره تجمعی یک شایستگی.

        فرمول:
            score = (outcome_score × 0.60) +
                    (process_score × 0.30) +
                    (neutral_score × 0.10)
        """
        evidence_list = self.evidence_buffer[competency]

        if not evidence_list:
            self.competency_scores[competency] = 0.0
            return

        # ✅ فاز D: جدا کردن شواهد بر اساس نوع
        outcome_ev = [
            e for e in evidence_list
            if e.get("evidence_type") == "outcome"
        ]
        process_ev = [
            e for e in evidence_list
            if e.get("evidence_type") == "process"
        ]
        neutral_ev = [
            e for e in evidence_list
            if e.get("evidence_type") not in ("outcome", "process")
        ]

        def weighted_mean(evs: list) -> Optional[float]:
            """میانگین وزنی یک گروه (۰ تا ۱۰۰)"""
            if not evs:
                return None
            total_w = sum(e["weight"] for e in evs)
            if total_w == 0:
                return 0.0
            weighted_sum = sum(
                e["value"] * e["weight"] for e in evs
            )
            return (weighted_sum / total_w) * 100

        outcome_score = weighted_mean(outcome_ev)
        process_score = weighted_mean(process_ev)
        neutral_score = weighted_mean(neutral_ev)

        # ✅ ترکیب با وزن‌های پویا
        components = []
        if outcome_score is not None:
            components.append((outcome_score, 0.60))
        if process_score is not None:
            components.append((process_score, 0.30))
        if neutral_score is not None:
            components.append((neutral_score, 0.10))

        if not components:
            self.competency_scores[competency] = 0.0
            return

        # نرمال‌سازی وزن‌ها
        total_weight = sum(w for _, w in components)
        score = sum(s * w for s, w in components) / total_weight

        self.competency_scores[competency] = round(score, 2)

    def get_score_breakdown(self, competency: str) -> dict:
        """
        جزئیات محاسبه‌ی نمره (برای دیباگ و تحلیل).
        Returns: {
            "outcome": (score, weight, count),
            "process": (score, weight, count),
            "neutral": (score, weight, count),
            "final": score,
        }
        """
        evidence_list = self.evidence_buffer[competency]
        result = {
            "outcome": None,
            "process": None,
            "neutral": None,
            "final": self.competency_scores.get(competency, 0.0),
        }
        for etype, key in [
            ("outcome", "outcome"),
            ("process", "process"),
            ("neutral", "neutral"),
        ]:
            evs = [
                e for e in evidence_list
                if (
                    e.get("evidence_type") == etype
                    if etype != "neutral"
                    else e.get("evidence_type") not in ("outcome", "process")
                )
            ]
            if evs:
                total_w = sum(e["weight"] for e in evs)
                if total_w > 0:
                    s = sum(e["value"] * e["weight"] for e in evs)
                    score = (s / total_w) * 100
                    result[key] = {
                        "score": round(score, 2),
                        "count": len(evs),
                        "total_weight": round(total_w, 2),
                    }
        return result
    
    def get_score(self, competency: str) -> float:
        """دریافت نمره فعلی یک شایستگی (بین ۰ تا ۱۰۰)"""
        return self.competency_scores.get(competency, 0.0)
    
    def get_all_scores(self) -> Dict[str, float]:
        """دریافت نمرات تمام شایستگی‌ها"""
        return self.competency_scores.copy()
    
    def get_score_level(self, score: float) -> str:
        """
        تبدیل نمره عددی به سطح کیفی
        
        Args:
            score: نمره بین ۰ تا ۱۰۰
            
        Returns:
            سطح کیفی (بسیار خوب، خوب، متوسط، نیاز به توسعه)
        """
        if score >= 85:
            return "بسیار خوب"
        elif score >= 70:
            return "خوب"
        elif score >= 50:
            return "متوسط"
        else:
            return "نیاز به توسعه"
    
    def get_interpretation(self, competency: str) -> str:
        """
        دریافت تفسیر کیفی نمره یک شایستگی
        """
        score = self.get_score(competency)
        level = self.get_score_level(score)
        name_fa = self.COMPETENCY_NAMES_FA.get(competency, competency)
        
        interpretations = {
            "honesty": {
                "بسیار خوب": f"شما به شکلی استثنایی پایبند به حقیقت و اصول اخلاقی هستید.",
                "خوب": f"شما فردی صادق و قابل اتکا هستید، هرچند گاهی تحت فشار دچار تردید می‌شوید.",
                "متوسط": f"صداقت شما تا حد زیادی به شرایط وابسته است.",
                "نیاز به توسعه": f"منافع شخصی معمولاً بر ملاحظات اخلاقی شما اولویت دارد."
            },
            "trustworthiness": {
                "بسیار خوب": f"شما به شکلی قابل اتکا به تعهدات خود پایبند هستید.",
                "خوب": f"شما در اکثر شرایط قابل اعتماد هستید.",
                "متوسط": f"پایبندی شما به تعهدات نوسان دارد.",
                "نیاز به توسعه": f"شما در حفظ تعهدات و شفافیت نیاز به بهبود دارید."
            },
            "problem_solving": {
                "بسیار خوب": f"شما تحلیل‌گر نظام‌مندی هستید که به راحتی مسائل پیچیده را حل می‌کنید.",
                "خوب": f"شما در حل مسائل توانمند هستید اما گاهی عجولانه عمل می‌کنید.",
                "متوسط": f"شما در تشخیص ریشه مسائل نیاز به تقویت دارید.",
                "نیاز به توسعه": f"شما در تحلیل نظام‌مند مسائل نیاز به آموزش دارید."
            },
            "accountability": {
                "بسیار خوب": f"شما مسئولیت‌پذیری بالایی دارید و از اشتباهات خود درس می‌گیرید.",
                "خوب": f"شما در پذیرش مسئولیت قابل اتکا هستید.",
                "متوسط": f"شما گاهی از پذیرش مسئولیت اجتناب می‌کنید.",
                "نیاز به توسعه": f"شما در پاسخگویی و پذیرش پیامدها نیاز به بهبود دارید."
            }
        }
        
        return interpretations.get(competency, {}).get(level, "")
    
    def save_all_scores(self):
        """
        ذخیره نمرات در پایگاه داده.
        
        نکته مهم: فقط شایستگی‌هایی که در این فاز شاهد داشته‌اند ذخیره می‌شوند،
        تا نمرات فازهای قبلی بازنویسی نشوند.
        """
        saved_count = 0
        for competency in self.COMPETENCIES:
            count = self.evidence_counts[competency]
            # ✅ فقط شایستگی‌هایی که شاهد دارند
            if count == 0:
                continue
            
            score = self.competency_scores[competency]
            confidence = min(1.0, count / 10.0)
            
            self.data_logger.save_competency_score(
                competency=competency,
                score=score,
                confidence=round(confidence, 2),
                evidence_count=count
            )
            saved_count += 1
        
        print(f"✓ {saved_count} شایستگی در پایگاه داده ذخیره شد "
              f"(از ۴ شایستگی، {4 - saved_count} بدون شاهد در این فاز)")
    
    def reset(self):
        """بازنشانی تمام شواهد و نمرات (برای شروع مجدد)"""
        self.evidence_buffer = {comp: [] for comp in self.COMPETENCIES}
        self.competency_scores = {comp: 0.0 for comp in self.COMPETENCIES}
        self.evidence_counts = {comp: 0 for comp in self.COMPETENCIES}
        print("✓ EvidenceEngine بازنشانی شد")
    
    def get_summary(self) -> Dict:
        """دریافت خلاصه کامل وضعیت موتور شواهد"""
        return {
            "scores": self.competency_scores.copy(),
            "levels": {
                comp: self.get_score_level(score)
                for comp, score in self.competency_scores.items()
            },
            "counts": self.evidence_counts.copy(),
            "interpretations": {
                comp: self.get_interpretation(comp)
                for comp in self.COMPETENCIES
            }
        }