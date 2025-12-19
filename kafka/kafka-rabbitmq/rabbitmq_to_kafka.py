import json
import os
import signal
import sys
import time

import pika
import pika.exceptions
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable

# -------------------------
# Configuration (ENV VARS)
# -------------------------

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "guest")
RABBITMQ_QUEUE = os.getenv("RABBITMQ_QUEUE", "input_queue")

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "input.images")

PREFETCH_COUNT = int(os.getenv("PREFETCH_COUNT", "10"))

# -------------------------
# Graceful Shutdown
# -------------------------

running = True
producer = None


def shutdown_handler(signum, frame):
    global running
    print("Shutdown signal received...")
    running = False


signal.signal(signal.SIGTERM, shutdown_handler)
signal.signal(signal.SIGINT, shutdown_handler)

# -------------------------
# Kafka Producer Initialization
# -------------------------


def init_kafka_producer():
    """Initialise le producteur Kafka avec retry"""
    global producer
    retry_count = 0
    max_retries = 10

    while retry_count < max_retries and running:
        try:
            print(f"Attempting to connect to Kafka at {KAFKA_BOOTSTRAP_SERVERS}...")
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS.split(","),
                # Pas de serializer pour envoyer des données binaires brutes (images)
                value_serializer=None,
                retries=5,
                linger_ms=10,
                max_request_size=10485760,  # 10 MB pour supporter les grandes images
            )
            print("Successfully connected to Kafka!")
            return True
        except NoBrokersAvailable as e:
            retry_count += 1
            print(f"Kafka not available (attempt {retry_count}/{max_retries}): {e}")
            if retry_count < max_retries:
                time.sleep(5)
        except Exception as e:
            retry_count += 1
            print(
                f"Error connecting to Kafka (attempt {retry_count}/{max_retries}): {e}"
            )
            if retry_count < max_retries:
                time.sleep(5)

    print("Failed to connect to Kafka after maximum retries")
    return False


# -------------------------
# RabbitMQ Callback
# -------------------------


def on_message(channel, method_frame, header_frame, body):
    try:
        # body contient directement les données binaires de l'image
        # On les envoie telles quelles à Kafka
        if producer is None:
            raise RuntimeError("Kafka producer is not initialized")

        producer.send(KAFKA_TOPIC, value=body)
        producer.flush()

        channel.basic_ack(delivery_tag=method_frame.delivery_tag)
        print(f"Image forwarded to Kafka (size: {len(body)} bytes)")

    except Exception as e:
        print(f"Error processing message: {e}")
        channel.basic_nack(delivery_tag=method_frame.delivery_tag, requeue=True)


# -------------------------
# RabbitMQ Connection Loop
# -------------------------


def consume():
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
    parameters = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        credentials=credentials,
        heartbeat=30,
    )

    while running:
        try:
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
            channel.basic_qos(prefetch_count=PREFETCH_COUNT)
            channel.basic_consume(
                queue=RABBITMQ_QUEUE,
                on_message_callback=on_message,
            )

            print("Connected to RabbitMQ. Waiting for messages...")
            channel.start_consuming()

        except pika.exceptions.AMQPConnectionError as e:
            print(f"RabbitMQ connection failed: {e}")
            time.sleep(5)

        except Exception as e:
            print(f"Unexpected error: {e}")
            time.sleep(5)

    print("Shutting down connector...")
    if producer:
        producer.close()
    sys.exit(0)


if __name__ == "__main__":
    # Initialiser le producteur Kafka au démarrage
    if not init_kafka_producer():
        sys.exit(1)

    # Démarrer la consommation RabbitMQ
    consume()
