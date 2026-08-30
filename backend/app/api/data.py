"""数据导出/导入接口：仅管理员。"""
import json

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.core.deps import require_admin
from app.services.data_io import (
    ALL_SCOPES,
    export_scopes,
    export_all,
    import_scopes,
    import_all,
)

router = APIRouter(tags=["数据管理"])


@router.get("/data/export")
def export_data(
    scope: str = "all",
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """导出数据为 JSON 文件下载。

    scope 可选：all（全部）或 accounts/funders/users/activities/transactions/votes（单个），
    也支持逗号分隔多个，如 scope=transactions,activities。
    """
    scopes = _parse_scopes(scope)
    data = export_all(db) if scopes is None else export_scopes(db, scopes)
    content = json.dumps(data, ensure_ascii=False, indent=2)
    return Response(
        content=content,
        media_type="application/json",
        headers={
            "Content-Disposition": "attachment; filename=cashui-data.json"
        },
    )


@router.post("/data/import")
def import_data(
    payload: dict = Body(...),
    scope: str = "all",
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """从 JSON 合并追加导入数据。

    scope 可选：all（按 payload 中实际存在的 key 导入）或指定单个/多个类别。
    """
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="数据格式应为 JSON 对象")
    scopes = _parse_scopes(scope)
    result = import_all(db, payload) if scopes is None else import_scopes(db, payload, scopes)
    return result


def _parse_scopes(scope: str) -> list[str] | None:
    """解析 scope 参数；'all' 或空返回 None 表示全部。"""
    if not scope or scope == "all":
        return None
    parts = [s.strip() for s in scope.split(",") if s.strip()]
    for s in parts:
        if s not in ALL_SCOPES:
            raise HTTPException(status_code=400, detail=f"无效的 scope：{s}")
    return parts
