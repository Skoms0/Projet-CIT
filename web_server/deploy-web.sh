docker buildx build -t 10.0.1.56:5000/kafka-web-combo:latest --push .

kubectl apply -f k3s-web.yaml
