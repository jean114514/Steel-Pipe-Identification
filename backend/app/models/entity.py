from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Enum, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.utils.db_util import Base
import enum


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    EMPLOYEE = "employee"


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False, comment="用户名")
    password = Column(String(255), nullable=False, comment="密码")
    role = Column(Enum(UserRole), default=UserRole.EMPLOYEE, nullable=False, comment="角色")
    status = Column(Boolean, default=True, comment="状态：True启用 False禁用")
    create_time = Column(DateTime, default=func.now(), comment="创建时间")
    update_time = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")


class PipeRecord(Base):
    __tablename__ = "pipe_record"

    id = Column(Integer, primary_key=True, index=True)
    image_url = Column(String(255), comment="图片路径")
    pipe_number = Column(String(50), comment="钢管编号")
    recognize_count = Column(Integer, comment="识别数量")
    actual_count = Column(Integer, comment="入库数量")
    is_consistent = Column(Boolean, comment="是否一致")
    accuracy = Column(Float, comment="识别准确率(0-1)")
    operator_id = Column(Integer, comment="操作员ID")
    operator_name = Column(String(50), comment="操作员姓名")
    feedback_status = Column(String(20), default="normal", comment="反馈状态：normal/processing/resolved")
    feedback_message = Column(Text, comment="反馈消息")
    create_time = Column(DateTime, default=func.now(), comment="创建时间")


class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    image_url = Column(String(255), comment="入库图片路径")
    pipe_number = Column(String(50), unique=True, index=True, nullable=False, comment="钢管编号")
    quantity = Column(Integer, nullable=False, comment="入库数量")
    create_time = Column(DateTime, default=func.now(), comment="入库时间")
    update_time = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")

    # 反馈相关字段
    has_feedback = Column(Boolean, default=False, comment="是否有反馈")
    feedback_record_id = Column(Integer, comment="关联的识别记录ID")
    feedback_resolved = Column(Boolean, default=False, comment="反馈是否已解决")


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    record_id = Column(Integer, ForeignKey("pipe_record.id"), comment="识别记录ID")
    inventory_id = Column(Integer, ForeignKey("inventory.id"), comment="入库记录ID")
    pipe_number = Column(String(50), comment="钢管编号")
    user_id = Column(Integer, comment="反馈用户ID")
    user_name = Column(String(50), comment="反馈用户姓名")
    recognize_count = Column(Integer, comment="识别数量")
    actual_count = Column(Integer, comment="原入库数量")
    suggested_count = Column(Integer, comment="建议数量")
    feedback_type = Column(String(20), default="quantity_error", comment="反馈类型：quantity_error数量有误，request_add请求新增")
    message = Column(Text, comment="反馈消息")
    image_url = Column(String(255), comment="关联图片URL")
    status = Column(String(20), default="pending", comment="状态：pending/resolved/rejected")
    create_time = Column(DateTime, default=func.now(), comment="反馈时间")
    resolve_time = Column(DateTime, comment="解决时间")
    resolve_note = Column(Text, comment="处理备注")
    resolve_result = Column(String(20), default="pending", comment="处理结果：approved/rejected")