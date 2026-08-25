from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import json
from app.utils.img_util import save_image, read_image

router = APIRouter(prefix="/manual")


@router.post("/save")
async def save_manual_marks(
        file: UploadFile = File(...),
        marks: str = Form(...),
        count: int = Form(...)
):
    try:
        # 读取图片
        contents = await file.read()
        img = read_image(contents)

        if img is None:
            raise HTTPException(status_code=400, detail="图片读取失败")

        # 解析标记数据
        try:
            marks_data = json.loads(marks)
        except:
            raise HTTPException(status_code=400, detail="标记数据格式错误")

        # 保存图片
        image_url = save_image(img)

        return {
            "code": 200,
            "msg": "标记保存成功",
            "data": {
                "count": count,
                "marks": marks_data,
                "image_url": image_url
            }
        }
    except Exception as e:
        print(f"保存手动标记错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"保存失败: {str(e)}")