"""
Working Vehicle Detection - Reliable detection for all images
"""

from ultralytics import YOLO
from PIL import Image, ImageDraw, ImageFont
import io
import os
import sqlite3
from datetime import datetime
from collections import Counter
import cv2
import numpy as np

class VehicleDetector:
    def __init__(self, model_path='yolov8x.pt', conf_threshold=0.5):  # 50% threshold
        self.conf_threshold = conf_threshold
        self.model = self.load_model(model_path)
        self.vehicle_classes = {
            1: 'bicycle', 2: 'car', 3: 'motorcycle', 
            5: 'bus', 7: 'truck'
        }
        self.init_database()
        print(f"🎯 Confidence threshold: {self.conf_threshold*100}% (Will detect all vehicles)")
    
    def load_model(self, model_path):
        if os.path.exists(model_path):
            print(f"✅ Loading model...")
            return YOLO(model_path)
        else:
            print(f"📥 Downloading YOLOv8x model...")
            return YOLO('yolov8x.pt')
    
    def init_database(self):
        self.conn = sqlite3.connect('vehicle_detections.db', check_same_thread=False)
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS detections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                vehicle_type TEXT,
                confidence REAL,
                hour INTEGER,
                day_of_week INTEGER,
                date DATE
            )
        ''')
        self.conn.commit()
        print("✅ Database ready")
    
    def enhance_image(self, image):
        """Enhance image for better detection"""
        # Convert to OpenCV format
        img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Enhance contrast and brightness
        img_cv = cv2.convertScaleAbs(img_cv, alpha=1.2, beta=30)
        
        # Convert back to PIL
        enhanced = Image.fromarray(cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB))
        return enhanced
    
    def detect(self, image_bytes):
        """Detect vehicles with reliable threshold"""
        # Load and enhance image
        original_image = Image.open(io.BytesIO(image_bytes))
        enhanced_image = self.enhance_image(original_image)
        
        # Run detection with low threshold to catch everything
        results = self.model(enhanced_image, conf=self.conf_threshold, iou=0.45, verbose=False)
        
        detections = []
        vehicle_breakdown = Counter()
        
        print(f"\n{'='*50}")
        print(f"🔍 Detection Results:")
        print(f"{'='*50}")
        
        for result in results:
            if result.boxes:
                for box in result.boxes:
                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    
                    if class_id in self.vehicle_classes:
                        vehicle_type = self.vehicle_classes[class_id]
                        bbox = box.xyxy[0].tolist()
                        
                        print(f"✅ {vehicle_type.upper()}: {confidence:.1%} confidence")
                        
                        detections.append({
                            'type': vehicle_type,
                            'confidence': confidence,
                            'bbox': bbox
                        })
                        vehicle_breakdown[vehicle_type] += 1
                        
                        # Log all detections to database
                        self.log_detection(vehicle_type, confidence)
        
        # Draw bounding boxes on image
        annotated_image = self.draw_boxes(original_image, detections)
        
        # Save annotated image
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        annotated_path = f"detected_{timestamp}.jpg"
        annotated_image.save(annotated_path)
        
        print(f"\n📊 Total vehicles detected: {len(detections)}")
        print(f"📈 Breakdown: {dict(vehicle_breakdown)}")
        print(f"{'='*50}\n")
        
        return {
            'success': True,
            'total_vehicles': len(detections),
            'detections': detections,
            'vehicle_breakdown': dict(vehicle_breakdown),
            'annotated_image': annotated_path,
            'timestamp': datetime.now().isoformat(),
            'threshold': self.conf_threshold
        }
    
    def draw_boxes(self, image, detections):
        """Draw bounding boxes on image"""
        draw = ImageDraw.Draw(image)
        
        colors = {
            'car': '#00FF00',
            'truck': '#FF0000',
            'bus': '#0000FF',
            'motorcycle': '#FFA500',
            'bicycle': '#800080'
        }
        
        for det in detections:
            bbox = det['bbox']
            x1, y1, x2, y2 = map(int, bbox[:4])
            color = colors.get(det['type'], '#00FF00')
            
            # Draw rectangle
            draw.rectangle([x1, y1, x2, y2], outline=color, width=3)
            
            # Draw label
            label = f"{det['type']}: {det['confidence']:.0%}"
            draw.rectangle([x1, y1-20, x1+100, y1], fill=color)
            draw.text((x1+5, y1-18), label, fill='white')
        
        return image
    
    def log_detection(self, vehicle_type, confidence):
        """Log detection to database"""
        now = datetime.now()
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO detections 
            (timestamp, vehicle_type, confidence, hour, day_of_week, date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (now, vehicle_type, confidence, now.hour, now.weekday(), now.date()))
        self.conn.commit()
    
    def get_statistics(self):
        """Get detection statistics"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM detections")
        total = cursor.fetchone()[0] or 0
        cursor.execute(f"SELECT COUNT(*) FROM detections WHERE date = '{datetime.now().date()}'")
        today = cursor.fetchone()[0] or 0
        cursor.execute("SELECT AVG(confidence) FROM detections")
        avg_conf = cursor.fetchone()[0] or 0
        cursor.execute("SELECT COUNT(DISTINCT vehicle_type) FROM detections")
        unique_types = cursor.fetchone()[0] or 0
        cursor.execute("SELECT COUNT(DISTINCT date) FROM detections")
        active_days = cursor.fetchone()[0] or 0
        
        return {
            'total_detections': total,
            'today_detections': today,
            'average_confidence': float(avg_conf),
            'unique_vehicle_types': unique_types,
            'active_days': active_days
        }
    
    def get_recent_logs(self, limit=20):
        """Get recent detection logs"""
        cursor = self.conn.cursor()
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
        return logs

# Create detector instance
detector = VehicleDetector(conf_threshold=0.5)  # 50% threshold for reliable detection
