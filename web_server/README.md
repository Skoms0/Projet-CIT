# Kafka Frames → Web Viewer

Deux scripts:
- `server_web.py`: serveur Flask recevant des images JPEG via POST et les affichant sur `http://localhost:5000`
- `kafka_frame_consumer.py`: consumer Kafka lisant des frames (bytes JPEG) depuis un topic et les envoyant au serveur web

## Prérequis
- Python 3.9+
- Kafka accessible (ex: `localhost:9092`)
- pip install -r requirements.txt



build + push :


docker buildx build --platform linux/arm64 -t grouquet/frame-viewer:latest -f Dockerfile.web --push .

docker buildx build --platform linux/arm64 -t grouquet/kafka-frame-consumer:latest -f Dockerfile.consumer --push .



