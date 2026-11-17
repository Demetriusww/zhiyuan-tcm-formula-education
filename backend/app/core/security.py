# -*- coding: utf-8 -*-
"""
认证与安全工具：密码哈希(bcrypt) + JWT 签发/校验 + 当前用户依赖
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import AuthenticationError, AuthorizationError
from app.models.database_models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return pwd_context.verify(plain, hashed)
    except Exception:
        return False


def create_access_token(user_id: int, username: str) -> str:
    """签发 JWT，有效期见 settings.ACCESS_TOKEN_EXPIRE_MINUTES"""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "username": username, "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """FastAPI 依赖：解析 Bearer Token 并返回当前用户；未认证则 401"""
    if credentials is None:
        raise AuthenticationError("未登录，请先登录")
    try:
        payload = jwt.decode(credentials.credentials, settings.SECRET_KEY,
                             algorithms=[settings.ALGORITHM])
        user_id = int(payload.get("sub", "0"))
    except (JWTError, ValueError):
        raise AuthenticationError("登录状态无效或已过期，请重新登录")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise AuthenticationError("用户不存在")
    if not user.is_active:
        raise AuthenticationError("用户已被禁用")
    return user


def require_admin(current: User = Depends(get_current_user)) -> User:
    """FastAPI 依赖：要求当前用户具有管理员角色。"""
    if current.role != "admin":
        raise AuthorizationError("需要管理员权限")
    return current


def user_to_dict(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "nickname": user.nickname,
        "email": user.email,
        "role": user.role,
        "is_active": bool(user.is_active),
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }
