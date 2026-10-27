"""
اسکریپت تحلیل داده‌های جمع‌آوری‌شده از بازی
برای محاسبه نمرات شایستگی و تولید گزارش
"""
import os
import sys
import sqlite3
import pandas as pd
import numpy as np

# ✅ مسیر پروژه (پوشه والد analysis)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config import DB_PATH


class CompetencyAnalyzer:
    """تحلیل‌گر شایستگی‌ها"""

    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)

    def get_all_participants(self):
        """دریافت لیست تمام شرکت‌کنندگان"""
        query = (
            "SELECT participant_id, session_start, session_end "
            "FROM participants"
        )
        return pd.read_sql_query(query, self.conn)

    def get_events_for_participant(self, participant_id):
        """دریافت تمام رویدادهای یک شرکت‌کننده"""
        query = (
            "SELECT * FROM events "
            "WHERE participant_id = ? "
            "ORDER BY timestamp"
        )
        return pd.read_sql_query(query, self.conn, params=(participant_id,))

    def get_evidence_for_participant(self, participant_id):
        """دریافت تمام شواهد یک شرکت‌کننده"""
        query = (
            "SELECT * FROM evidence "
            "WHERE participant_id = ?"
        )
        return pd.read_sql_query(query, self.conn, params=(participant_id,))

    def calculate_competency_scores(self, participant_id):
        """محاسبه نمرات نهایی شایستگی‌ها"""
        evidence_df = self.get_evidence_for_participant(participant_id)

        competencies = ["honesty", "trustworthiness",
                        "problem_solving", "accountability"]
        scores = {}

        for comp in competencies:
            comp_evidence = evidence_df[
                evidence_df['competency'] == comp
            ]

            if len(comp_evidence) > 0:
                total_weight = comp_evidence['weight'].sum()
                weighted_sum = (
                    comp_evidence['evidence_value'] *
                    comp_evidence['weight']
                ).sum()
                score = (weighted_sum / total_weight * 100) \
                    if total_weight > 0 else 0

                scores[comp] = {
                    "score": round(score, 2),
                    "evidence_count": len(comp_evidence),
                    "confidence": 0.8
                }
            else:
                scores[comp] = {
                    "score": 0,
                    "evidence_count": 0,
                    "confidence": 0
                }

        return scores

    def generate_report(self, participant_id):
        """تولید گزارش کامل برای یک شرکت‌کننده"""
        scores = self.calculate_competency_scores(participant_id)

        report = {
            "participant_id": participant_id,
            "competency_scores": scores,
            "interpretation": self._interpret_scores(scores)
        }

        return report

    def _interpret_scores(self, scores):
        """تفسیر نمرات"""
        labels = {
            "honesty": "صداقت و یکپارچگی",
            "trustworthiness": "قابلیت اعتماد",
            "problem_solving": "حل مسئله",
            "accountability": "مسئولیت‌پذیری"
        }

        interpretation = {}
        for comp, data in scores.items():
            score = data["score"]
            label = labels.get(comp, comp)

            if score >= 80:
                level = "بسیار خوب"
            elif score >= 60:
                level = "خوب"
            elif score >= 40:
                level = "متوسط"
            else:
                level = "نیاز به توسعه"

            interpretation[label] = {
                "score": score,
                "level": level
            }

        return interpretation

    def export_to_csv(self, output_file="competency_scores.csv"):
        """صادرات نمرات تمام شرکت‌کنندگان به CSV"""
        participants = self.get_all_participants()

        all_scores = []
        for _, row in participants.iterrows():
            participant_id = row['participant_id']
            scores = self.calculate_competency_scores(participant_id)

            row_data = {"participant_id": participant_id}
            for comp, data in scores.items():
                row_data[f"{comp}_score"] = data["score"]
                row_data[f"{comp}_evidence_count"] = data["evidence_count"]

            all_scores.append(row_data)

        df = pd.DataFrame(all_scores)
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"✓ نمرات به فایل {output_file} صادر شد")

        return df

    def close(self):
        """بستن اتصال پایگاه داده"""
        self.conn.close()


if __name__ == "__main__":
    # مثال استفاده
    analyzer = CompetencyAnalyzer()

    # دریافت لیست شرکت‌کنندگان
    participants = analyzer.get_all_participants()
    print(f"تعداد شرکت‌کنندگان: {len(participants)}")

    # تولید گزارش برای اولین شرکت‌کننده
    if len(participants) > 0:
        first_participant = participants.iloc[0]['participant_id']
        report = analyzer.generate_report(first_participant)

        print(f"\nگزارش شرکت‌کننده {first_participant}:")
        for comp, data in report['competency_scores'].items():
            print(f"  {comp}: {data['score']:.2f} "
                  f"({data['evidence_count']} شواهد)")

    # صادرات به CSV
    analyzer.export_to_csv()

    analyzer.close()