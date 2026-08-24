"""活动接口：民主生活会 / 团建 / 年末聚餐。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Activity, ActivityType, User
from app.core.deps import get_current_user, require_advanced
from app.schemas.common import ActivityCreate, ActivityOut

router = APIRouter(tags=["活动"])


@router.get("/activities", response_model=list[ActivityOut])
def list_activities(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return db.scalars(
        select(Activity).order_by(Activity.date.desc())
    ).all()


@router.post("/activities", response_model=ActivityOut)
def create_activity(
    data: ActivityCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_advanced),
):
    if data.type not in ("民主生活会", "团建", "年末聚餐", "其他"):
        raise HTTPException(status_code=400, detail="无效的活动类型")

    # 业务规则：举办团建的当月，不开当月民主生活会
    if data.type == "团建":
        month = data.date.strftime("%Y-%m")
        conflict = db.scalar(
            select(Activity).where(
                Activity.type == ActivityType.meeting,
                func.strftime("%Y-%m", Activity.date) == month,
            )
        )
        if conflict is not None:
            raise HTTPException(
                status_code=400,
                detail=f"该月（{month}）已安排民主生活会，举办团建的当月不开例会",
            )

    a = Activity(
        name=data.name,
        type=ActivityType(data.type),
        date=data.date,
        budget=data.budget,
        note=data.note,
    )
    db.add(a)
    db.commit()
    db.refresh(a)
    return a
