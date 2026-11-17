"""
FastAPI应用入口
"""
import time
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.exceptions import TCMException
from app.core.logger import app_logger
from app.core.seed import init_and_seed
from app.api.v1 import api_router


def _iso_timestamp() -> str:
    """返回带本地时区偏移的 ISO-8601 时间字符串。"""
    return datetime.now().astimezone().isoformat(timespec="seconds")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    app_logger.info("=" * 50)
    app_logger.info(f"{settings.APP_NAME} 启动中...")
    app_logger.info(f"版本: {settings.APP_VERSION}")
    app_logger.info(f"调试模式: {settings.DEBUG}")
    app_logger.info("=" * 50)

    # 迁移数据库并灌入种子数据
    try:
        result = init_and_seed()
        app_logger.info(
            f"数据初始化完成: 药材{result.get('herbs', 0)}味 / "
            f"方剂{result.get('prescriptions', 0)}个"
            + ("（已有数据，跳过）" if result.get("skipped") else "")
        )
    except Exception as e:
        app_logger.error(f"数据初始化失败: {e}")

    yield
    
    # 关闭时
    app_logger.info("应用关闭中...")


# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="面向公众的中医方剂通识科普 API，提供方药资料检索与 DeepSeek 辅助问答",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应配置具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录请求日志"""
    start_time = time.time()
    
    # 记录请求信息
    client_host = request.client.host if request.client else "unknown"
    app_logger.info(f"请求: {request.method} {request.url.path} - 客户端: {client_host}")
    
    response = await call_next(request)
    
    # 记录响应信息
    process_time = time.time() - start_time
    app_logger.info(
        f"响应: {request.method} {request.url.path} - "
        f"状态: {response.status_code} - 耗时: {process_time:.3f}s"
    )
    
    # 添加响应头
    response.headers["X-Process-Time"] = str(process_time)
    
    return response


# 全局异常处理
@app.exception_handler(TCMException)
async def tcm_exception_handler(request: Request, exc: TCMException):
    """处理自定义异常"""
    app_logger.error(f"业务异常: {exc.code} - {exc.message}")
    headers = {"WWW-Authenticate": "Bearer"} if exc.code == "AUTHENTICATION_ERROR" else None
    return JSONResponse(
        status_code=exc.status_code,
        headers=headers,
        content={
            "code": exc.code,
            "message": exc.message,
            "details": exc.details,
            "timestamp": _iso_timestamp()
        }
    )


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
    """把 FastAPI 默认的 422 结构转换为契约规定的顶层错误结构。"""
    return JSONResponse(
        status_code=422,
        content={
            "code": "VALIDATION_ERROR",
            "message": "请求参数不合法",
            "details": {"errors": exc.errors()},
            "timestamp": _iso_timestamp(),
        },
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """统一 FastAPI/Starlette HTTPException 的响应结构。"""
    code_by_status = {
        401: "AUTHENTICATION_ERROR",
        403: "AUTHORIZATION_ERROR",
        404: "NOT_FOUND",
        429: "RATE_LIMIT_ERROR",
    }
    code = code_by_status.get(exc.status_code, "INTERNAL_ERROR" if exc.status_code >= 500 else "VALIDATION_ERROR")
    message = exc.detail if isinstance(exc.detail, str) else "请求处理失败"
    details = exc.detail if isinstance(exc.detail, dict) else {}
    headers = {"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None
    return JSONResponse(
        status_code=exc.status_code,
        headers=headers,
        content={
            "code": code,
            "message": message,
            "details": details,
            "timestamp": _iso_timestamp(),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """处理通用异常"""
    app_logger.error(f"系统异常: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "code": "INTERNAL_ERROR",
            "message": "服务器内部错误",
            "details": {"error": str(exc)} if settings.DEBUG else {},
            "timestamp": _iso_timestamp()
        }
    )


# 健康检查
@app.get("/health", tags=["系统"])
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "timestamp": _iso_timestamp()
    }


# API路由 - V1版本
app.include_router(api_router, prefix="/api/v1")

# API路由 - 兼容版本（无前缀）
from app.api.v1.endpoints import chat, prescriptions, herbs
app.include_router(chat.router, prefix="/api/chat", tags=["方剂科普问答"])
app.include_router(prescriptions.router, prefix="/api/prescriptions", tags=["方剂学习资料"])
app.include_router(herbs.router, prefix="/api/herbs", tags=["中药学习资料"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
