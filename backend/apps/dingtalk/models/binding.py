from __future__ import annotations

from django.db import models

from utils.models import BaseModel, UuidModel


class DeptBinding(UuidModel, BaseModel):
    """钉钉部门与本地部门绑定关系"""

    config = models.ForeignKey("DingTalkConfig", on_delete=models.CASCADE, related_name="dept_bindings")
    dingtalk_dept = models.ForeignKey("DingTalkDepartment", on_delete=models.CASCADE, related_name="bindings")
    local_dept_code = models.CharField(max_length=128, verbose_name="本地部门标识")

    class Meta:
        db_table = "dingtalk_dept_binding"
        unique_together = ("config", "dingtalk_dept", "local_dept_code")
        verbose_name = "钉钉部门绑定"
        verbose_name_plural = verbose_name


class UserBinding(UuidModel, BaseModel):
    """钉钉用户与本地用户绑定关系"""

    config = models.ForeignKey("DingTalkConfig", on_delete=models.CASCADE, related_name="user_bindings")
    dingtalk_user = models.ForeignKey("DingTalkUser", on_delete=models.CASCADE, related_name="bindings")
    local_user_id = models.CharField(max_length=128, verbose_name="本地用户标识")

    class Meta:
        db_table = "dingtalk_user_binding"
        unique_together = ("config", "dingtalk_user", "local_user_id")
        verbose_name = "钉钉用户绑定"
        verbose_name_plural = verbose_name
