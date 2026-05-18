"""
Simple Working Vehicle Detection App
"""

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from working_detection import detector
from datetime import datetime
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple HTML Interface
HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Vehicle Detection System</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .card {
            background: white;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        h1 {
            color: #333;
            margin-top: 0;
        }
        .upload-area {
            border: 2px dashed #667eea;
            border-radius: 10px;
            padding: 40px;
            text-align: center;
            cursor: pointer;
            background: #f8f9fa;
            margin: 20px 0;
        }
        .upload-area:hover {
            background: #e9ecef;
        }
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 16px;
            width: 100%;
        }
        button:hover {
            transform: translateY(-2px);
        }
        .result {
            background: #f8f9fa;
            padding: 15px;
            margin: 10px 0;
            border-radius: 8px;
            border-left: 4px solid #28a745;
        }
        .preview {
            max-width: 100%;
            border-radius: 10px;
            margin: 20px 0;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin-bottom: 20px;
        }
        .stat {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
        }
        .stat-number {
            font-size: 2em;
            font-weight: bold;
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
        .detected-image {
            max-width: 100%;
            border-radius: 10px;
            margin-top: 20px;
            border: 2px solid #28a745;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h1>🚗 Vehicle Detection System</h1>
            <p>Upload any image - Vehicles will be detected with bounding boxes</p>
            
            <div class="stats" id="stats">
                <div class="stat"><div class="stat-number" id="total">0</div><div>Total Detections</div></div>
                <div class="stat"><div class="stat-number" id="today">0</div><div>Today</div></div>
                <div class="stat"><div class="stat-number" id="avgConf">0%</div><div>Avg Confidence</div></div>
                <div class="stat"><div class="stat-number" id="types">0</div><div>Vehicle Types</div></div>
            </div>
            
            <div class="upload-area" onclick="document.getElementById('fileInput').click()">
                📸 Click to upload image<br>
                <small>JPG, PNG, JPEG</small>
                <input type="file" id="fileInput" accept="image/*" style="display:none" onchange="previewImage()">
            </div>
            
            <div id="preview"></div>
            
            <button onclick="detectVehicle()">🔍 Detect Vehicles</button>
            
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p>Processing image...</p>
            </div>
            
            <div id="results"></div>
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
                    document.getElementById('preview').innerHTML = `<img src="${e.target.result}" class="preview">`;
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
            document.getElementById('results').innerHTML = '';
            
            try {
                const response = await fetch('/detect', { method: 'POST', body: formData });
                const data = await response.json();
                
                if (data.success) {
                    // Show results
                    let html = `<h3>✅ Detection Complete!</h3>`;
                    html += `<p><strong>Total Vehicles:</strong> ${data.total_vehicles}</p>`;
                    html += `<p><strong>Timestamp:</strong> ${new Date(data.timestamp).toLocaleString()}</p>`;
                    
                    if (data.vehicle_breakdown && Object.keys(data.vehicle_breakdown).length > 0) {
                        html += `<h4>Vehicle Breakdown:</h4>`;
                        for (const [type, count] of Object.entries(data.vehicle_breakdown)) {
                            html += `<div class="result">${getIcon(type)} ${type.toUpperCase()}: ${count} vehicles</div>`;
                        }
                    }
                    
                    if (data.detections && data.detections.length > 0) {
                        html += `<h4>Individual Detections:</h4>`;
                        data.detections.forEach(d => {
                            html += `<div class="result">
                                ${getIcon(d.type)} <strong>${d.type.toUpperCase()}</strong><br>
                                Confidence: ${(d.confidence * 100).toFixed(1)}%
                            </div>`;
                        });
                        
                        // Show annotated image
                        if (data.annotated_image) {
                            html += `<h4>Detected Image:</h4>`;
                            html += `<img src="/image/${data.annotated_image}" class="detected-image">`;
                        }
                    }
                    
                    document.getElementById('results').innerHTML = html;
                    loadStats();
                } else {
                    document.getElementById('results').innerHTML = `<p style="color: red;">Error: ${data.error}</p>`;
                }
            } catch(e) {
                document.getElementById('results').innerHTML = `<p style="color: red;">Error: ${e.message}</p>`;
            } finally {
                document.getElementById('loading').style.display = 'none';
            }
        }
        
        function getIcon(type) {
            const icons = {
                'car': '🚗', 'truck': '🚚', 'bus': '🚌', 
                'motorcycle': '🏍️', 'bicycle': '🚲'
            };
            return icons[type] || '🚗';
        }
        
        async function loadStats() {
            try {
                const response = await fetch('/stats');
                const stats = await response.json();
                document.getElementById('total').textContent = stats.total_detections || 0;
                document.getElementById('today').textContent = stats.today_detections || 0;
                document.getElementById('avgConf').innerHTML = `${Math.round((stats.average_confidence || 0) * 100)}%`;
                document.getElementById('types').textContent = stats.unique_vehicle_types || 0;
            } catch(e) {
                console.error('Stats error:', e);
            }
        }
        
        loadStats();
        setInterval(loadStats, 10000);
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def home():
    return HTMLResponse(content=HTML)

@app.post("/detect")
async def detect(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()
        result = detector.detect(image_bytes)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/stats")
async def get_stats():
    return detector.get_statistics()

@app.get("/logs")
async def get_logs():
    return detector.get_recent_logs()

@app.get("/image/{filename}")
async def get_image(filename: str):
    return FileResponse(filename)

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("🚗 WORKING VEHICLE DETECTION SYSTEM")
    print("="*60)
    print("📍 Web Interface: http://localhost:8000")
    print("🎯 Detection Threshold: 50% (Detects all vehicles)")
    print("📊 Features: Bounding boxes, logging, analytics")
    print("="*60)
    print("\n✅ Server is running!\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
