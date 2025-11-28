docker buildx build -t tensorflow-app:latest --load .

kubectl apply -f tensorflow-app.yaml