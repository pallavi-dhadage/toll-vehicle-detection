# 🚗 Toll Plaza Vehicle Detection & Analytics System

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-009688.svg)](https://fastapi.tiangolo.com/)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-8.0.200-00FFFF.svg)](https://github.com/ultralytics/ultralytics)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14-336791.svg)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Real‑time vehicle detection, multi‑camera streaming, and traffic analytics for toll plazas.**  
Built with YOLOv8, FastAPI, PostgreSQL, and React with clean separation of concerns.

---

## 📌 Overview

The Toll Plaza Vehicle Detection System is a production‑ready solution that automatically detects and classifies vehicles (cars, trucks, buses, motorcycles, bicycles) in real time. It supports multiple IP cameras (RTSP/HTTP), provides per‑camera cross‑section statistics, generates daily Excel reports, visualizes traffic heatmaps, and sends real‑time alerts when vehicle volume exceeds configured thresholds. The system features a clean, maintainable codebase with separation of concerns, JWT-based authentication, and a modern responsive dashboard.

---

## ✨ Key Features

- **Vehicle Detection** – YOLOv8 detects **car, truck, bus, motorcycle, bicycle** with high accuracy
- **Multi‑Object Tracking** – DeepSORT assigns unique IDs to each vehicle, preventing double‑counting
- **Real‑Time Alerts** – Browser notifications when vehicle count exceeds configurable threshold
- **Multi‑Camera Streaming** – Support for multiple RTSP/HTTP camera feeds with live overlay detection
- **Per‑Camera Statistics** – Real-time running counts of each vehicle type per camera
- **Batch Image Upload** – Upload single, multiple, or ZIP archives with progress tracking
- **Live Webcam Capture** – Instant detection from local camera feeds
- **Daily Excel Reports** – Hourly breakdown and raw detection records
- **Hourly Heatmap** – Visualization of vehicle frequency per hour
- **Automatic License Plate Recognition (ALPR)** – PaddleOCR extracts plate numbers
- **User Authentication** – JWT‑based signup/login with protected admin panel
- **Dark/Light Theme** – Modern responsive UI with smooth animations
- **Clean Architecture** – Well-organized code with separation of concerns

---

## 🛠️ Tech Stack

| Component      | Technology                                                                        |
|----------------|-----------------------------------------------------------------------------------|
| **Backend**    | FastAPI, SQLAlchemy, PostgreSQL, PyTorch, YOLOv8, OpenCV, DeepSORT, PaddleOCR   |
| **Frontend**   | React, Tailwind CSS, Chart.js, JSZip, Framer Motion                             |
| **ML/AI**      | YOLOv8 (Detection), DeepSORT (Tracking), PaddleOCR (ALPR)                        |
| **Database**   | PostgreSQL or SQLite (development)                                               |
| **Language**   | Python (Backend), JavaScript (Frontend)                                          |

---

## 🏗️ Architecture & Project Structure

```
toll-vehicle-detection/
├── app/
│ └── main.py # FastAPI backend
├── frontend/
│ ├── professional_dashboard.html # Main dashboard
│ └── index.html # Redirect
├── models/
│ └── yolov8n.pt # YOLO model
├── .gitignore
├── LICENSE
├── README.md
├── requirements.txt
├── setup.sh
└── run.sh
```

### Separation of Concerns

The backend is organized with clear layers:

- **Core Layer** (`core/`) – Database, security, configuration
- **Models Layer** (`models/`) – ORM model definitions  
- **Schemas Layer** (`schemas/`) – Request/response validation
- **API Layer** (`api/v1/endpoints/`) – HTTP endpoint handlers
- **Services Layer** (`services/`) – Business logic & orchestration
- **ML Layer** (`ml/`) – Machine learning model wrappers
- **Utils Layer** (`utils/`) – Shared utilities

This architecture enables:
- ✅ Easy testing of individual components
- ✅ Clear dependency flow
- ✅ Service reusability across endpoints
- ✅ Simple feature addition
- ✅ Maintainability and scalability

---

## 📦 Installation & Setup

### Prerequisites

- Python 3.12+
- Docker (for PostgreSQL)
- Node.js 20+ (for React frontend – optional)
- Git

### Step 1: Clone the Repository

```bash
git clone https://github.com/pallavi-dhadage/toll-vehicle-detection.git
cd toll-vehicle-detection
```

### Step 2: Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
cd ..
```

### Step 4: Configure Environment Variables

```bash
cp backend/.env.example backend/.env
# Edit backend/.env with your configuration
```

Example `backend/.env`:
```ini
DATABASE_URL=sqlite:///./toll_vehicle.db
# Or for PostgreSQL:
# DATABASE_URL=postgresql://user:password@localhost/toll_vehicle_db

SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Step 5: Download YOLOv8 Model

The model will auto-download on first run:
```bash
cd models
# wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8m.pt
cd ..
```

### Step 6: Initialize Database

```bash
cd backend
python3 -c "from app.core.database import init_db; init_db()"
cd ..
```

### Step 7: Run the Backend

```bash
cd backend
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- Application: `http://localhost:8000`
- Interactive docs: `http://localhost:8000/docs`

### Step 8: Run the Frontend

**Option A: Static Frontend (Quick Start)**

```bash
cd frontend
python3 -m http.server 3001
```

Open `http://localhost:3001`

**Option B: React Frontend**

```bash
cd frontend
npm install
npm run dev
```

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

All endpoints are under `/api/v1/` prefix.

### Authentication
- `POST /auth/signup` – Register new user
- `POST /auth/token` – Login and get JWT token
- `GET /auth/me` – Get current user (requires auth)

### Detection
- `POST /detect/` – Upload image for vehicle detection
- `GET /detect/records?limit=10` – Get recent detections

### Reports
- `GET /reports/daily?date=2024-01-15` – Download daily Excel report

### Heatmap
- `GET /heatmap/?start=2024-01-15&end=2024-01-16` – Get hourly statistics

### Streaming
- `POST /stream/add` – Add camera stream
- `DELETE /stream/remove/{camera_id}` – Remove camera
- `GET /stream/list` – List active cameras
- `WebSocket /stream/ws/{camera_id}` – Real-time video stream

---
## � Configuration

### Model Configuration

Edit `backend/app/core/config.py`:

```python
# Detection thresholds
DETECTION_CONFIDENCE_THRESHOLD = 0.5
DETECTION_IOU_THRESHOLD = 0.5
YOLO_CONFIDENCE_THRESHOLD = 0.3

# Alert settings
ALERT_VEHICLE_COUNT_THRESHOLD = 3
ALERT_TIME_WINDOW_SECONDS = 60
```

---

## 🤖 Machine Learning Models

### YOLOv8 Detector
- **Location**: `backend/app/ml/detector.py`
- **Classes**: Car, Truck, Bus, Motorcycle, Bicycle

### DeepSORT Tracker
- **Location**: `backend/app/ml/tracker.py`
- **Purpose**: Multi-object tracking with ID assignment

### PaddleOCR (ALPR)
- **Location**: `backend/app/ml/alpr.py`
- **Purpose**: License plate text extraction

---

## 🔮 Future Enhancements

- [ ] Real-time WebSocket updates
- [ ] Traffic forecasting
- [ ] Edge deployment (NVIDIA Jetson)
- [ ] Mobile app (React Native)
- [ ] Role-based access control
- [ ] Advanced analytics
- [ ] Multi-lane tracking
- [ ] Custom model training interface

---

## 🔐 Security Considerations

- ✅ JWT-based authentication
- ✅ Password hashing with bcrypt
- ✅ CORS configured
- ⚠️ **TODO**: Change SECRET_KEY in production
- ⚠️ **TODO**: Configure CORS origins
- ⚠️ **TODO**: Use HTTPS in production
- ⚠️ **TODO**: Implement rate limiting

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Commit changes
4. Push to branch
5. Open a Pull Request

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details

---

## 🙏 Acknowledgements

- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics)
- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR)
- [DeepSORT](https://github.com/nwojke/deep_sort)
- [React](https://reactjs.org/)
- [Tailwind CSS](https://tailwindcss.com/)
- [Chart.js](https://www.chartjs.org/)

---

**⭐ If you find this project useful, please consider giving it a star!**

Last Updated: April 2026  
Version: 2.0.0
