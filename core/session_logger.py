"""
لاگ سیستم — ثبت همه‌ی print()ها در یک فایل
==============================================
- با شروع جلسه، یک فایل لاگ در logs/ ساخته می‌شود
- همه‌ی print()ها هم به terminal و هم به فایل می‌روند
- در پایان جلسه، فایل بسته می‌شود
- نگهداری ۵۰ لاگ آخر

نسخه: 1.0.0
"""
import os
import sys
import io
from datetime import datetime

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)
LOG_DIR = os.path.join(PROJECT_ROOT, "logs")
MAX_LOGS = 50


# ====================================================================
# Tee Stream — نوشتن هم‌زمان در دو stream
# ====================================================================
class _TeeStream(io.TextIOBase):
    """یک stream که به چند stream دیگر می‌نویسد"""

    def __init__(self, *streams):
        self._streams = list(streams)

    def write(self, data):
        for s in self._streams:
            try:
                s.write(data)
                s.flush()
            except Exception:
                pass
        return len(data) if data else 0

    def flush(self):
        for s in self._streams:
            try:
                s.flush()
            except Exception:
                pass

    def isatty(self):
        # اگر stream اصلی ترمینال نیست، بگو ترمینال نیست
        for s in self._streams:
            try:
                return s.isatty()
            except Exception:
                continue
        return False

    def fileno(self):
        for s in self._streams:
            try:
                return s.fileno()
            except Exception:
                continue
        raise OSError("No valid fileno")


# ====================================================================
# مدیر لاگ
# ====================================================================
class _SessionLogger:
    """مدیر سراسری لاگ جلسه"""

    def __init__(self):
        self._log_file = None
        self._path: str | None = None
        self._original_stdout = None
        self._original_stderr = None
        self._active = False

    # ----------------------------------------------------------------
    def start(self, participant_id: str = "") -> str | None:
        """شروع لاگ‌گیری"""
        if self._active:
            return self._path

        try:
            os.makedirs(LOG_DIR, exist_ok=True)
            timestamp = datetime.now().strftime(
                "%Y-%m-%d_%H-%M-%S"
            )
            safe_pid = "".join(
                c for c in participant_id
                if c.isalnum() or c in "-_"
            ) or "anon"
            fname = f"session_{timestamp}_{safe_pid}.log"
            path = os.path.join(LOG_DIR, fname)

            self._log_file = open(
                path, "w", encoding="utf-8", buffering=1
            )
            self._path = path
            self._original_stdout = sys.stdout
            self._original_stderr = sys.stderr

            sys.stdout = _TeeStream(
                self._original_stdout, self._log_file
            )
            sys.stderr = _TeeStream(
                self._original_stderr, self._log_file
            )

            self._active = True

            # پاک‌سازی لاگ‌های قدیمی
            self._cleanup_old_logs()

            # پیام شروع
            print("=" * 70)
            print(
                f"  Truthline Session Log — "
                f"{datetime.now().isoformat()}"
            )
            print(f"  Participant ID: {participant_id or 'unknown'}")
            print(f"  Log file: {fname}")
            print("=" * 70)

            return path
        except Exception as e:
            # اگر خطا داد، به حالت عادی برگرد
            self._active = False
            self._log_file = None
            print(f"⚠️ خطا در شروع لاگ: {e}")
            return None

    # ----------------------------------------------------------------
    def stop(self):
        """پایان لاگ‌گیری"""
        if not self._active:
            return

        try:
            print("=" * 70)
            print(
                f"  End of session — "
                f"{datetime.now().isoformat()}"
            )
            print("=" * 70)

            if self._original_stdout is not None:
                sys.stdout = self._original_stdout
            if self._original_stderr is not None:
                sys.stderr = self._original_stderr

            if self._log_file is not None:
                self._log_file.flush()
                self._log_file.close()
        except Exception:
            pass
        finally:
            self._log_file = None
            self._active = False

    # ----------------------------------------------------------------
    def _cleanup_old_logs(self):
        """حذف لاگ‌های قدیمی"""
        try:
            logs = sorted(
                [
                    f for f in os.listdir(LOG_DIR)
                    if f.startswith("session_")
                    and f.endswith(".log")
                ],
                reverse=True,
            )
            for fname in logs[MAX_LOGS:]:
                try:
                    os.remove(os.path.join(LOG_DIR, fname))
                except Exception:
                    pass
        except Exception:
            pass

    # ----------------------------------------------------------------
    @property
    def path(self) -> str | None:
        return self._path

    @property
    def is_active(self) -> bool:
        return self._active


# ====================================================================
# نمونه‌ی سراسری
# ====================================================================
_logger: _SessionLogger | None = None


def get_session_logger() -> _SessionLogger:
    global _logger
    if _logger is None:
        _logger = _SessionLogger()
    return _logger


def start_session_log(participant_id: str = "") -> str | None:
    return get_session_logger().start(participant_id)


def stop_session_log():
    get_session_logger().stop()


def list_session_logs() -> list:
    """لیست لاگ‌های موجود"""
    if not os.path.isdir(LOG_DIR):
        return []
    result = []
    for fname in sorted(
        os.listdir(LOG_DIR), reverse=True
    ):
        if not (
            fname.startswith("session_")
            and fname.endswith(".log")
        ):
            continue
        path = os.path.join(LOG_DIR, fname)
        try:
            size_kb = os.path.getsize(path) / 1024
            modified = datetime.fromtimestamp(
                os.path.getmtime(path)
            ).strftime("%Y-%m-%d %H:%M:%S")
            result.append({
                "name": fname,
                "path": path,
                "size_kb": size_kb,
                "modified": modified,
            })
        except Exception:
            continue
    return result


# ====================================================================
# CLI
# ====================================================================
if __name__ == "__main__":
    logs = list_session_logs()
    if not logs:
        print("هیچ لاگی وجود ندارد.")
    else:
        print(f"{len(logs)} لاگ:")
        for l in logs[:20]:
            print(
                f"  {l['name']}  "
                f"({l['size_kb']:.1f} KB)  "
                f"{l['modified']}"
            )
        if len(logs) > 20:
            print(f"  ... و {len(logs) - 20} مورد دیگر")