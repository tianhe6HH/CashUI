"""初始化数据库：建表、插入固定科目、创建默认管理员账号。

用法：python -m app.init_db
"""
import secrets

from sqlalchemy import select

from app.database import Base, engine, SessionLocal
from app.models import User, Role, Account, DEFAULT_ACCOUNTS
from app.core.security import hash_password
from app.config import DEFAULT_PASSWORD

DEFAULT_ADMIN_USERNAME = "admin"


def init():
    Base.metadata.create_all(bind=engine)
    # 默认密码优先取 .env 配置，未配置则生成随机密码（不硬编码，避免开源泄露）
    admin_password = DEFAULT_PASSWORD or secrets.token_urlsafe(8)

    db = SessionLocal()
    try:
        # 插入固定科目
        for name in DEFAULT_ACCOUNTS:
            if db.scalar(select(Account).where(Account.name == name)) is None:
                db.add(Account(name=name))
        db.commit()

        # 默认管理员（首次登录强制改密）
        if db.scalar(select(User).where(User.username == DEFAULT_ADMIN_USERNAME)) is None:
            db.add(
                User(
                    username=DEFAULT_ADMIN_USERNAME,
                    password_hash=hash_password(admin_password),
                    role=Role.admin,
                    display_name="管理员",
                    must_change_password=True,
                )
            )
            db.commit()
            print(f"已创建默认管理员：{DEFAULT_ADMIN_USERNAME} / {admin_password}（首次登录需改密）")
        else:
            print("默认管理员已存在，跳过")

        print(f"科目已就绪：{', '.join(DEFAULT_ACCOUNTS)}")
    finally:
        db.close()


if __name__ == "__main__":
    init()
