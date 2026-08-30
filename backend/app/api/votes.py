"""投票接口：所有人可发起、参与；参与人筛选、结果按角色分层。"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, delete
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    Vote,
    VoteOption,
    VoteParticipant,
    VoteBallot,
    User,
    Role,
)
from app.core.deps import get_current_user
from app.schemas.vote import (
    VoteCreate,
    VoteOut,
    VoteDetailOut,
    VoteResultItem,
    VoteOptionOut,
    VoteCast,
    VoteUpdate,
)

router = APIRouter(tags=["投票"])


def _status(v: Vote) -> str:
    now = datetime.now()
    if now < v.start_time:
        return "未开始"
    if now > v.end_time:
        return "已结束"
    return "进行中"


def _vote_out(v: Vote) -> VoteOut:
    out = VoteOut(
        id=v.id,
        title=v.title,
        description=v.description,
        account_id=v.account_id,
        account_name=v.account.name if v.account else None,
        amount=float(v.amount) if v.amount is not None else None,
        start_time=v.start_time,
        end_time=v.end_time,
        allow_multiselect=v.allow_multiselect,
        is_anonymous=v.is_anonymous,
        one_vote_per_user=v.one_vote_per_user,
        created_by=v.created_by,
        created_at=v.created_at,
        options=[VoteOptionOut.model_validate(o) for o in v.options],
        # participant_ids 仅返回发起人勾选的普通账号（高级账号自动参与，不在可编辑列表内）
        participant_ids=[
            p.user_id for p in v.participants if p.user is not None and p.user.role == Role.normal
        ],
    )
    return out


def _advanced_ids(db: Session) -> set[int]:
    return set(db.scalars(select(User.id).where(User.role == Role.advanced)).all())


def _build_participants(db: Session, participant_ids: list[int]) -> list[int]:
    """参与人 = 选中的普通账号 + 自动包含的所有高级账号（管理员不参与）。"""
    advanced_ids = _advanced_ids(db)
    if not advanced_ids:
        raise HTTPException(status_code=400, detail="系统暂无高级账号，无法发起投票")
    valid_normal = set(
        db.scalars(select(User.id).where(User.role == Role.normal)).all()
    )
    if not set(participant_ids).issubset(valid_normal):
        raise HTTPException(status_code=400, detail="包含无效的参与人")
    return list(set(participant_ids) | advanced_ids)


def _can_see_results(v: Vote, user: User) -> bool:
    """结果可见：结束后所有人可见；进行中仅高级/管理员/发起人可见。"""
    if _status(v) == "已结束":
        return True
    return user.role.value in ("admin", "advanced") or v.created_by == user.id


@router.get("/votes", response_model=list[VoteOut])
def list_votes(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    votes = db.scalars(select(Vote).order_by(Vote.created_at.desc())).all()
    return [_vote_out(v) for v in votes]


@router.post("/votes", response_model=VoteOut)
def create_vote(
    data: VoteCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """所有账号均可发起投票（高级账号自动参与、管理员不参与）。"""
    if data.end_time <= data.start_time:
        raise HTTPException(status_code=400, detail="结束时间必须晚于开始时间")
    if len(data.options) < 1:
        raise HTTPException(status_code=400, detail="至少需要一个选项")

    participant_ids = _build_participants(db, data.participant_ids)

    v = Vote(
        title=data.title,
        description=data.description,
        account_id=data.account_id,
        amount=data.amount,
        start_time=data.start_time,
        end_time=data.end_time,
        allow_multiselect=data.allow_multiselect,
        is_anonymous=data.is_anonymous,
        one_vote_per_user=data.one_vote_per_user,
        created_by=user.id,
    )
    for o in data.options:
        v.options.append(VoteOption(text=o.text, note=o.note))
    for uid in participant_ids:
        v.participants.append(VoteParticipant(user_id=uid))
    db.add(v)
    db.commit()
    db.refresh(v)
    return _vote_out(v)


@router.get("/votes/{vote_id}", response_model=VoteDetailOut)
def get_vote(
    vote_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    v = db.get(Vote, vote_id)
    if v is None:
        raise HTTPException(status_code=404, detail="投票不存在")

    detail = VoteDetailOut(
        **_vote_out(v).model_dump(),
        can_vote=False,
        has_voted=False,
        results_visible=False,
        my_option_ids=[],
        results=[],
    )

    participant_ids = {p.user_id for p in v.participants}
    status = _status(v)

    # 我的投票（普通账号进行中可看到自己的选择）
    my_ballots = db.scalars(
        select(VoteBallot).where(
            VoteBallot.vote_id == vote_id, VoteBallot.user_id == user.id
        )
    ).all()
    detail.my_option_ids = [b.option_id for b in my_ballots]
    detail.has_voted = len(my_ballots) > 0

    detail.can_vote = (
        status == "进行中"
        and user.id in participant_ids
        and (not v.one_vote_per_user or not detail.has_voted)
    )

    # 结果可见性
    detail.results_visible = _can_see_results(v, user)
    if detail.results_visible:
        counts = db.execute(
            select(VoteOption.id, VoteOption.text, func.count(VoteBallot.id))
            .outerjoin(VoteBallot, VoteBallot.option_id == VoteOption.id)
            .where(VoteOption.vote_id == vote_id)
            .group_by(VoteOption.id)
        ).all()
        detail.results = [
            VoteResultItem(option_id=r[0], text=r[1], count=r[2]) for r in counts
        ]
    return detail


@router.post("/votes/{vote_id}/cast")
def cast_vote(
    vote_id: int,
    data: VoteCast,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    v = db.get(Vote, vote_id)
    if v is None:
        raise HTTPException(status_code=404, detail="投票不存在")

    status = _status(v)
    if status != "进行中":
        raise HTTPException(status_code=400, detail=f"当前投票状态为「{status}」，无法投票")

    participant_ids = {p.user_id for p in v.participants}
    if user.id not in participant_ids:
        raise HTTPException(status_code=403, detail="您不是该投票的参与人")

    valid_ids = {
        o.id
        for o in db.scalars(
            select(VoteOption).where(VoteOption.vote_id == vote_id)
        ).all()
    }
    if not set(data.option_ids).issubset(valid_ids):
        raise HTTPException(status_code=400, detail="包含无效的选项")

    if not v.allow_multiselect and len(data.option_ids) > 1:
        raise HTTPException(status_code=400, detail="该投票不允许选择多个选项")

    if v.one_vote_per_user:
        already = db.scalar(
            select(VoteBallot).where(
                VoteBallot.vote_id == vote_id, VoteBallot.user_id == user.id
            )
        )
        if already is not None:
            raise HTTPException(status_code=400, detail="您已投过票")

    for oid in data.option_ids:
        db.add(
            VoteBallot(
                vote_id=vote_id, user_id=user.id, option_id=oid, note=data.note
            )
        )
    db.commit()
    return {"ok": True}


@router.put("/votes/{vote_id}", response_model=VoteOut)
def update_vote(
    vote_id: int,
    data: VoteUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """发起人可修改结束时间 / 参与人。"""
    v = db.get(Vote, vote_id)
    if v is None:
        raise HTTPException(status_code=404, detail="投票不存在")
    if v.created_by != user.id:
        raise HTTPException(status_code=403, detail="仅发起人可修改")

    if data.end_time is not None:
        v.end_time = data.end_time
    if data.participant_ids is not None:
        participant_ids = _build_participants(db, data.participant_ids)
        db.execute(delete(VoteParticipant).where(VoteParticipant.vote_id == vote_id))
        for uid in participant_ids:
            db.add(VoteParticipant(vote_id=vote_id, user_id=uid))
    db.commit()
    db.refresh(v)
    return _vote_out(v)


@router.delete("/votes/{vote_id}")
def delete_vote(
    vote_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """分级删除：未完成 → 高级+管理员；已完成 → 仅管理员。"""
    v = db.get(Vote, vote_id)
    if v is None:
        raise HTTPException(status_code=404, detail="投票不存在")

    status = _status(v)
    if status == "已结束":
        if user.role.value != "admin":
            raise HTTPException(status_code=403, detail="仅管理员可删除已完成的投票")
    else:
        if user.role.value not in ("admin", "advanced"):
            raise HTTPException(status_code=403, detail="仅管理员或高级账号可删除未完成的投票")

    db.execute(delete(VoteBallot).where(VoteBallot.vote_id == vote_id))
    db.execute(delete(VoteParticipant).where(VoteParticipant.vote_id == vote_id))
    db.execute(delete(VoteOption).where(VoteOption.vote_id == vote_id))
    db.delete(v)
    db.commit()
    return {"ok": True}
