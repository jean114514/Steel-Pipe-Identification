from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime
from typing import Optional
from app.utils.db_util import get_db
from app.models.entity import Inventory, Feedback, PipeRecord

router = APIRouter(prefix="/inventory")


# 添加入库记录
@router.post("/add")
async def add_inventory(
        file: UploadFile = File(...),
        pipe_number: str = Form(...),
        quantity: int = Form(...),
        db: Session = Depends(get_db)
):
    try:
        existing = db.query(Inventory).filter(Inventory.pipe_number == pipe_number).first()
        if existing:
            raise HTTPException(status_code=400, detail="钢管编号已存在")

        contents = await file.read()
        from app.utils.img_util import read_image, save_image
        img = read_image(contents)
        if img is None:
            raise HTTPException(status_code=400, detail="图片读取失败")
        image_url = save_image(img)

        inventory = Inventory(
            image_url=image_url,
            pipe_number=pipe_number,
            quantity=quantity
        )
        db.add(inventory)
        db.commit()
        db.refresh(inventory)

        return {
            "code": 200,
            "msg": "添加入库成功",
            "data": {
                "id": inventory.id,
                "pipe_number": inventory.pipe_number,
                "quantity": inventory.quantity,
                "image_url": inventory.image_url,
                "create_time": inventory.create_time.strftime("%Y-%m-%d %H:%M:%S")
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"添加入库错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"添加失败: {str(e)}")


# 获取入库列表
@router.get("/list")
def get_inventory_list(
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        pipe_number: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        db: Session = Depends(get_db)
):
    try:
        query = db.query(Inventory)

        if pipe_number:
            query = query.filter(Inventory.pipe_number.contains(pipe_number))

        if start_date:
            query = query.filter(Inventory.create_time >= start_date)
        if end_date:
            query = query.filter(Inventory.create_time <= end_date + " 23:59:59")

        total = query.count()
        items = query.order_by(Inventory.create_time.desc()).offset((page - 1) * page_size).limit(page_size).all()

        return {
            "code": 200,
            "msg": "查询成功",
            "data": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "list": [
                    {
                        "id": item.id,
                        "image_url": item.image_url,
                        "pipe_number": item.pipe_number,
                        "quantity": item.quantity,
                        "create_time": item.create_time.strftime("%Y-%m-%d %H:%M:%S"),
                        "has_feedback": item.has_feedback,
                        "feedback_resolved": item.feedback_resolved
                    } for item in items
                ]
            }
        }
    except Exception as e:
        print(f"查询入库列表错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


# 更新入库数量
@router.put("/update/{inventory_id}")
def update_inventory(
        inventory_id: int,
        quantity: int = Form(...),
        pipe_number: Optional[str] = Form(None),
        db: Session = Depends(get_db)
):
    try:
        inventory = db.query(Inventory).filter(Inventory.id == inventory_id).first()
        if not inventory:
            raise HTTPException(status_code=404, detail="入库记录不存在")

        if pipe_number and pipe_number != inventory.pipe_number:
            existing = db.query(Inventory).filter(Inventory.pipe_number == pipe_number).first()
            if existing:
                raise HTTPException(status_code=400, detail="钢管编号已存在")
            inventory.pipe_number = pipe_number

        inventory.quantity = quantity
        db.commit()

        return {
            "code": 200,
            "msg": "更新成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"更新入库错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")


# 删除入库记录
@router.delete("/delete/{inventory_id}")
def delete_inventory(inventory_id: int, db: Session = Depends(get_db)):
    try:
        inventory = db.query(Inventory).filter(Inventory.id == inventory_id).first()
        if not inventory:
            raise HTTPException(status_code=404, detail="入库记录不存在")

        # 先处理关联的反馈记录
        # 将关联的反馈记录的 inventory_id 设置为 NULL
        related_feedbacks = db.query(Feedback).filter(Feedback.inventory_id == inventory_id).all()
        for feedback in related_feedbacks:
            feedback.inventory_id = None
            # 可选：更新反馈状态
            feedback.status = "resolved"
            feedback.resolve_note = "关联的入库记录已被删除"
            feedback.resolve_time = datetime.now()

        # 删除入库记录
        db.delete(inventory)
        db.commit()

        return {
            "code": 200,
            "msg": "删除成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"删除入库错误: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")

# 根据钢管编号查询入库信息
@router.get("/search")
def search_inventory(
        pipe_number: str = Query(..., description="钢管编号"),
        db: Session = Depends(get_db)
):
    try:
        inventory = db.query(Inventory).filter(Inventory.pipe_number == pipe_number).first()
        if not inventory:
            return {
                "code": 404,
                "msg": "未找到该钢管编号的入库信息",
                "data": None
            }

        return {
            "code": 200,
            "msg": "查询成功",
            "data": {
                "id": inventory.id,
                "pipe_number": inventory.pipe_number,
                "quantity": inventory.quantity,
                "image_url": inventory.image_url,
                "create_time": inventory.create_time.strftime("%Y-%m-%d %H:%M:%S")
            }
        }
    except Exception as e:
        print(f"查询入库信息错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


# 提交反馈（支持两种类型，同时保存识别记录）
@router.post("/feedback")
def submit_feedback(
        record_id: int = Form(0),
        pipe_number: str = Form(...),
        recognize_count: int = Form(...),
        actual_count: int = Form(...),
        suggested_count: int = Form(...),
        message: str = Form(...),
        user_id: int = Form(...),
        user_name: str = Form(...),
        feedback_type: str = Form("quantity_error"),
        image_url: Optional[str] = Form(None),
        save_record: bool = Form(False),
        db: Session = Depends(get_db)
):
    try:
        # 如果需要保存识别记录且record_id为0
        if save_record and record_id == 0 and image_url:
            new_record = PipeRecord(
                image_url=image_url,
                pipe_number=pipe_number,
                recognize_count=recognize_count,
                actual_count=actual_count if actual_count > 0 else 0,
                is_consistent=(recognize_count == actual_count) if actual_count > 0 else False,
                accuracy=(recognize_count / actual_count) if actual_count > 0 else 0.0,
                operator_id=user_id,
                operator_name=user_name,
                feedback_status="processing",
                feedback_message=message
            )
            db.add(new_record)
            db.flush()
            record_id = new_record.id

        # 查找入库记录
        inventory = db.query(Inventory).filter(Inventory.pipe_number == pipe_number).first()

        # 创建反馈记录
        feedback = Feedback(
            record_id=record_id if record_id > 0 else None,
            pipe_number=pipe_number,
            user_id=user_id,
            user_name=user_name,
            recognize_count=recognize_count,
            actual_count=actual_count,
            suggested_count=suggested_count,
            feedback_type=feedback_type,
            message=message,
            image_url=image_url,
            status="pending",
            resolve_result="pending"
        )

        if inventory:
            feedback.inventory_id = inventory.id
            inventory.has_feedback = True
            inventory.feedback_resolved = False

        db.add(feedback)

        # 更新识别记录的反馈状态
        if record_id > 0:
            record = db.query(PipeRecord).filter(PipeRecord.id == record_id).first()
            if record:
                record.feedback_status = "processing"
                record.feedback_message = message

        db.commit()

        return {
            "code": 200,
            "msg": "反馈已提交，等待管理员处理",
            "data": {
                "record_id": record_id
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"提交反馈错误: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"提交失败: {str(e)}")


# 获取待处理反馈（管理员）
@router.get("/pending-feedback")
def get_pending_feedback(db: Session = Depends(get_db)):
    try:
        feedbacks = db.query(Feedback).filter(Feedback.status == "pending").order_by(Feedback.create_time.desc()).all()

        return {
            "code": 200,
            "msg": "查询成功",
            "data": [
                {
                    "id": f.id,
                    "record_id": f.record_id,
                    "inventory_id": f.inventory_id,
                    "pipe_number": f.pipe_number,
                    "user_name": f.user_name,
                    "recognize_count": f.recognize_count,
                    "actual_count": f.actual_count,
                    "suggested_count": f.suggested_count,
                    "feedback_type": f.feedback_type,
                    "message": f.message,
                    "image_url": f.image_url,
                    "create_time": f.create_time.strftime("%Y-%m-%d %H:%M:%S")
                } for f in feedbacks
            ]
        }
    except Exception as e:
        print(f"查询待处理反馈错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


# 获取已处理反馈（管理员）
@router.get("/resolved-feedback")
def get_resolved_feedback(db: Session = Depends(get_db)):
    try:
        feedbacks = db.query(Feedback).filter(Feedback.status == "resolved").order_by(Feedback.create_time.desc()).all()

        return {
            "code": 200,
            "msg": "查询成功",
            "data": [
                {
                    "id": f.id,
                    "record_id": f.record_id,
                    "inventory_id": f.inventory_id,
                    "pipe_number": f.pipe_number,
                    "user_name": f.user_name,
                    "recognize_count": f.recognize_count,
                    "actual_count": f.actual_count,
                    "suggested_count": f.suggested_count,
                    "feedback_type": f.feedback_type,
                    "message": f.message,
                    "image_url": f.image_url,
                    "status": f.status,
                    "resolve_note": f.resolve_note,
                    "resolve_result": f.resolve_result,
                    "create_time": f.create_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "resolve_time": f.resolve_time.strftime("%Y-%m-%d %H:%M:%S") if f.resolve_time else None
                } for f in feedbacks
            ]
        }
    except Exception as e:
        print(f"查询已处理反馈错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


# 获取用户的反馈记录
@router.get("/my-feedback")
def get_my_feedback(
        user_id: int = Query(...),
        db: Session = Depends(get_db)
):
    try:
        feedbacks = db.query(Feedback).filter(
            Feedback.user_id == user_id
        ).order_by(Feedback.create_time.desc()).all()

        return {
            "code": 200,
            "msg": "查询成功",
            "data": [
                {
                    "id": f.id,
                    "record_id": f.record_id,
                    "pipe_number": f.pipe_number,
                    "recognize_count": f.recognize_count,
                    "actual_count": f.actual_count,
                    "suggested_count": f.suggested_count,
                    "feedback_type": f.feedback_type,
                    "message": f.message,
                    "image_url": f.image_url,
                    "status": f.status,
                    "resolve_note": f.resolve_note,
                    "resolve_result": f.resolve_result,
                    "create_time": f.create_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "resolve_time": f.resolve_time.strftime("%Y-%m-%d %H:%M:%S") if f.resolve_time else None
                } for f in feedbacks
            ]
        }
    except Exception as e:
        print(f"查询用户反馈错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


# 获取单个反馈详情
@router.get("/feedback/{feedback_id}")
def get_feedback_detail(feedback_id: int, db: Session = Depends(get_db)):
    try:
        feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
        if not feedback:
            raise HTTPException(status_code=404, detail="反馈不存在")

        return {
            "code": 200,
            "msg": "查询成功",
            "data": {
                "id": feedback.id,
                "record_id": feedback.record_id,
                "inventory_id": feedback.inventory_id,
                "pipe_number": feedback.pipe_number,
                "user_name": feedback.user_name,
                "recognize_count": feedback.recognize_count,
                "actual_count": feedback.actual_count,
                "suggested_count": feedback.suggested_count,
                "feedback_type": feedback.feedback_type,
                "message": feedback.message,
                "image_url": feedback.image_url,
                "status": feedback.status,
                "resolve_note": feedback.resolve_note,
                "resolve_result": feedback.resolve_result,
                "create_time": feedback.create_time.strftime("%Y-%m-%d %H:%M:%S"),
                "resolve_time": feedback.resolve_time.strftime("%Y-%m-%d %H:%M:%S") if feedback.resolve_time else None
            }
        }
    except Exception as e:
        print(f"查询反馈详情错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


# 处理反馈（管理员）
@router.post("/resolve-feedback")
def resolve_feedback(
        feedback_id: int = Form(...),
        action: str = Form(...),
        resolve_note: str = Form(None),
        new_quantity: Optional[int] = Form(None),
        new_pipe_number: Optional[str] = Form(None),
        db: Session = Depends(get_db)
):
    try:
        feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
        if not feedback:
            raise HTTPException(status_code=404, detail="反馈不存在")

        feedback.status = "resolved"
        feedback.resolve_time = datetime.now()
        if resolve_note:
            feedback.resolve_note = resolve_note

        # 根据action决定处理结果
        if action == "approve":
            feedback.resolve_result = "approved"
        else:
            feedback.resolve_result = "rejected"

            # ========== 关键修改：拒绝时也要更新入库记录的状态 ==========
            # 如果是数量错误类型，更新入库记录的反馈状态
            if feedback.feedback_type == "quantity_error" and feedback.inventory_id:
                inventory = db.query(Inventory).filter(Inventory.id == feedback.inventory_id).first()
                if inventory:
                    inventory.has_feedback = False
                    inventory.feedback_resolved = True

            # 如果是请求新增类型，更新入库记录的反馈状态（如果有关联的入库记录）
            if feedback.feedback_type == "request_add" and feedback.inventory_id:
                inventory = db.query(Inventory).filter(Inventory.id == feedback.inventory_id).first()
                if inventory:
                    inventory.has_feedback = False
                    inventory.feedback_resolved = True

            # 更新识别记录反馈状态为rejected
            if feedback.record_id:
                record = db.query(PipeRecord).filter(PipeRecord.id == feedback.record_id).first()
                if record:
                    record.feedback_status = "rejected"

            db.commit()
            return {
                "code": 200,
                "msg": "已拒绝该反馈"
            }

        # ========== 批准逻辑 ==========
        # 确定使用的钢管编号
        final_pipe_number = new_pipe_number if new_pipe_number else feedback.pipe_number
        final_quantity = new_quantity if new_quantity is not None else feedback.suggested_count

        # 如果是数量错误类型，更新入库记录
        if feedback.feedback_type == "quantity_error" and feedback.inventory_id:
            inventory = db.query(Inventory).filter(Inventory.id == feedback.inventory_id).first()
            if inventory:
                # 如果钢管编号改变了，需要检查新编号是否已存在
                if new_pipe_number and new_pipe_number != inventory.pipe_number:
                    existing = db.query(Inventory).filter(Inventory.pipe_number == new_pipe_number).first()
                    if existing:
                        raise HTTPException(status_code=400, detail="钢管编号已存在")
                    inventory.pipe_number = new_pipe_number
                inventory.quantity = final_quantity
                inventory.feedback_resolved = True
                inventory.has_feedback = False  # 反馈已解决，恢复正常状态

        # 如果是请求新增类型，创建或更新入库记录
        if feedback.feedback_type == "request_add":
            existing = db.query(Inventory).filter(Inventory.pipe_number == final_pipe_number).first()
            if existing:
                # 如果已存在，更新数量
                existing.quantity = final_quantity
                existing.has_feedback = False
                existing.feedback_resolved = True
                feedback.inventory_id = existing.id
            elif feedback.image_url:
                # 创建新的入库记录
                inventory = Inventory(
                    image_url=feedback.image_url,
                    pipe_number=final_pipe_number,
                    quantity=final_quantity
                )
                db.add(inventory)
                db.flush()
                feedback.inventory_id = inventory.id

        # 更新识别记录
        if feedback.record_id:
            record = db.query(PipeRecord).filter(PipeRecord.id == feedback.record_id).first()
            if record:
                record.feedback_status = "resolved"
                record.pipe_number = final_pipe_number
                record.actual_count = final_quantity
                record.is_consistent = (record.recognize_count == final_quantity)
                if final_quantity == 0:
                    record.accuracy = 0.0
                else:
                    record.accuracy = record.recognize_count / final_quantity

        db.commit()

        return {
            "code": 200,
            "msg": "反馈已处理"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"处理反馈错误: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")


# 直接保存识别结果（不经过入库对比）
@router.post("/save-record-only")
def save_record_only(
        image_url: str = Form(...),
        recognize_count: int = Form(...),
        operator_id: int = Form(None),
        operator_name: str = Form(None),
        db: Session = Depends(get_db)
):
    try:
        record = PipeRecord(
            image_url=image_url,
            pipe_number=None,
            recognize_count=recognize_count,
            actual_count=0,
            is_consistent=False,
            accuracy=0.0,
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
                "id": record.id
            }
        }
    except Exception as e:
        db.rollback()
        print(f"保存记录错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"保存失败: {str(e)}")