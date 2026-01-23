from confluent_kafka import Consumer
import redis
import os

r = redis.Redis(host="redis", port=6379)

consumer = Consumer({
    "bootstrap.servers": os.getenv("KAFKA_BOOTSTRAP_SERVERS"),
    "group.id": "frame-ingestor",
    "auto.offset.reset": "latest"
})

consumer.subscribe(["processed.frames"])

while True:
    msg = consumer.poll(0.1)
    if msg and not msg.error():
        r.set("latest_frame", msg.value())
