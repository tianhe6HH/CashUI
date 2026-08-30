"""数据导出/导入服务（JSON 单文件）：支持 6 类数据的分功能/整体导出与导入。

6 类数据：
    accounts     科目
    funders      缴款人
    users        账号密码
    activities   活动
    transactions 记账明细
    votes        投票

导出时，外键一律用「业务字段」表示（科目名、缴款人名、用户名、活动名+日期），
避免跨库导入时因自增 id 不一致导致关联错乱。

导入为「合并追加」：不删除现有数据，只新增；某条数据引用的基础数据
（科目/缴款人/账号/活动）在目标库找不到时，跳过该条并记录提示。
"""
from datetime import datetime, date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Account,
    Activity,
    ActivityType,
    Funder,
    FunderType,
    Role,
    Transaction,
    TransactionType,
    User,
    Vote,
    VoteOption,
    VoteParticipant,
    VoteBallot,
)
from app.core.security import hash_password
from app.config import DEFAULT_PASSWORD

EXPORT_VERSION = 2

# 全部可导出/导入的数据类别（顺序即导入时的依赖顺序：先基础数据，后引用数据）
ALL_SCOPES = ["accounts", "funders", "users", "activities", "transactions", "votes"]


def _iso(v):
    return v.isoformat() if v is not None else None


# ---------------------------------------------------------------------------
# 导出
# ---------------------------------------------------------------------------
def _export_accounts(db: Session) -> list:
    return [
        {"name": a.name}
        for a in db.scalars(select(Account).order_by(Account.id)).all()
    ]


def _export_funders(db: Session) -> list:
    rows = []
    for f in db.scalars(select(Funder).order_by(Funder.id)).all():
        u = db.get(User, f.user_id) if f.user_id else None
        rows.append(
            {
                "name": f.name,
                "type": f.type.value,
                "username": u.username if u else None,
            }
        )
    return rows


def _export_users(db: Session) -> list:
    rows = []
    for u in db.scalars(select(User).order_by(User.id)).all():
        rows.append(
            {
                "username": u.username,
                # 数据库只存哈希，无法还原明文；密码列留空，导入时已存在账号不改密码
                "password": "",
                "role": u.role.value,
                "display_name": u.display_name or "",
            }
        )
    return rows


def _export_activities(db: Session) -> list:
    return [
        {
            "name": a.name,
            "type": a.type.value,
            "date": _iso(a.date),
            "budget": float(a.budget) if a.budget is not None else None,
            "note": a.note or "",
        }
        for a in db.scalars(select(Activity).order_by(Activity.id)).all()
    ]


def _export_transactions(db: Session) -> list:
    rows = []
    for t in db.scalars(select(Transaction).order_by(Transaction.id)).all():
        activity = db.get(Activity, t.activity_id) if t.activity_id else None
        funder = db.get(Funder, t.funder_id) if t.funder_id else None
        account = db.get(Account, t.account_id) if t.account_id else None
        created_by = db.get(User, t.created_by) if t.created_by else None
        rows.append(
            {
                "type": t.type.value,
                "amount": float(t.amount),
                "account_name": account.name if account else None,
                "funder_name": funder.name if funder else None,
                "activity_name": activity.name if activity else None,
                "activity_date": _iso(activity.date) if activity else None,
                "note": t.note or "",
                "created_by_username": created_by.username if created_by else None,
                "is_transfer": bool(t.is_transfer),
                "created_at": _iso(t.created_at),
            }
        )
    return rows


def _export_votes(db: Session) -> list:
    rows = []
    for v in db.scalars(select(Vote).order_by(Vote.id)).all():
        account = db.get(Account, v.account_id) if v.account_id else None
        created_by = db.get(User, v.created_by) if v.created_by else None
        options = db.scalars(
            select(VoteOption).where(VoteOption.vote_id == v.id).order_by(VoteOption.id)
        ).all()
        option_ids = [o.id for o in options]
        participant_usernames = []
        for p in db.scalars(
            select(VoteParticipant).where(VoteParticipant.vote_id == v.id)
        ).all():
            u = db.get(User, p.user_id)
            if u:
                participant_usernames.append(u.username)

        ballots = []
        for b in db.scalars(
            select(VoteBallot).where(VoteBallot.vote_id == v.id).order_by(VoteBallot.id)
        ).all():
            u = db.get(User, b.user_id)
            ballots.append(
                {
                    "username": u.username if u else None,
                    "option_index": option_ids.index(b.option_id) if b.option_id in option_ids else None,
                    "note": b.note or "",
                }
            )

        rows.append(
            {
                "title": v.title,
                "description": v.description or "",
                "account_name": account.name if account else None,
                "amount": float(v.amount) if v.amount is not None else None,
                "start_time": _iso(v.start_time),
                "end_time": _iso(v.end_time),
                "allow_multiselect": bool(v.allow_multiselect),
                "is_anonymous": bool(v.is_anonymous),
                "one_vote_per_user": bool(v.one_vote_per_user),
                "created_by_username": created_by.username if created_by else None,
                "options": [{"text": o.text, "note": o.note or ""} for o in options],
                "participants": participant_usernames,
                "ballots": ballots,
            }
        )
    return rows


_EXPORTERS = {
    "accounts": _export_accounts,
    "funders": _export_funders,
    "users": _export_users,
    "activities": _export_activities,
    "transactions": _export_transactions,
    "votes": _export_votes,
}


def export_scopes(db: Session, scopes: list[str]) -> dict:
    """按指定类别导出，返回 {scope: [...]}。"""
    result = {"version": EXPORT_VERSION, "exported_at": _iso(datetime.now())}
    for s in scopes:
        if s in _EXPORTERS:
            result[s] = _EXPORTERS[s](db)
    return result


def export_all(db: Session) -> dict:
    """导出全部 6 类数据。"""
    return export_scopes(db, ALL_SCOPES)


# ---------------------------------------------------------------------------
# 导入
# ---------------------------------------------------------------------------
def _match_account(db: Session, name: str):
    return db.scalar(select(Account).where(Account.name == name)) if name else None


def _match_funder(db: Session, name: str):
    return db.scalar(select(Funder).where(Funder.name == name)) if name else None


def _match_user(db: Session, username: str):
    return db.scalar(select(User).where(User.username == username)) if username else None


def _match_activity(db: Session, name: str, d: str):
    if not name:
        return None
    try:
        day = date.fromisoformat(d) if d else None
    except ValueError:
        day = None
    stmt = select(Activity).where(Activity.name == name)
    if day is not None:
        stmt = stmt.where(Activity.date == day)
    return db.scalars(stmt).first()


def _import_accounts(db: Session, data: list, skipped: list) -> int:
    count = 0
    for item in data:
        name = (item.get("name") or "").strip()
        if not name:
            skipped.append("科目（名称为空）跳过")
            continue
        if _match_account(db, name) is not None:
            continue  # 已存在，跳过
        db.add(Account(name=name))
        count += 1
    return count


def _import_funders(db: Session, data: list, skipped: list) -> int:
    count = 0
    for item in data:
        name = (item.get("name") or "").strip()
        if not name:
            skipped.append("缴款人（名称为空）跳过")
            continue
        if _match_funder(db, name) is not None:
            continue
        user = _match_user(db, item.get("username")) if item.get("username") else None
        db.add(
            Funder(
                name=name,
                type=FunderType(item.get("type") or "PL"),
                user_id=user.id if user else None,
            )
        )
        count += 1
    return count


def _import_users(db: Session, data: list, skipped: list) -> int:
    count = 0
    for item in data:
        username = (item.get("username") or "").strip()
        if not username:
            skipped.append("账号（用户名为空）跳过")
            continue
        if _match_user(db, username) is not None:
            continue  # 已存在：不改密码、不改角色
        role = item.get("role") or "normal"
        if role not in ("admin", "advanced", "normal"):
            role = "normal"
        # 密码列留空：新账号使用默认密码
        db.add(
            User(
                username=username,
                password_hash=hash_password(DEFAULT_PASSWORD),
                role=Role(role),
                display_name=item.get("display_name") or "",
                must_change_password=True,
            )
        )
        count += 1
    return count


def _import_activities(db: Session, data: list, skipped: list) -> int:
    count = 0
    for item in data:
        name = (item.get("name") or "").strip()
        d = item.get("date")
        if not name:
            skipped.append("活动（名称为空）跳过")
            continue
        if _match_activity(db, name, d) is not None:
            continue
        db.add(
            Activity(
                name=name,
                type=ActivityType(item.get("type") or "其他"),
                date=date.fromisoformat(d) if d else date.today(),
                budget=item.get("budget"),
                note=item.get("note", ""),
            )
        )
        count += 1
    return count


def _import_transactions(db: Session, data: list, skipped: list) -> int:
    count = 0
    for item in data:
        try:
            account = _match_account(db, item.get("account_name"))
            if account is None:
                raise ValueError(f"科目「{item.get('account_name')}」不存在")

            funder = _match_funder(db, item.get("funder_name")) if item.get("funder_name") else None
            if item.get("funder_name") and funder is None:
                raise ValueError(f"缴款人「{item.get('funder_name')}」不存在")

            activity = None
            if item.get("activity_name"):
                activity = _match_activity(db, item.get("activity_name"), item.get("activity_date"))
                if activity is None:
                    raise ValueError(f"活动「{item.get('activity_name')}」不存在")

            created_by = _match_user(db, item.get("created_by_username"))
            if item.get("created_by_username") and created_by is None:
                raise ValueError(f"操作人「{item.get('created_by_username')}」不存在")

            ttype = TransactionType(item.get("type") or "expense")
            amount = float(item.get("amount") or 0)
            note = item.get("note", "") or ""
            created_at = item.get("created_at")

            # 去重：类型+金额+科目+缴款人+备注+时间戳完全一致视为重复
            dup_conds = [
                Transaction.type == ttype,
                Transaction.amount == amount,
                Transaction.account_id == account.id,
                Transaction.funder_id == (funder.id if funder else None),
                Transaction.note == note,
            ]
            if created_at:
                dup_conds.append(Transaction.created_at == created_at)
            if db.scalar(select(Transaction.id).where(*dup_conds).limit(1)) is not None:
                continue  # 已存在，跳过

            db.add(
                Transaction(
                    type=ttype,
                    amount=amount,
                    account_id=account.id,
                    funder_id=funder.id if funder else None,
                    activity_id=activity.id if activity else None,
                    note=note,
                    created_by=created_by.id if created_by else None,
                    is_transfer=bool(item.get("is_transfer")),
                )
            )
            count += 1
        except Exception as e:  # noqa: BLE001
            skipped.append(f"记账（金额 {item.get('amount')}）跳过：{e}")
    return count


def _import_votes(db: Session, data: list, skipped: list) -> int:
    count = 0
    for item in data:
        try:
            account = _match_account(db, item.get("account_name")) if item.get("account_name") else None
            if item.get("account_name") and account is None:
                raise ValueError(f"科目「{item.get('account_name')}」不存在")

            created_by = _match_user(db, item.get("created_by_username"))
            if item.get("created_by_username") and created_by is None:
                raise ValueError(f"发起人「{item.get('created_by_username')}」不存在")

            title = item.get("title", "")
            start_time = datetime.fromisoformat(item.get("start_time"))
            end_time = datetime.fromisoformat(item.get("end_time"))

            # 去重：标题+开始时间+结束时间一致视为重复
            dup = db.scalar(
                select(Vote.id).where(
                    Vote.title == title,
                    Vote.start_time == start_time,
                    Vote.end_time == end_time,
                ).limit(1)
            )
            if dup is not None:
                continue  # 已存在，跳过

            v = Vote(
                title=title,
                description=item.get("description", ""),
                account_id=account.id if account else None,
                amount=item.get("amount"),
                start_time=start_time,
                end_time=end_time,
                allow_multiselect=bool(item.get("allow_multiselect")),
                is_anonymous=bool(item.get("is_anonymous")),
                one_vote_per_user=bool(item.get("one_vote_per_user")),
                created_by=created_by.id if created_by else None,
            )
            db.add(v)
            db.flush()

            options = []
            for o in item.get("options", []):
                opt = VoteOption(vote_id=v.id, text=o.get("text", ""), note=o.get("note", ""))
                db.add(opt)
                db.flush()
                options.append(opt)

            for uname in item.get("participants", []):
                u = _match_user(db, uname)
                if u is None:
                    skipped.append(f"投票「{item.get('title')}」参与人「{uname}」不存在，跳过该参与人")
                    continue
                db.add(VoteParticipant(vote_id=v.id, user_id=u.id))

            for b in item.get("ballots", []):
                u = _match_user(db, b.get("username"))
                idx = b.get("option_index")
                if u is None or idx is None or idx >= len(options):
                    skipped.append(
                        f"投票「{item.get('title')}」选票（用户 {b.get('username')}）无法匹配，跳过"
                    )
                    continue
                db.add(
                    VoteBallot(
                        vote_id=v.id,
                        user_id=u.id,
                        option_id=options[idx].id,
                        note=b.get("note", ""),
                    )
                )
            count += 1
        except Exception as e:  # noqa: BLE001
            skipped.append(f"投票「{item.get('title')}」跳过：{e}")
    return count


_IMPORTERS = {
    "accounts": _import_accounts,
    "funders": _import_funders,
    "users": _import_users,
    "activities": _import_activities,
    "transactions": _import_transactions,
    "votes": _import_votes,
}


def import_scopes(db: Session, data: dict, scopes: list[str]) -> dict:
    """按指定类别合并追加导入，返回各类别导入数量与跳过提示。"""
    skipped = []
    stats = {}
    for s in scopes:
        if s in _IMPORTERS and s in data:
            stats[s] = _IMPORTERS[s](db, data[s], skipped)
        else:
            stats[s] = 0
    db.commit()
    stats["skipped"] = skipped
    return stats


def import_all(db: Session, data: dict) -> dict:
    """整体导入：根据 data 中实际存在的 key 按依赖顺序导入。"""
    scopes = [s for s in ALL_SCOPES if s in data]
    return import_scopes(db, data, scopes)
