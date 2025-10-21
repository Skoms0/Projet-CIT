# à lancer sur le Raspberry Pi avec une caméra connectée

import subprocess
import cv2
import paho.mqtt.client as mqtt
import base64
import numpy as np
import time
import os

broker = "localhost"
topic = "camera/image"

client = mqtt.Client()
client.connect(broker, 1883, 60)
tmp_file = "/tmp/frame.jpg"

def capture_image():
    subprocess.run([
        "raspistill",
        "-n",             # no preview
        "-rot", "180",    # rotation de 180°
        "-o", tmp_file,   # output file
        "-w", "640",      # width
        "-h", "480",      # height
        "-q", "100"       # 100 = qualité max, aucune compression JPEG
    ])

def encode_image():
    with open(tmp_file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode("utf-8")

# Boucle principale : capture et envoi d'images toutes les 5 secondes
while True:
    capture_image()
    encoded = encode_image()
    client.publish(topic, encoded)
    print(f"Image sent ({len(encoded)//1024} KB)")
    time.sleep(5)