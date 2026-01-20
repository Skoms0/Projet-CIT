import os
import signal
import sys
import time
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable
import paho.mqtt.client as mqtt

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

RUNNING = True
PRODUCER = None


# -------------------------
# Graceful Shutdown
# -------------------------
def shutdown_handler(signum, frame):
    global RUNNING
    print("Shutdown signal received...")
    RUNNING = False


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
# MQTT Callbacks
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


# -------------------------
# MQTT Consumer Loop
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
        while RUNNING:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        for client in clients:
            client.loop_stop()
            client.disconnect()
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
    consume_mqtt()
