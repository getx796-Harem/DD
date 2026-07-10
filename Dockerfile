FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    libgconf-2-4 \
    libnss3 \
    libxss1 \
    fonts-liberation \
    libgbm1 \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py accounts.txt ./
CMD ["python", "main.py"]
