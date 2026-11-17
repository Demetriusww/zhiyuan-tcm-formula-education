"""
日志配置模块
提供统一的日志记录功能
"""
import logging
import logging.handlers
import os
import sys
from datetime import datetime
from typing import Optional

from app.core.config import settings


class ColoredFormatter(logging.Formatter):
    """带颜色的日志格式化器"""
    
    # ANSI颜色代码
    COLORS = {
        'DEBUG': '\033[36m',      # 青色
        'INFO': '\033[32m',       # 绿色
        'WARNING': '\033[33m',    # 黄色
        'ERROR': '\033[31m',      # 红色
        'CRITICAL': '\033[35m',   # 紫色
    }
    RESET = '\033[0m'
    
    def format(self, record):
        # 保存原始级别名称
        original_levelname = record.levelname
        
        # 添加颜色
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.RESET}"
        
        # 格式化
        result = super().format(record)
        
        # 恢复原始级别名称
        record.levelname = original_levelname
        
        return result


def setup_logger(
    name: str,
    level: Optional[str] = None,
    log_file: Optional[str] = None,
    use_color: bool = True
) -> logging.Logger:
    """
    设置日志记录器
    
    Args:
        name: 日志记录器名称
        level: 日志级别
        log_file: 日志文件路径
        use_color: 是否使用彩色输出
    
    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    
    # 设置日志级别
    log_level = level or settings.LOG_LEVEL
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # 避免重复添加处理器
    if logger.handlers:
        return logger

    # LOG_FORMAT may be set by the host process to a format name (for example
    # "json"). In that case use the application's normal text format instead
    # of passing the name directly to logging.Formatter.
    log_format = settings.LOG_FORMAT
    if "%" not in log_format:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # 创建格式化器
    formatter = logging.Formatter(log_format)
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    
    if use_color:
        colored_formatter = ColoredFormatter(log_format)
        console_handler.setFormatter(colored_formatter)
    else:
        console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    
    # 文件处理器
    if log_file or settings.LOG_FILE:
        file_path = log_file or settings.LOG_FILE
        
        # 确保日志目录存在
        log_dir = os.path.dirname(file_path)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # 使用RotatingFileHandler进行日志轮转
        file_handler = logging.handlers.RotatingFileHandler(
            file_path,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


# 应用主日志记录器
app_logger = setup_logger("tcm_platform")

# 模块特定的日志记录器
auth_logger = setup_logger("tcm_platform.auth")
db_logger = setup_logger("tcm_platform.database")
llm_logger = setup_logger("tcm_platform.llm")
analysis_logger = setup_logger("tcm_platform.analysis")
api_logger = setup_logger("tcm_platform.api")


def log_function_call(logger: logging.Logger):
    """函数调用日志装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = datetime.now()
            logger.debug(f"调用函数: {func.__name__}, 参数: args={args}, kwargs={kwargs}")
            
            try:
                result = func(*args, **kwargs)
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                logger.debug(f"函数 {func.__name__} 执行成功, 耗时: {duration:.3f}s")
                return result
            except Exception as e:
                logger.error(f"函数 {func.__name__} 执行失败: {str(e)}")
                raise
        
        return wrapper
    return decorator


def log_api_call(logger: logging.Logger = api_logger):
    """API调用日志装饰器"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = datetime.now()
            client_ip = kwargs.get('request', {}).get('client', {}).get('host', 'unknown')
            
            logger.info(f"API调用开始: {func.__name__}, 客户端: {client_ip}")
            
            try:
                result = await func(*args, **kwargs)
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                logger.info(f"API调用成功: {func.__name__}, 耗时: {duration:.3f}s")
                return result
            except Exception as e:
                logger.error(f"API调用失败: {func.__name__}, 错误: {str(e)}")
                raise
        
        return wrapper
    return decorator
