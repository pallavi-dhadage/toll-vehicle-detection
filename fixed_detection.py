"""
Fixed Vehicle Detection - Shows ALL Vehicle Types (Car, Bus, Truck, Motorcycle)
"""

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO
from PIL import Image
import io
import os
import sqlite3
from datetime import datetime
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
def init_database():
    conn = sqlite3.connect('vehicle_detections.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS detections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME,
            vehicle_type TEXT,
            confidence REAL,
            hour INTEGER,
            date DATE
        )
    ''')
    conn.commit()
    conn.close()

init_database()

# Load model
print("Loading YOLOv8x model...")
model = YOLO('yolov8x.pt') if os.path.exists('yolov8x.pt') else YOLO('yolov8x.pt')
print("Model loaded successfully!")

# Complete vehicle classes mapping
VEHICLE_CLASSES = {
    1: 'bicycle',
    2: 'car', 
    3: 'motorcycle',
    4: 'airplane',  # Not typical for roads
    5: 'bus',
    6: 'train',    # Not typical for roads  
    7: 'truck',
    8: 'boat'      # Not typical for roads
}

# Only road vehicles
ROAD_VEHICLES = {1: 'bicycle', 2: 'car', 3: 'motorcycle', 5: 'bus', 7: 'truck'}

def log_detection(vehicle_type, confidence):
    """Log detection to database"""
    conn = sqlite3.connect('vehicle_detections.db')
    cursor = conn.cursor()
    now = datetime.now()
    cursor.execute('''
        INSERT INTO detections (timestamp, vehicle_type, confidence, hour, date)
        VALUES (?, ?, ?, ?, ?)
    ''', (now, vehicle_type, confidence, now.hour, now.date()))
    conn.commit()
    conn.close()

# Enhanced HTML with better debugging
ENHANCED_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Vehicle Detection - All Types</title>
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
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
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
            padding: 40px;
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
        
        .preview-img {
            max-width: 100%;
            border-radius: 10px;
            margin-top: 20px;
            max-height: 300px;
            object-fit: contain;
        }
        
        .result-item {
            background: #f8f9fa;
            padding: 15px;
            margin: 10px 0;
            border-radius: 8px;
            border-left: 4px solid #28a745;
        }
        
        .vehicle-icon {
            font-size: 24px;
            margin-right: 10px;
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
        
        .confidence-high {
            color: #28a745;
            font-weight: bold;
        }
        
        .confidence-medium {
            color: #ffc107;
            font-weight: bold;
        }
        
        .log-table {
            width: 100%;
            border-collapse: collapse;
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
            <h1>🚗 Complete Vehicle Detection System</h1>
            <p>Detects: Cars, Buses, Trucks, Motorcycles, Bicycles | 92%+ Confidence</p>
        </div>
        
        <div class="dashboard" id="dashboard">
            <div class="stat-card primary">
                <div class="stat-number" id="totalDetections">0</div>
                <div>Total Detections</div>
            </div>
            <div class="stat-card primary">
                <div class="stat-number" id="todayDetections">0</div>
                <div>Today</div>
            </div>
            <div class="stat-card primary">
                <div class="stat-number" id="avgConfidence">0%</div>
                <div>Avg Confidence</div>
            </div>
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
                <button class="btn" onclick="detectVehicles()">🔍 Detect All Vehicles (92%+ Confidence)</button>
                <div class="loading" id="loading">
                    <div class="spinner"></div>
                    <p>Analyzing image with YOLOv8x...</p>
                </div>
                <div id="detectionResults"></div>
            </div>
            
            <div class="card">
                <h2>📊 Recent Detections Log</h2>
                <div id="recentLogs"></div>
                <button class="btn" onclick="refreshData()" style="margin-top: 10px;">🔄 Refresh</button>
            </div>
        </div>
    </div>
    
    <script>
        let currentFile = null;
        
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
                    
                    if (data.vehicle_breakdown && Object.keys(data.vehicle_breakdown).length > 0) {
                        html += '<h4>Vehicle Breakdown:</h4>';
                        for (const [type, count] of Object.entries(data.vehicle_breakdown)) {
                            const icon = getVehicleIcon(type);
                            html += `<p>${icon} ${type.toUpperCase()}: ${count}</p>`;
                        }
                    }
                    
                    if (data.detections && data.detections.length > 0) {
                        html += '<h4 style="margin-top: 15px;">Individual Detections:</h4>';
                        for (const d of data.detections) {
                            const confPercent = (d.confidence * 100).toFixed(1);
                            const confClass = d.confidence >= 0.92 ? 'confidence-high' : 'confidence-medium';
                            const icon = getVehicleIcon(d.type);
                            html += `
                                <div class="result-item">
                                    <span class="vehicle-icon">${icon}</span>
                                    <strong>${d.type.toUpperCase()}</strong><br>
                                    Confidence: <span class="${confClass}">${confPercent}%</span><br>
                                    Position: [${Math.round(d.bbox[0])}, ${Math.round(d.bbox[1])}]
                                </div>
                            `;
                        }
                    } else {
                        html += '<p style="color: orange;">⚠️ No vehicles detected with 92%+ confidence</p>';
                        html += '<p>💡 Tips:<br>- Try images with clearer vehicles<br>- Ensure good lighting<br>- Vehicles should be visible</p>';
                    }
                    
                    document.getElementById('detectionResults').innerHTML = html;
                    
                    // Refresh stats and logs
                    loadStatistics();
                    loadRecentLogs();
                } else {
                    document.getElementById('detectionResults').innerHTML = `<p style="color: red;">❌ Error: ${data.error}</p>`;
                }
            } catch (error) {
                document.getElementById('detectionResults').innerHTML = `<p style="color: red;">❌ Error: ${error.message}</p>`;
            } finally {
                document.getElementById('loading').style.display = 'none';
            }
        }
        
        function getVehicleIcon(type) {
            const icons = {
                'car': '🚗',
                'bus': '🚌',
                'truck': '🚚',
                'motorcycle': '🏍️',
                'bicycle': '🚲'
            };
            return icons[type] || '🚗';
        }
        
        async function loadStatistics() {
            try {
                const response = await fetch('/statistics');
                const stats = await response.json();
                document.getElementById('totalDetections').textContent = stats.total_detections || 0;
                document.getElementById('todayDetections').textContent = stats.today_detections || 0;
                document.getElementById('avgConfidence').textContent = `${Math.round((stats.average_confidence || 0) * 100)}%`;
            } catch(e) {
                console.error('Failed to load stats:', e);
            }
        }
        
        async function loadRecentLogs() {
            try {
                const response = await fetch('/recent-logs');
                const logs = await response.json();
                
                if (logs.length === 0) {
                    document.getElementById('recentLogs').innerHTML = '<p>No detections yet. Upload an image to get started!</p>';
                    return;
                }
                
                let html = '<table class="log-table">';
                html += '<thead><tr><th>Time</th><th>Vehicle Type</th><th>Confidence</th></tr></thead>';
                html += '<tbody>';
                
                for (const log of logs) {
                    const icon = getVehicleIcon(log.vehicle_type);
                    html += `
                        <tr>
                            <td>${new Date(log.timestamp).toLocaleTimeString()}</td>
                            <td>${icon} ${log.vehicle_type.toUpperCase()}</td>
                            <td>${(log.confidence * 100).toFixed(1)}%</td>
                        </tr>
                    `;
                }
                
                html += '</tbody></table>';
                document.getElementById('recentLogs').innerHTML = html;
            } catch(e) {
                console.error('Failed to load logs:', e);
            }
        }
        
        function refreshData() {
            loadStatistics();
            loadRecentLogs();
        }
        
        // Load initial data
        loadStatistics();
        loadRecentLogs();
        
        // Auto-refresh every 15 seconds
        setInterval(() => {
            loadStatistics();
            loadRecentLogs();
        }, 15000);
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
        
        # Use lower confidence for debugging, then filter
        results = model(image, conf=0.5, verbose=False)  # Lower threshold to catch all vehicles
        
        detections = []
        vehicle_breakdown = {}
        
        print(f"Processing image: {file.filename}")
        print(f"Raw results: {len(results[0].boxes) if results[0].boxes else 0} objects detected")
        
        for result in results:
            if result.boxes:
                for box in result.boxes:
                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    
                    # Check if it's a road vehicle
                    if class_id in ROAD_VEHICLES:
                        vehicle_type = ROAD_VEHICLES[class_id]
                        
                        # Only log if confidence is 70%+ (for testing, then we'll show 92%+ in UI)
                        if confidence >= 0.7:
                            detections.append({
                                'type': vehicle_type,
                                'confidence': confidence,
                                'bbox': box.xyxy[0].tolist()
                            })
                            
                            # Count for breakdown
                            vehicle_breakdown[vehicle_type] = vehicle_breakdown.get(vehicle_type, 0) + 1
                            
                            # Log to database only for 92%+ confidence
                            if confidence >= 0.92:
                                log_detection(vehicle_type, confidence)
                                print(f"✅ Logged: {vehicle_type} with {confidence:.1%} confidence")
                            else:
                                print(f"⚠️ {vehicle_type} detected but below 92% threshold: {confidence:.1%}")
        
        # Filter to show only 92%+ in response
        high_conf_detections = [d for d in detections if d['confidence'] >= 0.92]
        
        print(f"Total high-confidence detections (92%+): {len(high_conf_detections)}")
        print(f"Vehicle breakdown: {vehicle_breakdown}")
        
        return {
            "success": True,
            "total_vehicles": len(high_conf_detections),
            "detections": high_conf_detections,
            "vehicle_breakdown": vehicle_breakdown,
            "timestamp": datetime.now().isoformat(),
            "message": f"Found {len(high_conf_detections)} vehicles with 92%+ confidence"
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        return {"success": False, "error": str(e)}

@app.get("/statistics")
async def get_stats():
    """Get detection statistics"""
    conn = sqlite3.connect('vehicle_detections.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM detections")
    total = cursor.fetchone()[0]
    
    cursor.execute(f"SELECT COUNT(*) FROM detections WHERE date = '{datetime.now().date()}'")
    today = cursor.fetchone()[0]
    
    cursor.execute("SELECT AVG(confidence) FROM detections")
    avg_conf = cursor.fetchone()[0] or 0
    
    conn.close()
    
    return {
        "total_detections": total,
        "today_detections": today,
        "average_confidence": avg_conf
    }

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

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("🚗 COMPLETE VEHICLE DETECTION SYSTEM")
    print("="*60)
    print("📍 Web Interface: http://localhost:8000")
    print("🎯 Detects: Cars, Buses, Trucks, Motorcycles, Bicycles")
    print("📊 Confidence Threshold: 92%+ for logging")
    print("="*60)
    print("\n✅ Server is starting...\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
