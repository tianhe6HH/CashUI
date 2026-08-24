"""结余与科目接口：所有账号均可查看。"""
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Account, Transaction, TransactionType
from app.core.deps import get_current_user, require_admin
from app.schemas.common import AccountOut

router = APIRouter(tags=["结余"])


class AccountUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=32)


class TransferRequest(BaseModel):
    from_account_id: int
    to_account_id: int
    amount: float = Field(gt=0)
    note: str = ""


@router.get("/accounts", response_model=list[AccountOut])
def list_accounts(
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    """科目清单（记账下拉用）。"""
    return db.scalars(select(Account).order_by(Account.id)).all()


@router.post("/accounts", response_model=AccountOut)
def create_account(
    data: AccountUpdate,
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
):
    """新增科目（仅管理员）。"""
    if db.scalar(select(Account).where(Account.name == data.name)):
        raise HTTPException(status_code=400, detail="科目已存在")
    acc = Account(name=data.name)
    db.add(acc)
    db.commit()
    db.refresh(acc)
    return acc


@router.put("/accounts/{account_id}", response_model=AccountOut)
def update_account(
    account_id: int,
    data: AccountUpdate,
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
):
    """修改科目名称（仅管理员）。"""
    acc = db.get(Account, account_id)
    if acc is None:
        raise HTTPException(status_code=404, detail="科目不存在")
    if db.scalar(select(Account).where(Account.name == data.name, Account.id != account_id)):
        raise HTTPException(status_code=400, detail="科目名称已存在")
    acc.name = data.name
    db.commit()
    db.refresh(acc)
    return acc


@router.delete("/accounts/{account_id}")
def delete_account(
    account_id: int,
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
):
    """删除科目（仅管理员，且该科目下无交易）。"""
    acc = db.get(Account, account_id)
    if acc is None:
        raise HTTPException(status_code=404, detail="科目不存在")
    has_tx = db.scalar(
        select(Transaction.id).where(Transaction.account_id == account_id).limit(1)
    )
    if has_tx is not None:
        raise HTTPException(status_code=400, detail="该科目下存在收支记录，无法删除")
    db.delete(acc)
    db.commit()
    return {"ok": True}


@router.post("/transfer")
def transfer(
    data: TransferRequest,
    db: Session = Depends(get_db),
    admin: object = Depends(require_admin),
):
    """科目结转（仅管理员）：从转出科目转出、转入到另一科目。"""
    if data.from_account_id == data.to_account_id:
        raise HTTPException(status_code=400, detail="转出科目与转入科目不能相同")

    from_acc = db.get(Account, data.from_account_id)
    to_acc = db.get(Account, data.to_account_id)
    if from_acc is None or to_acc is None:
        raise HTTPException(status_code=400, detail="科目不存在")

    # 校验转出科目结余充足
    income = db.scalar(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.account_id == data.from_account_id,
            Transaction.type == TransactionType.income,
        )
    )
    expense = db.scalar(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.account_id == data.from_account_id,
            Transaction.type == TransactionType.expense,
        )
    )
    balance = round(float(income or 0) - float(expense or 0), 2)
    if data.amount > balance:
        raise HTTPException(
            status_code=400,
            detail=f"科目「{from_acc.name}」结余不足，当前结余 ¥{balance}",
        )

    note = data.note or f"科目结转：{from_acc.name} → {to_acc.name}"
    db.add(
        Transaction(
            type=TransactionType.expense,
            amount=data.amount,
            account_id=data.from_account_id,
            note=f"结转转出至「{to_acc.name}」{(' ' + note) if data.note else ''}",
            created_by=admin.id,
            is_transfer=True,
        )
    )
    db.add(
        Transaction(
            type=TransactionType.income,
            amount=data.amount,
            account_id=data.to_account_id,
            note=f"结转转入自「{from_acc.name}」{(' ' + note) if data.note else ''}",
            created_by=admin.id,
            is_transfer=True,
        )
    )
    db.commit()
    return {"ok": True}


@router.get("/balance")
def get_balance(
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    """总结余 + 各科目结余（可选时间段筛选）。"""
    accounts = []
    total_income = 0.0
    total_expense = 0.0
    for acc in db.scalars(select(Account).order_by(Account.id)).all():
        income_conds = [
            Transaction.account_id == acc.id,
            Transaction.type == TransactionType.income,
        ]
        expense_conds = [
            Transaction.account_id == acc.id,
            Transaction.type == TransactionType.expense,
        ]
        if start_date:
            income_conds.append(func.date(Transaction.created_at) >= start_date)
            expense_conds.append(func.date(Transaction.created_at) >= start_date)
        if end_date:
            income_conds.append(func.date(Transaction.created_at) <= end_date)
            expense_conds.append(func.date(Transaction.created_at) <= end_date)

        income = db.scalar(
            select(func.coalesce(func.sum(Transaction.amount), 0)).where(*income_conds)
        )
        expense = db.scalar(
            select(func.coalesce(func.sum(Transaction.amount), 0)).where(*expense_conds)
        )
        # 结转产生的内部调拨，不计入总收入/总支出
        transfer_income = db.scalar(
            select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                *income_conds, Transaction.is_transfer == True
            )
        )
        transfer_expense = db.scalar(
            select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                *expense_conds, Transaction.is_transfer == True
            )
        )
        income = round(float(income or 0), 2)
        expense = round(float(expense or 0), 2)
        transfer_income = round(float(transfer_income or 0), 2)
        transfer_expense = round(float(transfer_expense or 0), 2)
        total_income += income - transfer_income
        total_expense += expense - transfer_expense
        accounts.append(
            {
                "account_id": acc.id,
                "name": acc.name,
                "income": income,
                "expense": expense,
                "balance": round(income - expense, 2),
            }
        )

    return {
        "total_income": round(total_income, 2),
        "total_expense": round(total_expense, 2),
        "balance": round(total_income - total_expense, 2),
        "accounts": accounts,
    }
