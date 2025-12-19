FROM python:3.11-slim

WORKDIR /app

# Copier les dépendances et installer
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le script
COPY rabbitmq_to_kafka.py .

# Exécuter le connecteur
CMD ["python", "-u", "rabbitmq_to_kafka.py"]
