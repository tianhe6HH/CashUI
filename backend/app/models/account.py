"""科目模型（专款专用：民主生活会 / 团建 / 年末聚餐 / 其他）。"""
from datetime import datetime

from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

# 固定科目清单（「综合使用」置首）
DEFAULT_ACCOUNTS = ["综合使用", "民主生活会", "团建", "年末聚餐"]


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(32), unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
