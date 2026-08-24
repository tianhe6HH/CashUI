"""活动模型（民主生活会 / 团建 / 年末聚餐）。"""
import enum
from datetime import datetime, date

from sqlalchemy import String, Enum, DateTime, Date, func, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ActivityType(str, enum.Enum):
    meeting = "民主生活会"
    team_building = "团建"
    dinner = "年末聚餐"
    other = "其他"


class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    type: Mapped[ActivityType] = mapped_column(Enum(ActivityType))
    date: Mapped[date] = mapped_column(Date)
    budget: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    note: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
