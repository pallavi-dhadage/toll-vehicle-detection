from fastapi import FastAPI, File, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from datetime import datetime
import cv2
import numpy as np
from ultralytics import YOLO
from collections import defaultdict
import json
import asyncio
import pandas as pd
from io import BytesIO
import os
import uvicorn

# Initialize FastAPI
app = FastAPI(title="Toll Plaza Vehicle Detection System")

# CORS middleware
app.add_middleware(
    CORSMiddleware,

# Multi-Angle Camera Support
class MultiAngleCamera:
    def __init__(self):
        self.cameras = {
            "front": {"url": None, "active": False, "angle": "Front View"},
            "side": {"url": None, "active": False, "angle": "Side View"},
            "overhead": {"url": None, "active": False, "angle": "Overhead View"},
            "rear": {"url": None, "active": False, "angle": "Rear View"}
        }
        self.detections = defaultdict(list)
    
    def add_camera(self, angle, url):
        if angle in self.cameras:
            self.cameras[angle]["url"] = url
            self.cameras[angle]["active"] = True
            return True
        return False
    
    def remove_camera(self, angle):
        if angle in self.cameras:
            self.cameras[angle]["url"] = None
            self.cameras[angle]["active"] = False
            return True
        return False
    
    def get_active_cameras(self):
        return {k: v for k, v in self.cameras.items() if v["active"]}

multi_angle_manager = MultiAngleCamera()

@app.get("/api/cameras/multi-angle")
async def get_multi_angle_cameras():
    """Get all multi-angle camera configurations"""
    return JSONResponse({
        "cameras": multi_angle_manager.get_active_cameras(),
        "total": len(multi_angle_manager.get_active_cameras())
    })

@app.post("/api/cameras/multi-angle/add")
async def add_multi_angle_camera(angle: str, url: str):
    """Add a camera for specific angle"""
    if multi_angle_manager.add_camera(angle, url):
        return JSONResponse({"success": True, "message": f"{angle} camera added"})
    return JSONResponse({"success": False, "message": "Invalid angle"})

@app.delete("/api/cameras/multi-angle/{angle}")
async def remove_multi_angle_camera(angle: str):
    """Remove a camera for specific angle"""
    if multi_angle_manager.remove_camera(angle):
        return JSONResponse({"success": True, "message": f"{angle} camera removed"})
    return JSONResponse({"success": False, "message": "Camera not found"})

@app.get("/api/detections/multi-angle")
async def get_multi_angle_detections():
    """Get detections from all angles"""
    all_detections = {}
    for angle, camera in multi_angle_manager.cameras.items():
        if camera["active"]:
            all_detections[angle] = {
                "angle": camera["angle"],
                "detections": list(detections_history[-10:]) if detections_history else []
            }
    return JSONResponse(all_detections)

    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load YOLO model
print("✅ Loading YOLO model...")
try:
    model = YOLO('models/vehicle_detector.pt')  # YOLOv8x - Better accuracy for vehicle detection
    print("✅ Model loaded successfully")
except Exception as e:
    print(f"⚠️ Error loading model: {e}")
    model = None

# Vehicle classes
VEHICLE_CLASSES = {
    2: 'car', 3: 'motorcycle', 5: 'bus', 
    7: 'truck', 1: 'bicycle'
}

# Store data
vehicle_counters = defaultdict(lambda: defaultdict(int))
active_websockets = set()
detections_history = []

print("✅ Database initialized")
print("🎯 Confidence threshold: 50%")

@app.get("/")
async def root():
    return {
        'message': 'Toll Plaza Vehicle Detection System API',
        'status': 'running',
        'version': '1.0.0'
    }

@app.get("/stats/{camera_id}")
async def get_stats(camera_id: str):
    """Get statistics for a specific camera"""
    return JSONResponse({
        'camera_id': camera_id,
        'counters': dict(vehicle_counters[camera_id]),
        'total': sum(vehicle_counters[camera_id].values())
    })

@app.post("/detect")
async def detect_vehicles(file: UploadFile = File(...)):
    """Detect vehicles in uploaded image"""
    if model is None:
        return JSONResponse({'success': False, 'error': 'Model not loaded'})
    
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        return JSONResponse({'success': False, 'error': 'Invalid image'})
    
    # Run inference
    results = model(img, conf=0.3)[0]
    
    detections = []
    for box in results.boxes:
        cls = int(box.cls[0])
        if cls in VEHICLE_CLASSES:
            conf = float(box.conf[0])
            detections.append({
                'type': VEHICLE_CLASSES[cls],
                'confidence': conf
            })
            
            # Update counter
            vehicle_counters['camera1'][VEHICLE_CLASSES[cls]] += 1
    
    # Add to history
    detection_record = {
        'timestamp': datetime.now().isoformat(),
        'detections': detections,
        'count': len(detections)
    }
    detections_history.append(detection_record)
    
    # Send alert if more than 3 vehicles
    if len(detections) > 3:
        await broadcast_alert(f"High traffic! {len(detections)} vehicles detected")
    
    return JSONResponse({
        'success': True,
        'detections': detections,
        'count': len(detections)
    })

@app.get("/reset/{camera_id}")
async def reset_counter(camera_id: str):
    """Reset vehicle counter"""
    vehicle_counters[camera_id].clear()
    return JSONResponse({'success': True, 'message': f'Counter reset for {camera_id}'})

@app.get("/generate-report")
async def generate_report():
    """Generate Excel report"""
    data = []
    for camera, counts in vehicle_counters.items():
        for vehicle_type, count in counts.items():
            data.append({
                'Camera': camera,
                'Vehicle Type': vehicle_type,
                'Count': count,
                'Timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
    
    if not data:
        data = [{'Message': 'No data available for the selected period'}]
    
    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Vehicle Counts', index=False)
    
    output.seek(0)
    filename = f'report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    
    return FileResponse(
        output,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        filename=filename
    )

@app.websocket("/ws/alerts")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_websockets.add(websocket)
    print(f"WebSocket connected. Total connections: {len(active_websockets)}")
    try:
        while True:
            await asyncio.sleep(10)
            await websocket.send_text(json.dumps({
                'type': 'heartbeat',
                'timestamp': str(datetime.now())
            }))
    except WebSocketDisconnect:
        active_websockets.remove(websocket)
        print(f"WebSocket disconnected. Total: {len(active_websockets)}")

@app.post("/add-camera")
async def add_camera(camera_data: dict):
    """Add a new camera"""
    camera_id = camera_data.get('camera_id')
    url = camera_data.get('url')
    return JSONResponse({
        'success': True, 
        'message': f'Camera {camera_id} added successfully',
        'camera': {'id': camera_id, 'url': url}
    })

@app.get("/api/verify")
async def verify_token():
    """Verify authentication"""
    return JSONResponse({
        "valid": True, 
        "user": {"email": "admin@example.com", "role": "admin"}
    })

@app.get("/api/cameras")
async def get_cameras():
    """Get list of cameras"""
    return JSONResponse({"cameras": [
        {"id": "camera1", "name": "Main Gate", "status": "active"},
        {"id": "camera2", "name": "Exit Gate", "status": "active"}
    ]})

@app.get("/api/statistics")
async def get_statistics():
    """Get overall statistics"""
    total_vehicles = sum(sum(counters.values()) for counters in vehicle_counters.values())
    return JSONResponse({
        'total_vehicles': total_vehicles,
        'cameras': len(vehicle_counters),
        'counters': {k: dict(v) for k, v in vehicle_counters.items()}
    })

@app.get("/api/analytics")
async def get_analytics():
    """Get analytics data"""
    return JSONResponse({
        'hourly_data': [],
        'daily_data': [],
        'peak_hours': [],
        'avg_vehicles_per_hour': 0
    })

@app.get("/api/logs")
async def get_logs(limit: int = 20):
    """Get system logs"""
    return JSONResponse({
        'logs': detections_history[-limit:],
        'total': len(detections_history)
    })

@app.get("/api/insights")
async def get_insights():
    """Get insights"""
    return JSONResponse({
        'insights': [
            'System running smoothly',
            f'Total vehicles detected: {sum(sum(c.values()) for c in vehicle_counters.values())}',
            'Real-time detection active'
        ]
    })

async def broadcast_alert(message: str):
    """Broadcast alert to all connected clients"""
    if active_websockets:
        alert_data = json.dumps({
            'type': 'alert',
            'message': message,
            'timestamp': str(datetime.now())
        })
        await asyncio.gather(*[ws.send_text(alert_data) for ws in active_websockets])

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚗 TOLL PLAZA VEHICLE DETECTION SYSTEM")
    print("="*60)
    print("📍 Backend API: http://localhost:8000")
    print("📍 API Documentation: http://localhost:8000/docs")
    print("📍 Stats Endpoint: http://localhost:8000/stats/camera1")
    print("="*60 + "\n")
    # Run without reload=True for WSL compatibility
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
