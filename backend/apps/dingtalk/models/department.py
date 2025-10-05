from __future__ import annotations

from django.db import models

from utils.models import BaseModel


class DingTalkDepartment(BaseModel):
    """钉钉部门快照"""

    dept_id = models.BigIntegerField(primary_key=True, verbose_name="部门ID")
    config = models.ForeignKey(
        "DingTalkConfig",
        on_delete=models.CASCADE,
        related_name="departments",
        verbose_name="所属配置",
        default="default",
    )
    name = models.CharField(max_length=255, verbose_name="部门名称")
    parent_id = models.BigIntegerField(null=True, blank=True, verbose_name="父级部门ID")
    order = models.BigIntegerField(null=True, blank=True, verbose_name="排序")
    leader_userid = models.CharField(max_length=128, blank=True, default="", verbose_name="负责人")
    dept_type = models.CharField(max_length=64, blank=True, default="", verbose_name="部门类型")
    source_info = models.JSONField(default=dict, blank=True, verbose_name="原始数据")

    class Meta:
        db_table = "dingtalk_department"
        verbose_name = "钉钉部门"
        verbose_name_plural = verbose_name
        ordering = ("dept_id",)

    def __str__(self) -> str:  # pragma: no cover - 管理界面辅助
        return f"{self.name}({self.dept_id})"
