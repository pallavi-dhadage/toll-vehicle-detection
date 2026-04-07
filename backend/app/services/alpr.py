import os
os.environ['PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK'] = 'True'
os.environ['PADDLEOCR_LOG_LEVEL'] = 'ERROR'

import cv2
import numpy as np
from paddleocr import PaddleOCR
import re

ocr = PaddleOCR(use_angle_cls=True, lang='en')

def extract_plate_from_image(image_bytes, bbox):
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    x1, y1, x2, y2 = map(int, bbox)
    margin = 15
    y1 = max(0, y1 - margin)
    y2 = min(img.shape[0], y2 + margin)
    x1 = max(0, x1 - margin)
    x2 = min(img.shape[1], x2 + margin)
    crop = img[y1:y2, x1:x2]
    if crop.size == 0:
        return None
    result = ocr.ocr(crop, cls=True)
    if not result or not result[0]:
        return None
    texts = [line[1][0] for line in result[0]]
    plates = [t for t in texts if re.match(r'^[A-Z0-9]{6,10}$', t.upper())]
    if plates:
        return plates[0].upper()
    for t in texts:
        cleaned = re.sub(r'[^A-Z0-9]', '', t.upper())
        if 6 <= len(cleaned) <= 10:
            return cleaned
    return None
