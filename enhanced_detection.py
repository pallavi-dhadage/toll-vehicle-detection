"""
Enhanced Vehicle Detection System with Logging and Heatmap
Features: Vehicle type prediction, timestamp logging, daily/hourly heatmap
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO
from PIL import Image
import io
import os
import json
import sqlite3
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from collections import Counter
import plotly.express as px
import plotly.graph_objects as go
from plotly.utils import PlotlyJSONEncoder
import base64

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database for logging
def init_database():
    conn = sqlite3.connect('vehicle_detections.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS detections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME,
            vehicle_type TEXT,
            confidence REAL,
            image_path TEXT,
            hour INTEGER,
            day_of_week INTEGER,
            date DATE
        )
    ''')
    conn.commit()
    conn.close()

init_database()

# Load model
MODEL_PATH = 'yolov8x.pt'
if os.path.exists(MODEL_PATH):
    print(f"Loading model from {MODEL_PATH}")
    model = YOLO(MODEL_PATH)
else:
    print("Downloading model...")
    model = YOLO('yolov8x.pt')

VEHICLE_CLASSES = {1: 'bicycle', 2: 'car', 3: 'motorcycle', 5: 'bus', 7: 'truck'}

def log_detection(vehicle_type, confidence, image_path=None):
    """Log detection to database"""
    conn = sqlite3.connect('vehicle_detections.db')
    cursor = conn.cursor()
    now = datetime.now()
    cursor.execute('''
        INSERT INTO detections (timestamp, vehicle_type, confidence, image_path, hour, day_of_week, date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (now, vehicle_type, confidence, image_path, now.hour, now.weekday(), now.date()))
    conn.commit()
    conn.close()

def get_heatmap_data(period='day'):
    """Get heatmap data for visualizations"""
    conn = sqlite3.connect('vehicle_detections.db')
    
    if period == 'hour':
        # Hourly heatmap data
        query = '''
            SELECT hour, vehicle_type, COUNT(*) as count
            FROM detections
            WHERE date >= date('now', '-7 days')
            GROUP BY hour, vehicle_type
            ORDER BY hour
        '''
        df = pd.read_sql_query(query, conn)
        
        # Create pivot table for heatmap
        if not df.empty:
            pivot = df.pivot(index='hour', columns='vehicle_type', values='count').fillna(0)
            return pivot
    else:
        # Daily heatmap data
        query = '''
            SELECT date, vehicle_type, COUNT(*) as count
            FROM detections
            WHERE date >= date('now', '-30 days')
            GROUP BY date, vehicle_type
            ORDER BY date
        '''
        df = pd.read_sql_query(query, conn)
        if not df.empty:
            pivot = df.pivot(index='date', columns='vehicle_type', values='count').fillna(0)
            return pivot
    
    conn.close()
    return pd.DataFrame()

def get_statistics():
    """Get comprehensive statistics"""
    conn = sqlite3.connect('vehicle_detections.db')
    
    # Total detections
    total = pd.read_sql_query("SELECT COUNT(*) as count FROM detections", conn)['count'][0]
    
    # Vehicle type distribution
    type_dist = pd.read_sql_query("SELECT vehicle_type, COUNT(*) as count FROM detections GROUP BY vehicle_type", conn)
    type_dict = dict(zip(type_dist['vehicle_type'], type_dist['count']))
    
    # Hourly distribution
    hourly = pd.read_sql_query("SELECT hour, COUNT(*) as count FROM detections GROUP BY hour ORDER BY hour", conn)
    hourly_dict = dict(zip(hourly['hour'], hourly['count']))
    
    # Today's stats
    today = datetime.now().date()
    today_stats = pd.read_sql_query(f"SELECT COUNT(*) as count FROM detections WHERE date = '{today}'", conn)['count'][0]
    
    # Peak hour
    peak_hour = hourly.loc[hourly['count'].idxmax(), 'hour'] if not hourly.empty else 0
    
    # Average confidence
    avg_conf = pd.read_sql_query("SELECT AVG(confidence) as avg FROM detections", conn)['avg'][0] or 0
    
    conn.close()
    
    return {
        'total_detections': total,
        'vehicle_distribution': type_dict,
        'hourly_distribution': hourly_dict,
        'today_detections': today_stats,
        'peak_hour': f"{peak_hour}:00 - {peak_hour+1}:00",
        'average_confidence': avg_conf
    }

# Enhanced HTML with heatmap
ENHANCED_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Enhanced Vehicle Detection System</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .dashboard {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: white;
            border-radius: 15px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        
        .stat-card.primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .stat-number {
            font-size: 2.5em;
            font-weight: bold;
        }
        
        .stat-label {
            font-size: 0.9em;
            margin-top: 10px;
            opacity: 0.9;
        }
        
        .main-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        
        .card h2 {
            color: #333;
            margin-bottom: 20px;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }
        
        .upload-area {
            border: 2px dashed #667eea;
            border-radius: 10px;
            padding: 30px;
            text-align: center;
            cursor: pointer;
            background: #f8f9fa;
            transition: all 0.3s ease;
        }
        
        .upload-area:hover {
            background: #e9ecef;
            border-color: #764ba2;
        }
        
        .upload-area input {
            display: none;
        }
        
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 16px;
            width: 100%;
            margin-top: 20px;
            transition: transform 0.2s;
        }
        
        .btn:hover {
            transform: translateY(-2px);
        }
        
        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        
        .preview-img {
            max-width: 100%;
            border-radius: 10px;
            margin-top: 20px;
        }
        
        .result-item {
            background: #f8f9fa;
            padding: 12px;
            margin: 10px 0;
            border-radius: 8px;
            border-left: 4px solid #28a745;
        }
        
        .loading {
            display: none;
            text-align: center;
            margin-top: 20px;
        }
        
        .spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .heatmap-container {
            margin-top: 20px;
        }
        
        .log-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }
        
        .log-table th, .log-table td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        
        .log-table th {
            background: #667eea;
            color: white;
        }
        
        .log-table tr:hover {
            background: #f5f5f5;
        }
        
        @media (max-width: 768px) {
            .main-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚗 Enhanced Vehicle Detection System</h1>
            <p>Real-time detection with logging, analytics, and heatmaps</p>
        </div>
        
        <div class="dashboard" id="statsDashboard">
            <!-- Stats will be loaded here -->
        </div>
        
        <div class="main-grid">
            <div class="card">
                <h2>📸 Upload & Detect</h2>
                <div class="upload-area" onclick="document.getElementById('fileInput').click()">
                    📸 Click to upload vehicle image
                    <br><small>Supports: JPG, PNG, JPEG</small>
                    <input type="file" id="fileInput" accept="image/*" onchange="previewImage()">
                </div>
                <div id="preview"></div>
                <button class="btn" onclick="detectVehicles()">🔍 Detect & Log Vehicles (92%+ Confidence)</button>
                <div class="loading" id="loading">
                    <div class="spinner"></div>
                    <p>Processing with YOLOv8x...</p>
                </div>
                <div id="detectionResults"></div>
            </div>
            
            <div class="card">
                <h2>📊 Recent Detections Log</h2>
                <div id="recentLogs"></div>
                <button class="btn" onclick="refreshLogs()" style="margin-top: 10px;">🔄 Refresh Logs</button>
            </div>
        </div>
        
        <div class="card">
            <h2>🔥 Detection Heatmap (Hourly Pattern)</h2>
            <div id="hourlyHeatmap" class="heatmap-container"></div>
        </div>
        
        <div class="card">
            <h2>📈 Vehicle Type Distribution</h2>
            <div id="vehicleDistribution"></div>
        </div>
    </div>
    
    <script>
        let currentFile = null;
        
        // Load all data on page load
        window.onload = function() {
            loadStatistics();
            loadHeatmap();
            loadRecentLogs();
            loadVehicleDistribution();
        };
        
        function previewImage() {
            const file = document.getElementById('fileInput').files[0];
            if (file) {
                currentFile = file;
                const reader = new FileReader();
                reader.onload = function(e) {
                    document.getElementById('preview').innerHTML = '<img src="' + e.target.result + '" class="preview-img">';
                };
                reader.readAsDataURL(file);
            }
        }
        
        async function detectVehicles() {
            if (!currentFile) {
                alert('Please select an image first');
                return;
            }
            
            const formData = new FormData();
            formData.append('file', currentFile);
            
            document.getElementById('loading').style.display = 'block';
            document.getElementById('detectionResults').innerHTML = '';
            
            try {
                const response = await fetch('/detect/', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (data.success) {
                    let html = '<h3>✅ Detection Results:</h3>';
                    html += `<p><strong>Total Vehicles:</strong> ${data.total_vehicles}</p>`;
                    html += `<p><strong>Timestamp:</strong> ${new Date(data.timestamp).toLocaleString()}</p>`;
                    
                    if (data.detections && data.detections.length > 0) {
                        html += '<div style="margin-top: 15px;">';
                        for (const d of data.detections) {
                            const confPercent = (d.confidence * 100).toFixed(1);
                            html += '<div class="result-item">';
                            html += `<strong>🚗 ${d.type.toUpperCase()}</strong><br>`;
                            html += `Confidence: ${confPercent}%<br>`;
                            html += `Time: ${new Date().toLocaleTimeString()}`;
                            html += '</div>';
                        }
                        html += '</div>';
                    }
                    
                    document.getElementById('detectionResults').innerHTML = html;
                    
                    // Refresh all data
                    loadStatistics();
                    loadHeatmap();
                    loadRecentLogs();
                    loadVehicleDistribution();
                } else {
                    document.getElementById('detectionResults').innerHTML = `<p style="color: red;">❌ Error: ${data.error}</p>`;
                }
            } catch (error) {
                document.getElementById('detectionResults').innerHTML = `<p style="color: red;">❌ Error: ${error.message}</p>`;
            } finally {
                document.getElementById('loading').style.display = 'none';
            }
        }
        
        async function loadStatistics() {
            const response = await fetch('/statistics');
            const stats = await response.json();
            
            const dashboard = document.getElementById('statsDashboard');
            dashboard.innerHTML = `
                <div class="stat-card primary">
                    <div class="stat-number">${stats.total_detections}</div>
                    <div class="stat-label">Total Detections</div>
                </div>
                <div class="stat-card primary">
                    <div class="stat-number">${stats.today_detections}</div>
                    <div class="stat-label">Today's Detections</div>
                </div>
                <div class="stat-card primary">
                    <div class="stat-number">${(stats.average_confidence * 100).toFixed(0)}%</div>
                    <div class="stat-label">Avg Confidence</div>
                </div>
                <div class="stat-card primary">
                    <div class="stat-number">${stats.peak_hour}</div>
                    <div class="stat-label">Peak Hour</div>
                </div>
            `;
        }
        
        async function loadHeatmap() {
            const response = await fetch('/heatmap/hourly');
            const data = await response.json();
            
            if (data.figure) {
                const figure = JSON.parse(data.figure);
                Plotly.newPlot('hourlyHeatmap', figure.data, figure.layout);
            }
        }
        
        async function loadRecentLogs() {
            const response = await fetch('/recent-logs');
            const logs = await response.json();
            
            let html = '<table class="log-table">';
            html += '<thead><tr><th>Time</th><th>Vehicle Type</th><th>Confidence</th></tr></thead>';
            html += '<tbody>';
            
            for (const log of logs) {
                html += `<tr>
                    <td>${new Date(log.timestamp).toLocaleString()}</td>
                    <td><strong>${log.vehicle_type.toUpperCase()}</strong></td>
                    <td>${(log.confidence * 100).toFixed(1)}%</td>
                </tr>`;
            }
            
            html += '</tbody></table>';
            document.getElementById('recentLogs').innerHTML = html;
        }
        
        async function loadVehicleDistribution() {
            const response = await fetch('/vehicle-distribution');
            const data = await response.json();
            
            if (data.figure) {
                const figure = JSON.parse(data.figure);
                Plotly.newPlot('vehicleDistribution', figure.data, figure.layout);
            }
        }
        
        function refreshLogs() {
            loadRecentLogs();
            loadStatistics();
        }
        
        // Auto-refresh every 30 seconds
        setInterval(() => {
            loadStatistics();
            loadRecentLogs();
        }, 30000);
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def home():
    return HTMLResponse(content=ENHANCED_HTML)

@app.post("/detect/")
async def detect_vehicle(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        results = model(image, conf=0.92, verbose=False)
        
        detections = []
        for result in results:
            if result.boxes:
                for box in result.boxes:
                    class_id = int(box.cls[0])
                    if class_id in VEHICLE_CLASSES:
                        confidence = float(box.conf[0])
                        vehicle_type = VEHICLE_CLASSES[class_id]
                        
                        detections.append({
                            'type': vehicle_type,
                            'confidence': confidence,
                            'bbox': box.xyxy[0].tolist()
                        })
                        
                        # Log each detection to database
                        log_detection(vehicle_type, confidence, None)
        
        return {
            "success": True,
            "total_vehicles": len(detections),
            "detections": detections,
            "timestamp": datetime.now().isoformat(),
            "message": f"Found {len(detections)} vehicles with 92%+ confidence"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/statistics")
async def get_stats():
    """Get detection statistics"""
    return get_statistics()

@app.get("/heatmap/hourly")
async def get_hourly_heatmap():
    """Get hourly heatmap data as Plotly figure"""
    pivot = get_heatmap_data('hour')
    
    if pivot.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data available yet", x=0.5, y=0.5)
    else:
        fig = px.imshow(pivot.T, 
                        labels=dict(x="Hour of Day", y="Vehicle Type", color="Count"),
                        title="Vehicle Detection Heatmap (Last 7 Days)",
                        aspect="auto",
                        color_continuous_scale="Viridis")
        fig.update_layout(height=400)
    
    return {"figure": json.dumps(fig, cls=PlotlyJSONEncoder)}

@app.get("/vehicle-distribution")
async def get_vehicle_distribution():
    """Get vehicle type distribution pie chart"""
    stats = get_statistics()
    distribution = stats['vehicle_distribution']
    
    if distribution:
        fig = go.Figure(data=[go.Pie(labels=list(distribution.keys()), 
                                     values=list(distribution.values()),
                                     hole=.3)])
        fig.update_layout(title="Vehicle Type Distribution", height=400)
    else:
        fig = go.Figure()
        fig.add_annotation(text="No data available yet", x=0.5, y=0.5)
    
    return {"figure": json.dumps(fig, cls=PlotlyJSONEncoder)}

@app.get("/recent-logs")
async def get_recent_logs(limit: int = 20):
    """Get recent detection logs"""
    conn = sqlite3.connect('vehicle_detections.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT timestamp, vehicle_type, confidence 
        FROM detections 
        ORDER BY timestamp DESC 
        LIMIT ?
    ''', (limit,))
    
    logs = []
    for row in cursor.fetchall():
        logs.append({
            'timestamp': row[0],
            'vehicle_type': row[1],
            'confidence': row[2]
        })
    
    conn.close()
    return logs

@app.get("/export-data")
async def export_data():
    """Export detection data as CSV"""
    conn = sqlite3.connect('vehicle_detections.db')
    df = pd.read_sql_query("SELECT * FROM detections ORDER BY timestamp DESC", conn)
    conn.close()
    
    csv_data = df.to_csv(index=False)
    return JSONResponse(content={"csv": csv_data})

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("🚗 ENHANCED VEHICLE DETECTION SYSTEM")
    print("="*60)
    print("📍 Web Interface: http://localhost:8000")
    print("🎯 Confidence Threshold: 92%")
    print("📊 Features: Logging, Heatmaps, Analytics")
    print("="*60)
    print("\n✅ Server is starting...\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
