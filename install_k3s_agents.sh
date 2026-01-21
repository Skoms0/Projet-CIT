#!/bin/bash

# Utilisateur SSH
USER="root"

# IPs des Raspberry Pi
HOSTS=(
  10.0.1.13
  10.0.1.52
  10.0.1.53
  10.0.1.54
  10.0.1.55
)

# Lecture du token depuis le fichier
TOKEN_FILE="k3s_token.txt"

if [[ ! -f "$TOKEN_FILE" ]]; then
  echo "Fichier token introuvable : $TOKEN_FILE"
  exit 1
fi

K3S_TOKEN=$(cat "$TOKEN_FILE")

K3S_URL="https://10.0.1.56:6443"


for HOST in "${HOSTS[@]}"; do
  echo "Installation K3s agent sur $HOST"

ssh -o ConnectTimeout=5 ${USER}@${HOST} "bash -s" <<EOF &
curl -sfL https://get.k3s.io | \
  K3S_URL=${K3S_URL} \
  K3S_TOKEN=${K3S_TOKEN} \
  sh -

# Création du fichier registries.yaml
sudo mkdir -p /etc/rancher/k3s
sudo tee /etc/rancher/k3s/registries.yaml > /dev/null <<YAML
mirrors:
  "10.0.1.56:5000":
    endpoint:
      - "http://10.0.1.56:5000"
YAML

# Redémarrage de l’agent K3s
sudo systemctl restart k3s-agent

# Création du daemon.json
sudo tee /etc/docker/daemon.json > /dev/null <<JSON
{
  "insecure-registries" : ["10.0.1.56:5000"]
}
JSON

sudo systemctl restart docker
EOF

done

wait
echo "Installation terminée sur toutes les machines"

