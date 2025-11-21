sudo docker exec -it rabbitmq rabbitmqctl add_user davidra davidra
sudo docker exec -it rabbitmq rabbitmqctl set_user_tags davidra administrator
sudo docker exec -it rabbitmq rabbitmqctl set_permissions -p / davidra ".*" ".*" ".*"
