"""M06 管理员接口：用户管理与审计日志。"""
import json
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, func, or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import NotFoundError, ValidationError
from app.core.security import require_admin, user_to_dict
from app.models.database_models import AuditLog, User
from app.models.schemas import (
    APIResponse,
    AdminRoleUpdateRequest,
    AdminStatusUpdateRequest,
)

router = APIRouter(tags=["系统管理"])


def _page_payload(items, total: int, page: int, page_size: int) -> dict:
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if total else 0,
    }


def _get_user(db: Session, user_id: int) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundError(f"用户ID {user_id} 不存在")
    return user


def _active_admin_count(db: Session) -> int:
    return (
        db.query(func.count(User.id))
        .filter(User.role == "admin", User.is_active.is_(True))
        .scalar()
        or 0
    )


def _write_audit(
    db: Session,
    operator: User,
    action: str,
    target_type: str,
    target_id: int,
    detail: Optional[dict] = None,
) -> None:
    db.add(
        AuditLog(
            operator_id=operator.id,
            operator_name=operator.username,
            action=action,
            target_type=target_type,
            target_id=str(target_id),
            detail=json.dumps(detail or {}, ensure_ascii=False),
        )
    )


def _audit_to_dict(log: AuditLog) -> dict:
    try:
        detail = json.loads(log.detail) if log.detail else {}
    except json.JSONDecodeError:
        detail = {"raw": log.detail}
    return {
        "id": log.id,
        "operator_id": log.operator_id,
        "operator_name": log.operator_name,
        "action": log.action,
        "target_type": log.target_type,
        "target_id": log.target_id,
        "detail": detail,
        "created_at": log.created_at.isoformat() if log.created_at else None,
    }


@router.get("/users", response_model=APIResponse, summary="用户列表")
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = Query(None, description="用户名、昵称或邮箱"),
    role: Optional[str] = Query(None, pattern="^(user|admin)$"),
    is_active: Optional[bool] = Query(None),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    query = db.query(User)
    if keyword:
        text = keyword.strip()
        if text:
            pattern = f"%{text}%"
            query = query.filter(
                or_(
                    User.username.ilike(pattern),
                    User.nickname.ilike(pattern),
                    User.email.ilike(pattern),
                )
            )
    if role:
        query = query.filter(User.role == role)
    if is_active is not None:
        query = query.filter(User.is_active.is_(is_active))

    total = query.count()
    rows = (
        query.order_by(desc(User.created_at), desc(User.id))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return APIResponse(
        message="获取成功",
        data=_page_payload(
            [user_to_dict(item) for item in rows],
            total,
            page,
            page_size,
        ),
    )


@router.get("/users/{user_id}", response_model=APIResponse, summary="用户详情")
def get_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return APIResponse(message="获取成功", data=user_to_dict(_get_user(db, user_id)))


@router.put("/users/{user_id}/role", response_model=APIResponse, summary="修改用户角色")
def update_user_role(
    user_id: int,
    request: AdminRoleUpdateRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    target = _get_user(db, user_id)
    if target.id == current_user.id and request.role != "admin":
        raise ValidationError("不能降低当前登录管理员自己的角色")
    if (
        target.role == "admin"
        and request.role != "admin"
        and _active_admin_count(db) <= 1
    ):
        raise ValidationError("系统必须至少保留一名启用状态的管理员")
    if target.role == request.role:
        return APIResponse(message="用户角色未变化", data=user_to_dict(target))

    old_role = target.role
    target.role = request.role
    _write_audit(
        db,
        current_user,
        "change_role",
        "user",
        target.id,
        {"old_role": old_role, "new_role": request.role},
    )
    db.commit()
    db.refresh(target)
    return APIResponse(message="用户角色更新成功", data=user_to_dict(target))


@router.put("/users/{user_id}/status", response_model=APIResponse, summary="启用或禁用用户")
def update_user_status(
    user_id: int,
    request: AdminStatusUpdateRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    target = _get_user(db, user_id)
    if target.id == current_user.id and not request.is_active:
        raise ValidationError("不能禁用当前登录账号")
    if (
        target.role == "admin"
        and target.is_active
        and not request.is_active
        and _active_admin_count(db) <= 1
    ):
        raise ValidationError("系统必须至少保留一名启用状态的管理员")
    if bool(target.is_active) == request.is_active:
        return APIResponse(message="用户状态未变化", data=user_to_dict(target))

    target.is_active = request.is_active
    _write_audit(
        db,
        current_user,
        "enable_user" if request.is_active else "disable_user",
        "user",
        target.id,
        {"is_active": request.is_active},
    )
    db.commit()
    db.refresh(target)
    return APIResponse(
        message="用户状态更新成功",
        data=user_to_dict(target),
    )


@router.get("/audit-logs", response_model=APIResponse, summary="审计日志")
def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    action: Optional[str] = Query(None, max_length=50),
    operator_id: Optional[int] = Query(None, gt=0),
    target_type: Optional[str] = Query(None, max_length=50),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action == action.strip())
    if operator_id:
        query = query.filter(AuditLog.operator_id == operator_id)
    if target_type:
        query = query.filter(AuditLog.target_type == target_type.strip())

    total = query.count()
    rows = (
        query.order_by(desc(AuditLog.created_at), desc(AuditLog.id))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return APIResponse(
        message="获取成功",
        data=_page_payload(
            [_audit_to_dict(item) for item in rows],
            total,
            page,
            page_size,
        ),
    )
