import pika
import time
import base64

# Configuration RabbitMQ
RABBITMQ_HOST = "rabbitmq-bootstrap"  # ou l'IP de ton service k8s
RABBITMQ_PORT = 5672
QUEUE_NAME = "/cam/h264/cam13"

# Fichier image à envoyer (exemple)
IMAGE_PATH = "image_example.jpg"

# Connexion à RabbitMQ
connection = pika.BlockingConnection(
    pika.ConnectionParameters(host=RABBITMQ_HOST, port=RABBITMQ_PORT)
)
channel = connection.channel()

# Déclarer la queue (idempotent)
channel.queue_declare(queue=QUEUE_NAME, durable=True)

def send_image(image_path):
    """Lit l'image, encode en base64 et envoie dans RabbitMQ"""
    with open(image_path, "rb") as f:
        img_bytes = f.read()
    # Encode l'image en base64 pour transmission
    img_b64 = base64.b64encode(img_bytes).decode('utf-8')
    
    channel.basic_publish(
        exchange='',
        routing_key=QUEUE_NAME,
        body=img_b64,
        properties=pika.BasicProperties(
            delivery_mode=2  # persistant
        )
    )
    print(f"[x] Image envoyée : {image_path}")

# Envoi périodique
try:
    while True:
        send_image(IMAGE_PATH)
        time.sleep(5)  # toutes les 5 secondes
except KeyboardInterrupt:
    print("Interruption par l'utilisateur")
finally:
    connection.close()
