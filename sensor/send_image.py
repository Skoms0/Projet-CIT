#!/usr/bin/env python3
import paho.mqtt.client as mqtt
import argparse
import os

BROKERS = ["10.0.1.52", "10.0.1.53", "10.0.1.54"]
TOPIC = "test/topic"
USERNAME = "davidra"
PASSWORD = "davidra"

def publish_image(image_path):
    if not os.path.isfile(image_path):
        print("[ERROR] image file not found:", image_path)
        return

    with open(image_path, "rb") as f:
        img_bytes = f.read()

    print("[INFO] Loaded image '{}' ({} bytes)".format(image_path, len(img_bytes)))

    for broker in BROKERS:
        client = mqtt.Client(client_id="publisher", clean_session=True)
        client.username_pw_set(USERNAME, PASSWORD)
        try:
            print(f"[INFO] Connecting to {broker} ...")
            client.connect(broker, 1883, 60)
            client.publish(TOPIC, img_bytes, qos=1)
            client.disconnect()
            print(f"[SUCCESS] Image published to broker {broker}")
            return
        except Exception as e:
            print(f"[ERROR] Failed to connect to {broker}: {e}")

    print("[FATAL] Could not publish to any broker.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send one image via MQTT")
    parser.add_argument("--image", type=str, required=True, help="Path to the image")
    args = parser.parse_args()

    publish_image(args.image)
