"""数据管理工具：账号密码 + 6 类数据的导出/导入。

用法（在 backend 目录下）：
    # 单独设置/创建某个账号的密码（role 可选：admin / advanced / normal，默认 normal）
    venv\\Scripts\\python data_manager.py set 用户名 密码 [角色]

    # 批量导入账号（CSV 文件，表头：username,password,role）
    venv\\Scripts\\python data_manager.py import-accounts 文件.csv

    # 导出数据（scope 可选：all 或 accounts/funders/users/activities/transactions/votes，
    #   多个用逗号分隔）
    venv\\Scripts\\python data_manager.py export 输出.json [scope]

    # 从 JSON 文件合并追加导入数据（scope 可选，默认 all）
    venv\\Scripts\\python data_manager.py import-data 文件.json [scope]

账号 CSV 说明：
    - 表头固定为：username,password,role
    - password 留空：已存在账号不改密码；新账号使用默认密码（123456）
    - password 有值：将该账号密码设为该明文值（bcrypt 哈希后存储）
    - role 可选：admin / advanced / normal，留空默认 normal
"""
import csv
import json
import sys

from sqlalchemy import select

from app.database import SessionLocal
from app.models import User, Role
from app.core.security import hash_password
from app.config import DEFAULT_PASSWORD
from app.services.data_io import (
    ALL_SCOPES,
    export_all,
    export_scopes,
    import_all,
    import_scopes,
)

VALID_ROLES = {"admin", "advanced", "normal"}

_SCOPE_LABELS = {
    "accounts": "科目",
    "funders": "缴款人",
    "users": "账号密码",
    "activities": "活动",
    "transactions": "记账明细",
    "votes": "投票",
}


def _parse_scope(raw: str) -> list[str] | None:
    """解析 scope；'all'/空返回 None。"""
    raw = (raw or "").strip()
    if not raw or raw == "all":
        return None
    parts = [s.strip() for s in raw.split(",") if s.strip()]
    for s in parts:
        if s not in ALL_SCOPES:
            print(f"无效的 scope：{s}（可选 {', '.join(ALL_SCOPES)}）")
            sys.exit(1)
    return parts


def _parse_role(raw: str) -> str:
    role = (raw or "").strip().lower()
    return role if role in VALID_ROLES else "normal"


def _upsert_user(db, username: str, password: str, role: str) -> str:
    """创建或更新单个账号，返回结果描述。"""
    user = db.scalar(select(User).where(User.username == username))
    if user is None:
        pwd = password or DEFAULT_PASSWORD
        db.add(
            User(
                username=username,
                password_hash=hash_password(pwd),
                role=Role(role),
                display_name="",
                must_change_password=True,
            )
        )
        return f"已创建账号 {username}（角色 {role}，密码 {'(默认)' if not password else '(自定义)'}）"
    # 已存在：角色更新；密码仅在有值时更新，留空则保留原密码
    user.role = Role(role)
    if password:
        user.password_hash = hash_password(password)
        user.must_change_password = True
        user.failed_attempts = 0
        user.locked_until = None
        return f"已更新账号 {username} 的角色与密码"
    return f"已更新账号 {username} 的角色（密码未改动）"


def cmd_set(args):
    if len(args) < 2:
        print("用法：data_manager.py set 用户名 密码 [角色]")
        sys.exit(1)
    username, password = args[0], args[1]
    role = _parse_role(args[2] if len(args) > 2 else "")
    db = SessionLocal()
    try:
        msg = _upsert_user(db, username, password, role)
        db.commit()
        print(msg)
    finally:
        db.close()


def cmd_import_accounts(args):
    if len(args) < 1:
        print("用法：data_manager.py import-accounts 文件.csv")
        sys.exit(1)
    path = args[0]
    db = SessionLocal()
    try:
        with open(path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames or "username" not in reader.fieldnames:
                print("CSV 缺少表头 username，请检查文件格式")
                sys.exit(1)
            count = 0
            for row in reader:
                username = (row.get("username") or "").strip()
                if not username:
                    continue
                password = (row.get("password") or "").strip()
                role = _parse_role(row.get("role"))
                msg = _upsert_user(db, username, password, role)
                print(msg)
                count += 1
            db.commit()
        print(f"共处理 {count} 个账号")
    finally:
        db.close()


def cmd_export(args):
    if len(args) < 1:
        print("用法：data_manager.py export 输出.json [scope]")
        sys.exit(1)
    path = args[0]
    scopes = _parse_scope(args[1] if len(args) > 1 else "all")
    db = SessionLocal()
    try:
        data = export_all(db) if scopes is None else export_scopes(db, scopes)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        keys = [k for k in data.keys() if k in _SCOPE_LABELS]
        summary = "、".join(f"{_SCOPE_LABELS[k]} {len(data[k])}" for k in keys)
        print(f"已导出：{summary} → {path}")
    finally:
        db.close()


def cmd_import_data(args):
    if len(args) < 1:
        print("用法：data_manager.py import-data 文件.json [scope]")
        sys.exit(1)
    path = args[0]
    scopes = _parse_scope(args[1] if len(args) > 1 else "all")
    db = SessionLocal()
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        result = import_all(db, data) if scopes is None else import_scopes(db, data, scopes)
        imported = {_SCOPE_LABELS[k]: result[k] for k in result if k in _SCOPE_LABELS}
        print(f"已导入：{imported}")
        if result["skipped"]:
            print(f"跳过 {len(result['skipped'])} 条：")
            for s in result["skipped"]:
                print(f"  - {s}")
    finally:
        db.close()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    command = sys.argv[1]
    args = sys.argv[2:]
    if command == "set":
        cmd_set(args)
    elif command == "import-accounts":
        cmd_import_accounts(args)
    elif command == "export":
        cmd_export(args)
    elif command == "import-data":
        cmd_import_data(args)
    else:
        print(f"未知命令：{command}\n")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
