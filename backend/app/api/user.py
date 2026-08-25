from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import hashlib
from app.utils.db_util import get_db
from app.models.entity import User, UserRole, PipeRecord, Inventory

router = APIRouter(prefix="/user")


# Pydantic模型
class UserRegister(BaseModel):
    username: str
    password: str
    # 移除role字段，注册时只能是员工


class UserLogin(BaseModel):
    username: str
    password: str
    role: str


class UserUpdate(BaseModel):
    status: Optional[bool] = None
    role: Optional[str] = None


# 密码加密
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed


# 初始化管理员账号
def init_admin_user(db: Session):
    admin = db.query(User).filter(
        User.username == "admin",
        User.role == "admin"
    ).first()
    if not admin:
        admin = User(
            username="admin",
            password=hash_password("123456"),
            role="admin",
            status=True
        )
        db.add(admin)
        db.commit()
        print("✅ 管理员账号创建成功！账号：admin，密码：123456")


# 注册（只能注册员工）
@router.post("/register")
async def register(user: UserRegister, db: Session = Depends(get_db)):
    # 固定角色为employee
    role = "employee"

    # 检查用户名是否已存在（同一角色下不能重名）
    existing_user = db.query(User).filter(
        User.username == user.username,
        User.role == role
    ).first()
    if existing_user:
        raise HTTPException(status_code=400, detail=f"用户名已存在，请更换用户名")

    # 创建新用户
    new_user = User(
        username=user.username,
        password=hash_password(user.password),
        role=role,
        status=True
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "code": 200,
        "msg": "注册成功",
        "data": {
            "id": new_user.id,
            "username": new_user.username,
            "role": new_user.role
        }
    }


# 登录
@router.post("/login")
async def login(user: UserLogin, db: Session = Depends(get_db)):
    # 根据用户名和角色查找用户
    db_user = db.query(User).filter(
        User.username == user.username,
        User.role == user.role
    ).first()

    if not db_user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    # 验证密码
    if not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    # 检查账号状态
    if not db_user.status:
        raise HTTPException(status_code=403, detail="账号已被禁用，请联系管理员")

    return {
        "code": 200,
        "msg": "登录成功",
        "data": {
            "id": db_user.id,
            "username": db_user.username,
            "role": db_user.role
        }
    }


# 获取所有用户（管理员专用）
@router.get("/users")
async def get_users(
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=100),
        role: Optional[str] = None,
        keyword: Optional[str] = None,
        db: Session = Depends(get_db)
):
    query = db.query(User)

    if role:
        query = query.filter(User.role == role)
    else:
        # 默认不显示管理员账号列表中的管理员（保护admin账号）
        query = query.filter(User.role == "employee")

    if keyword:
        query = query.filter(User.username.contains(keyword))

    total = query.count()
    users = query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "code": 200,
        "msg": "查询成功",
        "data": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "list": [
                {
                    "id": u.id,
                    "username": u.username,
                    "role": u.role,
                    "status": u.status,
                    "create_time": u.create_time.strftime("%Y-%m-%d %H:%M:%S")
                } for u in users
            ]
        }
    }


# 更新用户状态（管理员专用）
@router.put("/user/{user_id}/status")
async def update_user_status(
        user_id: int,
        status: bool,
        db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 不能禁用admin账号
    if user.username == "admin" and user.role == "admin":
        raise HTTPException(status_code=403, detail="不能禁用管理员账号")

    user.status = status
    db.commit()

    return {
        "code": 200,
        "msg": "状态更新成功"
    }


# 重置用户密码（管理员专用）
@router.post("/user/{user_id}/reset-password")
async def reset_password(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 不能重置admin密码
    if user.username == "admin" and user.role == "admin":
        raise HTTPException(status_code=403, detail="不能重置管理员密码")

    user.password = hash_password("123456")
    db.commit()

    return {
        "code": 200,
        "msg": "密码已重置为123456"
    }


# 删除用户（管理员专用）
@router.delete("/user/{user_id}")
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 不能删除admin账号
    if user.username == "admin" and user.role == "admin":
        raise HTTPException(status_code=403, detail="不能删除管理员账号")

    db.delete(user)
    db.commit()

    return {
        "code": 200,
        "msg": "删除成功"
    }


# 获取统计数据
@router.get("/statistics")
async def get_statistics(db: Session = Depends(get_db)):
    try:
        # 用户统计
        total_users = db.query(User).filter(User.role == "employee").count()
        admin_count = db.query(User).filter(User.role == "admin").count()
        employee_count = db.query(User).filter(User.role == "employee").count()
        active_users = db.query(User).filter(User.status == True, User.role == "employee").count()

        # 钢管识别统计
        total_records = db.query(PipeRecord).count()

        # 准确率统计
        avg_accuracy_result = db.query(func.avg(PipeRecord.accuracy)).scalar()
        avg_accuracy = float(avg_accuracy_result) if avg_accuracy_result else 0.0

        # 今日记录数
        from datetime import datetime, date
        today_date = date.today()
        today_start = datetime(today_date.year, today_date.month, today_date.day, 0, 0, 0)
        today_end = datetime(today_date.year, today_date.month, today_date.day, 23, 59, 59)
        today_count = db.query(PipeRecord).filter(
            PipeRecord.create_time >= today_start,
            PipeRecord.create_time <= today_end
        ).count()

        # 入库统计
        inventory_total = db.query(Inventory).count()
        pending_feedback = db.query(Inventory).filter(Inventory.has_feedback == True,
                                                      Inventory.feedback_resolved == False).count()

        return {
            "code": 200,
            "msg": "查询成功",
            "data": {
                "users": {
                    "total": total_users,
                    "admin": admin_count,
                    "employee": employee_count,
                    "active": active_users
                },
                "records": {
                    "total": total_records,
                    "today": today_count,
                    "avg_accuracy": avg_accuracy
                },
                "inventory": {
                    "total": inventory_total,
                    "pending_feedback": pending_feedback
                }
            }
        }
    except Exception as e:
        import traceback
        print(f"[统计错误] {str(e)}")
        print(f"[错误堆栈] {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"统计失败: {str(e)}")


# 获取所有识别记录
# 获取所有识别记录
@router.get("/all-records")
async def get_all_records(
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        pipe_number: Optional[str] = None,
        operator_name: Optional[str] = None,
        operator_id: Optional[int] = None,  # 添加 operator_id 参数
        db: Session = Depends(get_db)
):
    try:
        query = db.query(PipeRecord)

        # 添加 operator_id 筛选（用于普通用户只查看自己的记录）
        if operator_id is not None:
            query = query.filter(PipeRecord.operator_id == operator_id)

        if start_date:
            query = query.filter(PipeRecord.create_time >= start_date)
        if end_date:
            query = query.filter(PipeRecord.create_time <= end_date + " 23:59:59")
        if pipe_number:
            query = query.filter(PipeRecord.pipe_number.contains(pipe_number))
        if operator_name:
            query = query.filter(PipeRecord.operator_name.contains(operator_name))

        total = query.count()
        records = query.order_by(PipeRecord.create_time.desc()).offset((page - 1) * page_size).limit(page_size).all()

        return {
            "code": 200,
            "msg": "查询成功",
            "data": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "list": [
                    {
                        "id": r.id,
                        "image_url": r.image_url,
                        "pipe_number": r.pipe_number if r.pipe_number else "-",
                        "recognize_count": r.recognize_count,
                        "actual_count": r.actual_count,
                        "is_consistent": r.is_consistent,
                        "accuracy": float(r.accuracy) if r.accuracy else 0.0,
                        "feedback_status": r.feedback_status,
                        "operator_name": r.operator_name if r.operator_name else "未知",
                        "create_time": r.create_time.strftime("%Y-%m-%d %H:%M:%S")
                    } for r in records
                ]
            }
        }
    except Exception as e:
        import traceback
        print(f"[获取记录错误] {str(e)}")
        print(f"[错误堆栈] {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"获取记录失败: {str(e)}")



