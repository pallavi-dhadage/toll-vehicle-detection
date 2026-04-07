# 🚗 Toll Plaza Vehicle Detection & Analytics System

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688.svg)](https://fastapi.tiangolo.com/)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-8.0.200-00FFFF.svg)](https://github.com/ultralytics/ultralytics)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14-336791.svg)](https://www.postgresql.org/)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://reactjs.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3-38B2AC.svg)](https://tailwindcss.com/)
[![Docker](https://img.shields.io/badge/Docker-20.10-2496ED.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Real‑time vehicle detection, multi‑camera streaming, and traffic analytics for toll plazas.**  
Built with YOLOv8, FastAPI, PostgreSQL, React, and Docker.

---

## 📌 Overview

Toll Plaza Vehicle Detection System is a production‑ready solution that automatically detects and classifies vehicles (cars, trucks, buses, motorcycles, bicycles) in real time. It supports multiple IP cameras (RTSP/HTTP), provides per‑camera cross‑section statistics, generates daily Excel reports, visualises traffic heatmaps, and sends real‑time alerts when vehicle volume exceeds a threshold. The system includes user authentication (JWT) and a modern dark/light dashboard.

---

## ✨ Key Features

- **Vehicle Detection** – YOLOv8n (lightweight, fast) detects **car, truck, bus, motorcycle, bicycle**.
- **Multi‑Object Tracking** – DeepSORT assigns unique IDs to each vehicle, preventing double‑counting and enabling accurate lane‑wise counts.
- **Real‑Time Alerts** – Browser notifications when >3 vehicles of a type appear in 60 seconds (threshold configurable).
- **Multi‑Camera Streaming** – Add any RTSP/HTTP camera; bounding boxes with track IDs overlay the video feed.
- **Per‑Camera Cross‑Section Stats** – Running counts of each vehicle type (since last reset) displayed below each camera.
- **Batch Image Upload** – Upload single, multiple, or ZIP images; progress bar and per‑file results.
- **Live Webcam Capture** – Instant detection from your local camera.
- **Daily Excel Reports** – Hourly breakdown + raw detection records.
- **Hourly Heatmap** – Bar chart showing vehicle frequency per hour.
- **Automatic License Plate Recognition (ALPR)** – PaddleOCR extracts plate numbers from vehicle regions.
- **User Authentication** – JWT‑based signup/login, protected admin panel.
- **Dark / Light Theme** – Modern UI with gradient buttons, glassmorphism, and smooth animations.
- **Docker Support** – Run the whole stack with Docker Compose.

---

## 🛠️ Tech Stack

| Category       | Technologies                                                                 |
|----------------|------------------------------------------------------------------------------|
| **Backend**    | FastAPI, SQLAlchemy, PostgreSQL, PyTorch, YOLOv8, OpenCV, DeepSORT, PaddleOCR, JWT, WebSocket |
| **Frontend**   | React (or static HTML/CSS/JS), Tailwind CSS, Chart.js, JSZip, Framer Motion |
| **Infrastructure** | Docker, Docker Compose, Git, GitHub                                          |
| **Languages**  | Python, JavaScript, HTML/CSS                                                |

---

## 🏗️ Architecture

```text
Camera Streams (RTSP/HTTP) → Backend (FastAPI) → YOLOv8 + DeepSORT → WebSocket → Frontend (React)
                               ↑
                               │
User Uploads (images/zip) ────┘
                               │
PostgreSQL (detections, users) ←── SQLAlchemy
```

---

## 📦 Installation & Setup

### Prerequisites

- Python 3.12+
- Docker (for PostgreSQL)
- Node.js 20+ (for React frontend – optional)
- Git

### 1. Clone the repository

```bash
git clone https://github.com/pallavi-dhadage/toll-vehicle-detection.git
cd toll-vehicle-detection
```

### 2. Create virtual environment & install backend dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
```

### 3. Download YOLOv8 model (lightweight)

```bash
mkdir -p backend/models
cd backend/models
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt
cd ../..
```

### 4. Start PostgreSQL database (Docker)

```bash
docker run -d --name toll_db -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=toll_vehicle_db -p 5432:5432 postgres:14
```

### 5. Configure environment

Create `backend/.env`:

```ini
DATABASE_URL=postgresql://postgres:postgres@localhost/toll_vehicle_db
```

### 6. Run the backend

```bash
cd backend
source ../venv/bin/activate
OMP_NUM_THREADS=1 uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 7. Run the static frontend (recommended for quick start)

```bash
cd ../frontend
python3 -m http.server 3001
```

Then open `http://localhost:3001`.

### 8. (Optional) Run the React frontend

```bash
cd ../frontend-react
npm install
npm run dev
```

Then open `http://localhost:5173`.

---

## 🧪 Usage

### Authentication

- Click **Login / Sign Up** in the sidebar.
- Create an account (email, password, full name). After signup, you’re automatically logged in.
- The **Admin Panel** becomes visible only to logged‑in users.

### Dashboard

- **Upload Images / ZIP** – select files, click “Detect Vehicles”. A progress bar shows processing; results appear below.
- **Live Camera** – allow camera access, click “Capture & Detect” to take a snapshot and get detections.
- **Recent Detections** – table with time, vehicle type, confidence, and license plate (if recognised).

### Reports

- Choose a date and download an Excel report (hourly breakdown + raw records).
- Quick “Download Today’s Report” button.

### Heatmap

- Shows a bar chart of vehicle counts per hour for the current month.

### Live Streams

- Add a camera: enter a unique ID, RTSP/HTTP URL, and FPS (e.g., 2). Click “Add Camera”.
- The video appears with bounding boxes overlaid. Below it, a **cross‑section** table shows counts of each vehicle type since the camera was added or last reset.
- Click **Reset Stats** to clear the counts for that camera.
- When more than 3 vehicles of a type are detected in 60 seconds, a browser notification and a yellow alert message appear on the camera feed.

### Admin Panel

- Accessible only when logged in.
- Displays database statistics (total detections, unique types, last detection) and system info.
- Placeholder for clearing all records.

---

## 📡 API Endpoints

| Method | Endpoint                       | Description                          |
|--------|--------------------------------|--------------------------------------|
| POST   | `/detect/`                     | Upload an image → detection results  |
| GET    | `/detect/records?limit=10`     | Get recent detections                |
| GET    | `/reports/daily?date=YYYY-MM-DD` | Download Excel report               |
| GET    | `/heatmap/?start=&end=`        | Get hourly counts for date range     |
| POST   | `/auth/signup`                 | Register new user                    |
| POST   | `/auth/token`                  | Login → returns JWT                  |
| GET    | `/auth/me`                     | Get current user info (protected)    |
| POST   | `/stream/add`                  | Add a camera (JSON: `camera_id, url, fps`) |
| DELETE | `/stream/remove/{camera_id}`   | Remove a camera                      |
| GET    | `/stream/list`                 | List all camera IDs                  |
| WebSocket | `/stream/ws/{camera_id}`     | Real‑time detection stream           |

---

## 📸 Screenshots

*(Add your own screenshots here)*

- Dashboard  
  ![Dashboard](https://via.placeholder.com/800x400?text=Dashboard+Screenshot)

- Live Streams with bounding boxes & stats  
  ![Live Streams](https://via.placeholder.com/800x400?text=Live+Streams)

- Heatmap  
  ![Heatmap](https://via.placeholder.com/800x400?text=Heatmap)

---

## 🔮 Future Enhancements

- **Automatic Number Plate Recognition (ALPR)** – already integrated.
- **Traffic Forecasting** – predict peak hours using historical data.
- **Edge Deployment** – run detection on‑camera (NVIDIA Jetson).
- **Mobile App** – React Native companion for field staff.
- **Role‑Based Access Control** – operator, analyst, admin roles.
- **Export to CSV/JSON** – additional data export formats.

---

## 🐳 Docker Deployment (Optional)

A `docker-compose.yml` is included to run the whole stack:

```bash
docker-compose up -d --build
```

Access the frontend at `http://localhost`.

---

## 🤝 Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

---

## 📄 License

[MIT](LICENSE)

---

## 🙏 Acknowledgements

- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Tailwind CSS](https://tailwindcss.com/)
- [Chart.js](https://www.chartjs.org/)
- [JSZip](https://stuk.github.io/jszip/)
- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR)
- [Deep SORT](https://github.com/nwojke/deep_sort)

---

**⭐ Star this repository if you find it useful!**
```
