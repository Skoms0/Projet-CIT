# Etat du projet

En l'état la configuration se fait à la main
Il faudrait créer un fichier .env contenant l'adresse IP du noeud.
Le fichier de configuration est dans **docker-compose.yml**

´´´
docker-compose up -d
´´´
Après il faudrait joindre le cluster en exécutant **cluster-join.sh**

Et il faudrait créer l'user de n'importe quel noeud du cluster

# Prochaine étape

Déploiement K3S
Déploiement sur le noeud des sensors
Interconnexion avec kafka