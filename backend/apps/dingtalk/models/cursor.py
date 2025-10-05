from __future__ import annotations

from django.db import models

from utils.models import BaseModel


class SyncCursor(BaseModel):
    """记录增量同步游标"""

    TYPE_CHOICES = (
        ("department", "部门"),
        ("user", "用户"),
        ("attendance", "考勤"),
    )

    config = models.ForeignKey("DingTalkConfig", on_delete=models.CASCADE, related_name="sync_cursors")
    cursor_type = models.CharField(max_length=16, choices=TYPE_CHOICES)
    value = models.CharField(max_length=255, blank=True, default="")
    extra = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "dingtalk_sync_cursor"
        unique_together = ("config", "cursor_type")
        verbose_name = "钉钉同步游标"
        verbose_name_plural = verbose_name

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.config_id}:{self.cursor_type}={self.value}"
