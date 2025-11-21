#Assuming 10.0.1.52 is the master

# Stop the RabbitMQ app inside the container
sudo docker exec -it rabbitmq rabbitmqctl stop_app

# Reset the node (clears previous cluster state)
sudo docker exec -it rabbitmq rabbitmqctl reset

# Join the master
sudo docker exec -it rabbitmq rabbitmqctl join_cluster rabbit@10.0.1.52

# Start the app again
sudo docker exec -it rabbitmq rabbitmqctl start_app
