#!/bin/bash

# Script pour construire et déployer le connecteur RabbitMQ-Kafka dans k3s

set -e

echo "=== Construction de l'image Docker ==="
docker build -t rabbitmq-kafka-connector:latest .

echo ""
echo "=== Import de l'image dans k3s ==="
# Sauvegarder l'image dans un fichier temporaire
docker save rabbitmq-kafka-connector:latest -o /tmp/rabbitmq-kafka-connector.tar

# Importer l'image dans k3s
sudo k3s ctr images import /tmp/rabbitmq-kafka-connector.tar

# Nettoyer le fichier temporaire
rm /tmp/rabbitmq-kafka-connector.tar

echo ""
echo "=== Déploiement dans k3s ==="
kubectl apply -f rabbitmq-kafka-connector.yaml

echo ""
echo "=== Vérification du déploiement ==="
kubectl get pods -l app=rabbitmq-kafka-connector

echo ""
echo "=== Attente du démarrage du pod ==="
kubectl wait --for=condition=ready pod -l app=rabbitmq-kafka-connector --timeout=60s

echo ""
echo "=== Logs du connecteur ==="
kubectl logs -l app=rabbitmq-kafka-connector --tail=20 -f
