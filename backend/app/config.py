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

    # 所有账号的默认密码（新建/重置时使用）。
    # 为避免开源泄露，默认密码不硬编码在代码里，必须在 .env 中配置；
    # 未配置时，init_db 会生成随机密码并打印。
    DEFAULT_PASSWORD: str = ""

    # 是否启用「登录 IP 绑定」：开启后，登录时的 IP 发生变化会导致令牌失效，
    # 需重新登录。手机网络切换会导致 IP 变化，请谨慎开启。
    BIND_CLIENT_IP: bool = False

    # 报表输出目录
    REPORT_DIR: str = str(Path(__file__).resolve().parent.parent / "reports")

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

# 默认密码（从 .env 读取；为空时由 init_db 生成随机密码）
DEFAULT_PASSWORD = settings.DEFAULT_PASSWORD

