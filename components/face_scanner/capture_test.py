import cv2
import time
from pathlib import Path
from scanner import get_app

app = get_app()
camera = cv2.VideoCapture(0)

Path("captured_images").mkdir(exist_ok=True)

count = 1
last_capture = 0

while camera.isOpened():
    success, frame = camera.read()

    if not success:
        break

    faces = app.get(frame)

    for face in faces:
        x1, y1, x2, y2 = map(int, face.bbox)
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

    cv2.imshow("AeroID - Camera", frame)

    key = cv2.waitKey(1) & 0xFF

    if key == 32 and time.time() - last_capture >= 2:
        cv2.imwrite(f"captured_images/photo_{count}.jpg", frame)
        print("Photo saved!")
        count += 1
        last_capture = time.time()

    elif key == ord("q"):
        break

camera.release()
cv2.destroyAllWindows()