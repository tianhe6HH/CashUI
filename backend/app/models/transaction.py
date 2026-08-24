"""记账模型（收入 / 支出，按科目专款专用）。"""
import enum
from datetime import datetime

from sqlalchemy import String, Enum, DateTime, func, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TransactionType(str, enum.Enum):
    income = "income"    # 收入（缴款）
    expense = "expense"  # 支出（垫付）


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[TransactionType] = mapped_column(Enum(TransactionType))
    amount: Mapped[float] = mapped_column(Numeric(12, 2))
    # 科目：民主生活会 / 团建 / 年末聚餐 / 其他（专款专用）
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"))
    # 收入时必填：缴款人（谁缴的款）
    funder_id: Mapped[int | None] = mapped_column(
        ForeignKey("funders.id"), nullable=True
    )
    # 可选关联活动
    activity_id: Mapped[int | None] = mapped_column(
        ForeignKey("activities.id"), nullable=True
    )
    note: Mapped[str] = mapped_column(String(255), default="")
    # 操作人
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    # 关系
    account = relationship("Account")
    funder = relationship("Funder")
