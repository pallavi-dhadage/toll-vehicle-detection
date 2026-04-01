import os
os.environ['TORCH_WEIGHTS_ONLY'] = '0'

import cv2
import numpy as np
from ultralytics import YOLO

class VehicleDetector:
    def __init__(self, model_path="models/yolov8n.pt", imgsz=416):
        self.model = YOLO(model_path)
        # Set the inference image size (default is 640)
        self.model.overrides['imgsz'] = imgsz
        self.class_names = {
            2: "car",
            3: "motorcycle",
            5: "bus",
            7: "truck",
            1: "bicycle",
        }

    def detect(self, image_bytes):
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        results = self.model(img)
        detections = []
        for r in results[0].boxes:
            cls = int(r.cls[0])
            conf = float(r.conf[0])
            if conf > 0.5 and cls in self.class_names:
                detections.append({
                    "type": self.class_names[cls],
                    "confidence": conf,
                    "bbox": r.xyxy[0].tolist()
                })
        return detections

detector = VehicleDetector()
