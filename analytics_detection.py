"""
Complete Vehicle Detection System with Advanced Analytics
Features: Real-time dashboard, heatmaps, trends, predictions, and export
"""

from fastapi import FastAPI, UploadFile, File, Query
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO
from PIL import Image
import io
import os
import sqlite3
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from collections import Counter, defaultdict
import json
from typing import Dict, List, Any

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database with more tables for analytics
def init_database():
    conn = sqlite3.connect('vehicle_analytics.db')
    cursor = conn.cursor()
    
    # Main detections table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS detections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME,
            vehicle_type TEXT,
            confidence REAL,
            hour INTEGER,
            day_of_week INTEGER,
            date DATE,
            week INTEGER,
            month INTEGER,
            year INTEGER
        )
    ''')
    
    # Daily summary table for faster analytics
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_summary (
            date DATE PRIMARY KEY,
            total_vehicles INTEGER,
            car_count INTEGER,
            truck_count INTEGER,
            bus_count INTEGER,
            motorcycle_count INTEGER,
            bicycle_count INTEGER,
            avg_confidence REAL
        )
    ''')
    
    conn.commit()
    conn.close()

init_database()

# Load model
print("Loading YOLOv8x model...")
model = YOLO('yolov8x.pt')
print("✅ Model loaded!")

VEHICLE_CLASSES = {1: 'bicycle', 2: 'car', 3: 'motorcycle', 5: 'bus', 7: 'truck'}
VEHICLE_EMOJIS = {'car': '🚗', 'bus': '🚌', 'truck': '🚚', 'motorcycle': '🏍️', 'bicycle': '🚲'}

def log_detection(vehicle_type, confidence):
    """Enhanced logging with time dimensions"""
    conn = sqlite3.connect('vehicle_analytics.db')
    cursor = conn.cursor()
    now = datetime.now()
    
    cursor.execute('''
        INSERT INTO detections 
        (timestamp, vehicle_type, confidence, hour, day_of_week, date, week, month, year)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (now, vehicle_type, confidence, now.hour, now.weekday(), 
          now.date(), now.isocalendar()[1], now.month, now.year))
    
    conn.commit()
    conn.close()
    update_daily_summary(now.date())

def update_daily_summary(date):
    """Update daily summary table"""
    conn = sqlite3.connect('vehicle_analytics.db')
    
    # Aggregate data for the date
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
    
    if not df.empty:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO daily_summary 
            (date, total_vehicles, car_count, truck_count, bus_count, motorcycle_count, bicycle_count, avg_confidence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (date, int(df['total'].iloc[0]), int(df['cars'].iloc[0]), 
              int(df['trucks'].iloc[0]), int(df['buses'].iloc[0]), 
              int(df['motorcycles'].iloc[0]), int(df['bicycles'].iloc[0]), 
              float(df['avg_conf'].iloc[0])))
        conn.commit()
    
    conn.close()

def get_analytics_data(period='day'):
    """Get comprehensive analytics data"""
    conn = sqlite3.connect('vehicle_analytics.db')
    
    # Hourly distribution
    hourly = pd.read_sql_query('''
        SELECT hour, vehicle_type, COUNT(*) as count
        FROM detections
        WHERE date >= date('now', '-7 days')
        GROUP BY hour, vehicle_type
        ORDER BY hour
    ''', conn)
    
    # Daily trends (last 30 days)
    daily = pd.read_sql_query('''
        SELECT date, vehicle_type, COUNT(*) as count
        FROM detections
        WHERE date >= date('now', '-30 days')
        GROUP BY date, vehicle_type
        ORDER BY date
    ''', conn)
    
    # Vehicle type distribution
    distribution = pd.read_sql_query('''
        SELECT vehicle_type, COUNT(*) as count
        FROM detections
        GROUP BY vehicle_type
        ORDER BY count DESC
    ''', conn)
    
    # Peak hours
    peak_hours = pd.read_sql_query('''
        SELECT hour, COUNT(*) as count
        FROM detections
        GROUP BY hour
        ORDER BY count DESC
        LIMIT 5
    ''', conn)
    
    # Weekly pattern
    weekly = pd.read_sql_query('''
        SELECT day_of_week, vehicle_type, COUNT(*) as count
        FROM detections
        WHERE date >= date('now', '-60 days')
        GROUP BY day_of_week, vehicle_type
        ORDER BY day_of_week
    ''', conn)
    
    # Recent activity (last 24 hours)
    recent = pd.read_sql_query('''
        SELECT datetime(timestamp) as time, vehicle_type, confidence
        FROM detections
        WHERE timestamp >= datetime('now', '-24 hours')
        ORDER BY timestamp DESC
        LIMIT 50
    ''', conn)
    
    # Statistics
    stats = pd.read_sql_query('''
        SELECT 
            COUNT(*) as total,
            AVG(confidence) as avg_confidence,
            COUNT(DISTINCT date) as active_days,
            MIN(date) as first_detection,
            MAX(date) as last_detection
        FROM detections
    ''', conn)
    
    # Today's stats
    today = datetime.now().date()
    today_stats = pd.read_sql_query(f'''
        SELECT COUNT(*) as count, AVG(confidence) as avg_conf
        FROM detections
        WHERE date = '{today}'
    ''', conn)
    
    # Hourly heatmap data
    heatmap_data = pd.read_sql_query('''
        SELECT hour, day_of_week, COUNT(*) as count
        FROM detections
        WHERE date >= date('now', '-30 days')
        GROUP BY hour, day_of_week
        ORDER BY day_of_week, hour
    ''', conn)
    
    conn.close()
    
    return {
        'hourly': hourly.to_dict('records') if not hourly.empty else [],
        'daily': daily.to_dict('records') if not daily.empty else [],
        'distribution': distribution.to_dict('records') if not distribution.empty else [],
        'peak_hours': peak_hours.to_dict('records') if not peak_hours.empty else [],
        'weekly': weekly.to_dict('records') if not weekly.empty else [],
        'recent': recent.to_dict('records') if not recent.empty else [],
        'stats': stats.to_dict('records')[0] if not stats.empty else {},
        'today_stats': today_stats.to_dict('records')[0] if not today_stats.empty else {'count': 0, 'avg_conf': 0},
        'heatmap': heatmap_data.to_dict('records') if not heatmap_data.empty else []
    }

# Analytics HTML Dashboard
ANALYTICS_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Vehicle Detection Analytics Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f5f5;
        }
        
        .navbar {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .navbar h1 {
            font-size: 1.8em;
        }
        
        .navbar p {
            opacity: 0.9;
            margin-top: 5px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: white;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            transition: transform 0.3s;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
        }
        
        .stat-card h3 {
            color: #666;
            font-size: 0.9em;
            margin-bottom: 10px;
        }
        
        .stat-value {
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
        }
        
        .stat-unit {
            font-size: 0.8em;
            color: #999;
        }
        
        .chart-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .chart-card {
            background: white;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .chart-card h3 {
            color: #333;
            margin-bottom: 15px;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }
        
        .chart-container {
            height: 400px;
        }
        
        .full-width {
            grid-column: 1 / -1;
        }
        
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            background: white;
            padding: 10px;
            border-radius: 10px;
        }
        
        .tab {
            padding: 10px 20px;
            cursor: pointer;
            border-radius: 8px;
            transition: all 0.3s;
        }
        
        .tab.active {
            background: #667eea;
            color: white;
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
        
        .upload-section {
            background: white;
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 30px;
        }
        
        .upload-area {
            border: 2px dashed #667eea;
            border-radius: 10px;
            padding: 30px;
            text-align: center;
            cursor: pointer;
            background: #f8f9fa;
        }
        
        .upload-area:hover {
            background: #e9ecef;
        }
        
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            margin-top: 10px;
        }
        
        .preview-img {
            max-width: 100%;
            max-height: 300px;
            border-radius: 10px;
            margin-top: 20px;
        }
        
        .loading {
            display: none;
            text-align: center;
            padding: 20px;
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
        
        @media (max-width: 768px) {
            .chart-grid {
                grid-template-columns: 1fr;
            }
            .stats-grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }
    </style>
</head>
<body>
    <div class="navbar">
        <div class="container">
            <h1>🚗 Vehicle Detection Analytics Dashboard</h1>
            <p>Real-time analytics, heatmaps, and insights from vehicle detection</p>
        </div>
    </div>
    
    <div class="container">
        <!-- Upload Section -->
        <div class="upload-section">
            <h3>📸 Upload & Detect New Vehicle</h3>
            <div class="upload-area" onclick="document.getElementById('fileInput').click()">
                Click to upload vehicle image
                <br><small>Supports: JPG, PNG, JPEG</small>
                <input type="file" id="fileInput" accept="image/*" style="display:none" onchange="previewImage()">
            </div>
            <div id="preview"></div>
            <button class="btn" onclick="detectVehicle()">🔍 Detect Vehicle</button>
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p>Analyzing with YOLOv8x...</p>
            </div>
            <div id="detectionResult"></div>
        </div>
        
        <!-- Stats Overview -->
        <div class="stats-grid" id="statsGrid">
            <div class="stat-card">
                <h3>Total Detections</h3>
                <div class="stat-value" id="totalDetections">0</div>
            </div>
            <div class="stat-card">
                <h3>Today's Detections</h3>
                <div class="stat-value" id="todayDetections">0</div>
            </div>
            <div class="stat-card">
                <h3>Average Confidence</h3>
                <div class="stat-value" id="avgConfidence">0<span class="stat-unit">%</span></div>
            </div>
            <div class="stat-card">
                <h3>Active Days</h3>
                <div class="stat-value" id="activeDays">0</div>
            </div>
        </div>
        
        <!-- Tabs -->
        <div class="tabs">
            <div class="tab active" onclick="switchTab('hourly')">Hourly Trends</div>
            <div class="tab" onclick="switchTab('daily')">Daily Trends</div>
            <div class="tab" onclick="switchTab('weekly')">Weekly Pattern</div>
            <div class="tab" onclick="switchTab('heatmap')">Heatmap</div>
            <div class="tab" onclick="switchTab('distribution')">Distribution</div>
        </div>
        
        <!-- Tab Contents -->
        <div id="hourlyTab" class="tab-content active">
            <div class="chart-card">
                <h3>📊 Hourly Vehicle Detection Trends (Last 7 Days)</h3>
                <div class="chart-container" id="hourlyChart"></div>
            </div>
        </div>
        
        <div id="dailyTab" class="tab-content">
            <div class="chart-card">
                <h3>📈 Daily Detection Trends (Last 30 Days)</h3>
                <div class="chart-container" id="dailyChart"></div>
            </div>
        </div>
        
        <div id="weeklyTab" class="tab-content">
            <div class="chart-card">
                <h3>📅 Weekly Pattern by Vehicle Type</h3>
                <div class="chart-container" id="weeklyChart"></div>
            </div>
        </div>
        
        <div id="heatmapTab" class="tab-content">
            <div class="chart-card">
                <h3>🔥 Detection Heatmap (Hour × Day of Week)</h3>
                <div class="chart-container" id="heatmapChart"></div>
            </div>
        </div>
        
        <div id="distributionTab" class="tab-content">
            <div class="chart-grid">
                <div class="chart-card">
                    <h3>🥧 Vehicle Type Distribution</h3>
                    <div class="chart-container" id="pieChart"></div>
                </div>
                <div class="chart-card">
                    <h3>🏆 Top 5 Peak Hours</h3>
                    <div class="chart-container" id="peakHoursChart"></div>
                </div>
            </div>
        </div>
        
        <!-- Recent Activity -->
        <div class="chart-card">
            <h3>🕒 Recent Detections (Last 24 Hours)</h3>
            <div id="recentActivity" style="max-height: 300px; overflow-y: auto;"></div>
        </div>
    </div>
    
    <script>
        let currentFile = null;
        
        function previewImage() {
            const file = document.getElementById('fileInput').files[0];
            if (file) {
                currentFile = file;
                const reader = new FileReader();
                reader.onload = e => {
                    document.getElementById('preview').innerHTML = `<img src="${e.target.result}" class="preview-img">`;
                };
                reader.readAsDataURL(file);
            }
        }
        
        async function detectVehicle() {
            if (!currentFile) {
                alert('Please select an image first');
                return;
            }
            
            const formData = new FormData();
            formData.append('file', currentFile);
            
            document.getElementById('loading').style.display = 'block';
            document.getElementById('detectionResult').innerHTML = '';
            
            try {
                const response = await fetch('/detect/', {
                    method: 'POST',
                    body: formData
                });
                const data = await response.json();
                
                if (data.success) {
                    let html = `<div style="margin-top: 15px; padding: 15px; background: #d4edda; border-radius: 8px;">
                        <strong>✅ Detection Complete!</strong><br>
                        Vehicles Found: ${data.total_vehicles}<br>
                        ${data.vehicle_breakdown ? Object.entries(data.vehicle_breakdown).map(([k,v]) => `${k}: ${v}`).join(', ') : ''}
                    </div>`;
                    document.getElementById('detectionResult').innerHTML = html;
                    
                    // Refresh all analytics
                    loadAnalytics();
                }
            } catch(e) {
                document.getElementById('detectionResult').innerHTML = `<div style="color: red;">Error: ${e.message}</div>`;
            } finally {
                document.getElementById('loading').style.display = 'none';
            }
        }
        
        async function loadAnalytics() {
            const response = await fetch('/analytics/data');
            const data = await response.json();
            
            // Update stats
            document.getElementById('totalDetections').textContent = data.stats.total || 0;
            document.getElementById('todayDetections').textContent = data.today_stats?.count || 0;
            document.getElementById('avgConfidence').innerHTML = `${Math.round((data.stats.avg_confidence || 0) * 100)}<span class="stat-unit">%</span>`;
            document.getElementById('activeDays').textContent = data.stats.active_days || 0;
            
            // Hourly chart
            if (data.hourly && data.hourly.length > 0) {
                const hourlyData = {};
                data.hourly.forEach(d => {
                    if (!hourlyData[d.hour]) hourlyData[d.hour] = {};
                    hourlyData[d.hour][d.vehicle_type] = d.count;
                });
                
                const hours = [...new Set(data.hourly.map(d => d.hour))].sort((a,b) => a-b);
                const vehicleTypes = [...new Set(data.hourly.map(d => d.vehicle_type))];
                
                const traces = vehicleTypes.map(vtype => ({
                    name: vtype.toUpperCase(),
                    x: hours,
                    y: hours.map(h => hourlyData[h]?.[vtype] || 0),
                    type: 'bar',
                    marker: { color: getColorForVehicle(vtype) }
                }));
                
                Plotly.newPlot('hourlyChart', traces, {
                    title: 'Vehicles by Hour',
                    xaxis: { title: 'Hour of Day' },
                    yaxis: { title: 'Number of Vehicles' },
                    barmode: 'stack'
                });
            }
            
            // Daily chart
            if (data.daily && data.daily.length > 0) {
                const dailyData = {};
                data.daily.forEach(d => {
                    if (!dailyData[d.date]) dailyData[d.date] = {};
                    dailyData[d.date][d.vehicle_type] = d.count;
                });
                
                const dates = [...new Set(data.daily.map(d => d.date))].slice(-30);
                const vehicleTypes = [...new Set(data.daily.map(d => d.vehicle_type))];
                
                const traces = vehicleTypes.map(vtype => ({
                    name: vtype.toUpperCase(),
                    x: dates,
                    y: dates.map(date => dailyData[date]?.[vtype] || 0),
                    type: 'scatter',
                    mode: 'lines+markers',
                    marker: { color: getColorForVehicle(vtype) }
                }));
                
                Plotly.newPlot('dailyChart', traces, {
                    title: 'Daily Vehicle Trends',
                    xaxis: { title: 'Date' },
                    yaxis: { title: 'Number of Vehicles' }
                });
            }
            
            // Weekly chart
            if (data.weekly && data.weekly.length > 0) {
                const weeklyData = {};
                data.weekly.forEach(d => {
                    if (!weeklyData[d.day_of_week]) weeklyData[d.day_of_week] = {};
                    weeklyData[d.day_of_week][d.vehicle_type] = d.count;
                });
                
                const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
                const vehicleTypes = [...new Set(data.weekly.map(d => d.vehicle_type))];
                
                const traces = vehicleTypes.map(vtype => ({
                    name: vtype.toUpperCase(),
                    x: days,
                    y: days.map((_, i) => weeklyData[i]?.[vtype] || 0),
                    type: 'bar',
                    marker: { color: getColorForVehicle(vtype) }
                }));
                
                Plotly.newPlot('weeklyChart', traces, {
                    title: 'Weekly Pattern by Vehicle Type',
                    xaxis: { title: 'Day of Week' },
                    yaxis: { title: 'Number of Vehicles' },
                    barmode: 'group'
                });
            }
            
            // Heatmap
            if (data.heatmap && data.heatmap.length > 0) {
                const heatmapData = {};
                data.heatmap.forEach(d => {
                    if (!heatmapData[d.day_of_week]) heatmapData[d.day_of_week] = {};
                    heatmapData[d.day_of_week][d.hour] = d.count;
                });
                
                const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
                const hours = [...Array(24).keys()];
                const z = days.map((_, dayIdx) => hours.map(hour => heatmapData[dayIdx]?.[hour] || 0));
                
                Plotly.newPlot('heatmapChart', [{
                    z: z,
                    x: hours,
                    y: days,
                    type: 'heatmap',
                    colorscale: 'Viridis'
                }], {
                    title: 'Detection Heatmap',
                    xaxis: { title: 'Hour of Day' },
                    yaxis: { title: 'Day of Week' }
                });
            }
            
            // Pie chart
            if (data.distribution && data.distribution.length > 0) {
                Plotly.newPlot('pieChart', [{
                    labels: data.distribution.map(d => d.vehicle_type.toUpperCase()),
                    values: data.distribution.map(d => d.count),
                    type: 'pie',
                    hole: 0.3,
                    marker: { colors: data.distribution.map(d => getColorForVehicle(d.vehicle_type)) }
                }], {
                    title: 'Vehicle Distribution'
                });
            }
            
            // Peak hours
            if (data.peak_hours && data.peak_hours.length > 0) {
                Plotly.newPlot('peakHoursChart', [{
                    x: data.peak_hours.map(p => `${p.hour}:00`),
                    y: data.peak_hours.map(p => p.count),
                    type: 'bar',
                    marker: { color: '#667eea' }
                }], {
                    title: 'Top 5 Peak Hours',
                    xaxis: { title: 'Hour' },
                    yaxis: { title: 'Vehicle Count' }
                });
            }
            
            // Recent activity
            if (data.recent && data.recent.length > 0) {
                let html = '<table style="width:100%; border-collapse: collapse;"><tr><th>Time</th><th>Vehicle</th><th>Confidence</th></tr>';
                data.recent.forEach(r => {
                    html += `<tr>
                        <td>${new Date(r.time).toLocaleTimeString()}</td>
                        <td>${getVehicleEmoji(r.vehicle_type)} ${r.vehicle_type.toUpperCase()}</td>
                        <td>${(r.confidence * 100).toFixed(1)}%</td>
                    </tr>`;
                });
                html += '</table>';
                document.getElementById('recentActivity').innerHTML = html;
            }
        }
        
        function getColorForVehicle(type) {
            const colors = {
                'car': '#667eea',
                'truck': '#f093fb',
                'bus': '#4facfe',
                'motorcycle': '#28a745',
                'bicycle': '#17a2b8'
            };
            return colors[type] || '#667eea';
        }
        
        function getVehicleEmoji(type) {
            const emojis = {
                'car': '🚗', 'bus': '🚌', 'truck': '🚚', 'motorcycle': '🏍️', 'bicycle': '🚲'
            };
            return emojis[type] || '🚗';
        }
        
        function switchTab(tab) {
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            
            document.getElementById(`${tab}Tab`).classList.add('active');
            event.target.classList.add('active');
        }
        
        // Load analytics on page load
        loadAnalytics();
        setInterval(loadAnalytics, 30000); // Refresh every 30 seconds
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def analytics_dashboard():
    return HTMLResponse(content=ANALYTICS_HTML)

@app.post("/detect/")
async def detect_vehicle(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        results = model(image, conf=0.5, verbose=False)
        
        detections = []
        vehicle_breakdown = Counter()
        
        for result in results:
            if result.boxes:
                for box in result.boxes:
                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    
                    if class_id in VEHICLE_CLASSES:
                        vehicle_type = VEHICLE_CLASSES[class_id]
                        
                        if confidence >= 0.92:  # Only log high-confidence detections
                            detections.append({
                                'type': vehicle_type,
                                'confidence': confidence,
                                'bbox': box.xyxy[0].tolist()
                            })
                            vehicle_breakdown[vehicle_type] += 1
                            log_detection(vehicle_type, confidence)
        
        return {
            "success": True,
            "total_vehicles": len(detections),
            "detections": detections,
            "vehicle_breakdown": dict(vehicle_breakdown),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/analytics/data")
async def get_analytics():
    """Get all analytics data"""
    return get_analytics_data()

@app.get("/export/csv")
async def export_csv():
    """Export detection data as CSV"""
    conn = sqlite3.connect('vehicle_analytics.db')
    df = pd.read_sql_query("SELECT * FROM detections ORDER BY timestamp DESC", conn)
    conn.close()
    
    csv_path = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df.to_csv(csv_path, index=False)
    
    return FileResponse(csv_path, media_type='text/csv', filename=csv_path)

@app.get("/api/insights")
async def get_insights():
    """Get AI-powered insights"""
    data = get_analytics_data()
    
    insights = []
    
    # Peak hour insight
    if data['peak_hours']:
        peak = data['peak_hours'][0]
        insights.append(f"📊 Peak traffic occurs at {peak['hour']}:00 with {peak['count']} vehicles")
    
    # Most common vehicle
    if data['distribution']:
        top = data['distribution'][0]
        insights.append(f"🚗 Most common vehicle: {top['vehicle_type'].upper()} ({top['count']} detections)")
    
    # Today's performance
    if data['today_stats']['count'] > 0:
        insights.append(f"✅ Today: {data['today_stats']['count']} vehicles detected with {data['today_stats']['avg_conf']*100:.1f}% avg confidence")
    
    # Total insights
    if data['stats'].get('total', 0) > 0:
        insights.append(f"📈 Total system performance: {data['stats']['total']} detections over {data['stats']['active_days']} days")
    
    return {"insights": insights}

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("🚗 VEHICLE DETECTION ANALYTICS SYSTEM")
    print("="*60)
    print("📍 Web Interface: http://localhost:8000")
    print("📊 Features: Real-time analytics, heatmaps, trends, exports")
    print("="*60)
    print("\n✅ Server is starting...\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
