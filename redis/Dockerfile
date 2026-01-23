FROM python:3.11-alpine

WORKDIR /app

# Installer les dépendances de compilation pour confluent-kafka
RUN apk add --no-cache gcc musl-dev python3-dev librdkafka-dev make

# Copier requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY kafka-ingestor.py .

CMD ["python", "-u", "kafka-ingestor.py"]
