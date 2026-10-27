"""
مدیریت پشتیبان‌گیری از پایگاه داده
======================================
- ذخیره‌ی خودکار نسخه‌ی پشتیبان در data/backups/
- نگهداری ۳۰ نسخه‌ی آخر
- بازیابی از یک نسخه

نسخه: 1.0.0
"""
import os
import shutil
import sqlite3
from datetime import datetime

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

try:
    from config import DB_PATH, DATA_DIR
except ImportError:
    DATA_DIR = os.path.join(PROJECT_ROOT, "data")
    DB_PATH = os.path.join(DATA_DIR, "participants.db")

BACKUP_DIR = os.path.join(DATA_DIR, "backups")

# حداکثر تعداد نسخه‌های پشتیبان
MAX_BACKUPS = 30

# حداقل فاصله بین دو پشتیبان‌گیری خودکار (ثانیه)
MIN_INTERVAL_SEC = 60


# ====================================================================
# پشتیبان‌گیری
# ====================================================================
def create_backup(reason: str = "auto") -> str | None:
    """
    ساخت یک نسخه‌ی پشتیبان.

    Args:
        reason: دلیل پشتیبان‌گیری ("auto", "manual", "startup")

    Returns:
        مسیر فایل پشتیبان یا None در صورت خطا
    """
    if not os.path.exists(DB_PATH):
        print("⚠️ پایگاه داده وجود ندارد — پشتیبان ساخته نشد")
        return None

    # اطمینان از وجود پوشه‌ی پشتیبان
    os.makedirs(BACKUP_DIR, exist_ok=True)

    # اگر آخرین پشتیبان کمتر از MIN_INTERVAL_SEC ثانیه پیش است، صرف‌نظر
    if reason == "auto":
        latest = _get_latest_backup_time()
        if latest is not None:
            now = datetime.now().timestamp()
            if now - latest < MIN_INTERVAL_SEC:
                return None

    # ساخت نام فایل با timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_name = f"participants_{timestamp}_{reason}.db"
    backup_path = os.path.join(BACKUP_DIR, backup_name)

    try:
        # استفاده از API پشتیبان‌گیری SQLite (امن‌تر از کپی فایل)
        src = sqlite3.connect(DB_PATH)
        dst = sqlite3.connect(backup_path)
        with dst:
            src.backup(dst)
        dst.close()
        src.close()

        size_kb = os.path.getsize(backup_path) / 1024
        print(
            f"✓ پشتیبان ساخته شد: {backup_name} "
            f"({size_kb:.1f} KB)"
        )

        # پاکسازی نسخه‌های قدیمی
        cleanup_old_backups()

        return backup_path
    except Exception as e:
        print(f"⚠️ خطا در ساخت پشتیبان: {e}")
        return None


# ====================================================================
def cleanup_old_backups(keep: int = MAX_BACKUPS):
    """حذف پشتیبان‌های قدیمی، نگه‌داشتن `keep` نسخه‌ی آخر"""
    if not os.path.isdir(BACKUP_DIR):
        return

    backups = sorted(
        [
            f for f in os.listdir(BACKUP_DIR)
            if f.startswith("participants_") and f.endswith(".db")
        ],
        reverse=True,
    )

    if len(backups) <= keep:
        return

    to_delete = backups[keep:]
    for fname in to_delete:
        try:
            os.remove(os.path.join(BACKUP_DIR, fname))
        except Exception as e:
            print(f"⚠️ خطا در حذف {fname}: {e}")

    if to_delete:
        print(f"   {len(to_delete)} پشتیبان قدیمی حذف شد")


# ====================================================================
def _get_latest_backup_time() -> float | None:
    """timestamp آخرین پشتیبان"""
    if not os.path.isdir(BACKUP_DIR):
        return None
    files = [
        f for f in os.listdir(BACKUP_DIR)
        if f.startswith("participants_") and f.endswith(".db")
    ]
    if not files:
        return None
    latest = max(
        os.path.getmtime(os.path.join(BACKUP_DIR, f))
        for f in files
    )
    return latest


# ====================================================================
def list_backups() -> list:
    """لیست پشتیبان‌ها با اطلاعات"""
    if not os.path.isdir(BACKUP_DIR):
        return []
    result = []
    for fname in sorted(
        os.listdir(BACKUP_DIR), reverse=True
    ):
        if not (
            fname.startswith("participants_")
            and fname.endswith(".db")
        ):
            continue
        path = os.path.join(BACKUP_DIR, fname)
        result.append({
            "name": fname,
            "path": path,
            "size_kb": os.path.getsize(path) / 1024,
            "modified": datetime.fromtimestamp(
                os.path.getmtime(path)
            ).strftime("%Y-%m-%d %H:%M:%S"),
        })
    return result


# ====================================================================
def restore_backup(backup_path: str) -> bool:
    """
    بازیابی از یک پشتیبان. ابتدا از DB فعلی یک backup گرفته
    می‌شود تا امکان بازگشت باشد.
    """
    if not os.path.exists(backup_path):
        print(f"❌ پشتیبان یافت نشد: {backup_path}")
        return False

    try:
        # پشتیبان از DB فعلی
        if os.path.exists(DB_PATH):
            create_backup(reason="before_restore")
        shutil.copy2(backup_path, DB_PATH)
        print(f"✓ بازیابی انجام شد: {backup_path}")
        return True
    except Exception as e:
        print(f"❌ خطا در بازیابی: {e}")
        return False


# ====================================================================
# CLI
# ====================================================================
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "list":
        backups = list_backups()
        if not backups:
            print("هیچ پشتیبانی وجود ندارد.")
        else:
            print(f"{len(backups)} پشتیبان:")
            for b in backups:
                print(
                    f"  {b['name']}  "
                    f"({b['size_kb']:.1f} KB)  "
                    f"{b['modified']}"
                )
    elif len(sys.argv) > 1 and sys.argv[1] == "now":
        create_backup(reason="manual")
    elif len(sys.argv) > 1 and sys.argv[1] == "restore":
        if len(sys.argv) > 2:
            restore_backup(sys.argv[2])
        else:
            print(
                "استفاده: python -m core.backup_manager "
                "restore <path>"
            )
    else:
        print(
            "استفاده:\n"
            "  python -m core.backup_manager list     "
            "— لیست پشتیبان‌ها\n"
            "  python -m core.backup_manager now      "
            "— پشتیبان فوری\n"
            "  python -m core.backup_manager restore <path>  "
            "— بازیابی"
        )