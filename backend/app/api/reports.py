"""报表接口：管理员 + 高级账号可下载。"""
import re

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Report, User
from app.core.deps import require_advanced
from app.services.report import generate_monthly_report

router = APIRouter(tags=["报表"])

_MONTH_RE = re.compile(r"^\d{4}-\d{2}$")


@router.get("/reports")
def list_reports(
    db: Session = Depends(get_db),
    _: User = Depends(require_advanced),
):
    reports = db.scalars(
        select(Report).order_by(Report.month.desc())
    ).all()
    return [
        {"month": r.month, "generated_at": r.generated_at} for r in reports
    ]


@router.post("/reports/{month}/generate")
def generate_report(
    month: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_advanced),
):
    """按需生成指定月份报表。"""
    if not _MONTH_RE.match(month):
        raise HTTPException(status_code=400, detail="月份格式应为 YYYY-MM")
    generate_monthly_report(month)
    return {"ok": True, "month": month}


@router.get("/reports/{month}/download")
def download_report(
    month: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_advanced),
):
    """下载指定月份报表，若不存在则即时生成。"""
    if not _MONTH_RE.match(month):
        raise HTTPException(status_code=400, detail="月份格式应为 YYYY-MM")
    report = db.scalar(select(Report).where(Report.month == month))
    if report is None:
        generate_monthly_report(month)
        report = db.scalar(select(Report).where(Report.month == month))

    import os

    if report is None or not os.path.exists(report.file_path):
        raise HTTPException(status_code=404, detail="报表文件不存在")
    return FileResponse(
        report.file_path,
        filename=f"备用金报表-{month}.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
