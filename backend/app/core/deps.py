"""FastAPI 依赖：获取当前用户与角色校验。"""
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.security import decode_access_token
from app.models import User
from app.config import settings

bearer_scheme = HTTPBearer(auto_error=False)


def get_client_ip(request: Request) -> str:
    """获取客户端真实 IP（兼容 Nginx 反代的 X-Forwarded-For）。"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else ""


def _ip_prefix(ip: str, segments: int = 2) -> str:
    """取 IP 前 N 段做网段级判断（IPv4 默认前两段，如 1.2.3.4 -> 1.2）。"""
    parts = ip.split(".")
    if len(parts) >= segments:
        return ".".join(parts[:segments])
    return ip  # IPv6 或异常情况，回退为完整比较


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
    request: Request = None,
) -> User:
    """解析并返回当前登录用户。"""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录"
        )
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="登录已过期"
        )

    # 可选：登录 IP 绑定（开启后，IP 网段变化则令牌失效）
    if settings.BIND_CLIENT_IP:
        token_ip = payload.get("ip")
        if token_ip:
            current_ip = get_client_ip(request)
            if _ip_prefix(token_ip) != _ip_prefix(current_ip):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="登录 IP 已变化，请重新登录",
                )

    user = db.get(User, int(payload["sub"]))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在"
        )
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    """仅管理员。"""
    if user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限"
        )
    return user


def require_advanced(user: User = Depends(get_current_user)) -> User:
    """管理员或高级账号。"""
    if user.role.value not in ("admin", "advanced"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="需要高级账号权限"
        )
    return user
