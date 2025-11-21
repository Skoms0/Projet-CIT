# Module TensorFlow Lite + Spark Streaming

## Rôle du module
Cette partie du projet réalise **l’analyse d’images en temps réel** grâce à un modèle **TensorFlow Lite**.  
Elle reçoit des images encodées (bytes JPG), exécute la détection de personnes, annote l’image, puis renvoie le résultat dans un flux Kafka.

Pipeline cible :
Capteurs → MQTT/RabbitMQ → Kafka → Spark Streaming → TensorFlow Lite → Kafka → Web/Stockage

Le module permet :
- le chargement du modèle TFLite (EfficientDet Lite0),
- la détection d’objets image par image,
- l’annotation (bounding boxes),
- l’intégration dans Spark via un **UDF**.



## Structure des fichiers

### `traitement_image.py`
- Chargement du modèle TFLite  
- Fonction d’inférence  
- Conversion `bytes ↔ image`  
- Module réutilisable, compatible Spark/Kafka

### `spark.py`
- Lit les images depuis Kafka `input/images`
- Applique l’inférence via un UDF Spark
- Renvoie les images annotées dans `processed/frames`



## Installation

Installer les dépendances :

```bash
pip install -r requirements.txt
```

---

Ce projet utilise Spark. Il nécessite obligatoirement :

- Java 17 (OpenJDK / Temurin)
- JAVA_HOME correctement configuré

Vérification :

```bash
java -version
```

Doit afficher une version 17.x.

---

Ce projet utilise aussi 3 fichiers .jar :

1. spark-sql-kafka-0-10_2.13-3.5.0.jar
https://repo1.maven.org/maven2/org/apache/spark/spark-sql-kafka-0-10_2.13/3.5.0/spark-sql-kafka-0-10_2.13-3.5.0.jar

2. spark-token-provider-kafka-0-10_2.13-3.5.0.jar
https://repo1.maven.org/maven2/org/apache/spark/spark-token-provider-kafka-0-10_2.13/3.5.0/spark-token-provider-kafka-0-10_2.13-3.5.0.jar

3. kafka-clients-3.5.0.jar
https://repo1.maven.org/maven2/org/apache/kafka/kafka-clients/3.5.0/kafka-clients-3.5.0.jar

Dans PowerShell, exécuter :

```bash
python
```
```bash
import pyspark, os
print(os.path.dirname(pyspark.__file__))
```

La sortie sera du type :

`C:\Users\xxx\AppData\Local\Programs\Python\Python311\Lib\site-packages\pyspark`

Ouvrir ensuite :

`pyspark\jars`

C’est dans ce dossier que les JAR Kafka doivent être copiés.



## Exécution

Lancer le traitement Spark :

```bash
python spark.py
```

Assurez-vous que :

Kafka est actif,

les topics existent,

les images arrivent dans `input/images`.



## Résultat

Chaque image annotée contient :

un cadre autour des personnes détectées,

un score de confiance,

un format JPG adapté au streaming.

Les images peuvent ensuite être affichées, stockées ou consommées par d’autres microservices.
