FROM apache/spark:3.5.0

USER root

RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    pkg-config \
    libhdf5-dev \
    python3-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --upgrade pip

RUN pip install --no-cache-dir -r requirements.txt

USER spark

WORKDIR /opt/spark-apps
COPY ./spark.py .
COPY ./traitement_image.py .
COPY ./lite3x_detection_metadata.tflite .

COPY jars/ /opt/spark/jars/
