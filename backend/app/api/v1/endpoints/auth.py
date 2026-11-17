# -*- coding: utf-8 -*-
"""用户认证 API：注册 / 登录 / 当前用户"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import AuthenticationError, DuplicateError
from app.core.security import (
    create_access_token, get_current_user, hash_password,
    user_to_dict, verify_password,
)
from app.models.database_models import User
from app.models.schemas import APIResponse

router = APIRouter(tags=["用户认证"])


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=30, description="登录名")
    password: str = Field(..., min_length=6, max_length=64, description="密码(至少6位)")
    nickname: str = Field(None, max_length=30, description="昵称")
    email: str = Field(None, max_length=100, description="邮箱")


class LoginRequest(BaseModel):
    username: str = Field(..., description="登录名")
    password: str = Field(..., description="密码")


def _auth_payload(user: User) -> dict:
    token = create_access_token(user.id, user.username)
    return {"token": token, "token_type": "bearer", "user": user_to_dict(user)}


@router.post("/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """注册新用户"""
    name = req.username.strip()
    if db.query(User).filter(User.username == name).first():
        raise DuplicateError("用户名已被占用")
    if req.email and db.query(User).filter(User.email == req.email).first():
        raise DuplicateError("邮箱已被注册")
    user = User(
        username=name,
        password_hash=hash_password(req.password),
        nickname=(req.nickname or name).strip(),
        email=req.email,
        role="user",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return APIResponse(message="注册成功", data=_auth_payload(user))


@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """登录并签发 JWT"""
    user = db.query(User).filter(User.username == req.username.strip()).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise AuthenticationError("用户名或密码错误")
    if not user.is_active:
        raise AuthenticationError("用户已被禁用")
    return APIResponse(message="登录成功", data=_auth_payload(user))


@router.get("/me")
def me(current: User = Depends(get_current_user)):
    """获取当前登录用户信息"""
    return APIResponse(message="获取成功", data=user_to_dict(current))
