from __future__ import annotations

from django.db import models

from utils.models import BaseModel


class DingTalkUser(BaseModel):
    """钉钉用户快照"""

    userid = models.CharField(primary_key=True, max_length=128, verbose_name="用户ID")
    config = models.ForeignKey(
        "DingTalkConfig",
        on_delete=models.CASCADE,
        related_name="users",
        verbose_name="所属配置",
        default="default",
    )
    name = models.CharField(max_length=255, blank=True, default="", verbose_name="姓名")
    mobile = models.CharField(max_length=64, blank=True, default="", verbose_name="手机号")
    email = models.CharField(max_length=255, blank=True, default="", verbose_name="邮箱")
    active = models.BooleanField(default=True, verbose_name="是否激活")
    job_number = models.CharField(max_length=128, blank=True, default="", verbose_name="工号")
    title = models.CharField(max_length=255, blank=True, default="", verbose_name="职位")
    dept_ids = models.JSONField(default=list, blank=True, verbose_name="所属部门ID列表")
    unionid = models.CharField(max_length=255, blank=True, default="", verbose_name="UnionID")
    remark = models.CharField(max_length=255, blank=True, default="", verbose_name="备注")
    source_info = models.JSONField(default=dict, blank=True, verbose_name="原始数据")

    class Meta:
        db_table = "dingtalk_user"
        verbose_name = "钉钉用户"
        verbose_name_plural = verbose_name
        ordering = ("userid",)

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.name}({self.userid})"
