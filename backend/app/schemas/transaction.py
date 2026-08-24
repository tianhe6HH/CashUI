"""记账相关 Pydantic 模型。"""
from datetime import datetime

from pydantic import BaseModel, Field


class TransactionCreate(BaseModel):
    type: str  # income（收入） / expense（支出）
    amount: float = Field(gt=0)
    account_id: int  # 科目，必填
    funder_id: int | None = None  # 收入时必填
    activity_id: int | None = None
    note: str = ""


class TransactionOut(BaseModel):
    id: int
    type: str
    amount: float
    account_id: int
    account_name: str | None = None
    funder_id: int | None
    funder_name: str | None = None
    activity_id: int | None
    note: str
    created_at: datetime

    class Config:
        from_attributes = True


class TransactionPage(BaseModel):
    """分页查询结果。"""

    total: int
    page: int
    page_size: int
    items: list[TransactionOut]
