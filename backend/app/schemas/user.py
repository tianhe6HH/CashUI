"""用户相关 Pydantic 模型。"""
from datetime import datetime

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str
    password: str


class UserCreate(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = ""  # 留空则使用默认密码
    role: str = "normal"  # admin / advanced / normal
    display_name: str = ""


class ImportUser(BaseModel):
    """批量导入的单个账号。"""

    username: str = Field(min_length=1, max_length=64)
    role: str = "normal"


class ChangePasswordRequest(BaseModel):
    new_password: str = Field(min_length=6)


class BatchUpdateRequest(BaseModel):
    user_ids: list[int]
    role: str  # advanced / normal


class BatchIdsRequest(BaseModel):
    user_ids: list[int]


class UserOut(BaseModel):
    id: int
    username: str
    role: str
    display_name: str
    must_change_password: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
