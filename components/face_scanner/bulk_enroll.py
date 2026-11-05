"""Import many students from a folder of photos.
Name files:  2023001_Rahul Sharma.jpg   (extra photos: 2023001_Rahul Sharma_2.jpg)
    python -m components.face_scanner.bulk_enroll path\\to\\photos [--db students.db]
"""
import argparse
import re
from pathlib import Path

import cv2

from database import FaceDatabase, make_thumbnail
from scanner import get_app

EXTS = {".jpg", ".jpeg", ".png"}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("folder")
    p.add_argument("--db", default=None)
    a = p.parse_args()

    db = FaceDatabase(a.db) if a.db else FaceDatabase()
    app = get_app()
    ok = skipped = 0
    for f in sorted(Path(a.folder).iterdir()):
        if f.suffix.lower() not in EXTS:
            continue
        m = re.match(r"^([^_]+)_([^_]+)(?:_\d+)?$", f.stem)
        img = cv2.imread(str(f))
        if not m or img is None:
            print(f"SKIP (bad name/unreadable): {f.name}")
            skipped += 1
            continue
        faces = app.get(img)
        if len(faces) != 1:
            print(f"SKIP ({len(faces)} faces): {f.name}")
            skipped += 1
            continue
        db.add(m.group(2), faces[0].normed_embedding, {"student_id": m.group(1)},
               photo=make_thumbnail(img), reload=False)
        ok += 1
        if ok % 100 == 0:
            print(f"{ok} enrolled...")
    db.reload()
    print(f"Done. Enrolled {ok}, skipped {skipped}.")


if __name__ == "__main__":
    main()
