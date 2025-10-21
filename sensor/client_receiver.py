# à lancer sur le client qui reçoit et sauvegarde l'image

import paho.mqtt.client as mqtt
import base64

BROKER = "localhost"
PORT = 18830
TOPIC = "camera/image"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connecté au broker MQTT")
        client.subscribe(TOPIC)
        print(f"Abonné au topic '{TOPIC}'")
    else:
        print(f"Échec de connexion (code {rc})")

def on_message(client, userdata, msg):
    print("Image reçue, sauvegarde...")
    data = base64.b64decode(msg.payload)
    with open("received_image.jpg", "wb") as f:
        f.write(data)
    print("Image enregistrée sous 'received_image.jpg'")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER, PORT, 60)

print("En attente d'image...")
client.loop_forever()
