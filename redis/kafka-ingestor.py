from confluent_kafka import Consumer
import redis
import os

r = redis.Redis(host="redis", port=6379)

consumer = Consumer({
    "bootstrap.servers": "my-cluster-kafka-bootstrap.default.svc.cluster.local:9092",
    "group.id": "frame-ingestor",
    "auto.offset.reset": "latest"
})

consumer.subscribe(["processed.frames"])

while True:
    msg = consumer.poll(0.1)
    if msg and not msg.error():
        r.set("latest_frame", msg.value())
