import base64
import re
import sqlite3
import sys
import traceback
from pathlib import Path

# Make "backend.services..." importable no matter how the script is launched
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cv2
import numpy as np

from flask import Flask, jsonify, request
from flask_cors import CORS

import pandas as pd
from backend.services.face_matcher import FaceMatcher



app = Flask(__name__)

app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024

CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:5174",
                    "http://localhost:5173"]
    }
})


BASE_DIR = Path(__file__).resolve().parent.parent

# Load OpenCV's built-in face detector
CASCADE_PATH = str(
    BASE_DIR / "backend" / "models" / "haarcascade_frontalface_default.xml"
)

face_detector = cv2.CascadeClassifier(CASCADE_PATH)

if face_detector.empty():
    raise RuntimeError("Could not load OpenCV face detector")

# --- Buffalo_L identity matcher (additive; does not touch /api/detect-faces) ---
matcher = FaceMatcher()

# Minimum cosine similarity to count as a match.
MATCH_THRESHOLD = 0.35

TEST_DATA_DIR = BASE_DIR / "test_data"
DATA_DIR = BASE_DIR / "components" / "face_scanner" / "data"

# The students Excel file: the one in face_scanner/data is the main one
_excel_candidates = [
    DATA_DIR / "sample_students.xlsx",
    TEST_DATA_DIR / "sample_students.xlsx",
    TEST_DATA_DIR / "test_records.xlsx",
]
TEST_EXCEL = next((p for p in _excel_candidates if p.exists()), _excel_candidates[0])

# Folders where the face photos can be (checked in this order)
IMAGE_DIRS = [
    TEST_DATA_DIR / "images",
    DATA_DIR / "images",
    TEST_EXCEL.parent / "images",
    TEST_EXCEL.parent,
]

# Optional extra sources for the parent's name (image_code -> parent name)
PARENT_SOURCES = [
    (BASE_DIR / "components" / "face_scanner" / "data" / "aeroid_parents.db",
     "parents", "image_code", "parent_name"),
    (TEST_DATA_DIR / "test_records.db",
     "parent_records", "image_code", "name"),
]

# face key (e.g. 'jr_271') -> student record shown on the page
STUDENT_RECORDS = {}
# lowercase lookup: face key / Test ID / admission number -> face key
LOOKUP = {}


def _snake(text):
    """'Roll Number' -> 'roll_number'"""
    return re.sub(r"[^0-9a-z]+", "_", str(text).strip().lower()).strip("_")


def _to_native(value):
    """Convert pandas/numpy values into things jsonify can handle."""
    if value is None:
        return None
    if isinstance(value, (bytes, bytearray, memoryview)):
        return None
    if isinstance(value, pd.Timestamp):
        return value.date().isoformat()
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return None if np.isnan(value) else float(value)
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value


def _lookup_parent_name(image_code):
    """Look for the parent's name in the small parent databases."""
    for path, table, code_col, name_col in PARENT_SOURCES:
        try:
            if not path.exists() or path.stat().st_size == 0:
                continue
            connection = sqlite3.connect(f"{path.as_uri()}?mode=ro", uri=True)
            try:
                row = connection.execute(
                    f'SELECT "{name_col}" FROM "{table}" WHERE "{code_col}" = ?',
                    (image_code,)
                ).fetchone()
            finally:
                connection.close()
            if row and row[0]:
                return str(row[0])
        except Exception as e:
            print(f"[AeroID] Parent lookup skipped for {path.name}: {e}")
    return None


def _build_student(key, row):
    """Turn one Excel row into the record the frontend shows."""
    data = {_snake(col): _to_native(val) for col, val in row.items()}

    name = data.get("student_name") or data.get("students") or data.get("name")
    data["student_name"] = name
    data["name"] = name

    admission = (
        data.get("admission_number")
        or data.get("test_id")
        or key
    )
    data["admission_number"] = str(admission).strip()

    if not data.get("parent_name"):
        parent = _lookup_parent_name(key)
        if parent:
            data["parent_name"] = parent

    return data


def _enroll_test_identities():
    if not TEST_EXCEL.exists():
        print(f"[AeroID] Enrollment skipped — {TEST_EXCEL} not found")
        return

    df = pd.read_excel(TEST_EXCEL)
    print(f"[AeroID] Using Excel file: {TEST_EXCEL}")
    print(f"[AeroID] Excel columns: {list(df.columns)}")

    for _, row in df.iterrows():
        filename = str(row["Image Filename"]).strip()
        stem = filename.rsplit(".", 1)[0]        # 'jr_271.jpg' -> 'jr_271'
        img_path = next(
            (d / filename for d in IMAGE_DIRS if (d / filename).exists()), None
        )

        if img_path is None:
            print(f"[AeroID] MISSING image: {filename} (looked in {[str(d) for d in IMAGE_DIRS]})")
            continue

        img = cv2.imread(str(img_path))
        if img is None:
            print(f"[AeroID] UNREADABLE: {img_path}")
            continue

        ok = matcher.register_identity(stem, img)
        if ok:
            record = _build_student(stem, row)
            STUDENT_RECORDS[stem] = record
            for ident in (stem, record["admission_number"], record.get("test_id")):
                if ident:
                    LOOKUP[str(ident).strip().lower()] = stem
        print(f"[AeroID] {'Enrolled' if ok else 'NO_FACE'}: {stem} <- {filename}")

    print(f"[AeroID] Identity registry size: {len(matcher.embeddings)}")


_enroll_test_identities()


def find_student(identifier):
    """Find a student by face key, Test ID or admission number."""
    key = LOOKUP.get(str(identifier).strip().lower())
    return STUDENT_RECORDS.get(key) if key else None


# Get total registered students
@app.route("/api/students")
def student_count():
    return jsonify({"total": len(STUDENT_RECORDS)})


# Search for an individual student
@app.route("/api/students/<admission_number>")
def student_details(admission_number):
    student = find_student(admission_number)

    if student is None:
        return jsonify({"error": "Student not found"}), 404

    return jsonify(student)


@app.route("/api/recognize", methods=["POST"])
def recognize():
    if "image" not in request.files:
        return jsonify({"match": False, "error": "No image provided"}), 400

    file = request.files["image"]
    raw = file.read()
    if not raw:
        return jsonify({"match": False, "error": "Empty file"}), 400

    try:
        arr = np.frombuffer(raw, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    except Exception:
        img = None
    if img is None:
        return jsonify({"match": False, "error": "Could not decode image"}), 400

    try:
        results = matcher.match_identity(img, threshold=MATCH_THRESHOLD)
    except Exception as e:
        return jsonify({"match": False, "error": f"Matching failed: {e}"}), 500

    # Debug: shows the real similarity score in your terminal
    print(f"[AeroID] registry={len(matcher.embeddings)} results={results}")

    if not results:
        return jsonify({"match": False, "error": "No face detected"}), 422

    best = results[0]
    if not best["matched"]:
        return jsonify({
            "match": False,
            "error": "No registered face matches this image",
            "confidence": best["confidence"],
            "bbox": best["bbox"],
        }), 404

    student = find_student(best["key"])
    admission_number = student["admission_number"] if student else best["key"]

    return jsonify({
        "match": True,
        "admission_number": admission_number,
        "student": student,
        "confidence": best["confidence"],
        "bbox": best["bbox"],
    }), 200


# Detect faces in a submitted photograph
@app.route("/api/detect-faces", methods=["POST"])
def detect_faces():
    data = request.get_json(silent=True)

    if not data or not isinstance(data.get("image"), str):
        return jsonify({"error": "No image provided"}), 400

    image_data = data["image"]

    if "," not in image_data:
        return jsonify({"error": "Invalid image format"}), 400

    try:
        encoded_image = image_data.split(",", 1)[1]
        image_bytes = base64.b64decode(
            encoded_image,
            validate=True
        )

        image_array = np.frombuffer(
            image_bytes,
            dtype=np.uint8
        )

        image = cv2.imdecode(
            image_array,
            cv2.IMREAD_COLOR
        )

        if image is None:
            return jsonify({"error": "Could not read image"}), 400

        gray = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2GRAY
        )

        faces = face_detector.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(40, 40)
        )

        boxes = [
            {
                "x": int(x),
                "y": int(y),
                "width": int(w),
                "height": int(h)
            }
            for x, y, w, h in faces
        ]

        return jsonify({
            "success": True,
            "face_count": len(boxes),
            "faces": boxes
        })

    except Exception:
        return jsonify({
            "error": "Image processing failed"
        }), 400


@app.errorhandler(Exception)
def handle_unexpected_error(e):
    from werkzeug.exceptions import HTTPException
    if isinstance(e, HTTPException):
        return e
    traceback.print_exc()
    return jsonify({"error": f"Server error: {e}"}), 500


@app.route("/")
def home():
    return jsonify({
        "message": "AeroID Backend is running!"
    })


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )
