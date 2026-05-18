"""
Vehicle Detection Model Training Script
Train YOLOv8 for high-confidence vehicle detection (92%+)
"""

from ultralytics import YOLO
import torch
import os
from datetime import datetime

def train_vehicle_model():
    """Train YOLOv8 model on vehicle dataset"""
    
    print("="*60)
    print("🚗 VEHICLE DETECTION MODEL TRAINING")
    print("="*60)
    
    # Check if dataset exists
    if not os.path.exists("vehicle_dataset/data.yaml"):
        print("❌ Dataset not found! Run prepare_vehicle_dataset.py first")
        return
    
    # Load pre-trained model
    print("\n📦 Loading YOLOv8 model...")
    model = YOLO('yolov8m.pt')  # Using medium model for balance of speed/accuracy
    
    # Training parameters for high confidence
    results = model.train(
        data='vehicle_dataset/data.yaml',
        epochs=100,              # More epochs for better learning
        imgsz=640,               # Image size
        batch=16,                # Batch size (reduce if memory issues)
        patience=20,             # Early stopping patience
        save=True,               # Save checkpoints
        save_period=10,          # Save every 10 epochs
        device=0 if torch.cuda.is_available() else 'cpu',  # Use GPU if available
        workers=8,               # Number of workers
        pretrained=True,         # Use pretrained weights
        optimizer='AdamW',       # Better optimizer
        lr0=0.001,               # Initial learning rate
        lrf=0.01,                # Final learning rate factor
        momentum=0.937,          # SGD momentum
        weight_decay=0.0005,     # Weight decay
        warmup_epochs=3,         # Warmup epochs
        warmup_momentum=0.8,     # Warmup momentum
        warmup_bias_lr=0.1,      # Warmup bias lr
        box=7.5,                 # Box loss gain
        cls=0.5,                 # Class loss gain
        dfl=1.5,                 # DFL loss gain
        hsv_h=0.015,             # HSV-Hue augmentation
        hsv_s=0.7,               # HSV-Saturation augmentation
        hsv_v=0.4,               # HSV-Value augmentation
        degrees=0.0,             # Rotation augmentation
        translate=0.1,           # Translation augmentation
        scale=0.5,               # Scaling augmentation
        shear=0.0,               # Shear augmentation
        perspective=0.0,         # Perspective augmentation
        flipud=0.0,              # Flip up-down
        fliplr=0.5,              # Flip left-right
        mosaic=1.0,              # Mosaic augmentation
        mixup=0.0,               # Mixup augmentation
        copy_paste=0.0,          # Copy-paste augmentation
    )
    
    print("\n✅ Training completed!")
    print(f"📁 Model saved to: runs/detect/train/weights/best.pt")
    
    # Export model for inference
    print("\n📤 Exporting model...")
    model.export(format='onnx')  # Export to ONNX for faster inference
    print("✅ Model exported to ONNX format")
    
    # Test the model on a sample
    print("\n🧪 Testing model...")
    test_model = YOLO('runs/detect/train/weights/best.pt')
    
    # Run validation
    val_results = test_model.val(data='vehicle_dataset/data.yaml')
    print(f"\n📊 Validation Results:")
    print(f"   mAP50: {val_results.box.map50:.2%}")
    print(f"   mAP50-95: {val_results.box.map:.2%}")
    
    return results

def download_pretrained_weights():
    """Download COCO pretrained weights if not exists"""
    if not os.path.exists('yolov8m.pt'):
        print("📥 Downloading YOLOv8 pretrained weights...")
        from ultralytics import YOLO
        model = YOLO('yolov8m.pt')  # This will download automatically
        print("✅ Download complete!")

if __name__ == "__main__":
    print("🚀 Starting Vehicle Detection Model Training")
    print("⚠️  Make sure you have labeled data in 'vehicle_dataset/'")
    print()
    
    # Download pretrained weights
    download_pretrained_weights()
    
    # Start training
    train_vehicle_model()
