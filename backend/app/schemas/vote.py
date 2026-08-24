"""投票相关 Pydantic 模型。"""
from datetime import datetime

from pydantic import BaseModel, Field


class VoteOptionCreate(BaseModel):
    text: str = Field(min_length=1, max_length=128)
    note: str = ""


class VoteCreate(BaseModel):
    title: str = Field(min_length=1, max_length=128)
    description: str = ""
    account_id: int | None = None
    amount: float | None = None
    start_time: datetime
    end_time: datetime
    allow_multiselect: bool = False
    is_anonymous: bool = False
    one_vote_per_user: bool = True
    options: list[VoteOptionCreate]
    participant_ids: list[int] = []  # 普通账号可为空，高级账号自动参与


class VoteCast(BaseModel):
    option_ids: list[int] = Field(min_length=1)
    note: str = ""


class VoteUpdate(BaseModel):
    """发起后可修改结束时间 / 参与人。"""

    end_time: datetime | None = None
    participant_ids: list[int] | None = None


class VoteOptionOut(BaseModel):
    id: int
    text: str
    note: str = ""

    class Config:
        from_attributes = True


class VoteResultItem(BaseModel):
    option_id: int
    text: str
    count: int


class VoteOut(BaseModel):
    id: int
    title: str
    description: str
    account_id: int | None
    account_name: str | None = None
    amount: float | None
    start_time: datetime
    end_time: datetime
    allow_multiselect: bool
    is_anonymous: bool
    one_vote_per_user: bool
    created_by: int | None
    created_at: datetime
    options: list[VoteOptionOut] = []
    participant_ids: list[int] = []

    class Config:
        from_attributes = True


class VoteDetailOut(VoteOut):
    """详情：含投票权限与结果（结果按角色分层可见）。"""

    can_vote: bool = False
    has_voted: bool = False
    results_visible: bool = False
    my_option_ids: list[int] = []
    results: list[VoteResultItem] = []
