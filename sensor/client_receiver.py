# À lancer sur le PC client qui reçoit et enregistre les images envoyées par le Raspberry

# --------------------------------
# Imports
import paho.mqtt.client as mqtt
import base64


# --------------------------------
# Configuration MQTT

# - broker : adresse du serveur MQTT (ici "localhost" car on passe par un tunnel SSH)
# - port : port local du tunnel (ex : 18830 redirigé vers 10.0.1.2:1883)
# - topic : canal sur lequel les images sont publiées par le Raspberry
BROKER = "localhost"
PORT = 18830
TOPIC = "camera/image"


# --------------------------------
# Fonction exécutée à la connexion au broker
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connecté au broker MQTT")
        client.subscribe(TOPIC)
        print(f"Abonné au topic '{TOPIC}'")
    else:
        print(f"Échec de connexion (code {rc})")

# --------------------------------
# Fonction exécutée à chaque message reçu
def on_message(client, userdata, msg):
    print("Image reçue, sauvegarde...")
    data = base64.b64decode(msg.payload)
    with open("received_image.jpg", "wb") as f:
        f.write(data)
    print("Image enregistrée sous 'received_image.jpg'")

# --------------------------------
# Création et configuration du client MQTT
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER, PORT, 60)

print("En attente d'image...")
client.loop_forever()
