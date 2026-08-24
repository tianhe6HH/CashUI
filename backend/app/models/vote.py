"""投票模型（费用审批 / 费用结转 / 通用投票）。"""
import enum
from datetime import datetime

from sqlalchemy import (
    String,
    Boolean,
    DateTime,
    ForeignKey,
    func,
    UniqueConstraint,
    Numeric,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Vote(Base):
    """一场投票。参与人筛选、结果按角色分层可见。"""

    __tablename__ = "votes"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(128))
    # 说明：为什么支出这么多钱、预算是什么
    description: Mapped[str] = mapped_column(String(500), default="")
    # 费用科目（可选）
    account_id: Mapped[int | None] = mapped_column(
        ForeignKey("accounts.id"), nullable=True
    )
    # 支出金额（可选）
    amount: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    start_time: Mapped[datetime] = mapped_column(DateTime)
    end_time: Mapped[datetime] = mapped_column(DateTime)
    # 可勾选规则
    allow_multiselect: Mapped[bool] = mapped_column(Boolean, default=False)
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=False)
    one_vote_per_user: Mapped[bool] = mapped_column(Boolean, default=True)
    # 发起人
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    # 关系
    options = relationship("VoteOption", cascade="all, delete-orphan")
    participants = relationship("VoteParticipant", cascade="all, delete-orphan")
    account = relationship("Account", foreign_keys=[account_id])


class VoteOption(Base):
    """投票选项（发起人完全自定义）。"""

    __tablename__ = "vote_options"

    id: Mapped[int] = mapped_column(primary_key=True)
    vote_id: Mapped[int] = mapped_column(ForeignKey("votes.id"))
    text: Mapped[str] = mapped_column(String(128))
    # 选项备注（可选，空则不显示）
    note: Mapped[str] = mapped_column(String(255), default="")


class VoteParticipant(Base):
    """投票参与人（发起人筛选，必含高级账号）。"""

    __tablename__ = "vote_participants"

    id: Mapped[int] = mapped_column(primary_key=True)
    vote_id: Mapped[int] = mapped_column(ForeignKey("votes.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))


class VoteBallot(Base):
    """投票记录（匿名仅在展示层生效）。"""

    __tablename__ = "vote_ballots"
    __table_args__ = (
        UniqueConstraint("vote_id", "user_id", "option_id", name="uq_vote_user_option"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    vote_id: Mapped[int] = mapped_column(ForeignKey("votes.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    option_id: Mapped[int] = mapped_column(ForeignKey("vote_options.id"))
    # 投票备注（如「不同意」时的说明）
    note: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
