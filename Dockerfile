FROM python:3.11-slim

# ติดตั้ง Chromium และ Chromedriver (ไม่ติดตั้งแพ็คเกจที่ไม่จำเป็น)
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# ติดตั้ง Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# คัดลอกไฟล์สคริปต์และไฟล์บัญชี
COPY checker.py accounts.txt ./

CMD ["python", "checker.py"]
