#!/usr/bin/env python3
"""
Test script for YOLOv8 vehicle detection
Demonstrates detection capabilities for toll plaza vehicles
"""

import cv2
import numpy as np
from ultralytics import YOLO
import os

def test_yolo_detection():
    """Test YOLO detection on sample images"""

    # Load model
    model_path = "yolov8m.pt"
    if not os.path.exists(model_path):
        print(f"Model {model_path} not found!")
        return

    model = YOLO(model_path)
    print("YOLOv8 model loaded successfully")

    # Vehicle type mapping for toll plaza
    VEHICLE_MAPPING = {
        1: "bicycle",    # bicycle
        2: "car",        # car
        3: "rickshaw",   # motorcycle -> rickshaw
        5: "truck",      # bus -> truck
        7: "truck",      # truck
    }

    # Create a sample test image (simple colored rectangles as vehicles)
    def create_test_image():
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        img[:] = [200, 200, 200]  # Light gray background

        # Draw some "vehicles" as colored rectangles
        # Car (red rectangle)
        cv2.rectangle(img, (100, 200), (250, 300), (0, 0, 255), -1)
        # Truck (blue rectangle)
        cv2.rectangle(img, (350, 180), (550, 320), (255, 0, 0), -1)
        # Bicycle (green rectangle)
        cv2.rectangle(img, (50, 350), (120, 420), (0, 255, 0), -1)

        return img

    # Test with synthetic image
    test_img = create_test_image()

    print("Testing detection on synthetic image...")
    results = model(test_img, conf=0.3)

    print(f"Detection Results:")
    print(f"Number of detections: {len(results[0].boxes) if results[0].boxes is not None else 0}")

    if results[0].boxes is not None:
        for i, box in enumerate(results[0].boxes):
            class_id = int(box.cls[0])
            confidence = float(box.conf[0])
            coco_class = model.names[class_id]

            # Map to toll plaza vehicle types
            vehicle_type = VEHICLE_MAPPING.get(class_id, "unknown")

            if vehicle_type != "unknown":
                print(f"  Detection {i+1}: {coco_class} -> {vehicle_type} (confidence: {confidence:.3f})")

    print("\nNote: This test uses a synthetic image with colored rectangles.")
    print("For real vehicle detection, upload actual vehicle images to the API.")

def test_api_detection():
    """Test the detection API"""
    import requests

    try:
        # Create a simple test image
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        img[:] = [255, 255, 255]  # White image

        # Save temporarily
        cv2.imwrite('test_image.jpg', img)

        # Test API
        url = "http://localhost:8000/detect/"
        with open('test_image.jpg', 'rb') as f:
            files = {'file': f}
            response = requests.post(url, files=files)

        if response.status_code == 200:
            result = response.json()
            print("API Test Results:")
            print(f"Detections found: {len(result['detections'])}")
            for det in result['detections']:
                print(f"  - {det['type']} (confidence: {det['confidence']})")
        else:
            print(f"API test failed: {response.status_code}")

        # Cleanup
        os.remove('test_image.jpg')

    except Exception as e:
        print(f"API test failed: {e}")

if __name__ == "__main__":
    print("Toll Plaza Vehicle Detection - YOLOv8 Test")
    print("=" * 50)

    test_yolo_detection()
    print("\n" + "=" * 50)
    test_api_detection()