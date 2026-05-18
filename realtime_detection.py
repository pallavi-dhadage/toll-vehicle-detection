"""
Real-Time Vehicle Detection with Webcam and Live Stream Support
"""

from ultralytics import YOLO
from PIL import Image
import io
import os
import sqlite3
from datetime import datetime
from collections import Counter
import cv2
import numpy as np
import base64
from fastapi import WebSocket, WebSocketDisconnect
import asyncio
import threading

class RealTimeDetector:
    def __init__(self, model_path='yolov8x.pt', conf_threshold=0.5):
        self.conf_threshold = conf_threshold
        self.model = self.load_model(model_path)
        self.vehicle_classes = {
            1: 'bicycle', 2: 'car', 3: 'motorcycle', 
            5: 'bus', 7: 'truck'
        }
        self.colors = {
            'car': (0, 255, 0),      # Green
            'truck': (0, 0, 255),    # Red
            'bus': (255, 0, 0),      # Blue
            'motorcycle': (0, 255, 255),  # Yellow
            'bicycle': (255, 0, 255)      # Purple
        }
        self.init_database()
        self.active_connections = []
        self.current_frame = None
        self.running = False
        print(f"🎯 Real-time detection ready! Threshold: {self.conf_threshold*100}%")
    
    def load_model(self, model_path):
        if os.path.exists(model_path):
            print(f"✅ Loading YOLOv8x model...")
            return YOLO(model_path)
        else:
            print(f"📥 Downloading model...")
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
    
    def log_detection(self, vehicle_type, confidence):
        now = datetime.now()
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO detections 
            (timestamp, vehicle_type, confidence, hour, day_of_week, date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (now, vehicle_type, confidence, now.hour, now.weekday(), now.date()))
        self.conn.commit()
    
    def detect_frame(self, frame):
        """Detect vehicles in a single frame"""
        results = self.model(frame, conf=self.conf_threshold, verbose=False)
        
        detections = []
        for result in results:
            if result.boxes:
                for box in result.boxes:
                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    
                    if class_id in self.vehicle_classes:
                        vehicle_type = self.vehicle_classes[class_id]
                        bbox = box.xyxy[0].tolist()
                        
                        detections.append({
                            'type': vehicle_type,
                            'confidence': confidence,
                            'bbox': bbox
                        })
                        
                        # Log every 10 detections to avoid spam
                        if len(detections) % 10 == 0:
                            self.log_detection(vehicle_type, confidence)
        
        return detections
    
    def draw_detections(self, frame, detections):
        """Draw bounding boxes on frame"""
        for det in detections:
            bbox = det['bbox']
            x1, y1, x2, y2 = map(int, bbox[:4])
            vehicle_type = det['type']
            confidence = det['confidence']
            
            color = self.colors.get(vehicle_type, (0, 255, 0))
            
            # Draw rectangle
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            
            # Draw label background
            label = f"{vehicle_type}: {confidence:.0%}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            cv2.rectangle(frame, (x1, y1-25), (x1+label_size[0], y1), color, -1)
            
            # Draw label text
            cv2.putText(frame, label, (x1, y1-5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        
        return frame
    
    def process_webcam(self, source=0):
        """Process webcam stream"""
        cap = cv2.VideoCapture(source)
        self.running = True
        
        while self.running:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Detect vehicles
            detections = self.detect_frame(frame)
            
            # Draw detections
            annotated_frame = self.draw_detections(frame, detections)
            
            # Store current frame for WebSocket
            _, buffer = cv2.imencode('.jpg', annotated_frame)
            self.current_frame = base64.b64encode(buffer).decode('utf-8')
            
            # Notify all WebSocket connections
            asyncio.run(self.broadcast_frame())
            
            # Add FPS counter
            cv2.putText(annotated_frame, f"Vehicles: {len(detections)}", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            cv2.imshow('Vehicle Detection - Press Q to quit', annotated_frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()
        self.running = False
    
    async def broadcast_frame(self):
        """Send frame to all connected WebSocket clients"""
        if self.active_connections and self.current_frame:
            for connection in self.active_connections:
                try:
                    await connection.send_json({
                        'frame': self.current_frame,
                        'timestamp': datetime.now().isoformat()
                    })
                except:
                    pass
    
    def get_statistics(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM detections")
        total = cursor.fetchone()[0] or 0
        cursor.execute(f"SELECT COUNT(*) FROM detections WHERE date = '{datetime.now().date()}'")
        today = cursor.fetchone()[0] or 0
        cursor.execute("SELECT AVG(confidence) FROM detections")
        avg_conf = cursor.fetchone()[0] or 0
        
        # Get recent detections per minute
        cursor.execute('''
            SELECT datetime(timestamp, 'localtime') as time, vehicle_type, confidence
            FROM detections
            WHERE timestamp >= datetime('now', '-5 minutes')
            ORDER BY timestamp DESC
        ''')
        recent = cursor.fetchall()
        
        return {
            'total_detections': total,
            'today_detections': today,
            'average_confidence': float(avg_conf),
            'recent_detections': [{'time': r[0], 'type': r[1], 'confidence': r[2]} for r in recent]
        }

# Initialize detector
detector = RealTimeDetector(conf_threshold=0.5)
