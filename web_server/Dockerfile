FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt ./requirements.txt
COPY server_web.py .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5000
CMD ["python", "server_web.py"]
