import cv2
import numpy as np
from app.core.yolo_pipe import detect_by_yolo  # 导入YOLO检测


def calculate_average_radius(marks):
    """计算平均半径，用于自适应标记大小"""
    if not marks:
        return 20
    radii = [m["radius"] for m in marks]
    return int(np.mean(radii))


def detect_pipe(img, conf=0.3):
    count, marks = detect_by_yolo(img, conf=conf)
    avg_r = calculate_average_radius(marks)

    # 统一格式，兼容前端
    result_marks = []
    for m in marks:
        result_marks.append({
            "x": m["x"],
            "y": m["y"],
            "radius": m["radius"] if m["radius"] > 0 else avg_r
        })

    return count, result_marks, avg_r