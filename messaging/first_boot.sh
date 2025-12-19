#!/bin/bash

# --- STEP 1: K8s Cleanup ---
kubectl delete statefulset rabbitmq --ignore-not-found
kubectl delete deployment rabbitmq --ignore-not-found
kubectl delete svc rabbitmq-headless rabbitmq-service --ignore-not-found
kubectl delete configmap rabbitmq-config --ignore-not-found
kubectl delete pvc -l app=rabbitmq --ignore-not-found

# --- STEP 2: K3S Restart (Optional: only if you want to wipe the K3S engine too) ---
# /usr/local/bin/k3s-uninstall.sh # Uncomment this to fully wipe K3S

# --- STEP 3: Start/Ensure K3S Master is running with fixed token ---
curl -sfL https://get.k3s.io | K3S_TOKEN="K102934f8d6d2ab982cd7f0fdc480c04e9eec7214dc191ededb344a80fbfb1f4a82" sh -s - server

# --- STEP 4: Deploy RabbitMQ ---
sudo kubectl apply -f rabbitmqcluster.yml