"""
自定义异常类定义
统一错误处理机制
"""
from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class TCMException(Exception):
    """基础异常类"""
    def __init__(
        self,
        message: str = "发生错误",
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(TCMException):
    """数据验证错误"""
    def __init__(self, message: str = "数据验证失败", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details
        )


class NotFoundError(TCMException):
    """资源不存在错误"""
    def __init__(self, message: str = "资源不存在", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details=details
        )


class DuplicateError(TCMException):
    """数据重复错误"""
    def __init__(self, message: str = "数据已存在", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="DUPLICATE_ERROR",
            status_code=status.HTTP_409_CONFLICT,
            details=details
        )


class AuthenticationError(TCMException):
    """认证错误"""
    def __init__(self, message: str = "认证失败", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="AUTHENTICATION_ERROR",
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details
        )


class AuthorizationError(TCMException):
    """授权错误"""
    def __init__(self, message: str = "权限不足", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="AUTHORIZATION_ERROR",
            status_code=status.HTTP_403_FORBIDDEN,
            details=details
        )


class LLMServiceError(TCMException):
    """大模型服务错误"""
    def __init__(self, message: str = "AI服务调用失败", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="LLM_SERVICE_ERROR",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=details
        )


class DatabaseError(TCMException):
    """数据库错误"""
    def __init__(self, message: str = "数据库操作失败", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="DATABASE_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )


class PrescriptionAnalysisError(TCMException):
    """方剂分析错误"""
    def __init__(self, message: str = "方剂分析失败", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="ANALYSIS_ERROR",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )


class RateLimitError(TCMException):
    """请求频率限制错误"""
    def __init__(self, message: str = "请求过于频繁，请稍后再试", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="RATE_LIMIT_ERROR",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details=details
        )


class ImportValidationError(TCMException):
    """导入文件整体无法解析或格式不合法"""
    def __init__(self, message: str = "导入文件校验失败", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="IMPORT_VALIDATION_ERROR",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details
        )


class ExportError(TCMException):
    """导出文件生成失败"""
    def __init__(self, message: str = "导出文件生成失败", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="EXPORT_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )


def handle_exception(exc: TCMException) -> HTTPException:
    """将自定义异常转换为HTTPException"""
    return HTTPException(
        status_code=exc.status_code,
        detail={
            "code": exc.code,
            "message": exc.message,
            "details": exc.details
        }
    )
