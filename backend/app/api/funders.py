"""缴款人接口（资金来源主体：部长 / 项目经理 / PL）。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Funder, FunderType, Transaction, TransactionType, User
from app.core.deps import require_advanced
from app.schemas.common import FunderCreate, FunderOut, FunderUpdate

router = APIRouter(tags=["缴款人"])


@router.get("/funders", response_model=list[FunderOut])
def list_funders(
    db: Session = Depends(get_db),
    _: User = Depends(require_advanced),
):
    return db.scalars(select(Funder).order_by(Funder.id)).all()


@router.post("/funders", response_model=FunderOut)
def create_funder(
    data: FunderCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_advanced),
):
    """新增缴款人：从已有账号中选择。"""
    if data.type not in ("部长", "项目经理", "PL"):
        raise HTTPException(status_code=400, detail="无效的缴款人类型")
    user = db.get(User, data.user_id)
    if user is None:
        raise HTTPException(status_code=400, detail="账号不存在")
    if db.scalar(select(Funder).where(Funder.user_id == data.user_id)):
        raise HTTPException(status_code=400, detail="该账号已是缴款人")
    f = Funder(name=user.username, type=FunderType(data.type), user_id=user.id)
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


@router.put("/funders/{funder_id}", response_model=FunderOut)
def update_funder(
    funder_id: int,
    data: FunderUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_advanced),
):
    """修改缴款人：类型或关联账号。"""
    f = db.get(Funder, funder_id)
    if f is None:
        raise HTTPException(status_code=404, detail="缴款人不存在")

    if data.type is not None:
        if data.type not in ("部长", "项目经理", "PL"):
            raise HTTPException(status_code=400, detail="无效的缴款人类型")
        f.type = FunderType(data.type)

    if data.user_id is not None:
        user = db.get(User, data.user_id)
        if user is None:
            raise HTTPException(status_code=400, detail="账号不存在")
        dup = db.scalar(
            select(Funder).where(Funder.user_id == data.user_id, Funder.id != funder_id)
        )
        if dup is not None:
            raise HTTPException(status_code=400, detail="该账号已是缴款人")
        f.user_id = user.id
        f.name = user.username

    db.commit()
    db.refresh(f)
    return f


@router.delete("/funders/{funder_id}")
def delete_funder(
    funder_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_advanced),
):
    """删除缴款人：其历史收入记录的缴款人置为空（前端显示为「未知」）。"""
    f = db.get(Funder, funder_id)
    if f is None:
        raise HTTPException(status_code=404, detail="缴款人不存在")

    # 该缴款人关联的收入记录，缴款人置空
    income_count = db.scalar(
        select(func.count()).select_from(Transaction).where(
            Transaction.funder_id == funder_id
        )
    ) or 0

    for t in db.scalars(
        select(Transaction).where(Transaction.funder_id == funder_id)
    ).all():
        t.funder_id = None

    db.delete(f)
    db.commit()
    return {"ok": True, "affected_income": income_count}


@router.get("/funders/detail")
def funder_detail(
    db: Session = Depends(get_db),
    _: User = Depends(require_advanced),
):
    """每个缴款人的累计缴款额。"""
    rows = db.execute(
        select(
            Funder.id,
            Funder.name,
            Funder.type,
            Funder.user_id,
            func.coalesce(func.sum(Transaction.amount), 0).label("total"),
        )
        .outerjoin(
            Transaction,
            (Transaction.funder_id == Funder.id)
            & (Transaction.type == TransactionType.income),
        )
        .group_by(Funder.id)
    ).all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "type": r.type,
            "user_id": r.user_id,
            "total": round(float(r.total), 2),
        }
        for r in rows
    ]
