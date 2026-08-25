from fastapi import APIRouter, Form, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime
from app.models.entity import PipeRecord
from app.utils.db_util import get_db

router = APIRouter()


@router.post("/save")
def save_pipe_result(
        image_url: str = Form(...),
        pipe_number: str = Form(None),
        recognize_count: int = Form(...),
        actual_count: int = Form(...),
        operator_id: int = Form(None),
        operator_name: str = Form(None),
        db: Session = Depends(get_db)
):
    try:
        print(f"[保存记录] 图片URL: {image_url}")
        print(f"[保存记录] 钢管编号: {pipe_number}")
        print(f"[保存记录] 识别数量: {recognize_count}")
        print(f"[保存记录] 入库数量: {actual_count}")
        print(f"[保存记录] 操作员ID: {operator_id}")
        print(f"[保存记录] 操作员名称: {operator_name}")

        # ===================== 核心修改：计算 F1 分数 =====================
        if actual_count == 0:
            accuracy = 0.0
        else:
            # 正确识别数量 = 识别数和真实数的较小值（无重叠场景）
            tp = min(recognize_count, actual_count)
            # 精确率 Precision
            precision = tp / recognize_count if recognize_count != 0 else 0.0
            # 召回率 Recall
            recall = tp / actual_count if actual_count != 0 else 0.0
            # F1 分数（综合准确率）
            if (precision + recall) == 0:
                accuracy = 0.0
            else:
                accuracy = 2 * (precision * recall) / (precision + recall)
        # =================================================================

        # 创建记录对象
        record = PipeRecord(
            image_url=image_url,
            pipe_number=pipe_number,
            recognize_count=recognize_count,
            actual_count=actual_count,
            is_consistent=(recognize_count == actual_count),
            accuracy=accuracy,
            operator_id=operator_id if operator_id else 0,
            operator_name=operator_name if operator_name else "未知",
            feedback_status="normal"
        )

        db.add(record)
        db.commit()
        db.refresh(record)

        return {
            "code": 200,
            "msg": "保存成功",
            "data": {
                "id": record.id,
                "is_consistent": record.is_consistent,
                "accuracy": accuracy
            }
        }
    except Exception as e:
        db.rollback()
        import traceback
        print(f"[保存错误] {str(e)}")
        print(f"[错误堆栈] {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"保存失败: {str(e)}")


@router.get("/records")
def get_records(
        start_date: str = Query(None),
        end_date: str = Query(None),
        pipe_number: str = Query(None),
        operator_id: int = Query(None),
        db: Session = Depends(get_db)
):
    try:
        query = db.query(PipeRecord)

        if operator_id is not None:
            query = query.filter(PipeRecord.operator_id == operator_id)

        if start_date:
            try:
                start = datetime.strptime(start_date, "%Y-%m-%d")
                query = query.filter(PipeRecord.create_time >= start)
            except ValueError:
                pass

        if end_date:
            try:
                end = datetime.strptime(end_date, "%Y-%m-%d")
                end = end.replace(hour=23, minute=59, second=59)
                query = query.filter(PipeRecord.create_time <= end)
            except ValueError:
                pass

        if pipe_number:
            query = query.filter(PipeRecord.pipe_number.contains(pipe_number))

        records = query.order_by(PipeRecord.create_time.desc()).all()

        return {
            "code": 200,
            "msg": "查询成功",
            "data": {
                "records": [
                    {
                        "id": r.id,
                        "image_url": r.image_url,
                        "pipe_number": r.pipe_number if r.pipe_number else "-",
                        "recognize_count": r.recognize_count,
                        "actual_count": r.actual_count,
                        "is_consistent": r.is_consistent,
                        "accuracy": float(r.accuracy) if r.accuracy else 0.0,
                        "feedback_status": r.feedback_status,
                        "create_time": r.create_time.strftime("%Y-%m-%d %H:%M:%S")
                    } for r in records
                ]
            }
        }
    except Exception as e:
        import traceback
        print(f"[查询错误] {str(e)}")
        print(f"[错误堆栈] {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


# 更新识别记录的对比数据（用于重新对比）
@router.put("/update/{record_id}")
def update_record(
        record_id: int,
        pipe_number: str = Form(...),
        actual_count: int = Form(...),
        db: Session = Depends(get_db)
):
    try:
        record = db.query(PipeRecord).filter(PipeRecord.id == record_id).first()
        if not record:
            raise HTTPException(status_code=404, detail="记录不存在")

        record.pipe_number = pipe_number
        record.actual_count = actual_count
        record.is_consistent = (record.recognize_count == actual_count)

        # ===================== 同步修改：更新时也用 F1 =====================
        if actual_count == 0:
            record.accuracy = 0.0
        else:
            tp = min(record.recognize_count, actual_count)
            precision = tp / record.recognize_count if record.recognize_count != 0 else 0.0
            recall = tp / actual_count if actual_count != 0 else 0.0
            if (precision + recall) == 0:
                record.accuracy = 0.0
            else:
                record.accuracy = 2 * (precision * recall) / (precision + recall)
        # ===================================================================

        db.commit()

        return {
            "code": 200,
            "msg": "更新成功"
        }
    except Exception as e:
        db.rollback()
        print(f"更新记录错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")