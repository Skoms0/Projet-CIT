kubectl create namespace kafka

kubectl apply -f https://strimzi.io/install/latest?namespace=kafka -n kafka
kubectl apply -f kafka-cluster.yaml -n kafka
kubectl apply -f kafka-connect/kafka-connect.yaml -n kafka