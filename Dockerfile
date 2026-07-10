FROM python:3.11-slim

# ติดตั้ง chromium และ chromedriver
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# ติดตั้ง Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# คัดลอกไฟล์สคริปต์และบัญชี
COPY checker.py accounts.txt ./

CMD ["python", "checker.py"]
