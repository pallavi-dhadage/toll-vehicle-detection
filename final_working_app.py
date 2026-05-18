"""
Toll Plaza AI - Complete Working Vehicle Detection System
No WebSocket - Pure HTTP/REST API
"""

from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO
from PIL import Image
import io
import os
import sqlite3
from datetime import datetime
from collections import Counter
import pandas as pd
import hashlib
import secrets
from typing import List

app = FastAPI(title="Toll Plaza AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create directories
os.makedirs("uploads", exist_ok=True)

# Initialize database
def init_db():
    conn = sqlite3.connect('tollplaza.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS detections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME,
        vehicle_type TEXT,
        confidence REAL,
        hour INTEGER,
        day_of_week INTEGER,
        date DATE
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS daily_summary (
        date DATE PRIMARY KEY,
        total_vehicles INTEGER,
        car_count INTEGER,
        truck_count INTEGER,
        bus_count INTEGER,
        motorcycle_count INTEGER,
        bicycle_count INTEGER,
        avg_confidence REAL,
        toll_collected REAL
    )''')
    
    # Insert admin user
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        hashed = hashlib.sha256('admin123'.encode()).hexdigest()
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                  ('admin', hashed, 'admin'))
    
    conn.commit()
    conn.close()

init_db()

# Load model
print("Loading YOLOv8 model...")
model = YOLO('yolov8x.pt') if os.path.exists('yolov8x.pt') else YOLO('yolov8m.pt')
print("✅ Model loaded!")

VEHICLE_CLASSES = {1: 'bicycle', 2: 'car', 3: 'motorcycle', 5: 'bus', 7: 'truck'}
VEHICLE_TOLL = {'car': 50, 'truck': 200, 'bus': 150, 'motorcycle': 30, 'bicycle': 10}

def log_detection(vehicle_type, confidence):
    conn = sqlite3.connect('tollplaza.db')
    c = conn.cursor()
    now = datetime.now()
    c.execute('''INSERT INTO detections 
                 (timestamp, vehicle_type, confidence, hour, day_of_week, date)
                 VALUES (?, ?, ?, ?, ?, ?)''',
              (now, vehicle_type, confidence, now.hour, now.weekday(), now.date()))
    conn.commit()
    
    # Update daily summary
    update_daily_summary(now.date())
    conn.close()

def update_daily_summary(date):
    conn = sqlite3.connect('tollplaza.db')
    query = '''SELECT 
               COUNT(*) as total,
               SUM(CASE WHEN vehicle_type='car' THEN 1 ELSE 0 END) as cars,
               SUM(CASE WHEN vehicle_type='truck' THEN 1 ELSE 0 END) as trucks,
               SUM(CASE WHEN vehicle_type='bus' THEN 1 ELSE 0 END) as buses,
               SUM(CASE WHEN vehicle_type='motorcycle' THEN 1 ELSE 0 END) as motorcycles,
               SUM(CASE WHEN vehicle_type='bicycle' THEN 1 ELSE 0 END) as bicycles,
               AVG(confidence) as avg_conf
               FROM detections WHERE date = ?'''
    
    df = pd.read_sql_query(query, conn, params=[date])
    
    if not df.empty and df['total'].iloc[0] > 0:
        toll = (df['cars'].iloc[0] * VEHICLE_TOLL['car'] +
                df['trucks'].iloc[0] * VEHICLE_TOLL['truck'] +
                df['buses'].iloc[0] * VEHICLE_TOLL['bus'] +
                df['motorcycles'].iloc[0] * VEHICLE_TOLL['motorcycle'] +
                df['bicycles'].iloc[0] * VEHICLE_TOLL['bicycle'])
        
        c = conn.cursor()
        c.execute('''INSERT OR REPLACE INTO daily_summary 
                     (date, total_vehicles, car_count, truck_count, bus_count, 
                      motorcycle_count, bicycle_count, avg_confidence, toll_collected)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (date, int(df['total'].iloc[0]), int(df['cars'].iloc[0]),
                   int(df['trucks'].iloc[0]), int(df['buses'].iloc[0]),
                   int(df['motorcycles'].iloc[0]), int(df['bicycles'].iloc[0]),
                   float(df['avg_conf'].iloc[0]), toll))
        conn.commit()
    conn.close()

def detect_vehicles(image_bytes):
    image = Image.open(io.BytesIO(image_bytes))
    results = model(image, conf=0.5, verbose=False)
    
    detections = []
    for result in results:
        if result.boxes:
            for box in result.boxes:
                class_id = int(box.cls[0])
                if class_id in VEHICLE_CLASSES:
                    detections.append({
                        'type': VEHICLE_CLASSES[class_id],
                        'confidence': float(box.conf[0])
                    })
    return detections

# HTML Templates
LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Toll Plaza AI - Login</title>
    <style>
        body {
            font-family: 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            margin: 0;
        }
        .login-box {
            background: white;
            border-radius: 15px;
            padding: 40px;
            width: 350px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .login-box h2 { text-align: center; color: #333; margin-bottom: 30px; }
        .login-box input {
            width: 100%;
            padding: 12px;
            margin: 10px 0;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        .login-box button {
            width: 100%;
            padding: 12px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
        }
        .demo { text-align: center; margin-top: 20px; color: #666; }
    </style>
</head>
<body>
    <div class="login-box">
        <h2>🚗 Toll Plaza AI</h2>
        <form method="post" action="/login">
            <input type="text" name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Login</button>
        </form>
        <div class="demo">Demo: admin / admin123</div>
    </div>
</body>
</html>
"""

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Toll Plaza AI - Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', sans-serif; background: #f0f2f5; }
        
        .sidebar {
            position: fixed;
            left: 0;
            top: 0;
            width: 260px;
            height: 100%;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            padding: 20px;
        }
        .sidebar h2 { text-align: center; margin-bottom: 30px; }
        .nav-item {
            padding: 12px 20px;
            margin: 5px 0;
            cursor: pointer;
            border-radius: 10px;
            transition: 0.3s;
        }
        .nav-item:hover { background: rgba(255,255,255,0.2); }
        .nav-item.active { background: rgba(255,255,255,0.3); }
        
        .main-content {
            margin-left: 260px;
            padding: 20px;
        }
        .header {
            background: white;
            padding: 15px 25px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .logout-btn {
            background: #dc3545;
            color: white;
            border: none;
            padding: 8px 15px;
            border-radius: 5px;
            cursor: pointer;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin-bottom: 20px;
        }
        .stat-card {
            background: white;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
        }
        .stat-number { font-size: 2em; font-weight: bold; color: #2a5298; }
        .card {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .card h2 { margin-bottom: 15px; border-bottom: 2px solid #2a5298; padding-bottom: 10px; }
        .upload-area {
            border: 2px dashed #2a5298;
            border-radius: 10px;
            padding: 40px;
            text-align: center;
            cursor: pointer;
            background: #f8f9fa;
        }
        button {
            background: #2a5298;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            margin-top: 10px;
        }
        .preview-img { max-width: 120px; margin: 5px; border-radius: 5px; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #2a5298; color: white; }
        .page { display: none; }
        .page.active { display: block; }
        .result-box { background: #d4edda; padding: 15px; border-radius: 8px; margin-top: 15px; }
    </style>
</head>
<body>
    <div class="sidebar">
        <h2>🚗 TollPlaza AI</h2>
        <div class="nav-item active" onclick="showPage('dashboard')">📊 Dashboard</div>
        <div class="nav-item" onclick="showPage('reports')">📄 Reports</div>
        <div class="nav-item" onclick="showPage('heatmap')">🔥 Heatmap</div>
        <div class="nav-item" onclick="showPage('admin')">⚙️ Admin</div>
    </div>
    
    <div class="main-content">
        <div class="header">
            <h1>Vehicle Detection System</h1>
            <button class="logout-btn" onclick="logout()">Logout</button>
        </div>
        
        <div id="dashboard" class="page active">
            <div class="stats-grid">
                <div class="stat-card"><h3>Total Vehicles</h3><div class="stat-number" id="totalVehicles">0</div></div>
                <div class="stat-card"><h3>Today</h3><div class="stat-number" id="todayVehicles">0</div></div>
                <div class="stat-card"><h3>Toll Collected</h3><div class="stat-number" id="tollCollected">₹0</div></div>
                <div class="stat-card"><h3>Avg Confidence</h3><div class="stat-number" id="avgConfidence">0%</div></div>
            </div>
            
            <div class="card">
                <h2>Upload Images</h2>
                <div class="upload-area" onclick="document.getElementById('fileInput').click()">
                    📸 Click to upload vehicle images
                    <input type="file" id="fileInput" accept="image/*" multiple style="display:none" onchange="previewImages()">
                </div>
                <div id="previewContainer"></div>
                <button onclick="detectVehicles()">🔍 Detect Vehicles</button>
                <div id="detectionResult"></div>
            </div>
            
            <div class="card">
                <h2>Recent Detections</h2>
                <div id="recentTable"></div>
                <button onclick="downloadReport()">📥 Download Today's Report</button>
            </div>
        </div>
        
        <div id="reports" class="page">
            <div class="card">
                <h2>Daily Reports</h2>
                <p>Download Excel reports for any date.</p>
                <input type="date" id="reportDate">
                <button onclick="downloadReportByDate()">📥 Download Report</button>
            </div>
        </div>
        
        <div id="heatmap" class="page">
            <div class="card">
                <h2>Hourly Vehicle Frequency (Heatmap)</h2>
                <div id="heatmapChart" style="height: 500px;"></div>
            </div>
        </div>
        
        <div id="admin" class="page">
            <div class="card">
                <h2>Admin Panel</h2>
                <div class="stats-grid">
                    <div class="stat-card"><h3>Total Records</h3><div class="stat-number" id="adminTotal">0</div></div>
                    <div class="stat-card"><h3>Vehicle Types</h3><div class="stat-number" id="vehicleTypes">0</div></div>
                </div>
                <button onclick="clearRecords()" style="background:#dc3545;">🗑️ Clear All Records</button>
                <div style="margin-top:20px;">
                    <h3>System Info</h3>
                    <p>✅ Backend: Online</p>
                    <p>🤖 Model: YOLOv8x</p>
                    <p>🚗 Classes: car, truck, bus, motorcycle, bicycle</p>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let currentFiles = [];
        
        function showPage(page) {
            document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
            document.getElementById(page).classList.add('active');
            if (page === 'dashboard') loadDashboard();
            if (page === 'heatmap') loadHeatmap();
            if (page === 'admin') loadAdmin();
        }
        
        function previewImages() {
            const files = document.getElementById('fileInput').files;
            currentFiles = Array.from(files);
            const container = document.getElementById('previewContainer');
            container.innerHTML = '';
            files.forEach(file => {
                const reader = new FileReader();
                reader.onload = e => {
                    container.innerHTML += `<img src="${e.target.result}" class="preview-img">`;
                };
                reader.readAsDataURL(file);
            });
        }
        
        async function detectVehicles() {
            if (currentFiles.length === 0) { alert('Select images first'); return; }
            
            const formData = new FormData();
            currentFiles.forEach(f => formData.append('files', f));
            
            const response = await fetch('/api/detect', { method: 'POST', body: formData });
            const data = await response.json();
            
            let html = `<div class="result-box">
                <strong>✅ Detection Complete!</strong><br>
                Total Vehicles: ${data.total_vehicles}<br>`;
            for (const [type, count] of Object.entries(data.vehicle_breakdown)) {
                html += `${type}: ${count}<br>`;
            }
            html += `</div>`;
            document.getElementById('detectionResult').innerHTML = html;
            loadDashboard();
            loadRecentDetections();
        }
        
        async function loadDashboard() {
            const response = await fetch('/api/stats');
            const stats = await response.json();
            document.getElementById('totalVehicles').textContent = stats.total_detections || 0;
            document.getElementById('todayVehicles').textContent = stats.today_detections || 0;
            document.getElementById('tollCollected').innerHTML = `₹${stats.toll_collected || 0}`;
            document.getElementById('avgConfidence').innerHTML = `${Math.round((stats.average_confidence || 0) * 100)}%`;
        }
        
        async function loadRecentDetections() {
            const response = await fetch('/api/recent');
            const data = await response.json();
            let html = '<table> hilab<th>Time</th><th>Vehicle</th><th>Confidence</th></tr>';
            data.forEach(d => {
                html += `<tr>
                    <td>${new Date(d.timestamp).toLocaleString()}</td>
                    <td>${d.vehicle_type}</td>
                    <td>${(d.confidence * 100).toFixed(0)}%</span></td>
                </tr>`;
            });
            html += '</table>';
            document.getElementById('recentTable').innerHTML = html;
        }
        
        async function loadHeatmap() {
            const response = await fetch('/api/heatmap');
            const data = await response.json();
            
            const hours = Array.from({length: 24}, (_, i) => `${i}:00`);
            const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
            const matrix = Array(7).fill().map(() => Array(24).fill(0));
            
            data.forEach(d => {
                if (matrix[d.day_of_week] && matrix[d.day_of_week][d.hour] !== undefined) {
                    matrix[d.day_of_week][d.hour] = d.count;
                }
            });
            
            Plotly.newPlot('heatmapChart', [{
                z: matrix, x: hours, y: days,
                type: 'heatmap', colorscale: 'Viridis'
            }], { title: 'Vehicle Detection Heatmap' });
        }
        
        async function loadAdmin() {
            const response = await fetch('/api/stats');
            const stats = await response.json();
            document.getElementById('adminTotal').textContent = stats.total_detections || 0;
            
            const types = await fetch('/api/types');
            const typesData = await types.json();
            document.getElementById('vehicleTypes').textContent = typesData.join(', ') || '-';
        }
        
        async function clearRecords() {
            if (confirm('Delete all records?')) {
                await fetch('/api/clear', { method: 'DELETE' });
                loadDashboard();
                loadRecentDetections();
                loadAdmin();
                alert('Records cleared!');
            }
        }
        
        function downloadReport() {
            window.location.href = '/api/export';
        }
        
        function downloadReportByDate() {
            const date = document.getElementById('reportDate').value;
            if (date) window.location.href = `/api/export?date=${date}`;
            else alert('Select a date');
        }
        
        function logout() {
            window.location.href = '/logout';
        }
        
        loadDashboard();
        loadRecentDetections();
        setInterval(() => { if (document.getElementById('dashboard').classList.contains('active')) loadDashboard(); }, 10000);
    </script>
</body>
</html>
"""

# Routes
@app.get("/", response_class=HTMLResponse)
async def login_page():
    return HTMLResponse(content=LOGIN_HTML)

@app.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    hashed = hashlib.sha256(password.encode()).hexdigest()
    conn = sqlite3.connect('tollplaza.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, hashed))
    user = c.fetchone()
    conn.close()
    
    if user:
        response = RedirectResponse(url="/dashboard", status_code=303)
        return response
    return HTMLResponse(content=LOGIN_HTML)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    return HTMLResponse(content=DASHBOARD_HTML)

@app.get("/logout")
async def logout():
    return RedirectResponse(url="/", status_code=303)

@app.post("/api/detect")
async def detect_images(files: List[UploadFile] = File(...)):
    total = 0
    breakdown = Counter()
    
    for file in files:
        image_bytes = await file.read()
        detections = detect_vehicles(image_bytes)
        
        for d in detections:
            total += 1
            breakdown[d['type']] += 1
            log_detection(d['type'], d['confidence'])
    
    return {"total_vehicles": total, "vehicle_breakdown": dict(breakdown)}

@app.get("/api/stats")
async def get_stats():
    conn = sqlite3.connect('tollplaza.db')
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM detections")
    total = c.fetchone()[0] or 0
    
    c.execute(f"SELECT COUNT(*) FROM detections WHERE date = '{datetime.now().date()}'")
    today = c.fetchone()[0] or 0
    
    c.execute("SELECT AVG(confidence) FROM detections")
    avg = c.fetchone()[0] or 0
    
    c.execute(f"SELECT toll_collected FROM daily_summary WHERE date = '{datetime.now().date()}'")
    toll = c.fetchone()
    toll = toll[0] if toll else 0
    
    conn.close()
    return {"total_detections": total, "today_detections": today, "average_confidence": avg, "toll_collected": toll}

@app.get("/api/recent")
async def get_recent(limit: int = 10):
    conn = sqlite3.connect('tollplaza.db')
    c = conn.cursor()
    c.execute("SELECT timestamp, vehicle_type, confidence FROM detections ORDER BY timestamp DESC LIMIT ?", (limit,))
    data = [{"timestamp": row[0], "vehicle_type": row[1], "confidence": row[2]} for row in c.fetchall()]
    conn.close()
    return data

@app.get("/api/heatmap")
async def get_heatmap():
    conn = sqlite3.connect('tollplaza.db')
    c = conn.cursor()
    c.execute("SELECT hour, day_of_week, COUNT(*) as count FROM detections GROUP BY hour, day_of_week")
    data = [{"hour": row[0], "day_of_week": row[1], "count": row[2]} for row in c.fetchall()]
    conn.close()
    return data

@app.get("/api/types")
async def get_types():
    conn = sqlite3.connect('tollplaza.db')
    c = conn.cursor()
    c.execute("SELECT DISTINCT vehicle_type FROM detections")
    types = [row[0] for row in c.fetchall()]
    conn.close()
    return types

@app.delete("/api/clear")
async def clear_records():
    conn = sqlite3.connect('tollplaza.db')
    c = conn.cursor()
    c.execute("DELETE FROM detections")
    c.execute("DELETE FROM daily_summary")
    conn.commit()
    conn.close()
    return {"status": "cleared"}

@app.get("/api/export")
async def export_report(date: str = None):
    if not date:
        date = datetime.now().strftime('%Y-%m-%d')
    
    conn = sqlite3.connect('tollplaza.db')
    df = pd.read_sql_query("SELECT timestamp, vehicle_type, confidence FROM detections WHERE date = ?", conn, params=[date])
    conn.close()
    
    if df.empty:
        return {"error": "No data for selected date"}
    
    csv_path = f"toll_report_{date}.csv"
    df.to_csv(csv_path, index=False)
    return FileResponse(csv_path, filename=f"toll_report_{date}.csv")

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("🚗 TOLL PLAZA AI - VEHICLE DETECTION SYSTEM")
    print("="*60)
    print("📍 Web Interface: http://localhost:8000")
    print("👤 Login: admin / admin123")
    print("="*60)
    print("\n✅ Server is running! Ignore WebSocket warnings (they don't affect functionality)\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
