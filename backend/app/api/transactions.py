"""记账接口：收入（缴款）/ 支出（垫付），按科目专款专用。"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, delete
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Transaction, TransactionType, Funder, Account, User
from app.core.deps import get_current_user, require_admin
from app.schemas.transaction import (
    TransactionCreate,
    TransactionOut,
    TransactionPage,
)

router = APIRouter(tags=["记账"])


def _to_out(t: Transaction) -> TransactionOut:
    out = TransactionOut.model_validate(t)
    if t.account is not None:
        out.account_name = t.account.name
    if t.funder_id is not None and t.funder is not None:
        out.funder_name = t.funder.name
    elif t.type == TransactionType.income:
        # 收入记录原本关联的缴款人被删除后，显示为「未知」
        out.funder_name = "未知"
    return out


@router.get("/transactions", response_model=TransactionPage)
def list_transactions(
    type: str | None = Query(None),
    account_id: int | None = Query(None),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """管理员 + 高级账号可查看流水（普通账号不可见收入明细）。"""
    if user.role.value not in ("admin", "advanced"):
        raise HTTPException(status_code=403, detail="仅管理员或高级账号可查看收入明细")

    conditions = []
    if type:
        conditions.append(Transaction.type == TransactionType(type))
    if account_id:
        conditions.append(Transaction.account_id == account_id)
    if start_date:
        conditions.append(func.date(Transaction.created_at) >= start_date)
    if end_date:
        conditions.append(func.date(Transaction.created_at) <= end_date)

    total = (
        db.scalar(select(func.count()).select_from(Transaction).where(*conditions))
        or 0
    )

    stmt = (
        select(Transaction)
        .options(joinedload(Transaction.account), joinedload(Transaction.funder))
        .where(*conditions)
        .order_by(Transaction.created_at.desc(), Transaction.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = db.scalars(stmt).all()
    return TransactionPage(
        total=total,
        page=page,
        page_size=page_size,
        items=[_to_out(t) for t in rows],
    )


@router.post("/transactions", response_model=TransactionOut)
def create_transaction(
    data: TransactionCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """仅管理员记账。"""
    if data.type not in ("income", "expense"):
        raise HTTPException(status_code=400, detail="无效的收支类型")

    ttype = TransactionType(data.type)

    # 科目必须存在
    account = db.get(Account, data.account_id)
    if account is None:
        raise HTTPException(status_code=400, detail="科目不存在")

    # 支出时校验科目结余是否充足
    if ttype == TransactionType.expense:
        income = db.scalar(
            select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                Transaction.account_id == data.account_id,
                Transaction.type == TransactionType.income,
            )
        )
        expense = db.scalar(
            select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                Transaction.account_id == data.account_id,
                Transaction.type == TransactionType.expense,
            )
        )
        balance = round(float(income or 0) - float(expense or 0), 2)
        if data.amount > balance:
            raise HTTPException(
                status_code=400,
                detail=f"科目「{account.name}」结余不足，当前结余 ¥{balance}，无法支出 ¥{data.amount}",
            )

    # 收入必须关联缴款人
    if ttype == TransactionType.income and data.funder_id is None:
        raise HTTPException(status_code=400, detail="收入必须选择缴款人")
    if data.funder_id is not None and db.get(Funder, data.funder_id) is None:
        raise HTTPException(status_code=400, detail="缴款人不存在")

    t = Transaction(
        type=ttype,
        amount=data.amount,
        account_id=data.account_id,
        funder_id=data.funder_id,
        activity_id=data.activity_id,
        note=data.note,
        created_by=admin.id,
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return _to_out(t)


@router.delete("/transactions/{transaction_id}")
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """删除单条收支记录（仅管理员）。"""
    t = db.get(Transaction, transaction_id)
    if t is None:
        raise HTTPException(status_code=404, detail="记录不存在")
    db.delete(t)
    db.commit()
    return {"ok": True}


@router.delete("/transactions")
def delete_transactions_range(
    start_date: str = Query(...),
    end_date: str = Query(...),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """按时间段删除收支记录（仅管理员，起止日期均必填）。"""
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="开始日期不能晚于结束日期")

    result = db.execute(
        delete(Transaction).where(
            func.date(Transaction.created_at) >= start_date,
            func.date(Transaction.created_at) <= end_date,
        )
    )
    db.commit()
    return {"deleted": result.rowcount}
