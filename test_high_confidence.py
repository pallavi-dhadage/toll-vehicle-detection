"""
Test vehicle detection with 92%+ confidence
Uses pre-trained YOLOv8 models
"""

from ultralytics import YOLO
import cv2
import numpy as np
from PIL import Image
import os

class HighConfidenceDetector:
    def __init__(self, model_name='yolov8x.pt', conf_threshold=0.92):
        """
        Initialize high confidence detector
        
        Args:
            model_name: 'yolov8n.pt' (nano), 'yolov8s.pt' (small), 
                       'yolov8m.pt' (medium), 'yolov8l.pt' (large),
                       'yolov8x.pt' (extra large - best)
            conf_threshold: 0.92 = 92% minimum confidence
        """
        print(f"📦 Loading model: {model_name}")
        self.model = YOLO(model_name)
        self.conf_threshold = conf_threshold
        print(f"✅ Model loaded! Confidence threshold: {conf_threshold*100}%")
        
        # Vehicle classes in COCO dataset
        self.vehicle_classes = {
            1: 'bicycle', 2: 'car', 3: 'motorcycle', 
            5: 'bus', 7: 'truck'
        }
    
    def detect_vehicles(self, image_path):
        """Detect vehicles with high confidence"""
        print(f"\n🔍 Analyzing: {image_path}")
        
        # Run inference with high confidence threshold
        results = self.model(image_path, conf=self.conf_threshold, verbose=False)
        
        detections = []
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    
                    # Only include vehicle classes
                    if class_id in self.vehicle_classes:
                        bbox = box.xyxy[0].tolist()
                        detections.append({
                            'type': self.vehicle_classes[class_id],
                            'confidence': confidence,
                            'bbox': bbox,
                            'class_id': class_id
                        })
        
        return detections
    
    def draw_results(self, image_path, detections, output_path='detection_result.jpg'):
        """Draw detection results on image"""
        image = cv2.imread(image_path)
        
        for det in detections:
            x1, y1, x2, y2 = map(int, det['bbox'])
            confidence = det['confidence']
            vehicle_type = det['type']
            
            # Color coding by confidence
            if confidence >= 0.95:
                color = (0, 255, 0)  # Green - Excellent
                label_color = (0, 255, 0)
            elif confidence >= 0.92:
                color = (0, 255, 255)  # Yellow - High
                label_color = (0, 255, 255)
            else:
                color = (0, 165, 255)  # Orange - Good
                label_color = (0, 165, 255)
            
            # Draw bounding box
            cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
            
            # Draw label with confidence
            label = f"{vehicle_type}: {confidence:.1%}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            cv2.rectangle(image, (x1, y1-25), (x1+label_size[0], y1), color, -1)
            cv2.putText(image, label, (x1, y1-5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        
        # Save result
        cv2.imwrite(output_path, image)
        print(f"📸 Results saved to: {output_path}")
        return image
    
    def print_summary(self, detections):
        """Print detection summary"""
        if not detections:
            print(f"\n⚠️ No vehicles detected with {self.conf_threshold*100}%+ confidence")
            print("💡 Tips to improve detection:")
            print("   - Use better quality images")
            print("   - Ensure good lighting")
            print("   - Vehicles should be clearly visible")
            return
        
        print(f"\n✅ Detected {len(detections)} vehicles with {self.conf_threshold*100}%+ confidence:")
        
        # Count by type
        vehicle_counts = {}
        for det in detections:
            vtype = det['type']
            vehicle_counts[vtype] = vehicle_counts.get(vtype, 0) + 1
        
        for vtype, count in vehicle_counts.items():
            print(f"   • {vtype}: {count}")
        
        # Show confidence stats
        confidences = [d['confidence'] for d in detections]
        print(f"\n📊 Confidence Statistics:")
        print(f"   Average: {np.mean(confidences):.1%}")
        print(f"   Highest: {np.max(confidences):.1%}")
        print(f"   Lowest: {np.min(confidences):.1%}")

# Test on your image
if __name__ == "__main__":
    print("="*60)
    print("🚗 HIGH CONFIDENCE VEHICLE DETECTION (92%+)")
    print("="*60)
    
    # Check if model exists
    if not os.path.exists('yolov8x.pt'):
        print("\n📥 Downloading YOLOv8x model...")
        model = YOLO('yolov8x.pt')
    
    # Initialize detector
    detector = HighConfidenceDetector('yolov8x.pt', conf_threshold=0.92)
    
    # Find test images
    test_images = []
    for img in ['test_image.jpg', 'test_image.png', 'image.png', 'test.jpg', 'sample.jpg']:
        if os.path.exists(img):
            test_images.append(img)
    
    if test_images:
        for img_path in test_images:
            print("\n" + "="*50)
            # Detect vehicles
            detections = detector.detect_vehicles(img_path)
            
            # Print summary
            detector.print_summary(detections)
            
            # Draw and save results
            if detections:
                output_name = f'high_conf_{os.path.basename(img_path)}'
                detector.draw_results(img_path, detections, output_name)
    else:
        print("\n⚠️ No test images found!")
        print("Please add an image file (test_image.jpg, image.png, etc.)")
        print("\nYou can also test using the web interface:")
        print("1. Run: python app.py")
        print("2. Open http://localhost:8000")
        print("3. Upload an image")
