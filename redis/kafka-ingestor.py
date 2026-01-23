from confluent_kafka import Consumer, KafkaException
import redis
import os
import time

# ------------------------
# CONFIGURATION
# ------------------------

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "processed.frames")
KAFKA_GROUP_ID = os.getenv("KAFKA_GROUP_ID", "frame-ingestor")

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_KEY = os.getenv("REDIS_KEY", "latest_frame")

# ------------------------
# REDIS CLIENT
# ------------------------

def create_redis_client():
    return redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        decode_responses=False  # on stocke les bytes
    )

# ------------------------
# KAFKA CONSUMER
# ------------------------

def create_kafka_consumer():
    config = {
        "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
        "group.id": KAFKA_GROUP_ID,
        "auto.offset.reset": "latest",
        "enable.auto.commit": True,
        "session.timeout.ms": 10000,
    }
    consumer = Consumer(config)
    consumer.subscribe([KAFKA_TOPIC])
    return consumer

# ------------------------
# MAIN LOOP
# ------------------------

def main():
    print("🚀 Kafka → Redis Ingestor démarré")
    consumer = create_kafka_consumer()
    redis_client = create_redis_client()

    last_redis_error = 0

    try:
        while True:
            msg = consumer.poll(0.1)
            if msg is None:
                continue

            if msg.error():
                raise KafkaException(msg.error())

            frame = msg.value()
            if frame is None:
                continue

            try:
                redis_client.set(REDIS_KEY, frame)
            except Exception as e:
                now = time.time()
                if now - last_redis_error > 5:
                    print(f"⚠️ Redis indisponible : {e}")
                    last_redis_error = now
                time.sleep(0.5)
                redis_client = create_redis_client()

    except KeyboardInterrupt:
        print("\n🛑 Arrêt du consumer Kafka")

    finally:
        consumer.close()

if __name__ == "__main__":
    main()
