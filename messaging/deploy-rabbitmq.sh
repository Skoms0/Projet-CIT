## We suppose $CAPTORS and $RABBITMQUEUE contains list pf IPs like CAPTORS="10.0.1.12 10.0.1.13"
CAPTORS="10.0.1.13"
RABBITMQUEUE="10.0.1.52 10.0.1.53 10.0.1.54 10.0.1.55"
# Label Captors
for IP in $CAPTORS; do
  NODE=$(kubectl get nodes -o wide | grep -w "$IP" | awk '{print $1}')
  [ ! -z "$NODE" ] && kubectl label node $NODE role=captor --overwrite
done

# Label RabbitMQueue
for IP in $RABBITMQUEUE; do
  NODE=$(kubectl get nodes -o wide | grep -w "$IP" | awk '{print $1}')
  [ ! -z "$NODE" ] && kubectl label node $NODE role=rabbitqueue --overwrite
done


sudo kubectl apply -f rabbitmqcluster.yml
