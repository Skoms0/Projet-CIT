#!/usr/bin/env python3
import paho.mqtt.client as mqtt
import argparse
import os

BROKERS = ["10.0.1.13"]
TOPIC = "/cam/h264/cam13"
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
        client = mqtt.Client(client_id="publisher1968", clean_session=False)
        client.username_pw_set(USERNAME, PASSWORD)
        try:
            print(f"[INFO] Connecting to {broker} ...")
            client.connect(broker, 1883, 60)
            print(f"[INFO] Connection success")
            client.loop_start()
            msg_info=client.publish(TOPIC, img_bytes, qos=1, retain=False)
            msg_info.wait_for_publish()
            client.loop_stop()
            client.disconnect()
            print(f"[SUCCESS] Image published to broker {broker}")
            return
        except Exception as e:
            print(f"[ERROR] Failed to connect to {broker}: {e}")

    print("[FATAL] Could not publish to any broker.")

if __name__ == "__main__":
    publish_image("image.jpg")
