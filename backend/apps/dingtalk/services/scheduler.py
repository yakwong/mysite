"""计划任务调度适配层

默认提供空实现，项目可根据需要接入 Celery beat / APScheduler / Django-Q 等调度器。
"""

from __future__ import annotations

import logging
from typing import Iterable

from django.conf import settings
from django.db import connections
from django.db.utils import OperationalError, ProgrammingError
from django.utils import timezone

from ..models import DingTalkConfig
from .sync import SyncService

logger = logging.getLogger(__name__)


def autodiscover_schedules() -> None:
    """应用初始化时调用，针对启用的配置自动注册计划任务。

    默认实现仅打印日志，避免强绑定具体调度框架。
    使用者可在此函数中接入实际调度器。
    """

    try:
        # 在迁移阶段可能尚未创建表
        with connections["default"].cursor() as cursor:
            cursor.execute("SELECT 1 FROM dingtalk_config LIMIT 1")
    except (OperationalError, ProgrammingError):  # pragma: no cover - 仅在迁移阶段触发
        logger.debug("钉钉配置表尚未准备好，跳过计划任务加载")
        return

    configs = DingTalkConfig.enabled_configs()
    for config in configs:
        schedule = config.schedule or {}
        if not schedule:
            continue
        logger.info("检测到钉钉计划任务配置 config=%s schedule=%s（需要自行接入调度器）", config.id, schedule)


def run_scheduled_sync(config_id: str, operations: Iterable[str]) -> None:
    """供外部调度器调用的入口"""

    service = SyncService(DingTalkConfig.load(config_id))
    op_set = set(operations)
    if "departments" in op_set:
        service.sync_departments()
    if "users" in op_set:
        service.sync_users()
    if "attendance" in op_set:
        schedule = service.config.schedule or {}
        window = schedule.get("attendance_window", 1)
        end = settings.TIME_ZONE and timezone.now() or timezone.now()
        start = end - timezone.timedelta(days=window)
        service.sync_attendance(start, end)
