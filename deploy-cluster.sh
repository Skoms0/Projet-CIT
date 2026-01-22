# Start docker registry
docker run -d \
  --restart=always \
  -p 5000:5000 \
  --name registry \
  -v /opt/registry:/var/lib/registry \
  registry:2

# Messaging
cd messaging
chmod +x deploy-rabbitmq.sh
./deploy-rabbitmq.sh
cd ..

# Kafka
cd kafka
chmod +x deploy-kafka.sh
chmod +x initialize-helm.sh
./initialize-helm.sh
./deploy-kafka.sh
cd ..

# Kafka-Rabbitmq
cd kafka-rabbitmq
chmod +x build-and-deploy.sh
./build-and-deploy.sh
cd ..

# Spark
cd spark
chmod +x deploy-spark.sh
./deploy-spark.sh
cd ..

# Tensorflow
cd tensorflow
chmod +x deploy-tensorflow-app.sh
./deploy-tensorflow-app.sh
cd ..

