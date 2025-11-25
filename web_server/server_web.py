from flask import Flask, request, Response

"""
server_web.py
--------------

Serveur web Flask affichant en temps réel les images envoyées via /api/data.

- Reçoit exclusivement des images JPEG sous la clé 'frame'
  (en POST multipart/form-data).
- Stocke uniquement la dernière frame reçue (pas d’historique).
- Expose /frame pour récupérer la dernière image.
- La page HTML / affiche la vidéo en rafraîchissant l'image ~20 fps.

Ce serveur correspond à la partie "visualisation" du pipeline vidéo.
 
Dépendances :
- Flask
"""


app = Flask(__name__)

latest_frame = None  # dernière image reçue (bytes JPEG)

@app.route("/api/data", methods=["POST"])
def receive_frame():
    """
    Reçoit une image JPEG envoyée dans la clé 'frame'. (Refuse tout autre format)
    """
    global latest_frame

    # On exige obligatoirement un fichier nommé 'frame'
    if "frame" not in request.files:
        return {"error": "Aucune image reçue (clé 'frame' manquante)."}, 400

    # Lecture de l'image
    file = request.files["frame"]

    # Vérification du mimetype
    if file.mimetype not in ["image/jpeg", "image/jpg"]:
        return {"error": f"Format non supporté : {file.mimetype}. JPEG uniquement."}, 415

    img_bytes = file.read()
    latest_frame = img_bytes

    print("🖼️ Image reçue :", len(img_bytes), "bytes")

    return {"status": "ok"}, 200


@app.route("/frame")
def get_frame():
    """
    Renvoie la dernière image JPEG.
    """
    global latest_frame

    if latest_frame is None:
        return Response(status=204)

    return Response(latest_frame, mimetype="image/jpeg")


@app.route("/")
def index():
    return """
    <html>
      <head>
        <title>Flux vidéo Kafka → Web</title>
        <style>
          body {
            margin: 0;
            padding: 0;
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #222, #444);
            color: white;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
          }

          .container {
            text-align: center;
            background: rgba(255, 255, 255, 0.05);
            padding: 20px 30px;
            border-radius: 12px;
            box-shadow: 0 6px 25px rgba(0,0,0,0.4);
            backdrop-filter: blur(8px);
            border: 1px solid rgba(255,255,255,0.1);
          }

          h1 {
            margin-bottom: 15px;
            font-weight: 300;
            letter-spacing: 1px;
          }

          #video {
            width: 640px;
            max-width: 90vw;
            border-radius: 8px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            border: 2px solid rgba(255,255,255,0.2);
          }

          footer {
            margin-top: 15px;
            font-size: 12px;
            opacity: 0.7;
          }
        </style>
      </head>

      <body>
        <div class="container">
          <h1>🌍 Flux vidéo en direct</h1>

          <img id="video" src="/frame" />

          <footer>
            Kafka → Flask → HTML (20 fps)
          </footer>
        </div>

        <script>
          function refreshFrame() {
            const img = document.getElementById('video');
            img.src = '/frame?ts=' + new Date().getTime();
          }
          setInterval(refreshFrame, 50); // ~20 fps
        </script>
      </body>
    </html>
    """



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
