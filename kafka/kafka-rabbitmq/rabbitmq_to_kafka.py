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
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq.default.svc.cluster.local")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "1883"))
RABBITMQ_BROKERS = [RABBITMQ_HOST]
RABBITMQ_QUEUE = os.getenv("RABBITMQ_QUEUE", "/cam/h264/cam13")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "davidra")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "davidra")

KAFKA_BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP_SERVERS",
    "my-cluster-kafka-bootstrap.default.svc.cluster.local:9092",
)
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
            print(
                f"Error connecting to Kafka (attempt {retry_count}/{max_retries}): {e}"
            )
            time.sleep(5)

    print("Failed to connect to Kafka after max retries")
    return False


# -------------------------
# AMQP Callback
# -------------------------
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"[MQTT] Connected successfully to {userdata['broker']}")
        client.subscribe(RABBITMQ_QUEUE, qos=1)
    else:
        print(f"[MQTT] Connection failed with code {rc}")


def on_message(client, userdata, msg):
    try:
        if PRODUCER is None:
            raise RuntimeError("Kafka producer not initialized")

        # Envoi direct à Kafka
        PRODUCER.send(KAFKA_TOPIC, value=msg.payload)
        PRODUCER.flush()
        print(
            f"[MQTT -> Kafka] Forwarded message from topic {msg.topic} ({len(msg.payload)} bytes)"
        )

    except Exception as e:
        print(f"[ERROR] Failed to forward message: {e}")
        # Nack so another pod can try
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)


# -------------------------
# AMQP Consumer Loop
# -------------------------
def consume_mqtt():
    clients = []
    for broker in RABBITMQ_BROKERS:
        client = mqtt.Client(
            client_id=f"mqtt2kafka-{broker}",
            clean_session=False,
            userdata={"broker": broker},
        )
        client.username_pw_set(RABBITMQ_USER, RABBITMQ_PASSWORD)
        client.on_connect = on_connect
        client.on_message = on_message
        try:
            client.connect(broker, RABBITMQ_PORT, 60)
            client.loop_start()
            clients.append(client)
        except Exception as e:
            print(f"[ERROR] Could not connect to MQTT broker {broker}: {e}")

    # Boucle principale de maintien
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


# -------------------------
# Main
# -------------------------
if __name__ == "__main__":
    if not init_kafka_producer():
        sys.exit(1)
    consume_amqp()