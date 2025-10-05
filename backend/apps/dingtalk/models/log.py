from __future__ import annotations

from django.db import models

from utils.models import BaseModel, UuidModel
from ..constants import SyncOperation, SyncStatus


class DingTalkSyncLog(UuidModel, BaseModel):
    """记录同步执行情况"""

    LEVEL_CHOICES = (
        ("info", "信息"),
        ("warning", "警告"),
        ("error", "错误"),
    )

    operation = models.CharField(max_length=32, choices=[(item.value, item.name) for item in SyncOperation], verbose_name="操作类型")
    status = models.CharField(max_length=16, choices=[(item.value, item.name) for item in SyncStatus], verbose_name="状态")
    level = models.CharField(max_length=16, choices=LEVEL_CHOICES, default="info", verbose_name="级别")
    message = models.CharField(max_length=512, blank=True, default="", verbose_name="消息")
    detail = models.TextField(blank=True, default="", verbose_name="详细信息")
    stats = models.JSONField(default=dict, blank=True, verbose_name="统计数据")
    config = models.ForeignKey("DingTalkConfig", on_delete=models.CASCADE, related_name="sync_logs", verbose_name="所属配置")
    retry_count = models.PositiveIntegerField(default=0, verbose_name="重试次数")
    next_retry_at = models.DateTimeField(null=True, blank=True, verbose_name="下次重试时间")

    class Meta:
        db_table = "dingtalk_sync_log"
        verbose_name = "钉钉同步日志"
        verbose_name_plural = verbose_name
        ordering = ("-create_time",)

    def mark_failed(self, message: str, *, detail: str = "", level: str = "error", stats: dict | None = None) -> None:
        self.status = SyncStatus.FAILED.value
        self.level = level
        self.message = message
        self.detail = detail
        if stats is not None:
            self.stats = stats
        self.save(update_fields=["status", "level", "message", "detail", "stats", "update_time"])

    def mark_success(self, message: str, *, stats: dict | None = None) -> None:
        self.status = SyncStatus.SUCCESS.value
        self.level = "info"
        self.message = message
        if stats is not None:
            self.stats = stats
        self.save(update_fields=["status", "level", "message", "stats", "update_time"])
