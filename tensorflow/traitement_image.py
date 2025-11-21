import numpy as np
import cv2
import tensorflow as tf



# Chargement du modèle TensorFlow Lite
def build_interpreter(model_path: str, num_threads=4):

    interpreter = tf.lite.Interpreter(model_path=model_path, num_threads=num_threads)
    interpreter.allocate_tensors()
    return interpreter 



# Exécution de l’inférence brute
def detect_objects(interpreter, image_rgb):

    # Récupération des paramètres d'entrée / sortie
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    h, w = input_details[0]['shape'][1:3]  # taille attendue par le modèle

    # Redimensionnement de l'image pour l'entrée du réseau
    resized = cv2.resize(image_rgb, (w, h))
    input_data = np.expand_dims(resized, axis=0)

    # Normalisation éventuelle (EfficientDet Lite attend [-1, 1])
    if input_details[0]['dtype'] == np.float32:
        input_data = (input_data - 127.5) / 127.5

    # Envoi dans le modèle
    interpreter.set_tensor(input_details[0]['index'], input_data)
    interpreter.invoke()

    # Extraction des prédictions
    boxes = interpreter.get_tensor(output_details[0]['index'])[0]
    classes = interpreter.get_tensor(output_details[1]['index'])[0].astype(int)
    scores = interpreter.get_tensor(output_details[2]['index'])[0]

    return boxes, classes, scores



# Visualisation : dessin des boîtes sur l’image
def visualize(frame, boxes, classes, scores, labels, threshold=0.3, person_only=True):

    H, W, _ = frame.shape

    for i, score in enumerate(scores):
        if score < threshold:
            continue

        # Nom de la classe
        name = labels[classes[i]] if classes[i] < len(labels) else "obj"

        # Filtrer uniquement les personnes
        if person_only and name != "person":
            continue

        # Conversion coordonnées normalisées → pixels
        ymin, xmin, ymax, xmax = boxes[i]
        x1, y1 = int(xmin * W), int(ymin * H)
        x2, y2 = int(xmax * W), int(ymax * H)

        # Dessin de la boîte
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        # Texte (classe + score)
        cv2.putText(frame, f"{name} {score:.2f}", (x1, y1 - 5),
                    cv2.FONT_HERSHEY_PLAIN, 1.2, (255, 255, 255), 2)

    return frame



# Pipeline complet : octets → inférence → octets
def run_inference_bytes(interpreter, image_bytes, labels, threshold=0.3, person_only=True):

    # Décodage : bytes → image
    frame = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
    if frame is None:
        return None

    # Conversion BGR → RGB pour le réseau
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Inférence TFLite
    boxes, classes, scores = detect_objects(interpreter, rgb)

    # Visualisation
    frame = visualize(frame, boxes, classes, scores, labels, threshold=threshold, person_only=person_only)

    # Encodage en JPG
    ok, jpeg = cv2.imencode(".jpg", frame)
    if not ok:
        return None

    return jpeg.tobytes()
