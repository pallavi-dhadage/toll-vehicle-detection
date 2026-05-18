"""
Final Fixed Vehicle Detection - Shows ALL Vehicle Types Properly
"""

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO
from PIL import Image
import io
import os
import sqlite3
from datetime import datetime
from collections import Counter

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
model = YOLO('yolov8x.pt')
print("✅ Model loaded successfully!")

# Vehicle classes mapping
VEHICLE_CLASSES = {
    1: 'bicycle',
    2: 'car', 
    3: 'motorcycle',
    5: 'bus',
    7: 'truck'
}

# Emoji mapping for display
VEHICLE_EMOJIS = {
    'car': '🚗',
    'bus': '🚌',
    'truck': '🚚',
    'motorcycle': '🏍️',
    'bicycle': '🚲'
}

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
    print(f"📝 Logged: {vehicle_type} with {confidence:.1%} confidence")

# Complete HTML with better truck/bus display
COMPLETE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Complete Vehicle Detection - All Types</title>
    <meta charset="UTF-8">
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
            grid-template-columns: repeat(4, 1fr);
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
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .vehicle-icon {
            font-size: 32px;
        }
        
        .vehicle-info {
            flex: 1;
        }
        
        .vehicle-type {
            font-size: 18px;
            font-weight: bold;
            text-transform: uppercase;
        }
        
        .confidence {
            font-size: 14px;
            margin-top: 5px;
        }
        
        .confidence-high {
            color: #28a745;
            font-weight: bold;
        }
        
        .breakdown-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
            gap: 10px;
            margin: 15px 0;
        }
        
        .breakdown-item {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 10px;
            border-radius: 10px;
            text-align: center;
        }
        
        .breakdown-count {
            font-size: 24px;
            font-weight: bold;
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
        
        .log-table tr:hover {
            background: #f5f5f5;
        }
        
        @media (max-width: 768px) {
            .main-grid {
                grid-template-columns: 1fr;
            }
            .dashboard {
                grid-template-columns: repeat(2, 1fr);
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚗 Complete Vehicle Detection System</h1>
            <p>Detects: Cars 🚗 | Buses 🚌 | Trucks 🚚 | Motorcycles 🏍️ | Bicycles 🚲</p>
        </div>
        
        <div class="dashboard" id="dashboard">
            <div class="stat-card primary">
                <div class="stat-number" id="totalDetections">0</div>
                <div class="stat-label">Total Detections</div>
            </div>
            <div class="stat-card primary">
                <div class="stat-number" id="todayDetections">0</div>
                <div class="stat-label">Today</div>
            </div>
            <div class="stat-card primary">
                <div class="stat-number" id="avgConfidence">0%</div>
                <div class="stat-label">Avg Confidence</div>
            </div>
            <div class="stat-card primary">
                <div class="stat-number" id="uniqueTypes">0</div>
                <div class="stat-label">Vehicle Types</div>
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
                <button class="btn" onclick="refreshData()" style="margin-top: 10px; background: #6c757d;">🔄 Refresh Data</button>
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
                    
                    // Show vehicle breakdown
                    if (data.vehicle_breakdown && Object.keys(data.vehicle_breakdown).length > 0) {
                        html += '<h4>📊 Vehicle Breakdown:</h4>';
                        html += '<div class="breakdown-grid">';
                        for (const [type, count] of Object.entries(data.vehicle_breakdown)) {
                            const emoji = getVehicleEmoji(type);
                            html += `
                                <div class="breakdown-item">
                                    <div>${emoji}</div>
                                    <div class="breakdown-count">${count}</div>
                                    <div>${type.toUpperCase()}</div>
                                </div>
                            `;
                        }
                        html += '</div>';
                    }
                    
                    // Show individual detections
                    if (data.detections && data.detections.length > 0) {
                        html += '<h4 style="margin-top: 20px;">🔍 Individual Detections:</h4>';
                        for (const d of data.detections) {
                            const confPercent = (d.confidence * 100).toFixed(1);
                            const confClass = d.confidence >= 0.92 ? 'confidence-high' : '';
                            const emoji = getVehicleEmoji(d.type);
                            html += `
                                <div class="result-item">
                                    <div class="vehicle-icon">${emoji}</div>
                                    <div class="vehicle-info">
                                        <div class="vehicle-type">${d.type.toUpperCase()}</div>
                                        <div class="confidence">Confidence: <span class="${confClass}">${confPercent}%</span></div>
                                        <div class="confidence">Position: [${Math.round(d.bbox[0])}, ${Math.round(d.bbox[1])}]</div>
                                    </div>
                                </div>
                            `;
                        }
                    } else {
                        html += '<p style="color: orange; margin-top: 20px;">⚠️ No vehicles detected with 92%+ confidence</p>';
                        html += '<p>💡 Tips for better detection:<br>';
                        html += '• Use clearer, well-lit images<br>';
                        html += '• Ensure vehicles are clearly visible<br>';
                        html += '• Try images with vehicles from front/side views</p>';
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
        
        function getVehicleEmoji(type) {
            const emojis = {
                'car': '🚗',
                'bus': '🚌',
                'truck': '🚚',
                'motorcycle': '🏍️',
                'bicycle': '🚲'
            };
            return emojis[type] || '🚗';
        }
        
        async function loadStatistics() {
            try {
                const response = await fetch('/statistics');
                const stats = await response.json();
                document.getElementById('totalDetections').textContent = stats.total_detections || 0;
                document.getElementById('todayDetections').textContent = stats.today_detections || 0;
                document.getElementById('avgConfidence').textContent = `${Math.round((stats.average_confidence || 0) * 100)}%`;
                document.getElementById('uniqueTypes').textContent = stats.unique_vehicle_types || 0;
            } catch(e) {
                console.error('Failed to load stats:', e);
            }
        }
        
        async function loadRecentLogs() {
            try {
                const response = await fetch('/recent-logs');
                const logs = await response.json();
                
                if (logs.length === 0) {
                    document.getElementById('recentLogs').innerHTML = '<p style="text-align: center; color: #666;">No detections yet. Upload an image to get started!</p>';
                    return;
                }
                
                let html = '<table class="log-table">';
                html += '<thead><tr><th>Time</th><th>Vehicle</th><th>Confidence</th></tr></thead>';
                html += '<tbody>';
                
                for (const log of logs) {
                    const emoji = getVehicleEmoji(log.vehicle_type);
                    html += `
                        <tr>
                            <td>${new Date(log.timestamp).toLocaleTimeString()}</td>
                            <td>${emoji} ${log.vehicle_type.toUpperCase()}</td>
                            <td>${(log.confidence * 100).toFixed(1)}%</span></td>
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
        
        // Auto-refresh every 10 seconds
        setInterval(() => {
            loadStatistics();
            loadRecentLogs();
        }, 10000);
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def home():
    return HTMLResponse(content=COMPLETE_HTML)

@app.post("/detect/")
async def detect_vehicle(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        # Run detection with 0.5 threshold to catch all vehicles
        results = model(image, conf=0.5, verbose=False)
        
        detections = []
        vehicle_breakdown = Counter()
        
        print(f"\n{'='*50}")
        print(f"Processing: {file.filename}")
        print(f"{'='*50}")
        
        for result in results:
            if result.boxes:
                for box in result.boxes:
                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    
                    if class_id in VEHICLE_CLASSES:
                        vehicle_type = VEHICLE_CLASSES[class_id]
                        
                        print(f"Detected: {vehicle_type.upper()} - Confidence: {confidence:.1%}")
                        
                        # Only show and log detections with 92%+ confidence
                        if confidence >= 0.92:
                            detections.append({
                                'type': vehicle_type,
                                'confidence': confidence,
                                'bbox': box.xyxy[0].tolist()
                            })
                            vehicle_breakdown[vehicle_type] += 1
                            log_detection(vehicle_type, confidence)
                        else:
                            print(f"  ⚠️ Below 92% threshold (not logged)")
        
        print(f"\n✅ Total high-confidence detections (92%+): {len(detections)}")
        print(f"📊 Vehicle breakdown: {dict(vehicle_breakdown)}")
        print(f"{'='*50}\n")
        
        return {
            "success": True,
            "total_vehicles": len(detections),
            "detections": detections,
            "vehicle_breakdown": dict(vehicle_breakdown),
            "timestamp": datetime.now().isoformat(),
            "message": f"Found {len(detections)} vehicles with 92%+ confidence"
        }
    except Exception as e:
        print(f"❌ Error: {str(e)}")
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
    
    cursor.execute("SELECT COUNT(DISTINCT vehicle_type) FROM detections")
    unique_types = cursor.fetchone()[0] or 0
    
    conn.close()
    
    return {
        "total_detections": total,
        "today_detections": today,
        "average_confidence": avg_conf,
        "unique_vehicle_types": unique_types
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
    print("🎯 Detects: Cars 🚗 | Buses 🚌 | Trucks 🚚 | Motorcycles 🏍️")
    print("📊 Confidence Threshold: 92%+ for logging")
    print("="*60)
    print("\n✅ Server is starting...\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
