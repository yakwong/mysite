"""可供 Celery/FastWorker 等任务队列调用的封装"""

from __future__ import annotations

import logging
from datetime import datetime

from django.utils import timezone

from ..models import DingTalkConfig
from .sync import SyncService

logger = logging.getLogger(__name__)


def sync_departments_task(config_id: str, *, mode: str = "full") -> dict:
    service = SyncService(DingTalkConfig.load(config_id))
    result = service.sync_departments(mode=mode)
    logger.info("钉钉部门同步完成 config=%s result=%s", config_id, result)
    return result


def sync_users_task(config_id: str, *, mode: str = "full") -> dict:
    service = SyncService(DingTalkConfig.load(config_id))
    result = service.sync_users(mode=mode)
    logger.info("钉钉用户同步完成 config=%s result=%s", config_id, result)
    return result


def sync_attendance_task(config_id: str, *, start: datetime | None = None, end: datetime | None = None) -> dict:
    service = SyncService(DingTalkConfig.load(config_id))
    end = end or timezone.now()
    start = start or (end - timezone.timedelta(days=1))
    result = service.sync_attendance(start, end)
    logger.info("钉钉考勤同步完成 config=%s start=%s end=%s result=%s", config_id, start, end, result)
    return result


def full_sync_task(config_id: str) -> dict:
    service = SyncService(DingTalkConfig.load(config_id))
    result = service.full_sync()
    logger.info("钉钉全量同步完成 config=%s result=%s", config_id, result)
    return result
