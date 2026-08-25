import cv2
from ultralytics import YOLO

model = YOLO("best.pt")


def detect_by_yolo(img, conf=0.3):
    """
    YOLO全自动钢管检测，返回计数结果和标记信息
    """
    # 推理，置信度0.5，可根据效果调整
    results = model(img, verbose=False, conf=conf, max_det=2000)
    marks = []

    for r in results:
        for box in r.boxes:
            x1, y1, x2, y2 = box.xyxy[0]
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2
            r = min((x2 - x1) // 2, (y2 - y1) // 2)

            marks.append({
                "x": cx,
                "y": cy,
                "radius": r
            })

    return len(marks), marks