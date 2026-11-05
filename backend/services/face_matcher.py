# backend/services/face_matcher.py
import threading
import numpy as np
import cv2

try:
    from insightface.app import FaceAnalysis
except ImportError as e:
    raise RuntimeError(
        "insightface is not installed. Run: pip install insightface onnxruntime"
    ) from e


class FaceMatcher:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.embeddings = {}   # key -> np.ndarray (512,) L2-normalized
        self._init_model()

    def _init_model(self):
        # CPU by default; downloads buffalo_l (~326 MB) on first run to ~/.insightface/
        self.app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
        self.app.prepare(ctx_id=-1, det_size=(640, 640))

    # --- internal ---
    def _analyze(self, image_bgr: np.ndarray):
        """Return list of (bbox_xyxy, embedding) for all valid faces, largest first."""
        if image_bgr is None or image_bgr.size == 0:
            return []
        try:
            faces = self.app.get(image_bgr)
        except Exception:
            return []

        results = []
        for f in faces:
            x1, y1, x2, y2 = f.bbox
            if (x2 - x1) < 20 or (y2 - y1) < 20:
                continue  # skip tiny detections
            results.append(([float(x1), float(y1), float(x2), float(y2)],
                            f.normed_embedding.astype(np.float32)))

        results.sort(key=lambda t: (t[0][2] - t[0][0]) * (t[0][3] - t[0][1]),
                     reverse=True)
        return results

    # --- public API ---
    def register_identity(self, key: str, image_bgr: np.ndarray) -> bool:
        """Enroll one identity. Uses the largest face in the image."""
        faces = self._analyze(image_bgr)
        if not faces:
            return False
        self.embeddings[key] = faces[0][1]
        return True

    def match_identity(self, image_bgr: np.ndarray, threshold: float = 0.45):
        """
        Returns list of dicts, one per detected face:
        { bbox: [x1,y1,x2,y2], key: str|None, confidence: float, matched: bool }
        Only the largest face is scored; smaller faces are still returned
        with matched=False so the UI can draw boxes if desired.
        """
        faces = self._analyze(image_bgr)
        if not faces:
            return []

        out = []
        for idx, (bbox, emb) in enumerate(faces):
            if idx == 0 and self.embeddings:
                best_key, best_score = None, 0.0
                for key, ref in self.embeddings.items():
                    score = float(np.dot(emb, ref))   # cosine (both L2-normalized)
                    if score > best_score:
                        best_score, best_key = score, key
                matched = best_score >= threshold
                out.append({
                    "bbox": bbox,
                    "key": best_key if matched else None,
                    "confidence": round(best_score, 4),
                    "matched": matched,
                })
            else:
                out.append({"bbox": bbox, "key": None,
                            "confidence": 0.0, "matched": False})
        return out