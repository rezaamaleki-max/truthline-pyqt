# ============================================================
# Truthline Web — Docker Image
# ============================================================
FROM python:3.11-slim

# تنظیم منطقه‌زمانی و کدگذاری
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LANG=C.UTF-8

WORKDIR /app

# نصب وابستگی‌های سیستمی لازم برای گزارش‌گیری PDF فارسی
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libfreetype6 \
    libjpeg62-turbo \
    libpng16-16 \
    && rm -rf /var/lib/apt/lists/*

# ابتدا فقط requirements را کپی می‌کنیم تا cache بهتر عمل کند
# ابتدا فقط requirements را کپی می‌کنیم تا cache بهتر عمل کند
COPY requirements-web.txt .

# نصب پکیج‌ها از طریق میرور چابکان
RUN pip install --no-cache-dir \
    --index-url https://package-mirror.liara.ir/repository/pypi/simple \
    --trusted-host package-mirror.liara.ir \
    --retries 5 \
    --timeout 60 \
    -r requirements-web.txt

# سپس کل پروژه
COPY . .

# پورت داخلی NiceGUI
EXPOSE 8080

# اجرا
CMD ["python", "-m", "web_app.app"]