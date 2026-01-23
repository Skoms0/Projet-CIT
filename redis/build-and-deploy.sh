docker buildx build -t 10.0.1.56:5000/kafka-ingestor:1.0.0 --push .

kubectl apply -f kafka-ingestor.yaml

#kubectl apply -f redis.yaml


