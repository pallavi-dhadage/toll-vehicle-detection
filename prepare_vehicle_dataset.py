import os
import yaml
import random
from pathlib import Path

# Create dataset directories
dataset_dir = "vehicle_dataset"
os.makedirs(f"{dataset_dir}/train/images", exist_ok=True)
os.makedirs(f"{dataset_dir}/train/labels", exist_ok=True)
os.makedirs(f"{dataset_dir}/val/images", exist_ok=True)
os.makedirs(f"{dataset_dir}/val/labels", exist_ok=True)

# Vehicle classes mapping
classes = {
    0: 'car',
    1: 'truck', 
    2: 'bus',
    3: 'motorcycle',
    4: 'auto-rickshaw',
    5: 'bicycle'
}

# Create data.yaml for YOLO
data_yaml = {
    'path': f'/home/{os.getenv("USER")}/toll-vehicle-detection/vehicle_dataset',
    'train': 'train/images',
    'val': 'val/images',
    'nc': len(classes),
    'names': list(classes.values())
}

with open('vehicle_dataset/data.yaml', 'w') as f:
    yaml.dump(data_yaml, f, default_flow_style=False)

print("✅ Dataset structure created!")
print(f"📁 Dataset location: {dataset_dir}/")
print("📝 Classes:", list(classes.values()))

# Instructions for adding images
print("\n📌 NEXT STEPS:")
print("1. Add your vehicle images to 'vehicle_dataset/train/images/'")
print("2. Add corresponding label files to 'vehicle_dataset/train/labels/'")
print("3. Run training: python train_vehicle_model.py")
