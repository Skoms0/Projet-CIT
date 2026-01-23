docker buildx build -t 10.0.1.56:5000/kafka-ingestor:latest --push .

kubectl apply -f redis.yaml
kubectl apply -f kafka-ingestor.yaml
