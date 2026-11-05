"""Add one student.
    python -m components.face_scanner.enroll --name "Rahul" --image photo.jpg --info student_id=2023001
    python -m components.face_scanner.enroll --name "Rahul" --camera --info student_id=2023001
"""
import argparse

import cv2

from database import FaceDatabase, make_thumbnail
from scanner import get_app


try:
    from database import FaceDatabase, make_thumbnail
except ImportError:  # flat folder (testing)
    from database import FaceDatabase, make_thumbnail

def grab_from_camera():
    cap = cv2.VideoCapture(0)
    print("Press SPACE to capture, Q to cancel.")
    frame = None
    while True:
        ok, img = cap.read()
        if not ok:
            break
        cv2.imshow("Enroll", img)
        k = cv2.waitKey(1) & 0xFF
        if k == 32:
            frame = img
            break
        if k == ord("q"):
            break
    cap.release()
    cv2.destroyAllWindows()
    return frame


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--name", required=True)
    p.add_argument("--image")
    p.add_argument("--camera", action="store_true")
    p.add_argument("--info", action="append", default=[], help="key=value (repeatable)")
    a = p.parse_args()

    img = cv2.imread(a.image) if a.image else grab_from_camera()
    if img is None:
        raise SystemExit("No image.")
    faces = get_app().get(img)
    if len(faces) != 1:
        raise SystemExit(f"Need exactly 1 face, found {len(faces)}.")

    info = dict(kv.split("=", 1) for kv in a.info)
    FaceDatabase().add(a.name, faces[0].normed_embedding, info, photo=make_thumbnail(img))
    print(f"Enrolled {a.name}.")


if __name__ == "__main__":
    main()
