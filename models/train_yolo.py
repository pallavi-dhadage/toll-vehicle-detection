#!/usr/bin/env python3
"""
YOLOv8 Training Script for Toll Plaza Vehicle Detection
Trains a custom model to detect bicycle, car, truck, rickshaw from multiple angles
"""

import os
import torch
from ultralytics import YOLO

def create_sample_dataset():
    """Create a sample dataset structure for demonstration"""
    import shutil
    from pathlib import Path

    # Create dataset directories
    base_dir = Path("../datasets/toll_vehicles")
    for split in ['train', 'val', 'test']:
        (base_dir / f"images/{split}").mkdir(parents=True, exist_ok=True)
        (base_dir / f"labels/{split}").mkdir(parents=True, exist_ok=True)

    print("Dataset structure created. Add your images and labels to:")
    print(f"- Images: {base_dir}/images/")
    print(f"- Labels: {base_dir}/labels/")
    print("\nLabel format: class_id x_center y_center width height (normalized 0-1)")

def train_vehicle_detector():
    """Train YOLOv8 model for vehicle detection"""

    # Check if CUDA is available
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"Using device: {device}")

    # Load pre-trained model
    model = YOLO('yolov8m.pt')

    # Training parameters optimized for vehicle detection
    training_args = {
        'data': 'data.yaml',
        'epochs': 100,  # Increased for better training
        'batch': 16,    # Larger batch size if GPU allows
        'imgsz': 640,
        'device': device,
        'workers': 4,
        'patience': 20,  # More patience for early stopping
        'save': True,
        'save_period': 10,
        'cache': True,  # Enable cache for faster training
        'pretrained': True,

        # Optimization for multi-angle detection
        'cos_lr': True,  # Cosine learning rate
        'momentum': 0.937,
        'weight_decay': 0.0005,

        # Data augmentation for cross-section views
        'mosaic': 1.0,  # Increased mosaic
        'mixup': 0.2,   # Increased mixup
        'copy_paste': 0.1,

        # Vehicle-specific augmentations
        'degrees': 45,   # More rotation
        'translate': 0.3,
        'scale': 0.5,
        'shear': 10,
        'perspective': 0.0002,
        'flipud': 0.0,   # No vertical flip for vehicles
        'fliplr': 0.5,   # Horizontal flip
        'hsv_h': 0.015,
        'hsv_s': 0.4,
        'hsv_v': 0.3,

        # Project settings
        'project': 'runs/train',
        'name': 'toll_vehicle_detector',
    }

    # Start training
    print("Starting YOLOv8 training for toll plaza vehicle detection...")
    print("This may take several minutes...")
    results = model.train(**training_args)

    # Save the best model
    best_model_path = 'toll_vehicle_detector.pt'
    model.save(best_model_path)
    print(f"Training completed! Model saved as: {best_model_path}")

    return model

def validate_model(model_path='toll_vehicle_detector.pt'):
    """Validate the trained model"""
    if not os.path.exists(model_path):
        print(f"Model {model_path} not found. Using base model for validation.")
        model_path = 'yolov8m.pt'

    model = YOLO(model_path)

    # Run validation
    results = model.val(data='data.yaml', split='val')

    print("Validation Results:")
    print(f"mAP50: {results.box.map50:.3f}")
    print(f"mAP50-95: {results.box.map:.3f}")

    return results

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == 'create_dataset':
            create_sample_dataset()
        elif command == 'train':
            train_vehicle_detector()
        elif command == 'validate':
            validate_model()
        else:
            print("Usage: python train_yolo.py [create_dataset|train|validate]")
    else:
        print("Toll Plaza Vehicle Detection Training Script")
        print("Commands:")
        print("  create_dataset - Create dataset directory structure")
        print("  train         - Train YOLOv8 model")
        print("  validate      - Validate trained model")
        print("\nExample: python train_yolo.py train")