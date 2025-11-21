# à lancer sur le Raspberry Pi avec une caméra connectée

# --------------------------------
# Imports

import subprocess
import cv2
import paho.mqtt.client as mqtt
import base64
import numpy as np
import time
import os

# --------------------------------
# Configuration MQTT

# - broker : adresse du serveur MQTT (ex : "localhost" si Mosquitto est sur ce Raspberry ou "10.0.1.52" si le broker est distant)
# - port : port utilisé par le broker (par défaut 1883)
# - topic : nom du canal où seront envoyées les images
broker = "localhost"
port = 1883
topic = "camera/image"

client = mqtt.Client()
client.connect(broker, port, 60)
tmp_file = "/tmp/frame.jpg"


# --------------------------------
# capturer une image fixe avec la commande raspistill
def capture_image():
    subprocess.run([
        "raspistill",
        "-n",             # no preview
        "-rot", "180",    # rotation de 180°
        "-o", tmp_file,   # fichier de sortie
        "-w", "640",      # largeur
        "-h", "480",      # hauteur
        "-q", "100"       # 100 = qualité max, aucune compression JPEG
    ])


# --------------------------------
# Encodage en base64
def encode_image():
    with open(tmp_file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode("utf-8")


# --------------------------------
# MAIN : capture et envoi d'images toutes les 5 secondes
while True:
    capture_image()
    encoded = encode_image()
    client.publish(topic, encoded)
    print(f"Image sent ({len(encoded)//1024} KB)")
    time.sleep(5)