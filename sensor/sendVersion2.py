import time
import io
import paho.mqtt.client as mqtt
from picamera2 import Picamera2
from PIL import Image

BROKERS = ["10.0.1.13"]
TOPIC = "/cam/h264/cam13"
USERNAME = "davidra"
PASSWORD = "davidra"

def setup_mqtt():
    client = mqtt.Client(client_id="publisher1968", clean_session=False)
    client.username_pw_set(USERNAME, PASSWORD)
    client.connect(BROKERS[0], 1883, 60)
    client.loop_start()
    return client

def capture_and_publish(client, picam2):
    frame = picam2.capture_array()  # Capture rapide en mémoire

    # Convertir en RGB si nécessaire
    img = Image.fromarray(frame)
    if img.mode != "RGB":
        img = img.convert("RGB")  # <-- correction ici

    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=70)  # qualité réduite pour accélérer
    jpeg_bytes = buffer.getvalue()
    
    client.publish(TOPIC, jpeg_bytes, qos=1, retain=False)
    print(f"[INFO] Published frame ({len(jpeg_bytes)} bytes)")

if __name__ == "__main__":
    picam2 = Picamera2()
    picam2.start()
    client = setup_mqtt()

    try:
        while True:
            capture_and_publish(client, picam2)
            time.sleep(2)
    except KeyboardInterrupt:
        pass
    finally:
        picam2.close()
        client.loop_stop()
        client.disconnect()
