#!/usr/bin/env python3
"""
Dataset Preparation Script for Toll Plaza Vehicle Detection
Creates training dataset with vehicles from multiple angles
"""

import os
import cv2
import numpy as np
from pathlib import Path
import requests
from PIL import Image
import random

def create_synthetic_vehicle_dataset():
    """Create synthetic dataset with vehicles from multiple angles"""

    dataset_path = Path("../datasets/toll_vehicles")
    classes = ["bicycle", "car", "truck", "rickshaw"]

    # Create class mapping
    class_mapping = {name: idx for idx, name in enumerate(classes)}

    print("Creating synthetic vehicle dataset...")

    # Generate training images
    for split in ['train', 'val', 'test']:
        img_dir = dataset_path / f"images/{split}"
        label_dir = dataset_path / f"labels/{split}"

        # Number of images per split
        num_images = 500 if split == 'train' else 100

        for i in range(num_images):
            # Create base image
            img = create_vehicle_image()
            img_path = img_dir / f"{i:04d}.jpg"

            # Save image
            cv2.imwrite(str(img_path), img)

            # Create corresponding label file
            label_path = label_dir / f"{i:04d}.txt"
            create_vehicle_labels(img, label_path, class_mapping)

    print(f"Dataset created with {len(classes)} classes: {classes}")

def create_vehicle_image():
    """Create synthetic image with vehicles"""
    # Create road-like background
    height, width = 640, 640
    img = np.zeros((height, width, 3), dtype=np.uint8)

    # Road background (gray asphalt)
    img[:, :] = [100, 100, 100]

    # Add lane markings
    cv2.line(img, (width//2 - 5, 0), (width//2 - 5, height), (255, 255, 255), 10)
    cv2.line(img, (width//2 + 5, 0), (width//2 + 5, height), (255, 255, 255), 10)

    # Add some random vehicles
    num_vehicles = random.randint(1, 4)

    for _ in range(num_vehicles):
        vehicle_type = random.choice(['car', 'truck', 'bicycle', 'rickshaw'])
        angle = random.choice([0, 15, 30, 45, -15, -30, -45])  # Multi-angle

        x = random.randint(50, width - 150)
        y = random.randint(100, height - 150)

        draw_vehicle(img, vehicle_type, x, y, angle)

    return img

def draw_vehicle(img, vehicle_type, x, y, angle):
    """Draw a vehicle on the image"""

    if vehicle_type == 'car':
        # Draw car (red rectangle)
        points = np.array([[x, y], [x+80, y], [x+80, y+40], [x, y+40]], np.int32)
        cv2.fillPoly(img, [points], (0, 0, 255))
        # Add windows
        cv2.rectangle(img, (x+10, y+5), (x+35, y+20), (200, 200, 200), -1)
        cv2.rectangle(img, (x+45, y+5), (x+70, y+20), (200, 200, 200), -1)

    elif vehicle_type == 'truck':
        # Draw truck (blue rectangle, larger)
        points = np.array([[x, y], [x+120, y], [x+120, y+60], [x, y+60]], np.int32)
        cv2.fillPoly(img, [points], (255, 0, 0))
        # Add cargo area
        cv2.rectangle(img, (x+10, y+5), (x+110, y+25), (150, 150, 150), -1)

    elif vehicle_type == 'bicycle':
        # Draw bicycle (green)
        cv2.circle(img, (x+15, y+15), 12, (0, 255, 0), 2)  # Front wheel
        cv2.circle(img, (x+35, y+15), 12, (0, 255, 0), 2)  # Back wheel
        cv2.line(img, (x+15, y+15), (x+25, y+5), (0, 255, 0), 2)  # Frame
        cv2.line(img, (x+25, y+5), (x+35, y+15), (0, 255, 0), 2)  # Frame
        cv2.line(img, (x+25, y+5), (x+25, y-5), (0, 255, 0), 2)  # Seat post

    elif vehicle_type == 'rickshaw':
        # Draw rickshaw (yellow, three-wheeled)
        cv2.circle(img, (x+10, y+20), 8, (0, 255, 255), 2)  # Front wheel
        cv2.circle(img, (x+20, y+20), 8, (0, 255, 255), 2)  # Middle wheel
        cv2.circle(img, (x+40, y+20), 8, (0, 255, 255), 2)  # Back wheel
        cv2.rectangle(img, (x+15, y), (x+35, y+15), (0, 255, 255), -1)  # Body

def create_vehicle_labels(img, label_path, class_mapping):
    """Create YOLO format labels for the image"""
    height, width = img.shape[0], img.shape[1]

    labels = []

    # Simple object detection - find colored regions
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # Detect red cars
    lower_red = np.array([0, 50, 50])
    upper_red = np.array([10, 255, 255])
    mask_red = cv2.inRange(hsv, lower_red, upper_red)
    contours_red, _ = cv2.findContours(mask_red, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for contour in contours_red:
        if cv2.contourArea(contour) > 500:  # Minimum area
            x, y, w, h = cv2.boundingRect(contour)
            # Convert to YOLO format (normalized)
            x_center = (x + w/2) / width
            y_center = (y + h/2) / height
            w_norm = w / width
            h_norm = h / height
            labels.append(f"{class_mapping['car']} {x_center:.6f} {y_center:.6f} {w_norm:.6f} {h_norm:.6f}")

    # Detect blue trucks
    lower_blue = np.array([90, 50, 50])
    upper_blue = np.array([130, 255, 255])
    mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)
    contours_blue, _ = cv2.findContours(mask_blue, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for contour in contours_blue:
        if cv2.contourArea(contour) > 1000:  # Larger area for trucks
            x, y, w, h = cv2.boundingRect(contour)
            x_center = (x + w/2) / width
            y_center = (y + h/2) / height
            w_norm = w / width
            h_norm = h / height
            labels.append(f"{class_mapping['truck']} {x_center:.6f} {y_center:.6f} {w_norm:.6f} {h_norm:.6f}")

    # Detect green bicycles
    lower_green = np.array([40, 50, 50])
    upper_green = np.array([80, 255, 255])
    mask_green = cv2.inRange(hsv, lower_green, upper_green)
    contours_green, _ = cv2.findContours(mask_green, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for contour in contours_green:
        if cv2.contourArea(contour) > 200:
            x, y, w, h = cv2.boundingRect(contour)
            x_center = (x + w/2) / width
            y_center = (y + h/2) / height
            w_norm = w / width
            h_norm = h / height
            labels.append(f"{class_mapping['bicycle']} {x_center:.6f} {y_center:.6f} {w_norm:.6f} {h_norm:.6f}")

    # Detect yellow rickshaws
    lower_yellow = np.array([20, 50, 50])
    upper_yellow = np.array([40, 255, 255])
    mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)
    contours_yellow, _ = cv2.findContours(mask_yellow, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for contour in contours_yellow:
        if cv2.contourArea(contour) > 300:
            x, y, w, h = cv2.boundingRect(contour)
            x_center = (x + w/2) / width
            y_center = (y + h/2) / height
            w_norm = w / width
            h_norm = h / height
            labels.append(f"{class_mapping['rickshaw']} {x_center:.6f} {y_center:.6f} {w_norm:.6f} {h_norm:.6f}")

    # Write labels to file
    with open(label_path, 'w') as f:
        for label in labels:
            f.write(label + '\n')

def download_vehicle_dataset():
    """Download a real vehicle detection dataset"""
    print("Downloading vehicle detection dataset...")

    # For now, let's use a subset of COCO or create synthetic data
    # In a real scenario, you'd download datasets like:
    # - UA-DETRAC
    # - KITTI
    # - Cityscapes vehicles

    print("Using synthetic dataset for demonstration")
    print("For production, use real datasets like UA-DETRAC or KITTI")

if __name__ == "__main__":
    print("Toll Plaza Vehicle Detection - Dataset Preparation")
    print("=" * 60)

    # Create synthetic dataset
    create_synthetic_vehicle_dataset()

    print("\nDataset preparation complete!")
    print("Next: Run 'python train_yolo.py train' to train the model")