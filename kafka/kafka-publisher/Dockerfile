FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir kafka-python

COPY publisher.py .
COPY example-image.jpeg .

CMD ["python", "-u", "/app/publisher.py"]

