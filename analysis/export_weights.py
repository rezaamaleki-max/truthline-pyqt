"""
استخراج تمام وزن‌های شواهد از فایل‌های سناریو برای مستندسازی روایی
"""
import os
import json
import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCENARIOS_DIR = os.path.join(PROJECT_ROOT, "data", "scenarios")


def collect_weights():
    rows = []
    for phase_dir in sorted(os.listdir(SCENARIOS_DIR)):
        phase_path = os.path.join(SCENARIOS_DIR, phase_dir)
        if not os.path.isdir(phase_path):
            continue
        for fname in sorted(os.listdir(phase_path)):
            if not fname.endswith(".json"):
                continue
            with open(os.path.join(phase_path, fname), "r",
                      encoding="utf-8") as f:
                scen = json.load(f)
            em = scen.get("evidence_model", {})
            for ev_id, ev in em.items():
                rows.append({
                    "phase": phase_dir,
                    "scenario_id": scen.get("scenario_id", ""),
                    "title_fa": scen.get("title_fa", ""),
                    "evidence_key": ev_id,
                    "weight": ev.get("weight", 1.0),
                    "description": ev.get("description", ""),
                    "formula": ev.get("formula", ""),
                })
    df = pd.DataFrame(rows)
    # ✅ محاسبه وزن مجموع برای هر سناریو
    df["weight_sum_per_scenario"] = df.groupby(
        ["phase", "scenario_id"]
    )["weight"].transform("sum")
    df.to_csv("evidence_weights_audit.csv", index=False,
              encoding="utf-8-sig")
    print(f"✓ {len(df)} شاهد صادر شد → evidence_weights_audit.csv")
    print("\n⚠️ سناریوهایی که مجموع وزن‌شان ≠ 1.0 است:")
    bad = df[df["weight_sum_per_scenario"] != 1.0][
        ["scenario_id", "weight_sum_per_scenario"]
    ].drop_duplicates()
    print(bad.to_string(index=False))


if __name__ == "__main__":
    collect_weights()