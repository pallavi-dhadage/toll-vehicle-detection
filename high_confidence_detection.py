"""
High Confidence Vehicle Detection (92%+)
Uses trained model with confidence threshold
"""

from ultralytics import YOLO
import cv2
import numpy as np
from pathlib import Path

class HighConfidenceDetector:
    def __init__(self, model_path='runs/detect/train/weights/best.pt', conf_threshold=0.92):
        """
        Initialize detector with high confidence threshold
        
        Args:
            model_path: Path to trained model
            conf_threshold: Minimum confidence (default 0.92 = 92%)
        """
        self.model = YOLO(model_path)
        self.conf_threshold = conf_threshold
        self.vehicle_classes = {
            0: 'car', 1: 'truck', 2: 'bus', 
            3: 'motorcycle', 4: 'auto-rickshaw', 5: 'bicycle'
        }
        
    def detect(self, image_path):
        """Detect vehicles with high confidence"""
        
        # Run inference
        results = self.model(image_path, conf=self.conf_threshold, verbose=False)
        
        detections = []
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    
                    if confidence >= self.conf_threshold:
                        bbox = box.xyxy[0].tolist()
                        detections.append({
                            'type': self.vehicle_classes.get(class_id, 'vehicle'),
                            'confidence': confidence,
                            'bbox': bbox,
                            'class_id': class_id
                        })
        
        return detections
    
    def draw_detections(self, image_path, detections):
        """Draw bounding boxes on image"""
        image = cv2.imread(image_path)
        
        for det in detections:
            x1, y1, x2, y2 = map(int, det['bbox'])
            confidence = det['confidence']
            vehicle_type = det['type']
            
            # Color based on confidence
            if confidence >= 0.95:
                color = (0, 255, 0)  # Green - Very High
            elif confidence >= 0.92:
                color = (0, 255, 255)  # Yellow - High
            
            # Draw rectangle
            cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
            
            # Draw label
            label = f"{vehicle_type}: {confidence:.1%}"
            cv2.putText(image, label, (x1, y1-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        return image

# Integration with FastAPI
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse
import io
from PIL import Image

app = FastAPI()

# Initialize detector
detector = HighConfidenceDetector(conf_threshold=0.92)

@app.post("/detect-high-conf/")
async def detect_high_confidence(file: UploadFile = File(...)):
    """Detect vehicles with 92%+ confidence"""
    
    # Save uploaded image temporarily
    image_bytes = await file.read()
    temp_path = "temp_image.jpg"
    with open(temp_path, "wb") as f:
        f.write(image_bytes)
    
    # Run detection
    detections = detector.detect(temp_path)
    
    # Draw results
    annotated_image = detector.draw_detections(temp_path, detections)
    output_path = "detection_result.jpg"
    cv2.imwrite(output_path, annotated_image)
    
    return {
        "success": True,
        "total_vehicles": len(detections),
        "detections": detections,
        "min_confidence": 0.92,
        "all_above_threshold": all(d['confidence'] >= 0.92 for d in detections)
    }

if __name__ == "__main__":
    print("🚗 High Confidence Vehicle Detector (92%+)")
    print("Testing on sample image...")
    
    # Test on your test_image.jpg
    if Path("test_image.jpg").exists():
        detections = detector.detect("test_image.jpg")
        print(f"✅ Found {len(detections)} vehicles with 92%+ confidence")
        for det in detections:
            print(f"   {det['type']}: {det['confidence']:.1%}")
    else:
        print("⚠️ No test image found")
