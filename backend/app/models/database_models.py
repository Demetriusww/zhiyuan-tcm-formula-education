"""
数据库ORM模型定义
使用SQLAlchemy定义数据库表结构
"""
from datetime import datetime
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class Herb(Base):
    """中药数据库模型"""
    __tablename__ = "herbs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, index=True)
    pinyin = Column(String(50), nullable=True)
    property = Column(String(50), nullable=True)  # 性味：如"辛、微苦，温"
    flavor = Column(String(50), nullable=True)  # 药味：酸、苦、甘、辛、咸
    meridians = Column(String(200), nullable=True)  # 归经
    latin = Column(String(100), nullable=True)  # 拉丁名
    functions = Column(Text, nullable=True)  # 功效
    indications = Column(Text, nullable=True)  # 主治
    dosage = Column(String(100), nullable=True)  # 常用剂量
    precautions = Column(String(500), nullable=True)  # 禁忌
    modern_research = Column(Text, nullable=True)  # 现代研究
    description = Column(Text, nullable=True)  # 药材简介
    category = Column(String(50), nullable=True, index=True)  # 药材分类：解表药/清热药等
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    prescription_herbs = relationship("PrescriptionHerb", back_populates="herb")


class Prescription(Base):
    """方剂数据库模型"""
    __tablename__ = "prescriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True, unique=True)
    pinyin = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)  # 方剂描述
    # 类型取值见 schemas.PrescriptionType：经典名方/现代方剂/经验方/自定义方剂
    type = Column(String(20), default="经典名方", server_default="经典名方")
    source = Column(String(200), nullable=True)  # 来源
    indications = Column(Text, nullable=True)  # 主治症状
    functions = Column(Text, nullable=True)  # 功效
    usage = Column(Text, nullable=True)  # 用法用量
    precautions = Column(Text, nullable=True)  # 注意事项
    category = Column(String(50), nullable=True, index=True)  # 方剂分类：解表剂/补益剂等
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    herbs = relationship("PrescriptionHerb", back_populates="prescription", order_by="PrescriptionHerb.order")
    favorites = relationship(
        "Favorite",
        back_populates="prescription",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    efficacy_predictions = relationship(
        "EfficacyPrediction",
        back_populates="prescription",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class PrescriptionHerb(Base):
    """方剂-药物关联表"""
    __tablename__ = "prescription_herbs"
    
    id = Column(Integer, primary_key=True, index=True)
    prescription_id = Column(Integer, ForeignKey("prescriptions.id"), nullable=False)
    herb_id = Column(Integer, ForeignKey("herbs.id"), nullable=False)
    dosage = Column(String(50), nullable=True)  # 剂量
    preparation = Column(String(100), nullable=True)  # 炮制方法
    order = Column(Integer, default=0)  # 排序
    
    # 关系
    prescription = relationship("Prescription", back_populates="herbs")
    herb = relationship("Herb", back_populates="prescription_herbs")


class AnalysisRecord(Base):
    """分析记录数据库模型"""
    __tablename__ = "analysis_records"
    
    id = Column(Integer, primary_key=True, index=True)
    prescription_id = Column(Integer, ForeignKey("prescriptions.id"), nullable=True)
    analysis_type = Column(String(20), nullable=False)  # 分析类型
    input_data = Column(Text, nullable=True)  # 输入数据（JSON）
    result_data = Column(Text, nullable=True)  # 结果数据（JSON）
    created_at = Column(DateTime, default=datetime.utcnow)


class Conversation(Base):
    """对话记录数据库模型"""
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # user 或 assistant
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class AncientBook(Base):
    """古籍文献模型（M05）"""
    __tablename__ = "ancient_books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False, unique=True, index=True)
    dynasty = Column(String(30), nullable=True, index=True)
    author = Column(String(100), nullable=True)
    category = Column(String(30), nullable=True, index=True)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    prescriptions = Column(Text, nullable=True)  # JSON 数组字符串
    source_url = Column(String(500), nullable=True)
    sort_order = Column(Integer, default=0, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class User(Base):
    """平台用户模型"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), nullable=False, unique=True, index=True)  # 登录名
    password_hash = Column(String(200), nullable=False)  # bcrypt 哈希
    nickname = Column(String(50), nullable=True)  # 显示昵称
    email = Column(String(100), nullable=True)
    role = Column(String(20), default="user")  # user / admin
    is_active = Column(Boolean, default=True, nullable=False, server_default="1")  # 是否启用
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    favorites = relationship("Favorite", back_populates="user", cascade="all, delete-orphan")


class Favorite(Base):
    """用户收藏的方剂（一个用户可收藏多个方剂）"""
    __tablename__ = "favorites"
    __table_args__ = (
        UniqueConstraint("user_id", "prescription_id", name="uq_user_prescription"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    prescription_id = Column(
        Integer, ForeignKey("prescriptions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    user = relationship("User", back_populates="favorites")
    prescription = relationship("Prescription", back_populates="favorites")


class AuditLog(Base):
    """管理员关键操作审计日志（M06）"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    operator_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    operator_name = Column(String(50), nullable=True)
    action = Column(String(50), nullable=False, index=True)  # 如 change_role / disable_user
    target_type = Column(String(50), nullable=True)
    target_id = Column(String(50), nullable=True)
    detail = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class EfficacyPrediction(Base):
    """药效预测记录（M04）"""
    __tablename__ = "efficacy_predictions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    prescription_id = Column(
        Integer, ForeignKey("prescriptions.id", ondelete="CASCADE"), nullable=False
    )
    target_symptoms = Column(Text, nullable=True)  # JSON 数组字符串
    predicted_efficacy = Column(Float, nullable=True)  # 0-100
    confidence_level = Column(Float, nullable=True)  # 0-1
    mechanism_analysis = Column(Text, nullable=True)
    supporting_evidence = Column(Text, nullable=True)  # JSON 数组字符串
    contraindications = Column(Text, nullable=True)  # JSON 数组字符串
    risk_level = Column(String(10), default="low", server_default="low")
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    prescription = relationship("Prescription", back_populates="efficacy_predictions")


class RecognitionRecord(Base):
    """药材图像识别记录（网页/ESP32 上传均可产生）"""
    __tablename__ = "recognition_records"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(20), default="web")  # web / esp32
    image_path = Column(String(300), nullable=True)  # 本地保存路径或 URL
    raw_text = Column(Text, nullable=True)  # 模型原始返回
    herb_name = Column(String(100), nullable=True, index=True)  # 归一化后药材名
    herb_id = Column(Integer, ForeignKey("herbs.id"), nullable=True)  # 命中库内药材
    matched = Column(Integer, default=0)  # 1=命中知识库 0=未命中
    created_at = Column(DateTime, default=datetime.utcnow)
