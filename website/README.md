# AeroID
npm install && npm run dev   (API base: VITE_API_URL, default http://127.0.0.1:5000)

Flow: Drone vision tab -> Capture frame -> Scan -> Face scan tab -> Identify person
 1. POST /api/recognize (multipart field "image")  -> { match, admission_number, confidence, bbox }
 2. GET  /api/students/{admission_number}          -> student record
Backend example: backend/recognize_route.py (InsightFace buffalo_l). Flask needs CORS enabled.
