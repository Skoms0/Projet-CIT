import time
from kafka import KafkaProducer

# Configuration
KAFKA_BOOTSTRAP = "my-cluster-kafka-bootstrap:9092"
TOPIC = "input.images"
FILE_PATH = "example-image.jpeg"
INTERVAL = 5  # secondes

# Lecture du fichier en bytes
def load_image_bytes(path):
    with open(path, "rb") as f:
        return f.read()

def main():
    print("Démarrage du producteur Kafka...")
    producer = KafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP)
    img_data = load_image_bytes(FILE_PATH)

    while True:
        print(f"Envoi d'une image de {len(img_data)} bytes dans Kafka...")
        producer.send(TOPIC, img_data)
        producer.flush()
        time.sleep(INTERVAL)

if __name__ == "__main__":
    main()

