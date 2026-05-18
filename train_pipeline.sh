#!/bin/bash

echo "==================================="
echo "Vehicle Detection Training Pipeline"
echo "==================================="

# Step 1: Prepare dataset
echo "📁 Step 1: Preparing dataset..."
python3 prepare_vehicle_dataset.py

# Step 2: Augment data (if you have images)
echo "🔄 Step 2: Augmenting dataset..."
if [ -d "vehicle_dataset/train/images" ] && [ "$(ls -A vehicle_dataset/train/images)" ]; then
    python3 augment_dataset.py
else
    echo "⚠️ No images found. Please add images to vehicle_dataset/train/images/"
    echo "   Then run this script again."
    exit 1
fi

# Step 3: Train model
echo "🎯 Step 3: Training YOLOv8 model..."
python3 train_vehicle_model.py

# Step 4: Test model
echo "🧪 Step 4: Testing trained model..."
python3 high_confidence_detection.py

echo ""
echo "✅ Training complete!"
echo "📊 Model saved to: runs/detect/train/weights/best.pt"
echo "🎯 Now you can use high-confidence detection (92%+)"
