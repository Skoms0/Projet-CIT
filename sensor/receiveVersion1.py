import paho.mqtt.client as mqtt

BROKER = "10.0.1.52"
USERNAME = "davidra"
PASSWORD = "davidra"
TOPIC = "/cam/h264/#"
QOS = 1

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"[SUB] Connected to broker {client._host}")
        client.subscribe(TOPIC, qos=QOS)
    else:
        print(f"[SUB] Connection failed with code {rc}")

def on_message(client, userdata, msg):
    print(f"[SUB] Received {len(msg.payload)} bytes on topic {msg.topic}")
    # optional: save to file
    with open("received.jpg", "wb") as f:
        f.write(msg.payload)

client = mqtt.Client(client_id="subscriber1", clean_session=True)
client.username_pw_set(USERNAME, PASSWORD)
client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER, 1883)
client.loop_forever()