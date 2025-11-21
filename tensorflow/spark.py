from pyspark.sql import SparkSession
from pyspark.sql.functions import udf, col
from pyspark.sql.types import BinaryType

from traitement_image import (
    build_interpreter,
    run_inference_bytes
)



# Configuration
MODEL_PATH = "efficientdet_lite0.tflite"
LABELS = [
    "person", "bicycle", "car", "motorcycle", "airplane", "bus",
    "train", "truck", "boat", "traffic light", "fire hydrant"
]

KAFKA_INPUT_TOPIC = "input/images"
KAFKA_OUTPUT_TOPIC = "processed/frames"
KAFKA_SERVERS = "kafka_server"             # TODO: use real server


 
# Création du UDF Spark
def create_udf():

    def udf_fn(image_bytes):

        if image_bytes is None:
            return None

        # Lazy loading du modèle dans chaque worker Spark
        if not hasattr(udf_fn, "interpreter"):
            print("Loading TFLite model inside Spark worker...")
            udf_fn.interpreter = build_interpreter(MODEL_PATH, num_threads=4)

        # Rappel de l’inférence sur les bytes de l’image
        processed_bytes = run_inference_bytes(
            udf_fn.interpreter,
            image_bytes,
            LABELS,
            threshold=0.3,
            person_only=True
        )

        return processed_bytes

    return udf(udf_fn, BinaryType())



# Programme principal Spark
def main():

    # Création de la session Spark
    spark = SparkSession.builder \
        .appName("SparkTFInference") \
        .config("spark.executor.memory", "2g") \
        .config("spark.driver.memory", "2g") \
        .getOrCreate()

    # UDF d'inférence
    udf_inference = create_udf()

    # Lecture du flux Kafka en entrée
    raw = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_SERVERS) \
        .option("subscribe", KAFKA_INPUT_TOPIC) \
        .load()

    # Application de l'inférence sur la colonne "value"
    processed = raw.withColumn(
        "value",                     # colonne modifiée
        udf_inference(col("value"))  # UDF exécuté image par image
    ).select("value")                # Kafka n'a besoin que du champ "value"

    # Écriture du flux traité vers Kafka
    query = processed.writeStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_SERVERS) \
        .option("topic", KAFKA_OUTPUT_TOPIC) \
        .option("checkpointLocation", "spark_checkpoint_tf") \
        .start()

    # Boucle d’attente : Spark reste actif et traite les images en continu.
    query.awaitTermination()



# Lancement du programme
if __name__ == "__main__":
    main()
