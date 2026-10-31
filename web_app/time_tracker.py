# File: web_app/time_tracker.py
import asyncio
from nicegui import background_tasks
from web_app.db_manager import log_event_threadsafe

def mark_page_enter(page_key: str, participant_id: str, session_id: str):
    """
    ثبت زمان ورود به صفحه در دیتابیس.
    از همان مکانیسم log_event_threadsafe استفاده می‌کند.
    """
    if not participant_id or not session_id:
        return

    # ثبت در پس‌زمینه تا لود صفحه کند نشود
    background_tasks.create(
        asyncio.to_thread(
            log_event_threadsafe,
            participant_id=participant_id,
            session_id=session_id,
            event_type='page_enter',      # ✅ نوع رویداد جدید
            scenario_id=page_key,         # ✅ نام صفحه (مثلاً phase1)
            metadata={}
        )
    )