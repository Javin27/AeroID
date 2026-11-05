import cv2
from scanner import get_app

image_path = input("Enter photo path: ")

image = cv2.imread(image_path)

if image is None:
    print("Could not load image.")
    exit()

app = get_app()
faces = app.get(image)

print("Faces detected:", len(faces))

for face in faces:
    x1, y1, x2, y2 = map(int, face.bbox)
    cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)

cv2.imshow("AeroID - Image Detection", image)
cv2.waitKey(0)
cv2.destroyAllWindows()
