"""FastAPI 应用入口。"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.api import auth, users, balance, transactions, funders, activities, votes, reports
from app.services.scheduler import start_scheduler


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
        start_scheduler()

    @app.get("/")
    def root():
        return {"app": settings.APP_NAME, "docs": "/docs"}

    return app


app = create_app()
