# Désinstallation si présente
if [ -f /usr/local/bin/k3s-agent-uninstall.sh ]; then
  sudo /usr/local/bin/k3s-agent-uninstall.sh
fi

if [ -f /usr/local/bin/k3s-uninstall.sh ]; then
  sudo /usr/local/bin/k3s-uninstall.sh
fi

curl -sfL https://get.k3s.io | sh -

