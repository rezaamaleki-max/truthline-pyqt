"""بررسی کلمات لو دهنده در فایل‌های سناریو — اجرا: python check_revealing_words.py"""
import json
import os
import glob


# کلمات لو دهنده
REVEALING = [
    "صداقت",
    "دروغ",
    "پنهان‌کاری",
    "پنهان کاری",
    "تقلب",
    "فریب",
    "ریاکاری",
    "دورویی",
    "روراست",  # "با خودت روراست باشی" هم لو دهنده است
    "صادقانه",
    "صادق",
]


def find_in_text(text: str) -> list:
    """اگر کلمه‌ای در متن پیدا شد، لیست کلمات را برمی‌گرداند."""
    if not isinstance(text, str):
        return []
    return [w for w in REVEALING if w in text]


def scan_choices(scenario: dict, file_path: str):
    """اسکن تمام فیلدهای متنی در سناریو."""
    sid = scenario.get("scenario_id", "?")
    title = scenario.get("title_fa", "")

    # ---- فیلدهای سطح بالا ----
    matches = []

    # intro_sequence
    for i, d in enumerate(scenario.get("intro_sequence", [])):
        for field in ("text_fa", "text"):
            text = d.get(field, "")
            found = find_in_text(text)
            if found:
                matches.append({
                    "where": f"intro_sequence[{i}] ({d.get('speaker', '')})",
                    "field": field,
                    "text": text,
                    "words": found,
                })

    # dialogue_sequence
    for i, d in enumerate(scenario.get("dialogue_sequence", [])):
        for field in ("text_fa", "text"):
            text = d.get(field, "")
            found = find_in_text(text)
            if found:
                matches.append({
                    "where": f"dialogue_sequence[{i}] ({d.get('speaker', '')})",
                    "field": field,
                    "text": text,
                    "words": found,
                })

    # choices
    for i, c in enumerate(scenario.get("choices", [])):
        cid = c.get("id", i + 1)
        text = c.get("text_fa", "") or c.get("text", "")
        found = find_in_text(text)
        if found:
            matches.append({
                "where": f"choice id={cid}",
                "field": "text_fa",
                "text": text,
                "words": found,
            })

    # result_dialogue
    for i, d in enumerate(scenario.get("result_dialogue", [])):
        for field in ("text_fa", "text"):
            text = d.get(field, "")
            found = find_in_text(text)
            if found:
                matches.append({
                    "where": f"result_dialogue[{i}] ({d.get('speaker', '')})",
                    "field": field,
                    "text": text,
                    "words": found,
                })

    # result_dialogue_by_choice
    rdbc = scenario.get("result_dialogue_by_choice", {})
    for cid, dialogues in rdbc.items():
        for i, d in enumerate(dialogues):
            for field in ("text_fa", "text"):
                text = d.get(field, "")
                found = find_in_text(text)
                if found:
                    matches.append({
                        "where": f"result_dialogue_by_choice[{cid}][{i}] ({d.get('speaker', '')})",
                        "field": field,
                        "text": text,
                        "words": found,
                    })

    # result_dialogue_by_root_cause
    rdbr = scenario.get("result_dialogue_by_root_cause", {})
    for rc, dialogues in rdbr.items():
        for i, d in enumerate(dialogues):
            for field in ("text_fa", "text"):
                text = d.get(field, "")
                found = find_in_text(text)
                if found:
                    matches.append({
                        "where": f"result_dialogue_by_root_cause[{rc}][{i}] ({d.get('speaker', '')})",
                        "field": field,
                        "text": text,
                        "words": found,
                    })

    # rounds (برای AC-01)
    for r_idx, rnd in enumerate(scenario.get("rounds", [])):
        member = rnd.get("member_name", "?")
        # question_by_pressure
        qbp = rnd.get("question_by_pressure", {})
        for pressure, q in qbp.items():
            found = find_in_text(q)
            if found:
                matches.append({
                    "where": f"rounds[{r_idx}].question_by_pressure[{pressure}] ({member})",
                    "field": "question",
                    "text": q,
                    "words": found,
                })
        # choices
        for c in rnd.get("choices", []):
            text = c.get("text_fa", "")
            found = find_in_text(text)
            if found:
                matches.append({
                    "where": f"rounds[{r_idx}].choice id={c.get('id', '?')} ({member})",
                    "field": "text_fa",
                    "text": text,
                    "words": found,
                })
        # reactions_by_choice
        rbc = rnd.get("reactions_by_choice", {})
        for cid, reactions in rbc.items():
            for i, d in enumerate(reactions):
                text = d.get("text_fa", "")
                found = find_in_text(text)
                if found:
                    matches.append({
                        "where": f"rounds[{r_idx}].reactions_by_choice[{cid}][{i}] ({d.get('speaker', '')})",
                        "field": "text_fa",
                        "text": text,
                        "words": found,
                    })

    return {
        "file": os.path.basename(file_path),
        "path": file_path,
        "scenario_id": sid,
        "title": title,
        "matches": matches,
    }


def main():
    # همه‌ی فایل‌های JSON سناریو را پیدا کن
    base = "data/scenarios"
    all_files = glob.glob(
        os.path.join(base, "**", "*.json"),
        recursive=True,
    )

    if not all_files:
        print(f"❌ هیچ فایل JSON در {base} پیدا نشد.")
        print(f"   دایرکتوری فعلی: {os.getcwd()}")
        return

    print("=" * 70)
    print(f"🔍 جستجوی کلمات لو دهنده در {len(all_files)} فایل")
    print("=" * 70)
    print(f"کلمات: {', '.join(REVEALING)}")
    print()

    total_matches = 0
    files_with_matches = 0

    for path in sorted(all_files):
        try:
            with open(path, "r", encoding="utf-8") as f:
                scenario = json.load(f)
        except Exception as e:
            print(f"⚠️ خطا در خواندن {path}: {e}")
            continue

        result = scan_choices(scenario, path)
        matches = result["matches"]

        if not matches:
            continue

        files_with_matches += 1
        total_matches += len(matches)

        print("=" * 70)
        print(f"📄 {result['file']}")
        print(f"   سناریو: {result['scenario_id']} — {result['title']}")
        print(f"   تعداد: {len(matches)} مورد")
        print("-" * 70)

        for m in matches:
            print(f"   🔸 {m['where']}")
            print(f"      کلمات: {', '.join(m['words'])}")
            print(f"      متن: {m['text'][:200]}")
            if len(m['text']) > 200:
                print(f"           ... (ادامه)")
            print()

    print("=" * 70)
    print("📊 خلاصه")
    print("=" * 70)
    print(f"  فایل‌های دارای کلمات لو دهنده: {files_with_matches}")
    print(f"  مجموع موارد: {total_matches}")
    print()

    if total_matches == 0:
        print("✅ هیچ کلمه‌ی لو دهنده‌ای پیدا نشد.")


if __name__ == "__main__":
    main()