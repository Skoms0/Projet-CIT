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

---

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

---

## Installation

Installer les dépendances :

```bash
pip install -r requirements.txt
```

---

## Java Requirement
Ce projet utilise Spark. Il nécessite obligatoirement :

- Java 17 (OpenJDK / Temurin)
- JAVA_HOME correctement configuré

Vérification :

```bash
java -version
```

Doit afficher une version 17.x.

---

## Exécution

Lancer le traitement Spark :

```bash
python spark.py
```

Assurez-vous que :

Kafka est actif,

les topics existent,

les images arrivent dans `input/images`.

---

## Résultat

Chaque image annotée contient :

un cadre autour des personnes détectées,

un score de confiance,

un format JPG adapté au streaming.

Les images peuvent ensuite être affichées, stockées ou consommées par d’autres microservices.

---

## TODO – Développement du module d’affichage Web

### 1. Écrire un script Python pour consommer Kafka
- Se connecter au broker Kafka
- Lire en continu le topic `processed/frames`
- Récupérer la charge utile (Base64)

### 2. Convertir le message Kafka en image
- Décoder Base64 → bytes
- Décompresser JPG → image
- Préparer l’image pour diffusion Web (re-base64 si nécessaire)

### 3. Mettre en place un backend Web pour envoyer les images
Utilisation recommandée : **FastAPI + WebSocket**  
Responsabilités :
- Recevoir les images décodées
- Les transmettre en temps réel aux navigateurs connectés

### 4. Écrire une simple page HTML
- Ouvrir une connexion WebSocket
- Recevoir les images encodées
- Mettre à jour continuellement `<img src=...>` pour afficher le flux