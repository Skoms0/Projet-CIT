TOKEN_FILE="k3s_token.txt"
K3S_URL="https://10.0.1.56:6443"

if [[ ! -f "$TOKEN_FILE" ]]; then
  echo "Fichier token introuvable"
  exit 1
fi

K3S_TOKEN=$(cat "$TOKEN_FILE")


# Désinstallation si présente
if [ -f /usr/local/bin/k3s-agent-uninstall.sh ]; then
  sudo /usr/local/bin/k3s-agent-uninstall.sh
fi

if [ -f /usr/local/bin/k3s-uninstall.sh ]; then
  sudo /usr/local/bin/k3s-uninstall.sh
fi

# Supprime les images existantes pour être sûr d'avoir la dernière version (car on utilise les tag "latest")
docker images "10.0.1.56:5000/tensorflow-app" -q | xargs -r docker rmi
docker images "10.0.1.56:5000/rabbitmq-kafka-connector" -q | xargs -r docker rmi

# Installation AGENT
sudo curl -sfL https://get.k3s.io | \
  INSTALL_K3S_EXEC="agent" \
  K3S_URL="${K3S_URL}" \
  K3S_TOKEN="${K3S_TOKEN}" \
  sh -

# Registry insecure pour containerd
sudo mkdir -p /etc/rancher/k3s
sudo tee /etc/rancher/k3s/registries.yaml > /dev/null <<'YAML'
mirrors:
  "10.0.1.56:5000":
    endpoint:
      - "http://10.0.1.56:5000"
YAML

sudo tee /etc/docker/daemon.json > /dev/null <<'YAML'
{
  "insecure-registries" : ["10.0.1.56:5000"]
}
YAML


systemctl restart docker

sudo systemctl restart k3s-agent
sudo systemctl status k3s-agent --no-pager


echo "Installation terminée"
