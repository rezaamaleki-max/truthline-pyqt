"""
monitor.py — نسخه‌ی خودکار
PID سرور را از پورت 8080 پیدا می‌کند.
"""
import psutil
import time
import subprocess


def find_server_pid():
    """PID سرور را از پورت 8080 پیدا می‌کند."""
    try:
        result = subprocess.run(
            ["powershell", "-Command",
             "(Get-NetTCPConnection -LocalPort 8080 -State Listen).OwningProcess"],
            capture_output=True, text=True, timeout=5,
        )
        out = result.stdout.strip()
        if out and out.isdigit():
            return int(out)
    except Exception:
        pass
    return None


def monitor_resources(pid: int, interval: float = 2.0):
    """مانیتورینگ مصرف رم و CPU پروسه‌ی مشخص‌شده."""
    try:
        process = psutil.Process(pid)
    except psutil.NoSuchProcess:
        print(f"❌ پروسه‌ی {pid} وجود ندارد.")
        return

    print(f"شروع مانیتورینگ پروسه‌ی {pid} (Ctrl+C برای توقف)...")
    print(f"{'زمان':<10} {'رم (RSS)':<15} {'CPU %':<10}")
    print("-" * 40)

    try:
        while True:
            mem_info = process.memory_info()
            mem_mb = mem_info.rss / (1024 * 1024)
            cpu_percent = process.cpu_percent(interval=0.5)
            current_time = time.strftime("%H:%M:%S")
            print(f"{current_time:<10} {mem_mb:>10.2f} MB   {cpu_percent:>8.2f}%")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nمانیتورینگ متوقف شد.")


if __name__ == "__main__":
    pid = find_server_pid()
    if not pid:
        print("❌ سرور در حال اجرا نیست یا پورت 8080 پیدا نشد.")
        print("   ابتدا .\\activate.ps1 را اجرا کنید.")
        exit(1)

    print(f"✓ PID سرور: {pid}")
    monitor_resources(pid)