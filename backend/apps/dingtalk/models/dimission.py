"""钉钉离职人员数据模型"""

from __future__ import annotations

from django.db import models

from utils.models import BaseModel, UuidModel


class DingTalkDimissionUser(UuidModel, BaseModel):
    """钉钉离职员工快照"""

    userid = models.CharField(max_length=128, verbose_name="用户ID")
    config = models.ForeignKey(
        "DingTalkConfig",
        on_delete=models.CASCADE,
        related_name="dimission_users",
        verbose_name="所属配置",
        default="default",
    )
    name = models.CharField(max_length=255, blank=True, default="", verbose_name="姓名")
    mobile = models.CharField(max_length=64, blank=True, default="", verbose_name="手机号")
    job_number = models.CharField(max_length=128, blank=True, default="", verbose_name="工号")
    main_dept_id = models.BigIntegerField(null=True, blank=True, verbose_name="主部门ID")
    main_dept_name = models.CharField(max_length=255, blank=True, default="", verbose_name="主部门名称")
    handover_userid = models.CharField(max_length=128, blank=True, default="", verbose_name="交接人用户ID")
    last_work_day = models.DateField(null=True, blank=True, verbose_name="最后工作日")
    leave_time = models.DateTimeField(null=True, blank=True, verbose_name="离职时间")
    leave_reason = models.CharField(max_length=255, blank=True, default="", verbose_name="离职原因")
    reason_type = models.IntegerField(null=True, blank=True, verbose_name="原因类型")
    reason_memo = models.CharField(max_length=1024, blank=True, default="", verbose_name="离职备注")
    pre_status = models.IntegerField(null=True, blank=True, verbose_name="离职前状态")
    status = models.IntegerField(null=True, blank=True, verbose_name="离职状态")
    voluntary_reasons = models.JSONField(default=list, blank=True, verbose_name="主动离职原因")
    passive_reasons = models.JSONField(default=list, blank=True, verbose_name="被动离职原因")
    dept_ids = models.JSONField(default=list, blank=True, verbose_name="历史部门列表")
    source_info = models.JSONField(default=dict, blank=True, verbose_name="原始数据")

    class Meta:
        db_table = "dingtalk_dimission_user"
        verbose_name = "钉钉离职员工"
        verbose_name_plural = verbose_name
        unique_together = ("config", "userid")
        ordering = ("-leave_time", "userid")

    def __str__(self) -> str:  # pragma: no cover - 调试用途
        return f"{self.name or self.userid}({self.config_id})"

