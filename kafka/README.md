Experimenting with k3d:

- install k3d: docs online

- k3d cluster create <cluster name it doesn't matter>

- ```kubectl create namespace kafka```

- add to the manifest a pod for producing and consuming: 
```
apiVersion: v1
kind: Pod
metadata:
  name: kafka-producer
  namespace: kafka
spec:
  containers:
    - name: kafka-producer
      image: quay.io/strimzi/kafka:latest-kafka-4.1.0
      command: ["sleep", "infinity"]
  restartPolicy: Never
  
---
apiVersion: v1
kind: Pod
metadata:
  name: kafka-consumer
  namespace: kafka
spec:
  containers:
    - name: kafka-consumer
      image: quay.io/strimzi/kafka:latest-kafka-4.1.0
      command: ["sleep", "infinity"]
  restartPolicy: Never
```

- Install Strimzi :
```
kubectl apply -n kafka -f https://strimzi.io/install/latest?namespace=kafka
```

- Apply the manifest :
```kubectl apply -n kafka -f <filename of the kafka manifest>```

- Create a topic :

```
kubectl exec -it kafka-producer -n kafka -- /opt/kafka/bin/kafka-topics.sh \
  --create \
  --bootstrap-server my-cluster-kafka-bootstrap:9092 \
  --topic test-topic \
  --partitions 1 \
  --replication-factor 1
```

- Enter in the producer node to send messages :

```
kubectl exec -it kafka-producer -n kafka -- /opt/kafka/bin/kafka-console-producer.sh \
  --bootstrap-server my-cluster-kafka-bootstrap:9092 \
  --topic test-topic
```

- Enter in the consumer node to read messages : 
```
kubectl exec -it kafka-consumer -n kafka -- /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server my-cluster-kafka-bootstrap:9092 \
  --topic test-topic \
  --from-beginning
```
