from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import cv2
import numpy as np
from app.core.algorithm import detect_pipe
from app.utils.img_util import save_image, read_image

router = APIRouter()

@router.post("/recognize")
async def recognize_pipe(
        file: UploadFile = File(...),
        conf: float = Form(0.3),
):
    try:
        # 读取上传的图片
        contents = await file.read()
        img = read_image(contents)

        if img is None:
            raise HTTPException(status_code=400, detail="图片读取失败")

        # 把 conf 传给检测算法
        count, marks, avg_radius = detect_pipe(img, conf=conf)

        # 保存图片
        image_url = save_image(img)

        return {
            "code": 200,
            "msg": "识别成功",
            "data": {
                "count": count,
                "marks": marks,
                "avg_radius": avg_radius,  # 返回平均半径
                "image_url": image_url
            }
        }
    except Exception as e:
        print(f"识别错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"识别失败: {str(e)}")

@router.post("/crop")
async def crop_image(
        file: UploadFile = File(...),
        x: float = Form(...),
        y: float = Form(...),
        width: float = Form(...),
        height: float = Form(...)
):
    try:
        # 读取图片
        contents = await file.read()
        img = read_image(contents)

        if img is None:
            raise HTTPException(status_code=400, detail="图片读取失败")

        # 转换为整数坐标
        x = int(x)
        y = int(y)
        width = int(width)
        height = int(height)

        # 检查裁剪区域是否有效
        h, w = img.shape[:2]
        if x < 0 or y < 0 or width <= 0 or height <= 0:
            raise HTTPException(status_code=400, detail="无效的裁剪区域")

        # 计算裁剪区域（防止越界）
        x1 = max(0, int(x - width / 2))
        y1 = max(0, int(y - height / 2))
        x2 = min(w, int(x + width / 2))
        y2 = min(h, int(y + height / 2))

        # 裁剪图片
        cropped_img = img[y1:y2, x1:x2]

        # 保存裁剪后的图片
        image_url = save_image(cropped_img)

        return {
            "code": 200,
            "msg": "裁剪成功",
            "data": {
                "image_url": image_url
            }
        }
    except Exception as e:
        print(f"裁剪错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"裁剪失败: {str(e)}")