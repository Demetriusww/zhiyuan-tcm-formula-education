"""
项目配置文件
包含数据库配置、大模型API配置、缓存配置等
"""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings


ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    """应用配置类"""
    
    # 应用基础配置
    APP_NAME: str = "知源 · 中医方剂通识平台"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # 数据库配置
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "sqlite:///./tcm_prescription.db"
    )
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_POOL_RECYCLE: int = 3600
    
    # Redis缓存配置
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD")
    CACHE_DEFAULT_TIMEOUT: int = 3600  # 默认缓存1小时
    
    # 大模型API配置 - DeepSeek（OpenAI 兼容协议）
    # 隐私约定：API Key 不写入源码，统一配置在 backend/.env 的 LLM_API_KEY（该文件已被 .gitignore 忽略）
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_API_BASE: str = os.getenv("LLM_API_BASE", "https://api.deepseek.com")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "deepseek-chat")
    LLM_TEMPERATURE: float = 0.4
    LLM_MAX_TOKENS: int = 4096
    LLM_TIMEOUT: int = 90

    # 视觉模型API配置(药材图像识别) - Moonshot Kimi K2.6(支持图片输入),可换 qwen-vl
    # 说明: DeepSeek 无视觉能力,识别单独走视觉 provider;key 存放 backend/.env 的 VISION_*
    VISION_API_KEY: str = os.getenv("VISION_API_KEY", "")
    VISION_API_BASE: str = os.getenv("VISION_API_BASE", "https://api.moonshot.cn/v1")
    VISION_MODEL: str = os.getenv("VISION_MODEL", "kimi-k2.6")
    VISION_TIMEOUT: int = 120
    
    # 安全配置
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7天
    ALGORITHM: str = "HS256"
    
    # 日志配置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: str = "logs/app.log"
    
    # 性能配置
    MAX_WORKERS: int = 4
    REQUEST_TIMEOUT: int = 30
    
    # 方剂分析配置
    MAX_HERBS_PER_PRESCRIPTION: int = 30  # 单个方剂最大药味数
    MIN_HERBS_PER_PRESCRIPTION: int = 2   # 单个方剂最小药味数
    MAX_INPUT_LENGTH: int = 1000          # 最大输入长度
    
    # 分页配置
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 500

    # M01 批量导入/导出配置
    MAX_IMPORT_FILE_SIZE: int = 10 * 1024 * 1024  # 10 MB
    MAX_IMPORT_ROWS: int = 1000

    # 缓存配置（Redis 不可用时自动降级为直连数据库）
    CACHE_ENABLED: bool = os.getenv("CACHE_ENABLED", "true").lower() == "true"
    CACHE_PRESCRIPTION_TIMEOUT: int = 3600   # 方剂详情 1 小时
    CACHE_ANALYSIS_TIMEOUT: int = 1800       # 分析结果 30 分钟
    CACHE_SEARCH_TIMEOUT: int = 900          # 搜索结果 15 分钟
    
    class Config:
        env_file = str(ENV_FILE)
        case_sensitive = True


# 全局配置实例
settings = Settings()
