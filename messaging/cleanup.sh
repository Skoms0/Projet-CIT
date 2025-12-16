# 1. Delete the workload controllers
kubectl delete statefulset rabbitmq
kubectl delete deployment rabbitmq
kubectl delete daemonset rabbitmq

# 2. Delete the services and config
kubectl delete svc rabbitmq-headless rabbitmq-service
kubectl delete configmap rabbitmq-config
kubectl delete sa rabbitmq
kubectl delete role rabbitmq
kubectl delete rolebinding rabbitmq

# 3. CRITICAL: Delete the storage volumes (PVCs)
# If you don't do this, the new pods will try to attach to old, corrupted data.
kubectl delete pvc -l app=rabbitmq