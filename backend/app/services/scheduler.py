"""定时任务：每月自动生成上月报表。"""
import logging
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler

from app.services.report import generate_monthly_report

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def _job():
    """生成上一个月的报表。"""
    now = datetime.now()
    y, m = now.year, now.month
    if m == 1:
        y, m = y - 1, 12
    else:
        m -= 1
    month = f"{y}-{m:02d}"
    try:
        generate_monthly_report(month)
        logger.info("已自动生成报表：%s", month)
    except Exception as e:  # noqa: BLE001
        logger.error("生成报表失败：%s - %s", month, e)


def start_scheduler():
    """启动后台调度器（每月 1 号 00:00 执行）。"""
    global _scheduler
    if _scheduler is not None:
        return
    _scheduler = BackgroundScheduler()
    _scheduler.add_job(_job, "cron", day=1, hour=0, minute=0)
    _scheduler.start()
    logger.info("定时任务已启动")
