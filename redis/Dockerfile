WORKDIR /app

# Copier les dépendances et installer
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le script
COPY kafka-ingestor.py .

# Exécuter le connecteur
CMD ["python", "-u", "kafka-ingestor.py"]
