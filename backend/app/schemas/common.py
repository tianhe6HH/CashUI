"""科目、活动与缴款人 Pydantic 模型。"""
from datetime import date, datetime

from pydantic import BaseModel, Field


class AccountOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class ActivityCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    type: str  # 民主生活会 / 团建 / 年末聚餐 / 其他
    date: date
    budget: float | None = None
    note: str = ""


class ActivityOut(BaseModel):
    id: int
    name: str
    type: str
    date: date
    budget: float | None
    note: str
    created_at: datetime

    class Config:
        from_attributes = True


class FunderCreate(BaseModel):
    user_id: int  # 从已有账号中选择
    type: str  # 部长 / 项目经理 / PL


class FunderUpdate(BaseModel):
    type: str | None = None  # 部长 / 项目经理 / PL
    user_id: int | None = None  # 可选更换关联账号


class FunderOut(BaseModel):
    id: int
    name: str
    type: str
    user_id: int | None

    class Config:
        from_attributes = True
