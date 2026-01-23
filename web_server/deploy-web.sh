docker buildx build -t 10.0.1.56:5000/kafka-web-combo:latest --push .

kubectl label node raspberry-3b-1-13 web-disallowed=true


kubectl apply -f k3s-web.yaml
