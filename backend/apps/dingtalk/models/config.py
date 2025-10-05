from __future__ import annotations

from django.db import models
from django.utils import timezone

from utils.models import BaseModel


class DingTalkConfig(BaseModel):
    """钉钉集成配置，兼容原有 default 单例，也支持多实例"""

    DEFAULT_ID = "default"

    id = models.CharField(primary_key=True, max_length=32, default=DEFAULT_ID, editable=True, verbose_name="配置ID")
    name = models.CharField(max_length=128, default="默认钉钉配置", verbose_name="配置名称")
    tenant_id = models.CharField(max_length=128, blank=True, default="", verbose_name="租户ID")
    app_key = models.CharField(max_length=128, blank=True, default="", verbose_name="App Key")
    app_secret = models.CharField(max_length=256, blank=True, default="", verbose_name="App Secret")
    agent_id = models.CharField(max_length=64, blank=True, default="", verbose_name="Agent ID")
    enabled = models.BooleanField(default=False, verbose_name="是否启用")
    sync_users = models.BooleanField(default=True, verbose_name="同步用户")
    sync_departments = models.BooleanField(default=True, verbose_name="同步部门")
    sync_attendance = models.BooleanField(default=False, verbose_name="同步考勤")
    callback_url = models.CharField(max_length=512, blank=True, default="", verbose_name="回调地址")
    callback_token = models.CharField(max_length=128, blank=True, default="", verbose_name="回调Token")
    callback_aes_key = models.CharField(max_length=128, blank=True, default="", verbose_name="回调AES Key")
    remark = models.TextField(blank=True, default="", verbose_name="备注")

    access_token = models.CharField(max_length=512, blank=True, default="", verbose_name="访问令牌")
    access_token_expires_at = models.DateTimeField(null=True, blank=True, verbose_name="令牌过期时间")

    last_sync_time = models.DateTimeField(null=True, blank=True, verbose_name="最近同步时间")
    last_sync_status = models.CharField(max_length=32, blank=True, default="", verbose_name="最近同步状态")
    last_sync_message = models.CharField(max_length=512, blank=True, default="", verbose_name="最近同步信息")
    last_user_sync_time = models.DateTimeField(null=True, blank=True, verbose_name="用户最近同步时间")
    last_dept_sync_time = models.DateTimeField(null=True, blank=True, verbose_name="部门最近同步时间")
    last_attendance_sync_time = models.DateTimeField(null=True, blank=True, verbose_name="考勤最近同步时间")
    last_user_sync_count = models.IntegerField(default=0, verbose_name="最近同步用户数量")
    last_dept_sync_count = models.IntegerField(default=0, verbose_name="最近同步部门数量")
    last_attendance_sync_count = models.IntegerField(default=0, verbose_name="最近同步考勤数量")

    schedule = models.JSONField(default=dict, blank=True, verbose_name="计划任务配置")

    created_by = models.CharField(max_length=128, blank=True, default="", verbose_name="创建人")
    updated_by = models.CharField(max_length=128, blank=True, default="", verbose_name="最后修改人")

    class Meta:
        db_table = "dingtalk_config"
        verbose_name = "钉钉配置"
        verbose_name_plural = verbose_name

    def __str__(self) -> str:  # pragma: no cover - 仅用作管理界面展示
        return f"{self.name}({self.id})"

    @classmethod
    def load(cls, config_id: str | None = None) -> "DingTalkConfig":
        config_id = config_id or cls.DEFAULT_ID
        obj, _ = cls.objects.get_or_create(id=config_id, defaults={"name": "默认钉钉配置"})
        return obj

    @classmethod
    def enabled_configs(cls):
        return cls.objects.filter(enabled=True)

    def reset_access_token(self) -> None:
        self.access_token = ""
        self.access_token_expires_at = None
        self.save(update_fields=["access_token", "access_token_expires_at", "update_time"])

    def update_sync_state(
        self,
        *,
        status: str,
        message: str,
        stats: dict | None = None,
        user_sync_time: timezone.datetime | None = None,
        dept_sync_time: timezone.datetime | None = None,
        attendance_sync_time: timezone.datetime | None = None,
    ) -> None:
        stats = stats or {}
        self.last_sync_status = status
        self.last_sync_message = message
        self.last_sync_time = timezone.now()
        if "user_count" in stats:
            self.last_user_sync_count = stats["user_count"]
        if "dept_count" in stats:
            self.last_dept_sync_count = stats["dept_count"]
        if "attendance_count" in stats:
            self.last_attendance_sync_count = stats["attendance_count"]
        if user_sync_time:
            self.last_user_sync_time = user_sync_time
        if dept_sync_time:
            self.last_dept_sync_time = dept_sync_time
        if attendance_sync_time:
            self.last_attendance_sync_time = attendance_sync_time
        update_fields = {
            "last_sync_status",
            "last_sync_message",
            "last_sync_time",
            "last_user_sync_count",
            "last_dept_sync_count",
            "last_attendance_sync_count",
            "update_time",
        }
        if self.last_user_sync_time:
            update_fields.add("last_user_sync_time")
        if self.last_dept_sync_time:
            update_fields.add("last_dept_sync_time")
        if self.last_attendance_sync_time:
            update_fields.add("last_attendance_sync_time")
        self.save(update_fields=list(update_fields))
