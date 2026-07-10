FROM python:3.11-slim

# ไม่ต้องติดตั้ง chromium เพราะ webdriver_manager จะจัดการ driver เอง
# แต่ต้องติดตั้ง chrome (มีอยู่ใน repo ของ google) - หรือจะไม่ติดตั้งเลยก็ได้แล้วแต่
# วิธีที่ง่ายที่สุดคือใช้ undetected-chromedriver + webdriver_manager

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py accounts.txt ./

CMD ["python", "main.py"]
