"""认证接口：登录 / 登出 / 当前用户。"""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.core.security import create_access_token, verify_password, hash_password
from app.core.deps import get_current_user, get_client_ip
from app.config import settings
from app.schemas.user import LoginRequest, TokenResponse, UserOut, ChangePasswordRequest

router = APIRouter(tags=["认证"])


@router.post("/auth/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db), request: Request = None):
    user = db.scalar(select(User).where(User.username == data.username))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误"
        )

    now = datetime.now()
    # 管理员账号不应用失败锁定，避免被恶意尝试锁定后无法登录
    is_admin = user.role.value == "admin"

    if not is_admin:
        # 连续失败 10 次及以上：永久锁定，需管理员重置
        if user.failed_attempts >= 10:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="密码错误次数过多，请联系管理员重置密码",
            )

        # 临时锁定中：等待剩余时间
        if user.locked_until is not None:
            if now < user.locked_until:
                remain = int((user.locked_until - now).total_seconds())
                minutes = max(1, (remain + 59) // 60)
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"密码错误次数过多，请 {minutes} 分钟后再试",
                )
            # 锁定已到期，解除锁定
            user.locked_until = None
            db.commit()

    # 密码校验
    if not verify_password(data.password, user.password_hash):
        if not is_admin:
            user.failed_attempts += 1
            if user.failed_attempts == 3:
                user.locked_until = now + timedelta(minutes=1)
            elif user.failed_attempts >= 5:
                user.locked_until = now + timedelta(minutes=3)
            db.commit()

            if user.failed_attempts >= 10:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="密码错误次数过多，请联系管理员重置密码",
                )
            if user.failed_attempts == 3:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="密码连续错误 3 次，请 1 分钟后再试",
                )
            if user.failed_attempts == 5:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="密码连续错误 5 次，请 3 分钟后再试",
                )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误"
        )

    # 登录成功，重置失败次数与锁定
    user.failed_attempts = 0
    user.locked_until = None
    db.commit()
    ip = get_client_ip(request) if settings.BIND_CLIENT_IP else ""
    token = create_access_token(user.id, user.role.value, ip)
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.get("/auth/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.post("/auth/change-password")
def change_password(
    data: ChangePasswordRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """修改密码，并将强制改密标志置为 False。"""
    user.password_hash = hash_password(data.new_password)
    user.must_change_password = False
    db.commit()
    return {"ok": True}
