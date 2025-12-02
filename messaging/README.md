# Etat du projet

Le cluster RabbitMQ est déployable sur K3s
Le master K3S est sur 10.0.1.52

**user:davidra**
**password:davidra**

## Déploiement

Nettoyage:

```bash
sudo ./cleanup.sh
```

Pour déployer:

```bash
sudo kubectl apply -f rabbitmqcluster.yml
```

## Côté esclave

Pour déployer côte esclaves:

```bash
./client_k3s.sh
```

## Conseil

Côté publisher et subscriber, si la connexion se passe normalement mais qu'aucun message n'est envoyé/recu penser à:

- avoir un clientid unique pour le subscriber surtout

- pour le publisher s'assurer qu'il ne se déconnecte pas avant que le thread d'envoi ne finisse de s'exécuter

- utiliser clean session = False

- utiliser qos =1 si on veut que s'assurer que le message soit consommé au moins une fois
