Experimenting with k3d:

- install k3d: docs online

- k3d cluster create <cluster name it doesn't matter>

- ```kubectl create namespace kafka```

- ```kubectl apply -n kafka -f <filename of the kafka manifest>


Create a topic :

```
kubectl exec -it kafka-producer -n kafka -- /opt/kafka/bin/kafka-topics.sh \
  --create \
  --bootstrap-server my-cluster-kafka-bootstrap:9092 \
  --topic test-topic \
  --partitions 1 \
  --replication-factor 1
```

Enter in the producer node to send messages :

```
kubectl exec -it kafka-producer -n kafka -- /opt/kafka/bin/kafka-console-producer.sh \
  --bootstrap-server my-cluster-kafka-bootstrap:9092 \
  --topic test-topic
```

Enter in the consumer node to read messages : 
```
kubectl exec -it kafka-consumer -n kafka -- /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server my-cluster-kafka-bootstrap:9092 \
  --topic test-topic \
  --from-beginning
```
