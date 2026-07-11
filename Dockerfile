FROM python:3.11-slim
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py accounts.txt ./
CMD ["python", "main.py"]
