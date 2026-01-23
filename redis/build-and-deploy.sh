docker buildx build -t 10.0.1.56:5000/kafka-ingestor:latest --push .

#kubectl apply -f redis.yaml
helm repo add bitnami https://charts.bitnami.com/bitnami
helm install redis bitnami/redis \
  --set architecture=replication

kubectl apply -f kafka-ingestor.yaml

