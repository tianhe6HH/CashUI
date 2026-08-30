"""出资人模型（资金来源主体：部长 / 项目经理 / PL）。"""
import enum
from datetime import datetime

from sqlalchemy import String, Enum, DateTime, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class FunderType(str, enum.Enum):
    minister = "部长"
    manager = "项目经理"
    leader = "PL"


class Funder(Base):
    __tablename__ = "funders"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    type: Mapped[FunderType] = mapped_column(Enum(FunderType))
    # 可选关联登录账号
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
