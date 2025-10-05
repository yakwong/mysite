from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class DingTalkConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.dingtalk"
    verbose_name = "钉钉集成"

    def ready(self):
        # 延迟导入，避免模型未加载
        from . import signals  # noqa: F401
        from .services.scheduler import autodiscover_schedules

        try:
            autodiscover_schedules()
        except Exception:  # pragma: no cover - 调度加载失败不应阻塞应用
            logger.exception("加载钉钉计划任务失败")
