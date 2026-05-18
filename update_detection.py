# Add this to your detection.py to use trained model

import os
from ultralytics import YOLO

class HighConfidenceDetectionService:
    """Updated detection service with trained model"""
    
    def __init__(self, model_path='runs/detect/train/weights/best.pt'):
        self.conf_threshold = 0.92  # 92% minimum confidence
        
        # Try to load trained model
        if os.path.exists(model_path):
            self.model = YOLO(model_path)
            print(f"✅ Loaded trained model from {model_path}")
            print(f"🎯 Confidence threshold: {self.conf_threshold*100}%")
        else:
            # Fallback to pretrained
            self.model = YOLO('yolov8m.pt')
            print("⚠️ Trained model not found, using pretrained model")
            print("🎯 Run training first: python train_vehicle_model.py")
        
        self.vehicle_classes = {
            0: 'car', 1: 'truck', 2: 'bus', 
            3: 'motorcycle', 4: 'auto-rickshaw', 5: 'bicycle'
        }
    
    def detect(self, image_bytes):
        """Detect vehicles with 92%+ confidence"""
        from PIL import Image
        import io
        import cv2
        import numpy as np
        
        # Convert bytes to PIL Image
        image = Image.open(io.BytesIO(image_bytes))
        
        # Run inference with high confidence threshold
        results = self.model(image, conf=self.conf_threshold, verbose=False)
        
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
                            'bbox': bbox
                        })
        
        # Draw annotations
        image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        for det in detections:
            bbox = det['bbox']
            x1, y1, x2, y2 = map(int, bbox[:4])
            confidence = det['confidence']
            
            # Color based on confidence
            if confidence >= 0.95:
                color = (0, 255, 0)  # Green for 95%+
            else:
                color = (0, 255, 255)  # Yellow for 92-95%
            
            cv2.rectangle(image_cv, (x1, y1), (x2, y2), color, 2)
            label = f"{det['type']}: {confidence:.1%}"
            cv2.putText(image_cv, label, (x1, y1-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        return detections, image_cv
