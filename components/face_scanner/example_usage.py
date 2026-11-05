"""Run from the AeroID folder:  python -m components.face_scanner.example_usage"""
from components.face_scanner import FaceScanner, FaceDatabase

db = FaceDatabase()


def next_stage(result):
    photo_bytes = db.get_photo(result["person"]["id"])  # JPEG bytes, or None
    """Replace this with the next part of AeroID (verification, gate control, logging...)."""
    person = result["person"]
    print(f"Detected: {person['name']} | info={person['info']} | similarity={result['score']:.2f}")


def unknown_face(result):
    print("Unknown face detected")


if __name__ == "__main__":
    FaceScanner(db).run(on_match=next_stage, on_unknown=unknown_face)
