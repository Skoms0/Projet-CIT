FROM python:3.10-slim

# Dépendances système utiles à confluent-kafka (librdkafka)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    librdkafka-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./requirements.txt

RUN pip install --no-cache-dir -r requirements.txt


COPY kafka-ingestor.py .

CMD ["python", "-u", "kafka-ingestor.py"]
