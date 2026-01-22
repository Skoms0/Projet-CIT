export KUBECONFIG=/etc/rancher/k3s/k3s.yaml

helm repo add spark-operator https://kubeflow.github.io/spark-operator
helm repo update
helm upgrade --install spark-operator spark-operator/spark-operator -f spark-operator-values.yaml --set webhook.enable=false

kubectl create sa spark

kubectl create clusterrolebinding spark-role \
  --clusterrole=edit \
  --serviceaccount=default:spark
