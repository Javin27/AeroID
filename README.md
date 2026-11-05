## ⚡ Instructions

### Yokai Javin

### 1. Backend

From the project root:

```bash
pip install -r requirements.txt
python backend\app.py
```

The API runs at **http://127.0.0.1:5000**.
> The first start downloads the face model (~326 MB) and loads every student photo, so give it a moment.

### 2. Frontend

In a second terminal:

```bash
cd website
npm install
npm run dev
```

Open the link Vite prints (usually **http://localhost:5173**).

---

## 🧑‍🎓 Adding Students

1. Add a row to `components/face_scanner/data/sample_students.xlsx`

   | Image Code | Image Filename | Students | Test ID |
   |------------|----------------|----------|---------|
   | jr_271     | jr_271.jpg     | Javin    | T271    |

2. Put the photo in `test_data/images/`
3. Restart the backend

---

## 📁 Project Structure

```
AeroID/
├── backend/                       # Flask API + face matching
│   ├── app.py
│   └── services/face_matcher.py
├── website/                       # React + Vite frontend
├── components/face_scanner/data/  # Student Excel file
├── test_data/images/              # Student photos
└── requirements.txt
```

---

## 🛠️ Built With

Python · Flask · OpenCV · InsightFace (buffalo_l) · React · Vite

Made by **Javin Rathod** ( [Javin2710](https://github.com/Javin27) )

