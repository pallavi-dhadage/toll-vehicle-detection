"""
Final Vehicle Detection - Optimized Threshold
"""

from ultralytics import YOLO
from PIL import Image
import io
import os
import sqlite3
from datetime import datetime
from collections import Counter
import pandas as pd
import numpy as np

class VehicleDetector:
    def __init__(self, model_path='yolov8x.pt', conf_threshold=0.75):  # Changed to 75%
        self.conf_threshold = conf_threshold
        self.model = self.load_model(model_path)
        self.vehicle_classes = {1: 'bicycle', 2: 'car', 3: 'motorcycle', 5: 'bus', 7: 'truck'}
        self.init_database()
        print(f"🎯 Confidence threshold: {self.conf_threshold*100}%")
    
    def load_model(self, model_path):
        if os.path.exists(model_path):
            print(f"✅ Loading model from {model_path}")
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
                date DATE,
                week INTEGER,
                month INTEGER,
                year INTEGER
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_summary (
                date DATE PRIMARY KEY,
                total_vehicles INTEGER,
                car_count INTEGER,
                truck_count INTEGER,
                bus_count INTEGER,
                motorcycle_count INTEGER,
                bicycle_count INTEGER,
                avg_confidence REAL
            )
        ''')
        self.conn.commit()
        print("✅ Database initialized")
    
    def log_detection(self, vehicle_type, confidence):
        now = datetime.now()
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO detections 
            (timestamp, vehicle_type, confidence, hour, day_of_week, date, week, month, year)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (now, vehicle_type, confidence, now.hour, now.weekday(), 
              now.date(), now.isocalendar()[1], now.month, now.year))
        self.conn.commit()
        self.update_daily_summary(now.date())
        print(f"📝 LOGGED: {vehicle_type} with {confidence:.1%} confidence")
    
    def update_daily_summary(self, date):
        query = '''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN vehicle_type = 'car' THEN 1 ELSE 0 END) as cars,
                SUM(CASE WHEN vehicle_type = 'truck' THEN 1 ELSE 0 END) as trucks,
                SUM(CASE WHEN vehicle_type = 'bus' THEN 1 ELSE 0 END) as buses,
                SUM(CASE WHEN vehicle_type = 'motorcycle' THEN 1 ELSE 0 END) as motorcycles,
                SUM(CASE WHEN vehicle_type = 'bicycle' THEN 1 ELSE 0 END) as bicycles,
                AVG(confidence) as avg_conf
            FROM detections
            WHERE date = ?
        '''
        df = pd.read_sql_query(query, self.conn, params=[date])
        
        if not df.empty and not pd.isna(df['total'].iloc[0]):
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO daily_summary 
                (date, total_vehicles, car_count, truck_count, bus_count, 
                 motorcycle_count, bicycle_count, avg_confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (date, int(df['total'].iloc[0]), int(df['cars'].iloc[0]), 
                  int(df['trucks'].iloc[0]), int(df['buses'].iloc[0]), 
                  int(df['motorcycles'].iloc[0]), int(df['bicycles'].iloc[0]), 
                  float(df['avg_conf'].iloc[0]) if not pd.isna(df['avg_conf'].iloc[0]) else 0))
            self.conn.commit()
    
    def detect(self, image_bytes):
        image = Image.open(io.BytesIO(image_bytes))
        results = self.model(image, conf=self.conf_threshold, verbose=False)
        
        detections = []
        vehicle_breakdown = Counter()
        
        print(f"\n{'='*50}")
        print(f"🔍 Detection Results (Threshold: {self.conf_threshold*100}%):")
        print(f"{'='*50}")
        
        for result in results:
            if result.boxes:
                for box in result.boxes:
                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    
                    if class_id in self.vehicle_classes:
                        vehicle_type = self.vehicle_classes[class_id]
                        
                        print(f"✅ {vehicle_type.upper()}: {confidence:.1%} confidence")
                        detections.append({
                            'type': vehicle_type,
                            'confidence': confidence,
                            'bbox': box.xyxy[0].tolist()
                        })
                        vehicle_breakdown[vehicle_type] += 1
                        self.log_detection(vehicle_type, confidence)
        
        if len(detections) == 0:
            print(f"❌ No vehicles detected above {self.conf_threshold*100}% threshold")
        
        print(f"Total: {len(detections)} vehicles detected")
        print(f"{'='*50}\n")
        
        return {
            'success': True,
            'total_vehicles': len(detections),
            'detections': detections,
            'vehicle_breakdown': dict(vehicle_breakdown),
            'timestamp': datetime.now().isoformat(),
            'threshold': self.conf_threshold
        }
    
    def get_statistics(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM detections")
        total = cursor.fetchone()[0] or 0
        cursor.execute(f"SELECT COUNT(*) FROM detections WHERE date = '{datetime.now().date()}'")
        today = cursor.fetchone()[0] or 0
        cursor.execute("SELECT AVG(confidence) FROM detections")
        avg_conf = cursor.fetchone()[0]
        avg_conf = avg_conf if avg_conf is not None and not pd.isna(avg_conf) else 0
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
                'confidence': row[2] if not pd.isna(row[2]) else 0
            })
        return logs
    
    def get_analytics_data(self):
        try:
            hourly = pd.read_sql_query('''
                SELECT hour, vehicle_type, COUNT(*) as count
                FROM detections
                WHERE date >= date('now', '-7 days')
                GROUP BY hour, vehicle_type
                ORDER BY hour
            ''', self.conn)
            
            daily = pd.read_sql_query('''
                SELECT date, vehicle_type, COUNT(*) as count
                FROM detections
                WHERE date >= date('now', '-30 days')
                GROUP BY date, vehicle_type
                ORDER BY date
            ''', self.conn)
            
            distribution = pd.read_sql_query('''
                SELECT vehicle_type, COUNT(*) as count
                FROM detections
                GROUP BY vehicle_type
                ORDER BY count DESC
            ''', self.conn)
            
            peak_hours = pd.read_sql_query('''
                SELECT hour, COUNT(*) as count
                FROM detections
                GROUP BY hour
                ORDER BY count DESC
                LIMIT 5
            ''', self.conn)
            
            heatmap = pd.read_sql_query('''
                SELECT hour, day_of_week, COUNT(*) as count
                FROM detections
                WHERE date >= date('now', '-30 days')
                GROUP BY hour, day_of_week
                ORDER BY day_of_week, hour
            ''', self.conn)
            
            stats = self.get_statistics()
            
            today = datetime.now().date()
            today_stats = pd.read_sql_query(f'''
                SELECT COUNT(*) as count, AVG(confidence) as avg_conf
                FROM detections
                WHERE date = '{today}'
            ''', self.conn)
            
            return {
                'hourly': [{'hour': int(r['hour']), 'vehicle_type': r['vehicle_type'], 'count': int(r['count'])} 
                          for r in hourly.to_dict('records')] if not hourly.empty else [],
                'daily': [{'date': r['date'], 'vehicle_type': r['vehicle_type'], 'count': int(r['count'])} 
                         for r in daily.to_dict('records')] if not daily.empty else [],
                'distribution': [{'vehicle_type': r['vehicle_type'], 'count': int(r['count'])} 
                                for r in distribution.to_dict('records')] if not distribution.empty else [],
                'peak_hours': [{'hour': int(r['hour']), 'count': int(r['count'])} 
                              for r in peak_hours.to_dict('records')] if not peak_hours.empty else [],
                'stats': stats,
                'today_stats': {'count': int(today_stats['count'].iloc[0]), 'avg_conf': float(today_stats['avg_conf'].iloc[0])} 
                             if not today_stats.empty and not pd.isna(today_stats['count'].iloc[0]) else {'count': 0, 'avg_conf': 0},
                'heatmap': [{'hour': int(r['hour']), 'day_of_week': int(r['day_of_week']), 'count': int(r['count'])} 
                           for r in heatmap.to_dict('records')] if not heatmap.empty else []
            }
        except Exception as e:
            return {'hourly': [], 'daily': [], 'distribution': [], 'peak_hours': [], 
                    'stats': self.get_statistics(), 'today_stats': {'count': 0, 'avg_conf': 0}, 'heatmap': []}
    
    def export_csv(self):
        df = pd.read_sql_query("SELECT * FROM detections ORDER BY timestamp DESC", self.conn)
        csv_path = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(csv_path, index=False)
        return csv_path
    
    def get_insights(self):
        data = self.get_analytics_data()
        insights = []
        
        if data['peak_hours'] and len(data['peak_hours']) > 0:
            peak = data['peak_hours'][0]
            insights.append(f"Peak traffic at {peak['hour']}:00 with {peak['count']} vehicles")
        
        if data['distribution'] and len(data['distribution']) > 0:
            top = data['distribution'][0]
            insights.append(f"Most common: {top['vehicle_type'].upper()} ({top['count']} detections)")
        
        if data['today_stats']['count'] > 0:
            insights.append(f"Today: {data['today_stats']['count']} vehicles, {data['today_stats']['avg_conf']*100:.1f}% avg confidence")
        
        if data['stats'].get('total_detections', 0) > 0:
            insights.append(f"Total: {data['stats']['total_detections']} detections over {data['stats']['active_days']} days")
        
        if not insights:
            insights.append("Upload vehicle images to generate insights!")
        
        return insights

detector = VehicleDetector()
