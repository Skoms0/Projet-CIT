FROM python:3.10-slim

# Dépendances système utiles à confluent-kafka (librdkafka)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    librdkafka-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./requirements.txt
COPY server_web.py ./server_web.py
COPY kafka_frame_consumer.py ./kafka_frame_consumer.py

RUN pip install --no-cache-dir -r requirements.txt

# Petit script de lancement (web + consumer dans le même container)
RUN printf '%s\n' \
'#!/bin/sh' \
'set -e' \
'python server_web.py &' \
'WEB_PID=$!' \
'python kafka_frame_consumer.py &' \
'CONSUMER_PID=$!' \
'trap "kill $WEB_PID $CONSUMER_PID; exit 0" INT TERM' \
'wait' \
> /app/entrypoint.sh && chmod +x /app/entrypoint.sh

EXPOSE 5000
CMD ["/app/entrypoint.sh"]
