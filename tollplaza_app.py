"""
Toll Plaza AI - Complete Vehicle Detection System
Features: Dashboard, Reports, Heatmap, Live Streams, Admin Panel
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, status, Request, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from ultralytics import YOLO
from PIL import Image, ImageDraw
import io
import os
import sqlite3
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import pandas as pd
import numpy as np
import cv2
import json
import hashlib
import secrets
from typing import List, Dict, Any
import asyncio
import base64
from pathlib import Path

app = FastAPI(title="Toll Plaza AI - Vehicle Detection System", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBasic()

# Create directories
os.makedirs("static", exist_ok=True)
os.makedirs("uploads", exist_ok=True)
os.makedirs("detections", exist_ok=True)

# Database initialization
def init_database():
    conn = sqlite3.connect('tollplaza.db')
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            email TEXT,
            role TEXT,
            created_at DATETIME
        )
    ''')
    
    # Detections table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS detections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME,
            vehicle_type TEXT,
            confidence REAL,
            license_plate TEXT,
            image_path TEXT,
            camera_id TEXT,
            hour INTEGER,
            day_of_week INTEGER,
            date DATE,
            lane TEXT
        )
    ''')
    
    # Cameras table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cameras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            camera_id TEXT UNIQUE,
            name TEXT,
            url TEXT,
            location TEXT,
            status TEXT,
            added_at DATETIME
        )
    ''')
    
    # Daily summary
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_summary (
            date DATE PRIMARY KEY,
            total_vehicles INTEGER,
            car_count INTEGER,
            truck_count INTEGER,
            bus_count INTEGER,
            motorcycle_count INTEGER,
            bicycle_count INTEGER,
            avg_confidence REAL,
            toll_collected REAL
        )
    ''')
    
    # Insert default admin user
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        cursor.execute('''
            INSERT INTO users (username, password, email, role, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', ('admin', hashlib.sha256('admin123'.encode()).hexdigest(), 'admin@example.com', 'admin', datetime.now()))
    
    conn.commit()
    conn.close()

init_database()

# Load YOLO model
print("Loading YOLOv8 model...")
model = YOLO('yolov8x.pt') if os.path.exists('yolov8x.pt') else YOLO('yolov8m.pt')
print("Model loaded!")

VEHICLE_CLASSES = {1: 'bicycle', 2: 'car', 3: 'motorcycle', 5: 'bus', 7: 'truck'}
VEHICLE_ICONS = {'car': '🚗', 'truck': '🚚', 'bus': '🚌', 'motorcycle': '🏍️', 'bicycle': '🚲'}
VEHICLE_TOLL = {'car': 50, 'truck': 200, 'bus': 150, 'motorcycle': 30, 'bicycle': 10}

def verify_admin(credentials: HTTPBasicCredentials = Depends(security)):
    """Verify admin credentials"""
    conn = sqlite3.connect('tollplaza.db')
    cursor = conn.cursor()
    password_hash = hashlib.sha256(credentials.password.encode()).hexdigest()
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ? AND role = 'admin'", 
                   (credentials.username, password_hash))
    user = cursor.fetchone()
    conn.close()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return credentials.username

def log_detection(vehicle_type, confidence, license_plate="", camera_id="cam1", lane="Lane 1"):
    """Log vehicle detection"""
    conn = sqlite3.connect('tollplaza.db')
    cursor = conn.cursor()
    now = datetime.now()
    cursor.execute('''
        INSERT INTO detections 
        (timestamp, vehicle_type, confidence, license_plate, camera_id, hour, day_of_week, date, lane)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (now, vehicle_type, confidence, license_plate, camera_id, now.hour, now.weekday(), now.date(), lane))
    conn.commit()
    
    # Update daily summary
    update_daily_summary(now.date())
    conn.close()

def update_daily_summary(date):
    """Update daily summary"""
    conn = sqlite3.connect('tollplaza.db')
    query = '''
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN vehicle_type = 'car' THEN 1 ELSE 0 END) as cars,
            SUM(CASE WHEN vehicle_type = 'truck' THEN 1 ELSE 0 END) as trucks,
            SUM(CASE WHEN vehicle_type = 'bus' THEN 1 ELSE 0 END) as buses,
            SUM(CASE WHEN vehicle_type = 'motorcycle' THEN 1 ELSE 0 END) as motorcycles,
            SUM(CASE WHEN vehicle_type = 'bicycle' THEN 1 ELSE 0 END) as bicycles,
            AVG(confidence) as avg_conf
        FROM detections
        WHERE date = ?
    '''
    df = pd.read_sql_query(query, conn, params=[date])
    
    if not df.empty and df['total'].iloc[0] > 0:
        toll_collected = (df['cars'].iloc[0] * VEHICLE_TOLL['car'] +
                         df['trucks'].iloc[0] * VEHICLE_TOLL['truck'] +
                         df['buses'].iloc[0] * VEHICLE_TOLL['bus'] +
                         df['motorcycles'].iloc[0] * VEHICLE_TOLL['motorcycle'] +
                         df['bicycles'].iloc[0] * VEHICLE_TOLL['bicycle'])
        
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO daily_summary 
            (date, total_vehicles, car_count, truck_count, bus_count, motorcycle_count, bicycle_count, avg_confidence, toll_collected)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (date, int(df['total'].iloc[0]), int(df['cars'].iloc[0]), 
              int(df['trucks'].iloc[0]), int(df['buses'].iloc[0]), 
              int(df['motorcycles'].iloc[0]), int(df['bicycles'].iloc[0]), 
              float(df['avg_conf'].iloc[0]), toll_collected))
        conn.commit()
    conn.close()

def detect_vehicles(image_bytes):
    """Detect vehicles in image"""
    image = Image.open(io.BytesIO(image_bytes))
    results = model(image, conf=0.5, verbose=False)
    
    detections = []
    for result in results:
        if result.boxes:
            for box in result.boxes:
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])
                if class_id in VEHICLE_CLASSES:
                    detections.append({
                        'type': VEHICLE_CLASSES[class_id],
                        'confidence': confidence,
                        'bbox': box.xyxy[0].tolist()
                    })
    return detections, image

# ==================== HTML TEMPLATES ====================

# Main Dashboard HTML
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Toll Plaza AI - Vehicle Detection System</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f0f2f5; }
        
        /* Sidebar */
        .sidebar {
            position: fixed;
            left: 0;
            top: 0;
            width: 260px;
            height: 100%;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            padding: 20px;
            box-shadow: 2px 0 10px rgba(0,0,0,0.1);
            z-index: 100;
        }
        
        .sidebar h2 {
            text-align: center;
            margin-bottom: 30px;
            font-size: 1.5em;
        }
        
        .sidebar h2 span {
            font-size: 1.2em;
        }
        
        .nav-item {
            padding: 12px 20px;
            margin: 5px 0;
            cursor: pointer;
            border-radius: 10px;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .nav-item:hover {
            background: rgba(255,255,255,0.2);
        }
        
        .nav-item.active {
            background: rgba(255,255,255,0.3);
            border-left: 3px solid #ff6b6b;
        }
        
        /* Main Content */
        .main-content {
            margin-left: 260px;
            padding: 20px;
        }
        
        /* Header */
        .header {
            background: white;
            padding: 15px 25px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .header h1 { color: #333; font-size: 1.5em; }
        
        .user-info {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .logout-btn {
            background: #dc3545;
            color: white;
            border: none;
            padding: 8px 15px;
            border-radius: 5px;
            cursor: pointer;
        }
        
        /* Stats Cards */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .stat-card {
            background: white;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        
        .stat-card h3 { color: #666; font-size: 0.9em; margin-bottom: 10px; }
        .stat-number { font-size: 2em; font-weight: bold; color: #2a5298; }
        
        /* Cards */
        .card {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        
        .card h2 {
            margin-bottom: 15px;
            color: #333;
            border-bottom: 2px solid #2a5298;
            padding-bottom: 10px;
        }
        
        /* Upload Area */
        .upload-area {
            border: 2px dashed #2a5298;
            border-radius: 10px;
            padding: 40px;
            text-align: center;
            cursor: pointer;
            background: #f8f9fa;
        }
        
        .upload-area:hover { background: #e9ecef; }
        
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            margin-top: 10px;
        }
        
        .preview-img { max-width: 100%; border-radius: 10px; margin-top: 10px; }
        
        .detection-result {
            background: #d4edda;
            padding: 15px;
            border-radius: 8px;
            margin-top: 15px;
        }
        
        /* Table */
        .data-table {
            width: 100%;
            border-collapse: collapse;
        }
        
        .data-table th, .data-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        
        .data-table th { background: #2a5298; color: white; }
        .data-table tr:hover { background: #f5f5f5; }
        
        /* Tabs */
        .tabs { display: flex; gap: 10px; margin-bottom: 20px; }
        .tab { padding: 10px 20px; cursor: pointer; background: #e9ecef; border-radius: 5px; }
        .tab.active { background: #2a5298; color: white; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        
        /* Heatmap */
        .heatmap-container { padding: 20px; background: white; border-radius: 10px; }
        
        /* Live Stream */
        .camera-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
        }
        
        .camera-card {
            background: white;
            border-radius: 10px;
            overflow: hidden;
        }
        
        .camera-card video, .camera-card img {
            width: 100%;
            height: 300px;
            object-fit: cover;
            background: #000;
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .sidebar { width: 200px; }
            .main-content { margin-left: 200px; }
            .stats-grid { grid-template-columns: repeat(2, 1fr); }
        }
    </style>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
</head>
<body>
    <div class="sidebar">
        <h2>🚗 TollPlaza AI</h2>
        <div class="nav-item active" onclick="showPage('dashboard')">📊 Dashboard</div>
        <div class="nav-item" onclick="showPage('reports')">📄 Reports</div>
        <div class="nav-item" onclick="showPage('heatmap')">🔥 Heatmap</div>
        <div class="nav-item" onclick="showPage('livestreams')">📹 Live Streams</div>
        <div class="nav-item" onclick="showPage('admin')">⚙️ Admin Panel</div>
    </div>
    
    <div class="main-content">
        <div class="header">
            <h1>Vehicle Detection System</h1>
            <div class="user-info">
                <span id="userName">Admin</span>
                <button class="logout-btn" onclick="logout()">Logout</button>
            </div>
        </div>
        
        <!-- Dashboard Page -->
        <div id="dashboardPage" class="page active">
            <div class="stats-grid" id="statsGrid">
                <div class="stat-card"><h3>Total Vehicles</h3><div class="stat-number" id="totalVehicles">0</div></div>
                <div class="stat-card"><h3>Today</h3><div class="stat-number" id="todayVehicles">0</div></div>
                <div class="stat-card"><h3>Toll Collected</h3><div class="stat-number" id="tollCollected">₹0</div></div>
                <div class="stat-card"><h3>Avg Confidence</h3><div class="stat-number" id="avgConfidence">0%</div></div>
            </div>
            
            <div class="card">
                <h2>Upload Images / ZIP</h2>
                <div class="upload-area" onclick="document.getElementById('fileInput').click()">
                    📸 Choose files
                    <input type="file" id="fileInput" accept="image/*" multiple style="display:none" onchange="previewImages()">
                </div>
                <div id="previewContainer"></div>
                <button onclick="detectVehicles()">🔍 Detect Vehicles</button>
                <div id="detectionResults"></div>
            </div>
            
            <div class="card">
                <h2>Recent Detections</h2>
                <div id="recentDetections"></div>
                <button onclick="downloadReport()">📥 Download Today's Report</button>
            </div>
        </div>
        
        <!-- Reports Page -->
        <div id="reportsPage" class="page">
            <div class="card">
                <h2>Daily Reports</h2>
                <p>Download Excel reports for any date.</p>
                <input type="date" id="reportDate" value="2026-04-07">
                <button onclick="downloadReportByDate()">📥 Download Report</button>
            </div>
            <div class="card">
                <h2>Quick Access</h2>
                <button onclick="downloadReport()">📥 Download Today's Report</button>
            </div>
        </div>
        
        <!-- Heatmap Page -->
        <div id="heatmapPage" class="page">
            <div class="card">
                <h2>Hourly Vehicle Frequency (Heatmap)</h2>
                <div id="heatmapChart" style="height: 500px;"></div>
            </div>
        </div>
        
        <!-- Live Streams Page -->
        <div id="livestreamsPage" class="page">
            <div class="card">
                <h2>Live Camera Streams</h2>
                <button onclick="addCamera()">➕ Add a new camera</button>
                <div id="camerasGrid" class="camera-grid" style="margin-top: 20px;"></div>
            </div>
        </div>
        
        <!-- Admin Page -->
        <div id="adminPage" class="page">
            <div class="card">
                <h2>Admin Panel</h2>
                <div class="stats-grid">
                    <div class="stat-card"><h3>Total Detections</h3><div class="stat-number" id="adminTotal">0</div></div>
                    <div class="stat-card"><h3>Unique Vehicles</h3><div class="stat-number" id="uniqueTypes">0</div></div>
                    <div class="stat-card"><h3>Last Detection</h3><div class="stat-number" id="lastDetection">-</div></div>
                </div>
                <button onclick="clearRecords()" style="background: #dc3545;">🗑️ Clear All Detection Records</button>
                <div style="margin-top: 20px;">
                    <h3>System Info</h3>
                    <p>✅ Backend: Online</p>
                    <p>🤖 Model: YOLOv8x (COCO)</p>
                    <p>🚗 Classes: car, truck, bus, motorcycle, bicycle</p>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let currentPage = 'dashboard';
        let currentFiles = [];
        
        function showPage(page) {
            document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
            document.getElementById(page + 'Page').classList.add('active');
            document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
            event.target.classList.add('active');
            currentPage = page;
            
            if (page === 'dashboard') loadDashboard();
            if (page === 'heatmap') loadHeatmap();
            if (page === 'livestreams') loadCameras();
            if (page === 'admin') loadAdminStats();
        }
        
        function previewImages() {
            const files = document.getElementById('fileInput').files;
            currentFiles = Array.from(files);
            const container = document.getElementById('previewContainer');
            container.innerHTML = '';
            files.forEach(file => {
                const reader = new FileReader();
                reader.onload = e => {
                    container.innerHTML += `<img src="${e.target.result}" class="preview-img" style="max-width: 150px; margin: 5px;">`;
                };
                reader.readAsDataURL(file);
            });
        }
        
        async function detectVehicles() {
            if (currentFiles.length === 0) { alert('Select images first'); return; }
            
            const formData = new FormData();
            currentFiles.forEach(file => formData.append('files', file));
            
            const response = await fetch('/api/detect-batch', { method: 'POST', body: formData });
            const data = await response.json();
            
            let html = `<div class="detection-result"><strong>✅ Detection Complete!</strong><br>Total Vehicles: ${data.total_vehicles}<br>`;
            for (const [type, count] of Object.entries(data.vehicle_breakdown)) {
                html += `${type}: ${count}<br>`;
            }
            html += `</div>`;
            document.getElementById('detectionResults').innerHTML = html;
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
            const response = await fetch('/api/recent-detections');
            const detections = await response.json();
            let html = `<table class="data-table">
                <thead><tr><th>Time</th><th>Vehicle Type</th><th>Confidence</th><th>License Plate</th></tr></thead>
                <tbody>`;
            detections.forEach(d => {
                html += `<tr>
                    <td>${new Date(d.timestamp).toLocaleString()}</td>
                    <td>${getIcon(d.vehicle_type)} ${d.vehicle_type}</td>
                    <td>${(d.confidence * 100).toFixed(0)}%</td>
                    <td>${d.license_plate || '—'}</td>
                </tr>`;
            });
            html += `</tbody></table>`;
            document.getElementById('recentDetections').innerHTML = html;
        }
        
        async function loadHeatmap() {
            const response = await fetch('/api/heatmap-data');
            const data = await response.json();
            
            const hours = Array.from({length: 24}, (_, i) => `${i}:00`);
            const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
            
            const heatmapData = Array(7).fill().map(() => Array(24).fill(0));
            data.forEach(d => {
                if (heatmapData[d.day_of_week] && heatmapData[d.day_of_week][d.hour] !== undefined) {
                    heatmapData[d.day_of_week][d.hour] = d.count;
                }
            });
            
            Plotly.newPlot('heatmapChart', [{
                z: heatmapData,
                x: hours,
                y: days,
                type: 'heatmap',
                colorscale: 'Viridis',
                colorbar: { title: 'Vehicle Count' }
            }], {
                title: 'Vehicle Detection Heatmap',
                xaxis: { title: 'Hour of Day' },
                yaxis: { title: 'Day of Week' }
            });
        }
        
        async function loadCameras() {
            const response = await fetch('/api/cameras');
            const cameras = await response.json();
            let html = '';
            cameras.forEach(cam => {
                html += `<div class="camera-card">
                    <div style="background: #000; height: 300px; display: flex; align-items: center; justify-content: center;">
                        <span style="color: white;">Camera: ${cam.camera_id}</span>
                    </div>
                    <div style="padding: 15px;">
                        <h4>${cam.name}</h4>
                        <p>Location: ${cam.location}</p>
                        <p>Status: ${cam.status}</p>
                        <button onclick="removeCamera('${cam.camera_id}')">Remove</button>
                    </div>
                </div>`;
            });
            if (cameras.length === 0) html = '<p>No cameras added. Click "Add a new camera" to get started.</p>';
            document.getElementById('camerasGrid').innerHTML = html;
        }
        
        async function loadAdminStats() {
            const response = await fetch('/api/stats');
            const stats = await response.json();
            document.getElementById('adminTotal').textContent = stats.total_detections || 0;
            
            const typesResponse = await fetch('/api/vehicle-types');
            const types = await typesResponse.json();
            document.getElementById('uniqueTypes').textContent = types.join(', ') || '-';
            
            const recentResponse = await fetch('/api/recent-detections?limit=1');
            const recent = await recentResponse.json();
            if (recent.length > 0) {
                document.getElementById('lastDetection').textContent = new Date(recent[0].timestamp).toLocaleString();
            }
        }
        
        async function addCamera() {
            const cameraId = prompt('Enter Camera ID (unique):');
            if (!cameraId) return;
            const url = prompt('Enter RTSP/HTTP URL:');
            if (!url) return;
            const location = prompt('Enter Location:');
            
            await fetch('/api/cameras', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ camera_id: cameraId, name: `Camera ${cameraId}`, url: url, location: location })
            });
            loadCameras();
        }
        
        async function removeCamera(cameraId) {
            await fetch(`/api/cameras/${cameraId}`, { method: 'DELETE' });
            loadCameras();
        }
        
        async function clearRecords() {
            if (confirm('Are you sure? This will delete all detection records.')) {
                await fetch('/api/clear-records', { method: 'DELETE' });
                loadDashboard();
                loadAdminStats();
                loadRecentDetections();
                alert('Records cleared!');
            }
        }
        
        async function downloadReport() {
            window.location.href = '/api/export-report';
        }
        
        async function downloadReportByDate() {
            const date = document.getElementById('reportDate').value;
            window.location.href = `/api/export-report?date=${date}`;
        }
        
        function getIcon(type) {
            const icons = {'car': '🚗', 'truck': '🚚', 'bus': '🚌', 'motorcycle': '🏍️', 'bicycle': '🚲'};
            return icons[type] || '🚗';
        }
        
        function logout() {
            window.location.href = '/logout';
        }
        
        // Initial load
        loadDashboard();
        loadRecentDetections();
        setInterval(() => {
            if (currentPage === 'dashboard') loadDashboard();
        }, 10000);
    </script>
</body>
</html>
"""

# Login Page HTML
LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Toll Plaza AI - Login</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            margin: 0;
        }
        .login-container {
            background: white;
            border-radius: 15px;
            padding: 40px;
            width: 400px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .login-container h2 {
            text-align: center;
            color: #333;
            margin-bottom: 30px;
        }
        .login-container input {
            width: 100%;
            padding: 12px;
            margin: 10px 0;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        .login-container button {
            width: 100%;
            padding: 12px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
        }
        .error {
            color: red;
            text-align: center;
            margin-top: 10px;
        }
        .demo {
            text-align: center;
            margin-top: 20px;
            color: #666;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <h2>🚗 Toll Plaza AI</h2>
        <form action="/login" method="post">
            <input type="text" name="username" placeholder="Email" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Login</button>
        </form>
        <div class="demo">Demo: admin / admin123</div>
    </div>
</body>
</html>
"""

# ==================== API ENDPOINTS ====================

@app.get("/", response_class=HTMLResponse)
async def root():
    return HTMLResponse(content=LOGIN_HTML)

@app.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    conn = sqlite3.connect('tollplaza.db')
    cursor = conn.cursor()
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password_hash))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        response = RedirectResponse(url="/dashboard", status_code=303)
        response.set_cookie(key="session", value=secrets.token_urlsafe(32))
        return response
    return HTMLResponse(content=LOGIN_HTML.replace('<div class="demo">', '<div class="error">Invalid credentials</div><div class="demo">'))

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    return HTMLResponse(content=DASHBOARD_HTML)

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("session")
    return response

@app.post("/api/detect-batch")
async def detect_batch(files: List[UploadFile] = File(...)):
    total_vehicles = 0
    vehicle_breakdown = Counter()
    
    for file in files:
        image_bytes = await file.read()
        detections, _ = detect_vehicles(image_bytes)
        
        for det in detections:
            total_vehicles += 1
            vehicle_breakdown[det['type']] += 1
            log_detection(det['type'], det['confidence'])
    
    return {"total_vehicles": total_vehicles, "vehicle_breakdown": dict(vehicle_breakdown)}

@app.get("/api/stats")
async def get_stats():
    conn = sqlite3.connect('tollplaza.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM detections")
    total = cursor.fetchone()[0] or 0
    
    cursor.execute(f"SELECT COUNT(*) FROM detections WHERE date = '{datetime.now().date()}'")
    today = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT AVG(confidence) FROM detections")
    avg_conf = cursor.fetchone()[0] or 0
    
    cursor.execute(f"SELECT toll_collected FROM daily_summary WHERE date = '{datetime.now().date()}'")
    toll = cursor.fetchone()
    toll = toll[0] if toll else 0
    
    conn.close()
    return {"total_detections": total, "today_detections": today, "average_confidence": avg_conf, "toll_collected": toll}

@app.get("/api/recent-detections")
async def get_recent_detections(limit: int = 10):
    conn = sqlite3.connect('tollplaza.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT timestamp, vehicle_type, confidence, license_plate
        FROM detections ORDER BY timestamp DESC LIMIT ?
    ''', (limit,))
    detections = [{"timestamp": row[0], "vehicle_type": row[1], "confidence": row[2], "license_plate": row[3]} for row in cursor.fetchall()]
    conn.close()
    return detections

@app.get("/api/heatmap-data")
async def get_heatmap_data():
    conn = sqlite3.connect('tollplaza.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT hour, day_of_week, COUNT(*) as count
        FROM detections
        WHERE date >= date('now', '-30 days')
        GROUP BY hour, day_of_week
    ''')
    data = [{"hour": row[0], "day_of_week": row[1], "count": row[2]} for row in cursor.fetchall()]
    conn.close()
    return data

@app.get("/api/vehicle-types")
async def get_vehicle_types():
    conn = sqlite3.connect('tollplaza.db')
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT vehicle_type FROM detections")
    types = [row[0] for row in cursor.fetchall()]
    conn.close()
    return types

@app.get("/api/cameras")
async def get_cameras():
    conn = sqlite3.connect('tollplaza.db')
    cursor = conn.cursor()
    cursor.execute("SELECT camera_id, name, url, location, status FROM cameras")
    cameras = [{"camera_id": row[0], "name": row[1], "url": row[2], "location": row[3], "status": row[4]} for row in cursor.fetchall()]
    conn.close()
    return cameras

@app.post("/api/cameras")
async def add_camera(camera: dict):
    conn = sqlite3.connect('tollplaza.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO cameras (camera_id, name, url, location, status, added_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (camera['camera_id'], camera['name'], camera['url'], camera['location'], 'active', datetime.now()))
    conn.commit()
    conn.close()
    return {"status": "added"}

@app.delete("/api/cameras/{camera_id}")
async def delete_camera(camera_id: str):
    conn = sqlite3.connect('tollplaza.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cameras WHERE camera_id = ?", (camera_id,))
    conn.commit()
    conn.close()
    return {"status": "deleted"}

@app.delete("/api/clear-records")
async def clear_records():
    conn = sqlite3.connect('tollplaza.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM detections")
    cursor.execute("DELETE FROM daily_summary")
    conn.commit()
    conn.close()
    return {"status": "cleared"}

@app.get("/api/export-report")
async def export_report(date: str = None):
    if not date:
        date = datetime.now().strftime('%Y-%m-%d')
    
    conn = sqlite3.connect('tollplaza.db')
    query = "SELECT timestamp, vehicle_type, confidence, license_plate, lane FROM detections WHERE date = ?"
    df = pd.read_sql_query(query, conn, params=[date])
    conn.close()
    
    if df.empty:
        return {"error": "No data for selected date"}
    
    report_path = f"report_{date}.csv"
    df.to_csv(report_path, index=False)
    return FileResponse(report_path, media_type='text/csv', filename=f"toll_report_{date}.csv")

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("🚗 TOLL PLAZA AI - VEHICLE DETECTION SYSTEM")
    print("="*60)
    print("📍 Web Interface: http://localhost:8000")
    print("👤 Admin Login: admin / admin123")
    print("="*60)
    print("\n✅ Server is running!\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
