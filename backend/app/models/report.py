"""报表模型（记录已生成的月度 Excel 报表）。"""
from datetime import datetime

from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    month: Mapped[str] = mapped_column(String(7), unique=True, index=True)  # 格式 YYYY-MM
    file_path: Mapped[str] = mapped_column(String(255))
    generated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
