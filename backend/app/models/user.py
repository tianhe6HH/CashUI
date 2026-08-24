"""用户模型。"""
import enum
from datetime import datetime

from sqlalchemy import String, Enum, DateTime, func, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Role(str, enum.Enum):
    """账号角色。"""

    admin = "admin"          # 管理员
    advanced = "advanced"    # 高级账号
    normal = "normal"        # 普通账号


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(128))
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.normal)
    display_name: Mapped[str] = mapped_column(String(64), default="")
    # 是否需要强制修改密码（新建/重置后为 True，改密后为 False）
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=True)
    # 连续登录失败次数（达到阈值后临时锁定）
    failed_attempts: Mapped[int] = mapped_column(Integer, default=0)
    # 锁定截止时间（None 表示未锁定；达到 10 次后永久锁定需管理员重置）
    locked_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
