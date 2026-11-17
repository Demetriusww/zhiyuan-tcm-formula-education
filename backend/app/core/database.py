"""
数据库配置模块
提供SQLAlchemy数据库连接和会话管理
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings
from app.core.logger import app_logger

# 创建数据库引擎
# SQLite 不支持连接池参数，仅对非 SQLite 数据库启用连接池
if settings.DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=settings.DEBUG
    )
else:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        pool_recycle=settings.DATABASE_POOL_RECYCLE,
        echo=settings.DEBUG
    )

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 声明基类
Base = declarative_base()


def get_db() -> Session:
    """
    获取数据库会话
    用于FastAPI的依赖注入
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    初始化数据库
    创建所有表结构
    """
    try:
        Base.metadata.create_all(bind=engine)
        app_logger.info("数据库初始化完成")
    except Exception as e:
        app_logger.error(f"数据库初始化失败: {e}")
        raise


def close_db():
    """
    关闭数据库连接
    """
    engine.dispose()
    app_logger.info("数据库连接已关闭")
