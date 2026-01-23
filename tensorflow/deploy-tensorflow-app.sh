docker buildx build -t 10.0.1.56:5000/tensorflow-app:2.0.0 --push .

kubectl apply -f tensorflow-app.yaml
