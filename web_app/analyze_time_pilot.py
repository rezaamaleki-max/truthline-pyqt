# File: web_app/analyze_time_pilot.py
import sqlite3
import os
from collections import defaultdict

WEB_APP_DIR = os.path.dirname(os.path.abspath(__file__))
# آدرس دیتابیس (اگر دیسک دارید مسیر db اضافه می‌شود)
DB_PATH = os.path.join(WEB_APP_DIR, "data", "participants_web.db")
if os.path.exists(os.path.join(WEB_APP_DIR, "data", "db", "participants_web.db")):
    DB_PATH = os.path.join(WEB_APP_DIR, "data", "db", "participants_web.db")

def analyze_pilot_times():
    if not os.path.exists(DB_PATH):
        print(f"❌ دیتابیس یافت نشد: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # استخراج تمام زمان‌های ورود به صفحات
    c.execute("""
        SELECT participant_id, scenario_id, timestamp 
        FROM web_events 
        WHERE event_type = 'page_enter'
        ORDER BY participant_id, timestamp ASC
    """)
    rows = c.fetchall()
    conn.close()

    # ساختار: { participant_id: [ (page_key, timestamp), ... ] }
    user_events = defaultdict(list)
    for pid, page_key, ts in rows:
        user_events[pid].append((page_key, ts))

    times = defaultdict(list)

    # محاسبه تفاضل زمانی
    for pid, events in user_events.items():
        for i in range(len(events) - 1):
            page_key = events[i][0]
            time_start = events[i][1]
            time_end = events[i+1][1]
            
            duration = round(time_end - time_start, 1)
            
            # فیلتر کردن زمان‌های غیرمنطقی (مثلاً بالای ۲ ساعت یعنی کاربر رفته است)
            if 0 < duration < 7200:
                times[page_key].append(duration)

    print("=" * 75)
    print("⏱ گزارش زمان‌بندی مطالعه پایلوت (بر اساس timestamp دیتابیس)")
    print("=" * 75)
    
    order = [
        "intro", 
        "phase1", "night_1", "interlude_day2",
        "phase2", "night_2", "interlude_day3",
        "phase3", "night_3", "interlude_day4",
        "phase4", "letter_to_self",
        "hexaco", "crt", "tower_of_hanoi", "sd3", "sd", "feedback", 
        "interlude_epilogue", "results"
    ]
    
    total_avg = 0
    
    for key in order:
        if key not in times:
            continue
            
        vals = times[key]
        avg = sum(vals) / len(vals)
        mx = max(vals)
        mn = min(vals)
        total_avg += avg
        
        print(f"  {key:<22} | میانگین: {avg:>6.1f}s | کمینه: {mn:>6.1f}s | بیشینه: {mx:>6.1f}s | (n={len(vals)})")
        
    print("-" * 75)
    print(f"  {'مجموع میانگین‌ها':<22} | {total_avg:>6.1f} ثانیه (≈ {total_avg/60:.1f} دقیقه)")
    print("=" * 75)

if __name__ == "__main__":
    analyze_pilot_times()