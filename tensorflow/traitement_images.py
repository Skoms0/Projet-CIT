# ===============================================
# Détection de personnes en temps réel
# Kafka (images encodées) → TensorFlow Lite → OpenCV
# Compatible Windows / macOS / Linux
# pip install -r requirements.txt
# ===============================================

import time
import base64
import numpy as np
import cv2
import tensorflow as tf
from kafka import KafkaConsumer

# ==================== PARAMÈTRES ====================
MODEL_PATH = "efficientdet_lite0.tflite"   # Modèle TFLite
KAFKA_SERVER = "a_completer"               # Adresse du broker Kafka
KAFKA_TOPIC = "a_completer"                # Nom du topic Kafka
NUM_THREADS = 4
SCORE_THRESHOLD = 0.3
FILTER_PERSON_ONLY = True

LABELS = [
    "person", "bicycle", "car", "motorcycle", "airplane", "bus",
    "train", "truck", "boat", "traffic light", "fire hydrant"
]

# ==================== TFLITE BACKEND ====================
def build_interpreter(model_path: str, num_threads=4):
    """Charge et prépare un modèle TFLite."""
    interpreter = tf.lite.Interpreter(model_path=model_path, num_threads=num_threads)
    interpreter.allocate_tensors()
    return interpreter

def detect_objects(interpreter, image_rgb):
    """Exécute l'inférence brute avec TensorFlow Lite."""
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    h, w = input_details[0]['shape'][1:3]
    resized = cv2.resize(image_rgb, (w, h))
    input_data = np.expand_dims(resized, axis=0)
    if input_details[0]['dtype'] == np.float32:
        input_data = (input_data - 127.5) / 127.5
    interpreter.set_tensor(input_details[0]['index'], input_data)
    interpreter.invoke()
    boxes = interpreter.get_tensor(output_details[0]['index'])[0]
    classes = interpreter.get_tensor(output_details[1]['index'])[0].astype(int)
    scores = interpreter.get_tensor(output_details[2]['index'])[0]
    return boxes, classes, scores

# ==================== VISUALISATION ====================
def visualize(frame, boxes, classes, scores, labels, threshold=0.3, person_only=True):
    """Dessine les boîtes de détection."""
    imH, imW, _ = frame.shape
    for i, score in enumerate(scores):
        if score < threshold:
            continue
        name = labels[classes[i]] if classes[i] < len(labels) else "obj"
        if person_only and name.lower() != "person":
            continue
        ymin, xmin, ymax, xmax = boxes[i]
        x1, y1 = int(xmin * imW), int(ymin * imH)
        x2, y2 = int(xmax * imW), int(ymax * imH)
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        label = f"{name} {score:.2f}"
        cv2.putText(frame, label, (x1, max(15, y1 - 8)),
                    cv2.FONT_HERSHEY_PLAIN, 1.2, (255, 255, 255), 2)
    return frame

# ==================== MAIN ====================
def main():
    print("=======================================")
    print("Détection de personnes en temps réel")
    print(f"Modèle : {MODEL_PATH}")
    print(f"Kafka : {KAFKA_SERVER}")
    print(f"Topic : {KAFKA_TOPIC}")
    print("=======================================")

    # Chargement du modèle et initialisation Kafka
    interpreter = build_interpreter(MODEL_PATH, NUM_THREADS)
    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_SERVER,
        auto_offset_reset="latest",
        enable_auto_commit=True,
        group_id="tflite_display"
    )
    print("[OK] Modèle chargé et Kafka connecté.")
    print("Appuyez sur 'ESC' pour quitter.")

    cnt, fps, t0 = 0, 0.0, time.time()
    AVG_WIN = 10

    for msg in consumer:
        try:
            # Décodage base64 → image
            img_bytes = base64.b64decode(msg.value)
            frame = cv2.imdecode(np.frombuffer(img_bytes, np.uint8), cv2.IMREAD_COLOR)
            if frame is None:
                continue
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Inférence
            boxes, classes, scores = detect_objects(interpreter, rgb)

            # Visualisation
            frame = visualize(frame, boxes, classes, scores, LABELS,
                              threshold=SCORE_THRESHOLD, person_only=FILTER_PERSON_ONLY)

            # FPS
            cnt += 1
            if cnt % AVG_WIN == 0:
                t1 = time.time()
                fps = AVG_WIN / (t1 - t0)
                t0 = t1
            cv2.putText(frame, f"FPS: {fps:.1f}", (10, 28),
                        cv2.FONT_HERSHEY_PLAIN, 1.4, (0, 0, 255), 2)

            # Affichage
            cv2.imshow("Person Detection (Kafka + TensorFlow Lite)", frame)
            if cv2.waitKey(1) == 27:
                break

        except Exception as e:
            print("[ERREUR]", e)

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
