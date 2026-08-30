"""账号管理接口：仅管理员。"""
import csv
import io
import secrets

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select, delete
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Role, Funder, VoteParticipant, VoteBallot
from app.core.security import hash_password
from app.core.deps import require_admin, get_current_user
from app.config import DEFAULT_PASSWORD
from app.schemas.user import (
    UserCreate,
    UserOut,
    ImportUser,
    BatchUpdateRequest,
    BatchIdsRequest,
)

router = APIRouter(tags=["账号管理"])


def _default_password() -> str:
    """默认密码：优先 .env 配置，未配置则生成随机密码。"""
    return DEFAULT_PASSWORD or secrets.token_urlsafe(8)


def _validate_role(role: str):
    if role not in ("admin", "advanced", "normal"):
        raise HTTPException(status_code=400, detail="无效的角色")


def _new_user(username: str, password: str, role: str) -> User:
    """创建用户对象，密码留空时用默认密码。"""
    pwd = password or _default_password()
    return User(
        username=username,
        password_hash=hash_password(pwd),
        role=Role(role),
        display_name="",
        must_change_password=True,
    )


@router.get("/users", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return db.scalars(select(User).order_by(User.id)).all()


@router.get("/users/selectable")
def selectable_users(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """供投票参与人筛选的轻量用户列表（所有登录账号可用）。"""
    users = db.scalars(select(User).order_by(User.id)).all()
    return [
        {"id": u.id, "username": u.username, "role": u.role.value}
        for u in users
    ]


@router.post("/users", response_model=UserOut)
def create_user(
    data: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    _validate_role(data.role)
    if db.scalar(select(User).where(User.username == data.username)):
        raise HTTPException(status_code=400, detail="用户名已存在")
    user = _new_user(data.username, data.password, data.role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.put("/users/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    data: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """修改账号（含权限切换）。"""
    _validate_role(data.role)
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.role = Role(data.role)
    if data.password:
        user.password_hash = hash_password(data.password)
        user.must_change_password = True
    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="不能删除自己")
    _cleanup_user_related(db, user_id)
    db.delete(user)
    db.commit()
    return {"ok": True}


def _cleanup_user_related(db: Session, user_id: int):
    """删除账号时，级联清理关联的缴款人、投票参与、投票记录。"""
    db.execute(delete(Funder).where(Funder.user_id == user_id))
    db.execute(delete(VoteParticipant).where(VoteParticipant.user_id == user_id))
    db.execute(delete(VoteBallot).where(VoteBallot.user_id == user_id))


@router.post("/users/{user_id}/reset-password")
def reset_password(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """重置为默认密码，并强制下次登录改密。"""
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    pwd = _default_password()
    user.password_hash = hash_password(pwd)
    user.must_change_password = True
    user.failed_attempts = 0
    user.locked_until = None
    db.commit()
    return {"ok": True, "default_password": pwd}


@router.post("/users/batch-update")
def batch_update(
    data: BatchUpdateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """批量修改角色（普通账号 ↔ 高级账号）。"""
    if data.role not in ("advanced", "normal"):
        raise HTTPException(status_code=400, detail="批量修改仅支持普通/高级账号")
    for uid in data.user_ids:
        user = db.get(User, uid)
        if user is not None and user.role.value != "admin":
            user.role = Role(data.role)
    db.commit()
    return {"ok": True, "count": len(data.user_ids)}


@router.post("/users/batch-reset-password")
def batch_reset_password(
    data: BatchIdsRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """批量重置密码为默认密码（不含管理员）。"""
    pwd = _default_password()
    count = 0
    for uid in data.user_ids:
        user = db.get(User, uid)
        if user is not None and user.role.value != "admin":
            user.password_hash = hash_password(pwd)
            user.must_change_password = True
            user.failed_attempts = 0
            user.locked_until = None
            count += 1
    db.commit()
    return {"ok": True, "count": count, "default_password": pwd}


@router.post("/users/batch-delete")
def batch_delete(
    data: BatchIdsRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """批量删除账号（不含管理员）。"""
    count = 0
    for uid in data.user_ids:
        user = db.get(User, uid)
        if user is not None and user.role.value != "admin":
            _cleanup_user_related(db, uid)
            db.delete(user)
            count += 1
    db.commit()
    return {"ok": True, "count": count}


@router.post("/users/import", response_model=list[UserOut])
def import_users(
    data: list[ImportUser],
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """批量导入账号，统一使用默认密码。"""
    created = []
    for item in data:
        _validate_role(item.role)
        if db.scalar(select(User).where(User.username == item.username)):
            continue  # 跳过已存在的用户名
        user = _new_user(item.username, "", item.role)
        db.add(user)
        created.append(user)
    db.commit()
    for u in created:
        db.refresh(u)
    return created


@router.get("/users/export")
def export_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """导出所有账号为 CSV（username,password,role），密码列填默认密码，可手动改明文后由脚本导入。"""
    users = db.scalars(select(User).order_by(User.id)).all()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["username", "password", "role"])
    for u in users:
        # 数据库只存哈希，无法还原明文，这里统一填默认密码占位；
        # 管理员可手动改成明文密码，再通过 manage_accounts.py import 写回。
        writer.writerow([u.username, DEFAULT_PASSWORD, u.role.value])
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=accounts.csv"},
    )
