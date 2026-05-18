"""
Real-Time Vehicle Detection with Webcam and Live Stream
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from realtime_detection import detector
import asyncio
import json
from datetime import datetime
import threading

app = FastAPI(title="Real-Time Vehicle Detection")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        detector.active_connections = self.active_connections
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            detector.active_connections = self.active_connections

manager = ConnectionManager()

# Real-Time HTML Interface
REALTIME_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Real-Time Vehicle Detection</title>
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
        
        .main-grid {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 20px;
        }
        
        .video-card {
            background: white;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        
        .video-container {
            position: relative;
            background: #000;
            border-radius: 10px;
            overflow: hidden;
            margin-top: 15px;
        }
        
        video, .video-feed {
            width: 100%;
            height: auto;
            background: #000;
        }
        
        .controls {
            margin-top: 20px;
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 14px;
            transition: transform 0.2s;
        }
        
        button:hover {
            transform: translateY(-2px);
        }
        
        button.danger {
            background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
        }
        
        button.success {
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
        }
        
        .stats-card {
            background: white;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        
        .stat {
            background: #f8f9fa;
            padding: 15px;
            margin: 10px 0;
            border-radius: 10px;
            text-align: center;
        }
        
        .stat-number {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }
        
        .detection-list {
            max-height: 400px;
            overflow-y: auto;
        }
        
        .detection-item {
            background: #f8f9fa;
            padding: 10px;
            margin: 5px 0;
            border-radius: 8px;
            border-left: 4px solid #28a745;
            font-size: 12px;
        }
        
        .upload-area {
            border: 2px dashed #667eea;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            cursor: pointer;
            background: #f8f9fa;
            margin-top: 15px;
        }
        
        .upload-area:hover {
            background: #e9ecef;
        }
        
        .mode-selector {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        
        .mode-btn {
            flex: 1;
            background: #e9ecef;
            color: #333;
        }
        
        .mode-btn.active {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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
            <h1>🚗 Real-Time Vehicle Detection System</h1>
            <p>Live webcam feed | Vehicle detection | Real-time analytics</p>
        </div>
        
        <div class="mode-selector">
            <button class="mode-btn active" onclick="setMode('webcam')">📹 Live Webcam</button>
            <button class="mode-btn" onclick="setMode('upload')">📸 Upload Image</button>
        </div>
        
        <div class="main-grid">
            <div class="video-card">
                <h2>Live Detection Feed</h2>
                <div id="webcamMode">
                    <div class="controls">
                        <button id="startWebcam" onclick="startWebcam()" class="success">▶ Start Webcam</button>
                        <button id="stopWebcam" onclick="stopWebcam()" class="danger" disabled>⏹ Stop Webcam</button>
                        <button onclick="captureImage()">📸 Capture</button>
                    </div>
                    <div class="video-container">
                        <video id="webcam" autoplay playsinline style="width: 100%; display: none;"></video>
                        <img id="liveFeed" class="video-feed" style="display: none;">
                        <canvas id="canvas" style="display: none;"></canvas>
                    </div>
                </div>
                
                <div id="uploadMode" style="display: none;">
                    <div class="upload-area" onclick="document.getElementById('fileInput').click()">
                        📸 Click to upload vehicle image
                        <input type="file" id="fileInput" accept="image/*" style="display:none" onchange="uploadImage()">
                    </div>
                    <div id="uploadPreview"></div>
                    <div id="uploadResult"></div>
                </div>
            </div>
            
            <div class="stats-card">
                <h2>📊 Live Statistics</h2>
                <div class="stat">
                    <div class="stat-number" id="totalDetections">0</div>
                    <div>Total Detections</div>
                </div>
                <div class="stat">
                    <div class="stat-number" id="todayDetections">0</div>
                    <div>Today</div>
                </div>
                <div class="stat">
                    <div class="stat-number" id="avgConfidence">0%</div>
                    <div>Avg Confidence</div>
                </div>
                
                <h3 style="margin-top: 20px;">🕒 Recent Detections</h3>
                <div id="recentDetections" class="detection-list"></div>
            </div>
        </div>
    </div>
    
    <script>
        let currentMode = 'webcam';
        let mediaStream = null;
        let ws = null;
        let detectionInterval = null;
        
        // Connect WebSocket for live feed
        function connectWebSocket() {
            ws = new WebSocket(`ws://${window.location.host}/ws`);
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                if (data.frame) {
                    document.getElementById('liveFeed').src = 'data:image/jpeg;base64,' + data.frame;
                    document.getElementById('liveFeed').style.display = 'block';
                    document.getElementById('webcam').style.display = 'none';
                }
            };
            
            ws.onclose = () => {
                console.log('WebSocket disconnected, reconnecting...');
                setTimeout(connectWebSocket, 1000);
            };
        }
        
        async function startWebcam() {
            const video = document.getElementById('webcam');
            const liveFeed = document.getElementById('liveFeed');
            
            try {
                mediaStream = await navigator.mediaDevices.getUserMedia({ video: true });
                video.srcObject = mediaStream;
                video.style.display = 'block';
                liveFeed.style.display = 'none';
                
                document.getElementById('startWebcam').disabled = true;
                document.getElementById('stopWebcam').disabled = false;
                
                // Start sending frames
                startFrameCapture();
            } catch(err) {
                console.error('Webcam error:', err);
                alert('Could not access webcam. Please check permissions.');
            }
        }
        
        function stopWebcam() {
            if (mediaStream) {
                mediaStream.getTracks().forEach(track => track.stop());
                mediaStream = null;
            }
            
            if (detectionInterval) {
                clearInterval(detectionInterval);
            }
            
            document.getElementById('webcam').style.display = 'none';
            document.getElementById('startWebcam').disabled = false;
            document.getElementById('stopWebcam').disabled = true;
        }
        
        async function startFrameCapture() {
            const video = document.getElementById('webcam');
            const canvas = document.getElementById('canvas');
            const context = canvas.getContext('2d');
            
            detectionInterval = setInterval(async () => {
                if (video.readyState === video.HAVE_ENOUGH_DATA) {
                    canvas.width = video.videoWidth;
                    canvas.height = video.videoHeight;
                    context.drawImage(video, 0, 0, canvas.width, canvas.height);
                    
                    canvas.toBlob(async (blob) => {
                        const formData = new FormData();
                        formData.append('file', blob, 'frame.jpg');
                        
                        const response = await fetch('/detect-frame', {
                            method: 'POST',
                            body: formData
                        });
                        
                        const data = await response.json();
                        updateStats(data);
                    }, 'image/jpeg', 0.5);
                }
            }, 500); // Process every 500ms
        }
        
        async function captureImage() {
            const video = document.getElementById('webcam');
            const canvas = document.getElementById('canvas');
            const context = canvas.getContext('2d');
            
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            context.drawImage(video, 0, 0, canvas.width, canvas.height);
            
            canvas.toBlob(async (blob) => {
                const formData = new FormData();
                formData.append('file', blob, 'capture.jpg');
                
                const response = await fetch('/detect', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                alert(`Captured! Found ${data.total_vehicles} vehicles`);
                updateStats(data);
            }, 'image/jpeg');
        }
        
        async function uploadImage() {
            const file = document.getElementById('fileInput').files[0];
            if (!file) return;
            
            const formData = new FormData();
            formData.append('file', file);
            
            const preview = document.getElementById('uploadPreview');
            const reader = new FileReader();
            reader.onload = e => {
                preview.innerHTML = `<img src="${e.target.result}" style="max-width: 100%; border-radius: 10px; margin-top: 10px;">`;
            };
            reader.readAsDataURL(file);
            
            const response = await fetch('/detect', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            let html = `<div style="margin-top: 15px; padding: 15px; background: #d4edda; border-radius: 8px;">
                <strong>✅ Detection Complete!</strong><br>
                Vehicles Found: ${data.total_vehicles}<br>`;
            
            if (data.vehicle_breakdown) {
                for (const [type, count] of Object.entries(data.vehicle_breakdown)) {
                    html += `${type}: ${count}<br>`;
                }
            }
            html += `</div>`;
            
            document.getElementById('uploadResult').innerHTML = html;
            updateStats(data);
        }
        
        async function updateStats(data) {
            if (data.statistics) {
                document.getElementById('totalDetections').textContent = data.statistics.total_detections || 0;
                document.getElementById('todayDetections').textContent = data.statistics.today_detections || 0;
                document.getElementById('avgConfidence').innerHTML = `${Math.round((data.statistics.average_confidence || 0) * 100)}%`;
            }
            
            if (data.recent_detections) {
                let html = '';
                data.recent_detections.forEach(d => {
                    html += `<div class="detection-item">
                        <strong>${d.type.toUpperCase()}</strong><br>
                        ${new Date(d.time).toLocaleTimeString()} | ${(d.confidence * 100).toFixed(1)}%
                    </div>`;
                });
                document.getElementById('recentDetections').innerHTML = html || '<p>No recent detections</p>';
            }
        }
        
        async function loadStats() {
            const response = await fetch('/stats');
            const data = await response.json();
            updateStats({ statistics: data, recent_detections: data.recent_detections });
        }
        
        function setMode(mode) {
            currentMode = mode;
            
            if (mode === 'webcam') {
                document.getElementById('webcamMode').style.display = 'block';
                document.getElementById('uploadMode').style.display = 'none';
                if (mediaStream) startFrameCapture();
            } else {
                document.getElementById('webcamMode').style.display = 'none';
                document.getElementById('uploadMode').style.display = 'block';
                if (detectionInterval) clearInterval(detectionInterval);
            }
            
            document.querySelectorAll('.mode-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
        }
        
        // Initialize
        connectWebSocket();
        loadStats();
        setInterval(loadStats, 5000);
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def realtime_dashboard():
    return HTMLResponse(content=REALTIME_HTML)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.post("/detect")
async def detect_image(file: UploadFile = File(...)):
    """Detect vehicles in uploaded image"""
    image_bytes = await file.read()
    image = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
    
    detections = detector.detect_frame(image)
    annotated_frame = detector.draw_detections(image.copy(), detections)
    
    vehicle_breakdown = Counter([d['type'] for d in detections])
    
    return {
        "success": True,
        "total_vehicles": len(detections),
        "detections": detections,
        "vehicle_breakdown": dict(vehicle_breakdown),
        "statistics": detector.get_statistics(),
        "timestamp": datetime.now().isoformat()
    }

@app.post("/detect-frame")
async def detect_frame(file: UploadFile = File(...)):
    """Detect vehicles in video frame"""
    image_bytes = await file.read()
    image = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
    
    detections = detector.detect_frame(image)
    
    return {
        "total_vehicles": len(detections),
        "detections": detections,
        "statistics": detector.get_statistics(),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/stats")
async def get_stats():
    return detector.get_statistics()

@app.post("/start-webcam")
async def start_webcam():
    """Start webcam processing in background thread"""
    if not hasattr(detector, 'webcam_thread') or not detector.webcam_thread.is_alive():
        detector.webcam_thread = threading.Thread(target=detector.process_webcam, args=(0,))
        detector.webcam_thread.daemon = True
        detector.webcam_thread.start()
        return {"status": "started", "message": "Webcam processing started"}
    return {"status": "already_running", "message": "Webcam already running"}

@app.post("/stop-webcam")
async def stop_webcam():
    """Stop webcam processing"""
    detector.running = False
    return {"status": "stopped", "message": "Webcam processing stopped"}

if __name__ == "__main__":
    import uvicorn
    import numpy as np
    from collections import Counter
    
    print("\n" + "="*60)
    print("🚗 REAL-TIME VEHICLE DETECTION SYSTEM")
    print("="*60)
    print("📍 Web Interface: http://localhost:8000")
    print("🎥 Features:")
    print("   - Live webcam feed")
    print("   - Real-time detection")
    print("   - Image upload")
    print("   - Live statistics")
    print("="*60)
    print("\n✅ Server is running!\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
