# Add to your Flask app. pip install insightface onnxruntime opencv-python numpy flask-cors
import numpy as np, cv2
from flask import request, jsonify
from insightface.app import FaceAnalysis

face_app = FaceAnalysis(name="buffalo_l")          # the "Buffalo" model pack
face_app.prepare(ctx_id=-1, det_size=(640, 640))    # ctx_id=0 for GPU

# KNOWN: {admission_number: normalized 512-d embedding}. Build it from your student photos.
KNOWN = {}
THRESHOLD = 0.4

@app.post("/api/recognize")
def recognize():
    img = cv2.imdecode(np.frombuffer(request.files["image"].read(), np.uint8), cv2.IMREAD_COLOR)
    faces = face_app.get(img)
    if not faces:
        return jsonify(match=False, error="No face found in the image"), 422
    f = max(faces, key=lambda f: (f.bbox[2]-f.bbox[0]) * (f.bbox[3]-f.bbox[1]))
    best, score = None, -1
    for adm, emb in KNOWN.items():
        s = float(np.dot(f.normed_embedding, emb))
        if s > score: best, score = adm, s
    if best is None or score < THRESHOLD:
        return jsonify(match=False, error="No matching student"), 404
    return jsonify(match=True, admission_number=best, confidence=score, bbox=[float(v) for v in f.bbox])
