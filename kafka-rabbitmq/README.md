# RabbitMQ to Kafka Connector

Ce connecteur transfère automatiquement les messages (images) de RabbitMQ vers Kafka.

## Architecture

- **Source** : RabbitMQ queue `input_queue`
- **Destination** : Kafka topic `input.images`
- **Format** : Données binaires (images JPEG/PNG)

## Prérequis

- Cluster Kubernetes (k3s) en cours d'exécution
- RabbitMQ déployé avec l'utilisateur configuré
- Kafka déployé via Strimzi avec le topic `input.images`
- Docker installé pour construire l'image

## Déploiement

### 1. Construction et déploiement automatique

Le moyen le plus simple est d'utiliser le script automatisé :

```bash
cd kafka/kafka-rabbitmq
./build-and-deploy.sh
```

Ce script effectue automatiquement :

- Construction de l'image Docker
- Import de l'image dans k3s
- Déploiement dans Kubernetes
- Affichage des logs

### 2. Déploiement manuel

#### Étape 1 : Construire l'image Docker

```bash
docker build -t rabbitmq-kafka-connector:latest .
```

#### Étape 2 : Importer l'image dans k3s

```bash
docker save rabbitmq-kafka-connector:latest -o /tmp/rabbitmq-kafka-connector.tar
sudo k3s ctr images import /tmp/rabbitmq-kafka-connector.tar
rm /tmp/rabbitmq-kafka-connector.tar
```

#### Étape 3 : Déployer dans Kubernetes

```bash
kubectl apply -f rabbitmq-kafka-connector.yaml
```

## Configuration

Les variables d'environnement sont définies dans `rabbitmq-kafka-connector.yaml` :

| Variable                  | Valeur par défaut                                           | Description                   |
| ------------------------- | ----------------------------------------------------------- | ----------------------------- |
| `RABBITMQ_HOST`           | `rabbitmq.default.svc.cluster.local`                        | Adresse du serveur RabbitMQ   |
| `RABBITMQ_PORT`           | `5672`                                                      | Port RabbitMQ                 |
| `RABBITMQ_USER`           | `davidra`                                                   | Utilisateur RabbitMQ          |
| `RABBITMQ_PASSWORD`       | `davidra`                                                   | Mot de passe RabbitMQ         |
| `RABBITMQ_QUEUE`          | `input_queue`                                               | Queue RabbitMQ source         |
| `KAFKA_BOOTSTRAP_SERVERS` | `my-cluster-kafka-bootstrap.default.svc.cluster.local:9092` | Serveurs Kafka                |
| `KAFKA_TOPIC`             | `input.images`                                              | Topic Kafka destination       |
| `PREFETCH_COUNT`          | `10`                                                        | Nombre de messages préchargés |

### Modifier la configuration

Éditez `rabbitmq-kafka-connector.yaml` et redéployez :

```bash
kubectl apply -f rabbitmq-kafka-connector.yaml
kubectl rollout restart deployment/rabbitmq-kafka-connector
```

## Vérification

### État du déploiement

```bash
kubectl get pods -l app=rabbitmq-kafka-connector
```

### Logs en temps réel

```bash
kubectl logs -l app=rabbitmq-kafka-connector -f
```

### Statistiques détaillées

```bash
kubectl describe deployment rabbitmq-kafka-connector
kubectl describe pod -l app=rabbitmq-kafka-connector
```

## Surveillance

Le connecteur affiche dans les logs :

- Tentatives de connexion à Kafka (avec retry automatique)
- Connexion établie avec RabbitMQ
- Taille de chaque image transférée
- Erreurs de traitement

Exemple de logs :

```
Attempting to connect to Kafka at my-cluster-kafka-bootstrap.default.svc.cluster.local:9092...
Successfully connected to Kafka!
Connected to RabbitMQ. Waiting for messages...
Image forwarded to Kafka (size: 245678 bytes)
```

## Scalabilité

Le déploiement est configuré avec **3 réplicas** pour assurer la haute disponibilité.

Pour ajuster :

```bash
kubectl scale deployment rabbitmq-kafka-connector --replicas=5
```

## Dépannage

### Pod en CrashLoopBackOff

Vérifiez que Kafka et RabbitMQ sont accessibles :

```bash
kubectl logs -l app=rabbitmq-kafka-connector --tail=50
```

### Kafka non disponible

Le connecteur effectue 10 tentatives (50 secondes) pour se connecter à Kafka. Si Kafka n'est pas encore démarré, attendez que le pod se stabilise.

### RabbitMQ inaccessible

Vérifiez que RabbitMQ est déployé et accessible :

```bash
kubectl get svc rabbitmq
kubectl get pods -l app=rabbitmq
```

### Reconstruire après modification du code

```bash
./build-and-deploy.sh
```

Ou manuellement :

```bash
docker build -t rabbitmq-kafka-connector:latest .
docker save rabbitmq-kafka-connector:latest -o /tmp/rabbitmq-kafka-connector.tar
sudo k3s ctr images import /tmp/rabbitmq-kafka-connector.tar
rm /tmp/rabbitmq-kafka-connector.tar
kubectl rollout restart deployment/rabbitmq-kafka-connector
```

## Nettoyage

Pour supprimer le connecteur :

```bash
kubectl delete -f rabbitmq-kafka-connector.yaml
```
