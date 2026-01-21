export KUBECONFIG=/etc/rancher/k3s/k3s.yaml

helm repo add strimzi https://strimzi.io/charts/
helm repo update
helm upgrade --install strimzi-kafka strimzi/strimzi-kafka-operator -f strimzi-operator-values.yaml # install kafka operator

kubectl apply -f kafka-cluster.yaml # create kafka cluster
