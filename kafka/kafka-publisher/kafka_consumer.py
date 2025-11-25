from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("KafkaConsumerExample").getOrCreate()

df = spark.readStream.format("kafka") \
    .option("kafka.bootstrap.servers", "my-cluster-kafka-bootstrap.default.svc.cluster.local:9092") \
    .option("subscribe", "test-topic") \
    .load()

df.selectExpr("CAST(key AS STRING)", "CAST(value AS STRING)") \
  .writeStream \
  .format("console") \
  .start() \
  .awaitTermination()
  
  
      #.option("kafka.bootstrap.servers", "my-cluster-kafka-bootstrap.kafka:9092") \
