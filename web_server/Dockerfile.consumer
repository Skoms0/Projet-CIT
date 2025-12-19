FROM python:3.10-slim

# Install system dependencies (required for confluent-kafka on ARM)
RUN apt-get update && apt-get install -y --no-install-recommends \
    librdkafka-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only the needed files
COPY requirements.txt ./requirements.txt
COPY kafka_frame_consumer.py .

RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONUNBUFFERED=1

CMD ["python", "kafka_frame_consumer.py"]
