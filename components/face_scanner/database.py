"""SQLite store for students: name, info (JSON), 512-d InsightFace embedding, thumbnail."""
import json
import sqlite3
from pathlib import Path

import numpy as np

DEFAULT_DB = Path(__file__).with_name("aeroid_faces.db")
DIM = 512


class FaceDatabase:
    def __init__(self, path=DEFAULT_DB):
        self.conn = sqlite3.connect(str(path))
        self.conn.execute(
            """CREATE TABLE IF NOT EXISTS people (
                   id        INTEGER PRIMARY KEY AUTOINCREMENT,
                   name      TEXT NOT NULL,
                   info      TEXT,          -- JSON: student_id, class, ...
                   embedding BLOB NOT NULL, -- 512 x float32, L2-normalised
                   photo     BLOB           -- small JPEG thumbnail
               )"""
        )
        self.conn.commit()
        self.reload()

    def reload(self):
        rows = self.conn.execute("SELECT id, name, info, embedding FROM people").fetchall()
        self.people = [
            {"id": r[0], "name": r[1], "info": json.loads(r[2] or "{}")} for r in rows
        ]
        for p in self.people:  # several photos of one student share a student_id
            p["id_group"] = p["info"].get("student_id", p["id"])
        self.embeddings = (
            np.stack([np.frombuffer(r[3], dtype=np.float32) for r in rows])
            if rows
            else np.empty((0, DIM), dtype=np.float32)
        )

    def add(self, name, embedding, info=None, photo=None, reload=True):
        """reload=False for bulk imports; call db.reload() once at the end."""
        emb = np.asarray(embedding, dtype=np.float32)
        emb = emb / np.linalg.norm(emb)
        self.conn.execute(
            "INSERT INTO people (name, info, embedding, photo) VALUES (?, ?, ?, ?)",
            (name, json.dumps(info or {}), emb.tobytes(), photo),
        )
        self.conn.commit()
        if reload:
            self.reload()

    def get_photo(self, person_id):
        row = self.conn.execute("SELECT photo FROM people WHERE id = ?", (person_id,)).fetchone()
        return row[0] if row else None

    def find(self, embedding, threshold=0.5, margin=0.05):
        """Cosine-similarity search (higher = more similar).
        Returns (person, score) or (None, best_score).
        threshold : minimum similarity to accept
        margin    : best match must beat the best *different* student by this much
        """
        if len(self.embeddings) == 0:
            return None, None
        q = np.asarray(embedding, dtype=np.float32)
        q = q / np.linalg.norm(q)
        sims = self.embeddings @ q
        best = int(np.argmax(sims))
        if sims[best] < threshold:
            return None, float(sims[best])
        group = self.people[best]["id_group"]
        others = [s for s, p in zip(sims, self.people) if p["id_group"] != group]
        if others and (sims[best] - max(others)) < margin:
            return None, float(sims[best])
        return self.people[best], float(sims[best])


def make_thumbnail(bgr_image, max_side=256, quality=85):
    import cv2

    h, w = bgr_image.shape[:2]
    k = max_side / max(h, w)
    if k < 1:
        bgr_image = cv2.resize(bgr_image, (int(w * k), int(h * k)), interpolation=cv2.INTER_AREA)
    ok, buf = cv2.imencode(".jpg", bgr_image, [cv2.IMWRITE_JPEG_QUALITY, quality])
    return buf.tobytes() if ok else None
