FROM apache/spark:3.5.0

# Installer kafka-python si nécessaire

USER root

RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install -r ./requirements.txt

USER spark

# Copier le script Python
WORKDIR /opt/spark-apps
COPY ./spark.py .
COPY ./traitement_image.py .
COPY ./lite3x_detection_metadata.tflite .
# Copier les jars Kafka
COPY jars/ /opt/spark/jars/
