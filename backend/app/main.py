"""FastAPI 应用入口。"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import settings
from app.database import Base, engine
from app.api import auth, users, balance, transactions, funders, activities, votes, reports
from app.services.scheduler import start_scheduler


def _migrate_sqlite():
    """轻量迁移：为已有 SQLite 库补充新增列（生产环境建议改用 Alembic）。"""
    if not settings.DATABASE_URL.startswith("sqlite"):
        return
    with engine.begin() as conn:
        cols = {row[1] for row in conn.execute(text("PRAGMA table_info(transactions)"))}
        if "is_transfer" not in cols:
            conn.execute(
                text(
                    "ALTER TABLE transactions ADD COLUMN is_transfer BOOLEAN NOT NULL DEFAULT 0"
                )
            )
        # 将历史结转记录标记为内部调拨（幂等）
        conn.execute(
            text(
                "UPDATE transactions SET is_transfer = 1 "
                "WHERE is_transfer = 0 AND (note LIKE '结转转出至%' OR note LIKE '结转转入自%')"
            )
        )


def create_app() -> FastAPI:
    app = FastAPI(title=settings.APP_NAME)

    # 允许前端跨域访问（开发环境）
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册路由
    prefix = settings.API_PREFIX
    app.include_router(auth.router, prefix=prefix)
    app.include_router(users.router, prefix=prefix)
    app.include_router(balance.router, prefix=prefix)
    app.include_router(transactions.router, prefix=prefix)
    app.include_router(funders.router, prefix=prefix)
    app.include_router(activities.router, prefix=prefix)
    app.include_router(votes.router, prefix=prefix)
    app.include_router(reports.router, prefix=prefix)

    @app.on_event("startup")
    def on_startup():
        # 建表（生产环境建议改用 Alembic 迁移）
        Base.metadata.create_all(bind=engine)
        _migrate_sqlite()
        start_scheduler()

    @app.get("/")
    def root():
        return {"app": settings.APP_NAME, "docs": "/docs"}

    return app


app = create_app()
