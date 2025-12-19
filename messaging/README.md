# Etat du projet

Le cluster RabbitMQ est déployable sur K3s
Le master K3S est sur 10.0.1.52

**user:davidra**
**password:davidra**

## Déploiement

Si **rien est encore déployé**:

```bash
sudo ./first_boot
```

Sinon :

Nettoyage et lancement:

```bash
sudo ./cleanup.sh
```

Pour déployer sans nettoyer:

```bash
sudo kubectl apply -f rabbitmqcluster.yml
```

## Côté esclave

Pour déployer côte esclaves (cas d'un nouveau déploiement):
**changer K3S_URL si nous utilisons un autre serveur**

```bash
./client_k3s.sh
```

Token actuel si on utilise le même cluster:

```bash
K3S_TOKEN="K102934f8d6d2ab982cd7f0fdc480c04e9eec7214dc191ededb344a80fbfb1f4a82::server:05ae5f72b069f931cb43ce7ab0540ef6"
```

## Conseil

Côté publisher et subscriber, si la connexion se passe normalement mais qu'aucun message n'est envoyé/recu penser à:

- avoir un clientid unique pour le subscriber surtout

- pour le publisher s'assurer qu'il ne se déconnecte pas avant que le thread d'envoi ne finisse de s'exécuter

- utiliser clean session = False

- utiliser qos =1 si on veut que s'assurer que le message soit consommé au moins une fois

## Sur l'unicité des messages

Les queues subscriber sont automatiquement dupliquées c'est à dire que chaque subscriber obtient une copie du message. Il y a donc possibilité de traiter le message deux fois par la suite coté reactive streaming et app si on ne fait pas attention ou si ce n'est pas le but.

La solution serait d'utiliser les shared sub MQTTv5 mais [RabbitMQ ne prend pas en charge](https://www.rabbitmq.com/docs/mqtt#shared-subscriptions)

Nous avons de la chance que internalement Rabbitmq convertit le tout en une file amqp que l'on peut consommer avec ce protocole, il y a aussi possibilité de faire un bridge kafka mais nous sommes encore en investigation