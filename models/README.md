# Toll Plaza Vehicle Detection - YOLOv8 Training Guide

## Overview
This project uses YOLOv8 for real-time vehicle detection in toll plazas. The system can detect:
- **Bicycle** - Two-wheeled pedal vehicles
- **Car** - Four-wheeled passenger vehicles
- **Truck** - Large commercial vehicles
- **Rickshaw** - Three-wheeled auto-rickshaws/motorcycle taxis

## Current Setup
- **Model**: YOLOv8m (pre-trained on COCO dataset)
- **Detection Classes**: Mapped from COCO to toll plaza vehicles
- **Confidence Threshold**: 0.5 (high confidence for accuracy)
- **Multi-angle Support**: Handles vehicles from various perspectives

## Training a Custom Model

### 1. Prepare Dataset
Create a dataset with images of vehicles from multiple angles:

```
datasets/toll_vehicles/
├── images/
│   ├── train/     # Training images
│   ├── val/       # Validation images
│   └── test/      # Test images
└── labels/
    ├── train/     # YOLO format labels (.txt)
    ├── val/       # YOLO format labels (.txt)
    └── test/      # YOLO format labels (.txt)
```

### 2. Label Format
Each label file corresponds to an image with the same name:
```
class_id x_center y_center width height
```
- `class_id`: 0=bicycle, 1=car, 2=truck, 3=rickshaw
- Coordinates are normalized (0-1)

### 3. Train the Model
```bash
cd models
python train_yolo.py train
```

### 4. Training Parameters
- **Epochs**: 100
- **Batch Size**: 16
- **Image Size**: 640x640
- **Augmentations**: Rotation, flip, scale for multi-angle detection
- **Early Stopping**: Patience 20 epochs

## Multi-Angle Detection Features
The model is trained with augmentations to handle:
- **Front/Rear views** of vehicles
- **Side profiles** at different angles
- **Partial occlusions** common in toll plazas
- **Various lighting conditions**

## Testing the Model
```bash
# Test with sample image
curl -X POST "http://localhost:8000/detect/" -F "file=@vehicle_image.jpg"

# Expected response:
{
  "detections": [
    {
      "type": "car",
      "confidence": 0.892,
      "bbox": [150, 200, 400, 350]
    }
  ]
}
```

## Performance Optimization
- **GPU Acceleration**: Uses CUDA if available
- **Batch Processing**: Handles multiple images efficiently
- **Confidence Filtering**: Only returns high-confidence detections
- **Fallback Detection**: Uses mock data if YOLO fails

## Future Improvements
1. **Custom Dataset**: Collect toll plaza specific images
2. **Rickshaw Detection**: Train specifically for auto-rickshaws
3. **License Plate OCR**: Add number plate recognition
4. **Speed Estimation**: Calculate vehicle speed
5. **Vehicle Counting**: Track vehicle flow statistics