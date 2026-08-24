"""重置管理员密码为默认密码（管理员忘记密码时的兜底手段）。

用法（在 backend 目录下）：
    venv\\Scripts\\python.exe reset_admin_password.py [用户名]

不传用户名时默认重置 admin 账号。
"""
import sys

from sqlalchemy import select

from app.database import SessionLocal
from app.models import User
from app.core.security import hash_password
from app.config import DEFAULT_PASSWORD


def main():
    username = sys.argv[1] if len(sys.argv) > 1 else "admin"
    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.username == username))
        if user is None:
            print(f"未找到用户：{username}")
            return
        if user.role.value != "admin":
            print(f"用户 {username} 不是管理员，拒绝重置")
            return
        user.password_hash = hash_password(DEFAULT_PASSWORD)
        user.must_change_password = True
        db.commit()
        print(f"已将管理员 {username} 的密码重置为默认密码：{DEFAULT_PASSWORD}")
        print("请立即登录并修改密码")
    finally:
        db.close()


if __name__ == "__main__":
    main()
