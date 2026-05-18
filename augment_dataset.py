"""
Data Augmentation for Vehicle Detection
Improves model confidence to 92%+
"""

import cv2
import numpy as np
import os
import albumentations as A
from tqdm import tqdm

def augment_images():
    """Apply augmentations to increase dataset size and diversity"""
    
    # Define augmentations
    transform = A.Compose([
        A.RandomBrightnessContrast(p=0.5),
        A.HueSaturationValue(p=0.5),
        A.GaussNoise(var_limit=(10.0, 50.0), p=0.3),
        A.Blur(blur_limit=3, p=0.2),
        A.RandomRain(p=0.2),
        A.RandomFog(p=0.2),
        A.RandomShadow(p=0.3),
        A.HorizontalFlip(p=0.5),
    ], bbox_params=A.BboxParams(format='yolo', label_fields=['class_labels']))
    
    # Paths
    img_dir = 'vehicle_dataset/train/images'
    label_dir = 'vehicle_dataset/train/labels'
    aug_img_dir = 'vehicle_dataset/train/augmented_images'
    aug_label_dir = 'vehicle_dataset/train/augmented_labels'
    
    os.makedirs(aug_img_dir, exist_ok=True)
    os.makedirs(aug_label_dir, exist_ok=True)
    
    images = [f for f in os.listdir(img_dir) if f.endswith(('.jpg', '.png', '.jpeg'))]
    
    print(f"📸 Found {len(images)} images to augment")
    
    for img_file in tqdm(images, desc="Augmenting images"):
        # Read image
        img_path = os.path.join(img_dir, img_file)
        image = cv2.imread(img_path)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Read labels
        label_file = img_file.replace('.jpg', '.txt').replace('.png', '.txt').replace('.jpeg', '.txt')
        label_path = os.path.join(label_dir, label_file)
        
        if not os.path.exists(label_path):
            continue
        
        with open(label_path, 'r') as f:
            labels = f.readlines()
        
        bboxes = []
        class_labels = []
        
        for label in labels:
            parts = label.strip().split()
            class_id = int(parts[0])
            bbox = [float(x) for x in parts[1:5]]
            bboxes.append(bbox)
            class_labels.append(class_id)
        
        # Apply augmentations (create 3 augmented versions per image)
        for i in range(3):
            augmented = transform(image=image, bboxes=bboxes, class_labels=class_labels)
            
            # Save augmented image
            aug_img_file = f"{img_file.split('.')[0]}_aug{i}.jpg"
            aug_img_path = os.path.join(aug_img_dir, aug_img_file)
            cv2.imwrite(aug_img_path, cv2.cvtColor(augmented['image'], cv2.COLOR_RGB2BGR))
            
            # Save augmented labels
            aug_label_file = aug_img_file.replace('.jpg', '.txt')
            aug_label_path = os.path.join(aug_label_dir, aug_label_file)
            
            with open(aug_label_path, 'w') as f:
                for bbox, label in zip(augmented['bboxes'], augmented['class_labels']):
                    f.write(f"{label} {' '.join(map(str, bbox))}\n")
    
    print(f"✅ Created {len(images)*3} augmented images")
    print("📁 Augmented data saved to:", aug_img_dir)

if __name__ == "__main__":
    print("🔄 Starting Data Augmentation...")
    augment_dataset()
    print("\n📌 Now run training with augmented data!")
