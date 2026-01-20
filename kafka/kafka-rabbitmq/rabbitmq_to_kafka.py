import os
import signal
import sys
import time
import pika
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable

# -------------------------
# Configuration (ENV VARS)
# -------------------------
# AMQP Configuration
AMQP_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq-mqtt")
AMQP_PORT = int(os.getenv("RABBITMQ_PORT", 5672))
AMQP_USERNAME = os.getenv("RABBITMQ_USER", "davidra")      # FIXED: Matches YAML
AMQP_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "davidra")

# RabbitMQ Specifics
# We use a fixed queue name so multiple replicas share the work
AMQP_QUEUE_NAME = "video_processing_queue" 

# The topic filter from YAML (e.g., "cam/h264/#")
AMQP_BINDING_KEY = '.cam.h264.#'

# CONVERSION: MQTT uses '/', AMQP uses '.'
# We replace '/' with '.' to bind correctly to the amq.topic exchange


# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "input.images")
PREFETCH_COUNT = int(os.getenv("PREFETCH_COUNT", 10))

RUNNING = True
PRODUCER = None
AMQP_CONNECTION = None
AMQP_CHANNEL = None

# -------------------------
# Graceful Shutdown
# -------------------------
def shutdown_handler(signum, frame):
    global RUNNING, AMQP_CHANNEL
    print("Shutdown signal received...")
    RUNNING = False
    if AMQP_CHANNEL and AMQP_CHANNEL.is_open:
        print("[AMQP] Stopping consumption...")
        AMQP_CHANNEL.stop_consuming()

signal.signal(signal.SIGTERM, shutdown_handler)
signal.signal(signal.SIGINT, shutdown_handler)

# -------------------------
# Kafka Producer Initialization
# -------------------------
def init_kafka_producer():
    global PRODUCER
    retry_count = 0
    max_retries = 10

    while retry_count < max_retries and RUNNING:
        try:
            print(f"Connecting to Kafka at {KAFKA_BOOTSTRAP_SERVERS}...")
            PRODUCER = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=None,
                retries=5,
                linger_ms=10,
                max_request_size=10485760,  # 10 MB
            )
            print("Kafka connection established!")
            return True
        except NoBrokersAvailable as e:
            retry_count += 1
            print(f"Kafka not available (attempt {retry_count}/{max_retries}): {e}")
            time.sleep(5)
        except Exception as e:
            retry_count += 1
            print(f"Error connecting to Kafka (attempt {retry_count}/{max_retries}): {e}")
            time.sleep(5)

    print("Failed to connect to Kafka after max retries")
    return False

# -------------------------
# AMQP Callback
# -------------------------
def on_message(ch, method, properties, body):
    try:
        if PRODUCER is None:
            raise RuntimeError("Kafka producer not initialized")

        # Forward to Kafka
        # We use the AMQP routing key (e.g. cam.h264.cam13) as the Kafka key? 
        # Optional: key=method.routing_key.encode('utf-8')
        PRODUCER.send(KAFKA_TOPIC, value=body)
        
        # Log periodically or for every message if low volume
        print(f"[AMQP -> Kafka] Forwarded {len(body)} bytes from {method.routing_key}")

        # Ack to RabbitMQ
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        print(f"[ERROR] Failed to forward message: {e}")
        # Nack so another pod can try
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

# -------------------------
# AMQP Consumer Loop
# -------------------------
def consume_amqp():
    global AMQP_CONNECTION, AMQP_CHANNEL
    
    try:
        print(f"[AMQP] Connecting to {AMQP_HOST}:{AMQP_PORT} as {AMQP_USERNAME}...")
        credentials = pika.PlainCredentials(AMQP_USERNAME, AMQP_PASSWORD)
        parameters = pika.ConnectionParameters(
            host=AMQP_HOST, 
            port=AMQP_PORT, 
            credentials=credentials,
            heartbeat=600,
            blocked_connection_timeout=300
        )
        
        AMQP_CONNECTION = pika.BlockingConnection(parameters)
        AMQP_CHANNEL = AMQP_CONNECTION.channel()

        # 1. Declare Queue
        # We use a static name so all 3 replicas read from the SAME queue (Load Balancing)
        AMQP_CHANNEL.queue_declare(queue=AMQP_QUEUE_NAME, durable=True)

        # 2. Bind Queue to 'amq.topic'
        # The MQTT plugin forwards all messages to the 'amq.topic' exchange.
        # We bind our queue to that exchange using the converted binding key (dots instead of slashes).
        print(f"[AMQP] Binding queue '{AMQP_QUEUE_NAME}' to exchange 'amq.topic' with key '{AMQP_BINDING_KEY}'")
        AMQP_CHANNEL.queue_bind(
            exchange='amq.topic', 
            queue=AMQP_QUEUE_NAME, 
            routing_key=AMQP_BINDING_KEY
        )

        # 3. QoS
        AMQP_CHANNEL.basic_qos(prefetch_count=PREFETCH_COUNT)

        # 4. Start Consuming
        AMQP_CHANNEL.basic_consume(queue=AMQP_QUEUE_NAME, on_message_callback=on_message)
        
        print("[AMQP] Waiting for messages...")
        AMQP_CHANNEL.start_consuming()

    except Exception as e:
        print(f"[ERROR] AMQP Connection failed: {e}")
    finally:
        if AMQP_CONNECTION and AMQP_CONNECTION.is_open:
            AMQP_CONNECTION.close()
        if PRODUCER:
            PRODUCER.close()
        print("Shutdown complete")
        sys.exit(0)

if __name__ == "__main__":
    if not init_kafka_producer():
        sys.exit(1)
    consume_amqp()