import uuid
import cv2
import numpy as np
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SAVE_DIR = os.path.join(BASE_DIR, "static")

if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

def read_image(file_bytes):
    img_np = np.frombuffer(file_bytes, np.uint8)
    img = cv2.imdecode(img_np, cv2.IMREAD_COLOR)
    return img

def save_image(img):
    filename = f"{uuid.uuid4()}.png"
    save_path = os.path.join(SAVE_DIR, filename)
    cv2.imwrite(save_path, img)
    return f"/static/{filename}"