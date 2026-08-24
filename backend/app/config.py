"""应用配置。"""
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """全局配置，可通过环境变量或 .env 覆盖。"""

    # 应用
    APP_NAME: str = "备用金管理系统"
    API_PREFIX: str = "/api"

    # 数据库（默认使用项目根目录下的 cashui.db）
    DATABASE_URL: str = "sqlite:///./cashui.db"

    # JWT 密钥（生产环境务必通过环境变量覆盖为随机长字符串）
    SECRET_KEY: str = "change-me-to-a-long-random-secret"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 默认 24 小时

    # 报表输出目录
    REPORT_DIR: str = str(Path(__file__).resolve().parent.parent / "reports")

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

# 所有账号的默认密码（新建 / 重置时使用）
DEFAULT_PASSWORD = "xglsmc123."
