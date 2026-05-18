"""
Debug script to check what the model is detecting
"""

from ultralytics import YOLO
from PIL import Image
import os

# Load model
model = YOLO('yolov8x.pt')

# Vehicle classes
vehicle_classes = {
    1: 'bicycle', 2: 'car', 3: 'motorcycle', 
    5: 'bus', 7: 'truck'
}

# Find images in current directory
images = [f for f in os.listdir('.') if f.endswith(('.jpg', '.jpeg', '.png')) and 'export' not in f]

if not images:
    print("No images found. Please upload an image first.")
else:
    for img_path in images[:3]:  # Check first 3 images
        print(f"\n{'='*50}")
        print(f"Analyzing: {img_path}")
        print(f"{'='*50}")
        
        # Run detection with low threshold to see all detections
        results = model(img_path, conf=0.3, verbose=False)
        
        found_vehicles = False
        for result in results:
            if result.boxes:
                for box in result.boxes:
                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    
                    if class_id in vehicle_classes:
                        vehicle_type = vehicle_classes[class_id]
                        found_vehicles = True
                        
                        # Show confidence level
                        status = "✅ WILL BE LOGGED" if confidence >= 0.92 else "⚠️ BELOW 92% THRESHOLD"
                        print(f"{status}: {vehicle_type.upper()} - {confidence:.1%} confidence")
                    else:
                        print(f"Other object (class {class_id}): {confidence:.1%}")
        
        if not found_vehicles:
            print("❌ No vehicles detected in this image")
            print("   Tips:")
            print("   - Try images with clearer, larger vehicles")
            print("   - Ensure good lighting")
            print("   - Vehicles should be clearly visible")

print("\n" + "="*50)
print("To fix low confidence issues:")
print("1. Use higher quality images")
print("2. Ensure vehicles are clearly visible")
print("3. Try images with vehicles from front/side views")
print("="*50)
