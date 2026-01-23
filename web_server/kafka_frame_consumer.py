from confluent_kafka import Consumer, KafkaException
import requests
import threading
import os


"""
kafka_frame_consumer.py
---------------------

Ce script agit comme un pont entre Kafka et le serveur web Flask.

- Lit des frames (images JPEG encodées en bytes) dans un topic Kafka.
- Envoie les frames au serveur web via HTTP POST /api/data.
- Utilise un envoi asynchrone pour éviter de bloquer le consumer Kafka.

Dépendances :
- confluent-kafka
- requests
"""

# --------------------------
# CONFIGURATION
# --------------------------

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "test2")
GROUP_ID = os.getenv("GROUP_ID", "consumer-images-only")

WEB_SERVER_URL = os.getenv("WEB_SERVER_URL", "http://localhost:5000/api/data")

# --------------------------
# CONSUMER KAFKA
# --------------------------

def create_consumer():
    config = {
        "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
        "group.id": GROUP_ID,
        "auto.offset.reset": "latest" #pour prendre les dernières frames reçus par le topic sion --> earliest
    }
    consumer = Consumer(config)
    consumer.subscribe([KAFKA_TOPIC])
    return consumer


# --------------------------
# ENVOI AU SERVEUR WEB
# --------------------------

def send_frame_to_web(img_bytes):
    """
    Envoie une image JPEG au serveur web via HTTP POST.
    """
    try:
        response = requests.post(
            WEB_SERVER_URL,
            files={"frame": ("frame.jpg", img_bytes, "image/jpeg")},
            timeout=1
        )
        print(f"[WEB] FRAME {response.status_code}")
    except Exception as e:
        print(f"[ERROR] Envoi FRAME impossible : {e}")


def send_frame_async(img_bytes):
    """
    Envoie l'image dans un thread pour ne pas bloquer Kafka. --> sinon trop de latence entre 2 frames => vidéo saccadée
    """
    threading.Thread(target=send_frame_to_web, args=(img_bytes,), daemon=True).start()


# --------------------------
# MAIN LOOP
# --------------------------

def main():
    consumer = create_consumer()
    print(f"🚀 Consumer Kafka connecté au topic '{KAFKA_TOPIC}' (images uniquement)…")

    try:
        while True:
            msg = consumer.poll(0.01)  # poll rapide (100 Hz)

            if msg is None:
                continue

            if msg.error():
                raise KafkaException(msg.error())

            img_bytes = msg.value()

            # Vérification très basique qu'on a bien du binaire
            if not isinstance(img_bytes, (bytes, bytearray)):
                print("[ERROR] Message Kafka non binaire → ignoré")
                continue

            # Envoi non bloquant
            send_frame_async(img_bytes)

    except KeyboardInterrupt:
        print("\n🛑 Arrêt manuel du consumer Kafka.")

    finally:
        consumer.close()


if __name__ == "__main__":
    main()
