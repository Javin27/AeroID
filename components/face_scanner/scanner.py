"""Face scanner (InsightFace buffalo_l): camera/image -> detect -> DB lookup -> hand off."""
import time

import cv2
from insightface.app import FaceAnalysis

try:
    from .database import FaceDatabase
except ImportError:  # flat folder (testing)
    from database import FaceDatabase

_app = None


def get_app(use_gpu=False, det_size=(320, 320)):
    """Load the InsightFace model once (downloads buffalo_l on first run)."""
    global _app
    if _app is None:
        providers = (["CUDAExecutionProvider", "CPUExecutionProvider"]
                     if use_gpu else ["CPUExecutionProvider"])
        _app = FaceAnalysis(name="buffalo_l", providers=providers)
        _app.prepare(ctx_id=0 if use_gpu else -1, det_size=det_size)
    return _app


class FaceScanner:
    def __init__(self, db=None, threshold=0.5, margin=0.05, min_det_score=0.6,
                 cooldown=5.0, frame_skip=5, use_gpu=False, det_size=(320, 320)):
        """
        threshold     : min cosine similarity to accept (raise = stricter)
        margin        : best match must beat the next different student by this much
        min_det_score : ignore weak/blurry detections
        cooldown      : seconds before the same student triggers on_match again
        frame_skip    : run recognition on every Nth frame (speed on CPU)
        det_size      : detector input size. (320,320) is fast on a CPU; use (640,640)
                        if people stand far from the camera
        """
        self.db = db or FaceDatabase()
        self.threshold, self.margin = threshold, margin
        self.min_det_score = min_det_score
        self.cooldown, self.frame_skip = cooldown, frame_skip
        self.app = get_app(use_gpu, det_size)
        self._last_seen = {}

    def scan_frame(self, frame_bgr):
        results = []
        for f in self.app.get(frame_bgr):
            if f.det_score < self.min_det_score:
                continue
            person, score = self.db.find(f.normed_embedding, self.threshold, self.margin)
            x1, y1, x2, y2 = (int(v) for v in f.bbox)
            results.append({
                "matched": person is not None,
                "person": person,          # {"id", "name", "info"} or None
                "score": score,            # cosine similarity, higher = better
                "box": (y1, x2, y2, x1),   # top, right, bottom, left
                "embedding": f.normed_embedding,
            })
        return results

    def scan_image(self, path):
        return self.scan_frame(cv2.imread(path))

    def run(self, on_match, on_unknown=None, camera=0, show=True):
        """Webcam loop. Calls on_match(result) per recognised student. 'q' quits."""
        cap = cv2.VideoCapture(camera)
        if not cap.isOpened():
            raise RuntimeError(f"Could not open camera {camera}")
        n, results = 0, []
        try:
            while True:
                ok, frame = cap.read()
                if not ok:
                    break
                if n % self.frame_skip == 0:
                    results = self.scan_frame(frame)
                    for r in results:
                        self._handle(r, on_match, on_unknown)
                n += 1
                if show:
                    for r in results:
                        self._draw(frame, r)
                    cv2.imshow("AeroID - Face Scanner", frame)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break
        finally:
            cap.release()
            cv2.destroyAllWindows()

    def _handle(self, r, on_match, on_unknown):
        now = time.time()
        key = r["person"]["id_group"] if r["matched"] else "unknown"
        if now - self._last_seen.get(key, 0) < self.cooldown:
            return
        self._last_seen[key] = now
        if r["matched"]:
            on_match(r)
        elif on_unknown:
            on_unknown(r)

    @staticmethod
    def _draw(frame, r):
        top, right, bottom, left = r["box"]
        color = (0, 200, 0) if r["matched"] else (0, 0, 255)
        label = r["person"]["name"] if r["matched"] else "Unknown"
        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
        cv2.putText(frame, label, (left, max(top - 8, 15)), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)