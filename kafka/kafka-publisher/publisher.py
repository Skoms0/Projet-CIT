import base64
import time
from kafka import KafkaProducer

print("héhé")

KAFKA_BOOTSTRAP = "my-cluster-kafka-bootstrap:9092"
TOPIC = "input.images"
FILE_PATH = "example-image.jpeg"
INTERVAL = 5  # secondes

def load_image_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read())



def main():
    print("start main")
    producer = KafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP)
    img_data = load_image_base64(FILE_PATH)
    
    while True:
        print("Envoi d'une image dans Kafka...")
        producer.send(TOPIC, img_data)
        producer.flush()
        time.sleep(INTERVAL)

if __name__ == "__main__":
    main()
