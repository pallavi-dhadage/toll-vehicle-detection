from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO
import cv2
import numpy as np
from PIL import Image
import io
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load model
print("=" * 50)
print("Loading YOLOv8x model...")
if os.path.exists("yolov8x.pt"):
    model = YOLO("yolov8x.pt")
    print("✅ Loaded YOLOv8x model (best accuracy)")
else:
    print("📥 Downloading YOLOv8x model...")
    model = YOLO("yolov8x.pt")
    print("✅ Model downloaded")

vehicle_classes = {1: "bicycle", 2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}
print(f"🎯 Confidence threshold: 92%")
print("=" * 50)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Vehicle Detection 92%+</title>
    <style>
        body { font-family: Arial; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); margin: 0; padding: 20px; }
        .container { max-width: 800px; margin: 0 auto; }
        .card { background: white; border-radius: 15px; padding: 25px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
        h1 { color: #333; }
        .upload-area { border: 2px dashed #667eea; border-radius: 10px; padding: 40px; text-align: center; cursor: pointer; background: #f8f9fa; }
        .button { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; padding: 12px 30px; border-radius: 25px; cursor: pointer; width: 100%; margin-top: 20px; }
        .result { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #28a745; }
        img { max-width: 100%; border-radius: 10px; margin-top: 20px; }
        .stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-bottom: 20px; }
        .stat-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px; border-radius: 10px; text-align: center; }
        .stat-number { font-size: 2em; font-weight: bold; }
        .loading { display: none; text-align: center; margin-top: 20px; }
        .spinner { border: 3px solid #f3f3f3; border-top: 3px solid #667eea; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 0 auto; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h1>🚗 Vehicle Detection System (92%+ Confidence)</h1>
                <p>📸 Click to upload vehicle image</p>
                <input type="file" id="fileInput" accept="image/*" onchange="previewImage()">
            </div>
            <div id="preview"></div>
            <button class="button" onclick="detect()">🔍 Detect Vehicles (92%+ Confidence)</button>
            <div class="loading" id="loading"><div class="spinner"></div><p>Processing...</p></div>
            <div id="results"></div>
        </div>
    </div>
    <script>
        let currentFile = null;
        function previewImage() {
            const file = document.getElementById("fileInput").files[0];
            if (file) { currentFile = file; const reader = new FileReader();
            reader.onload = e => document.getElementById("preview").innerHTML = `<img src="${e.target.result}">`;
            reader.readAsDataURL(file); } }
        async function detect() {
            if (!currentFile) { alert("Select an image first"); return; }
            const formData = new FormData(); formData.append("file", currentFile);
            document.getElementById("loading").style.display = "block";
            try {
                const response = await fetch("/detect/", { method: "POST", body: formData });
                const data = await response.json();
                let html = `<div class="stats"><div class="stat-card"><div class="stat-number">${data.total_vehicles}</div><div>Vehicles</div></div>
                <div class="stat-card"><div class="stat-number">${(data.confidence_stats?.average * 100 || 0).toFixed(0)}%</div><div>Avg Confidence</div></div>
                <div class="stat-card"><div class="stat-number">92%</div><div>Min Threshold</div></div></div>`;
                if (data.detections && data.detections.length > 0) {
                    html += "<h3>✅ Detected Vehicles:</h3>";
                    data.detections.forEach(d => { html += `<div class="result"><strong>${d.type.toUpperCase()}</strong><br>Confidence: ${(d.confidence * 100).toFixed(1)}%</div>`; });
                } else { html += "<p>⚠️ No vehicles detected with 92%+ confidence</p>"; }
                document.getElementById("results").innerHTML = html;
            } catch(e) { document.getElementById("results").innerHTML = `<p>Error: ${e.message}</p>`; }
            finally { document.getElementById("loading").style.display = "none"; } }
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def home():
    return HTMLResponse(content=HTML_TEMPLATE)

@app.post("/detect/")
async def detect_vehicle(file: UploadFile = File(...)):
    image_bytes = await file.read()
    image = Image.open(io.BytesIO(image_bytes))
    results = model(image, conf=0.92, verbose=False)
    detections = []
    for result in results:
        if result.boxes:
            for box in result.boxes:
                class_id = int(box.cls[0])
                if class_id in vehicle_classes:
                    detections.append({
                        "type": vehicle_classes[class_id],
                        "confidence": float(box.conf[0]),
                        "bbox": box.xyxy[0].tolist()
                    })
    return {"success": True, "total_vehicles": len(detections), "detections": detections, "confidence_stats": {"average": sum(d["confidence"] for d in detections)/len(detections) if detections else 0, "threshold": 0.92}}

@app.get("/health")
async def health():
    return {"status": "healthy", "model": "YOLOv8x", "threshold": "92%"}

if __name__ == "__main__":
    import uvicorn
    print("\\n" + "="*50)
    print("🚗 VEHICLE DETECTION SYSTEM")
    print("="*50)
    print("📍 Web Interface: http://localhost:8000")
    print("🎯 Confidence Threshold: 92%")
    print("="*50 + "\\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
